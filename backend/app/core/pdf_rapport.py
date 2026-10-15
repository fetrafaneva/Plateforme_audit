"""Génération du PDF d'un rapport de mission validé (reportlab).

`construire_pdf(donnees)` reçoit un dictionnaire simple (voir `api/rapports.py`,
fonction `_donnees_pdf`) et renvoie le contenu du PDF en octets. Le module ne
touche ni à la base ni au disque, sauf pour lire les photos dont il reçoit le
chemin : il se teste donc seul.

Mise en page d'après le modèle de rapport du MID : en-tête du Ministère, titre,
objet, informations générales, puis sections numérotées, photos par district,
annexes et bloc de validation.
"""

import io
import os
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from PIL import Image as PILImage
from PIL import ImageOps
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    CondPageBreak,
    HRFlowable,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

MINISTERE = "MINISTÈRE DE L'INTÉRIEUR ET DE LA DÉCENTRALISATION"
FUSEAU_MADAGASCAR = timezone(timedelta(hours=3))
COULEUR_TITRE = colors.HexColor("#1F3A5F")
COULEUR_ENTETE_TABLEAU = colors.HexColor("#E8EDF3")
COULEUR_TRAIT = colors.HexColor("#B8C2CF")

MOIS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]
LIBELLES_PIECES = {
    "fiche_reception": "Fiche de réception technique",
    "fiche_presence": "Fiche de présence",
    "photo": "Photo",
    "fiche_evaluation": "Fiche d'évaluation",
    "autre": "Autre pièce",
}
LIBELLES_JOURNEE = {"prevue": "Prévue", "realisee": "Réalisée", "annulee": "Annulée"}

# Caractères que les polices courantes n'ont pas : remplacés plutôt que
# dessinés en carré noir.
SUBSTITUTIONS = {
    "→": "->", "←": "<-", "↔": "<->", "✓": "OK", "✔": "OK", "•": "-",
    "\u200b": "", "\ufeff": "", "\r": "", "\t": " ",
}

# (normal, gras, italique, gras italique). La police fournie avec reportlab
# (Vera) sert de dernier recours : elle est toujours présente.
_CANDIDATS_POLICES = [
    (
        r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\ariali.ttf", r"C:\Windows\Fonts\arialbi.ttf",
    ),
    (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
    ),
    (
        "/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf",
        "/Library/Fonts/Arial Italic.ttf", "/Library/Fonts/Arial Bold Italic.ttf",
    ),
]
_police_enregistree: str | None = None


def _police() -> str:
    global _police_enregistree
    if _police_enregistree:
        return _police_enregistree

    dossier_vera = Path(reportlab.__file__).parent / "fonts"
    candidats = list(_CANDIDATS_POLICES) + [
        tuple(str(dossier_vera / f) for f in ("Vera.ttf", "VeraBd.ttf", "VeraIt.ttf", "VeraBI.ttf"))
    ]
    for i, fichiers in enumerate(candidats):
        if all(os.path.isfile(f) for f in fichiers):
            nom = f"RapportMID{i}"
            for suffixe, fichier in zip(("", "-Bold", "-Italic", "-BoldItalic"), fichiers):
                pdfmetrics.registerFont(TTFont(nom + suffixe, fichier))
            pdfmetrics.registerFontFamily(
                nom, normal=nom, bold=nom + "-Bold", italic=nom + "-Italic",
                boldItalic=nom + "-BoldItalic",
            )
            _police_enregistree = nom
            return nom
    raise RuntimeError("Aucune police TrueType utilisable pour générer le PDF")


# ---------------------------------------------------------------------------
# Texte
# ---------------------------------------------------------------------------


def _nettoyer(texte) -> str:
    if texte is None:
        return ""
    texte = str(texte)
    for ancien, nouveau in SUBSTITUTIONS.items():
        texte = texte.replace(ancien, nouveau)
    glyphes = pdfmetrics.getFont(_police()).face.charToGlyph
    return "".join(c if c == "\n" or ord(c) in glyphes else "?" for c in texte)


def _p(texte) -> str:
    """Texte brut -> balisage de Paragraph (échappé, retours à la ligne conservés)."""
    return escape(_nettoyer(texte)).replace("\n", "<br/>")


def _date_courte(valeur) -> str:
    if isinstance(valeur, datetime):
        valeur = valeur.astimezone(FUSEAU_MADAGASCAR) if valeur.tzinfo else valeur
    return valeur.strftime("%d/%m/%Y") if valeur else "—"


def _date_longue(valeur) -> str:
    if not valeur:
        return "—"
    if isinstance(valeur, datetime):
        valeur = valeur.astimezone(FUSEAU_MADAGASCAR) if valeur.tzinfo else valeur
    return f"{valeur.day} {MOIS[valeur.month - 1]} {valeur.year}"


def _date_heure(valeur) -> str:
    if not valeur:
        return "—"
    local = valeur.astimezone(FUSEAU_MADAGASCAR) if valeur.tzinfo else valeur
    return local.strftime("%d/%m/%Y à %H:%M")


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------


def _styles(police: str) -> dict[str, ParagraphStyle]:
    base = dict(fontName=police, fontSize=10, leading=14)
    return {
        "texte": ParagraphStyle("texte", alignment=TA_JUSTIFY, spaceAfter=6, **base),
        "vide": ParagraphStyle("vide", textColor=colors.grey, spaceAfter=6, **base),
        "ministere": ParagraphStyle(
            "ministere", fontName=police + "-Bold", fontSize=11, leading=15, alignment=TA_CENTER
        ),
        "service": ParagraphStyle(
            "service", fontName=police, fontSize=9, leading=12, alignment=TA_CENTER
        ),
        "titre": ParagraphStyle(
            "titre", fontName=police + "-Bold", fontSize=20, leading=24, alignment=TA_CENTER,
            textColor=COULEUR_TITRE, spaceBefore=14, spaceAfter=8,
        ),
        "objet": ParagraphStyle(
            "objet", fontName=police + "-Bold", fontSize=11, leading=15, alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "h1": ParagraphStyle(
            "h1", fontName=police + "-Bold", fontSize=13, leading=17, textColor=COULEUR_TITRE,
            spaceBefore=14, spaceAfter=2, keepWithNext=1,
        ),
        "h2": ParagraphStyle(
            "h2", fontName=police + "-Bold", fontSize=11, leading=15, textColor=COULEUR_TITRE,
            spaceBefore=8, spaceAfter=4, keepWithNext=1,
        ),
        # Étiquette en gras placée au-dessus d'un texte : ne reste jamais seule en bas de page
        "etiquette": ParagraphStyle(
            "etiquette", fontName=police + "-Bold", fontSize=10, leading=14, spaceAfter=2,
            keepWithNext=1,
        ),
        "cellule": ParagraphStyle("cellule", fontName=police, fontSize=8.5, leading=11),
        "cellule_gras": ParagraphStyle(
            "cellule_gras", fontName=police + "-Bold", fontSize=8.5, leading=11
        ),
        "legende": ParagraphStyle(
            "legende", fontName=police, fontSize=8, leading=10, alignment=TA_CENTER,
            textColor=colors.HexColor("#444444"), spaceBefore=2, spaceAfter=6,
        ),
        "signature": ParagraphStyle(
            "signature", fontName=police, fontSize=9.5, leading=13, alignment=TA_CENTER
        ),
    }


def _tableau(lignes, largeurs, style_extra=()):
    tableau = Table(lignes, colWidths=largeurs, repeatRows=1)
    tableau.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COULEUR_ENTETE_TABLEAU),
                ("GRID", (0, 0), (-1, -1), 0.5, COULEUR_TRAIT),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                *style_extra,
            ]
        )
    )
    return tableau


# ---------------------------------------------------------------------------
# Blocs de contenu
# ---------------------------------------------------------------------------

_PUCE = re.compile(r"^([-*•]|\d+[.)])\s+")


def _bloc_texte(texte, S, police):
    """Texte libre -> paragraphes ; les lignes commençant par « - » deviennent une liste."""
    texte = (texte or "").strip()
    if not texte:
        return [Paragraph("<i>Non renseigné.</i>", S["vide"])]

    glyphes = pdfmetrics.getFont(police).face.charToGlyph
    puce = "•" if ord("•") in glyphes else "-"

    flux = []
    for bloc in re.split(r"\n\s*\n", texte.replace("\r", "")):
        lignes = [ligne.strip() for ligne in bloc.split("\n") if ligne.strip()]
        if not lignes:
            continue
        if all(_PUCE.match(ligne) for ligne in lignes):
            flux.append(_liste([_PUCE.sub("", ligne) for ligne in lignes], S, puce))
        else:
            flux.append(Paragraph(_p("\n".join(lignes)), S["texte"]))
    return flux


def _liste(elements, S, puce="•"):
    return ListFlowable(
        [ListItem(Paragraph(_p(e), S["texte"]), leftIndent=14) for e in elements],
        bulletType="bullet",
        start=puce,
        leftIndent=14,
        bulletFontName=_police(),
    )


def _lignes(texte):
    return [_PUCE.sub("", ligne.strip()) for ligne in (texte or "").splitlines() if ligne.strip()]


def _titre(texte, S, niveau=1):
    if niveau == 1:
        trait = HRFlowable(width="100%", thickness=0.6, color=COULEUR_TRAIT, spaceAfter=6)
        trait.keepWithNext = 1
        return [Paragraph(_p(texte), S["h1"]), trait]
    return [Paragraph(_p(texte), S["h2"])]


def _image(chemin, largeur_max, hauteur_max):
    """Photo redimensionnée et recompressée (corrige aussi l'orientation EXIF)."""
    try:
        with PILImage.open(chemin) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((1400, 1400))
            tampon = io.BytesIO()
            image.save(tampon, "JPEG", quality=85)
        largeur, hauteur = image.size
        echelle = min(largeur_max / largeur, hauteur_max / hauteur)
        tampon.seek(0)
        return Image(tampon, width=largeur * echelle, height=hauteur * echelle)
    except Exception:  # fichier absent ou illisible : on garde la légende seule
        return None


def _grille_photos(photos, S, largeur_page):
    colonne = largeur_page / 2
    cellules = []
    for photo in photos:
        contenu = []
        image = _image(photo.get("chemin"), colonne - 14, 6.2 * cm) if photo.get("chemin") else None
        if image is not None:
            contenu.append(image)
        else:
            contenu.append(Paragraph("<i>Image non disponible</i>", S["legende"]))
        contenu.append(Paragraph(_p(photo.get("legende") or photo["nom_original"]), S["legende"]))
        cellules.append(contenu)

    lignes = [cellules[i:i + 2] for i in range(0, len(cellules), 2)]
    if lignes and len(lignes[-1]) == 1:
        lignes[-1].append("")
    tableau = Table(lignes, colWidths=[colonne, colonne])
    tableau.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return tableau


def _fabrique_canvas(pied_gauche: str, police: str):
    """Canvas qui ajoute « Page i / n » : le nombre total n'est connu qu'à la fin."""

    class Numerote(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._etats = []

        def showPage(self):
            self._etats.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._etats)
            for etat in self._etats:
                self.__dict__.update(etat)
                self.setStrokeColor(COULEUR_TRAIT)
                self.setLineWidth(0.5)
                self.line(2 * cm, 1.7 * cm, A4[0] - 2 * cm, 1.7 * cm)
                self.setFont(police, 8)
                self.setFillColor(colors.HexColor("#555555"))
                self.drawString(2 * cm, 1.2 * cm, pied_gauche)
                self.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {self._pageNumber} / {total}")
                super().showPage()
            super().save()

    return Numerote


# ---------------------------------------------------------------------------
# Construction du document
# ---------------------------------------------------------------------------


def construire_pdf(d: dict) -> bytes:
    police = _police()
    S = _styles(police)
    largeur_page = A4[0] - 4 * cm

    axe = d.get("numero_axe") if d.get("numero_axe") is not None else d["id_axe"]
    story = []

    # --- En-tête ---
    story.append(Paragraph(_p(MINISTERE), S["ministere"]))
    story.append(Paragraph("-----", S["service"]))
    if d.get("service_auteur"):
        story.append(Paragraph(_p(d["service_auteur"].upper()), S["service"]))
    story.append(Paragraph("RAPPORT DE MISSION", S["titre"]))
    story.append(Paragraph(_p(f"OBJET : {d['titre_mission']}"), S["objet"]))

    # --- Informations générales ---
    story += _titre("Informations générales", S)
    districts = ", ".join(x["nom"] for x in d["districts"]) or "Aucun district rattaché"
    if d.get("periode_debut"):
        periode = f"Du {_date_longue(d['periode_debut'])} au {_date_longue(d['periode_fin'])}"
    else:
        periode = "Non renseignée"
    infos = [
        ("Axe d'intervention :", f"Axe {axe}"),
        ("Districts couverts :", districts),
        ("Période de la mission :", periode),
        ("Rédigé par :", d["auteur"]),
    ]
    lignes = [
        [Paragraph(_p(k), S["cellule_gras"]), Paragraph(_p(v), S["cellule"])] for k, v in infos
    ]
    tableau = Table(lignes, colWidths=[4.5 * cm, largeur_page - 4.5 * cm])
    tableau.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    story.append(tableau)
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Membres de l'équipe de mission :</b>", S["cellule"]))
    if d["membres"]:
        story.append(
            _liste(
                [f"{m['nom']} – {m['fonction'] or 'fonction non précisée'}" for m in d["membres"]],
                S,
            )
        )
    else:
        story.append(Paragraph("<i>Aucun participant enregistré.</i>", S["vide"]))

    # --- 1 et 2 ---
    story += _titre("1. Contexte", S)
    story += _bloc_texte(d.get("contexte"), S, police)
    story += _titre("2. Justification de la mission", S)
    story += _bloc_texte(d.get("justification"), S, police)

    # --- 3. Déroulement ---
    story += _titre("3. Déroulement des activités et méthodologie", S)
    story += _titre("3.1. Itinéraire suivi", S, 2)
    story.append(Paragraph(f"<b>Itinéraire réel :</b> {_p(d.get('itineraire_reel') or '—')}", S["texte"]))
    for district in d["districts"]:
        journees = d.get("journees", {}).get(district["id_mission_district"], [])
        bloc = [Paragraph(f"<b>Chronogramme réalisé à {_p(district['nom'])} :</b>", S["texte"])]
        if journees:
            lignes = [
                [
                    Paragraph(f"<b>{t}</b>", S["cellule"])
                    for t in (
                        "Date", "Lieu / Établissement", "Activités planifiées",
                        "Activités réellement réalisées", "Écart / Justification",
                    )
                ]
            ]
            for j in journees:
                date_txt = _date_courte(j.get("date"))
                if j.get("statut") not in (None, "realisee"):
                    etat = LIBELLES_JOURNEE.get(j["statut"], j["statut"]).lower()
                    date_txt += f"\n({etat})"
                lignes.append(
                    [
                        Paragraph(_p(date_txt), S["cellule"]),
                        Paragraph(_p(j.get("lieu") or "—"), S["cellule"]),
                        Paragraph(_p(j.get("activites_prevues") or "—"), S["cellule"]),
                        Paragraph(_p(j.get("activites_realisees") or "—"), S["cellule"]),
                        Paragraph(_p(j.get("ecart") or "—"), S["cellule"]),
                    ]
                )
            reste = largeur_page - 2.3 * cm - 2.7 * cm
            bloc.append(
                _tableau(lignes, [2.3 * cm, 2.7 * cm, reste / 3, reste / 3, reste / 3])
            )
        else:
            bloc.append(Paragraph("<i>Aucune journée enregistrée pour ce district.</i>", S["vide"]))
        bloc.append(Spacer(1, 6))
        # Le tableau peut se couper entre deux pages (en-tête répété) ; on évite seulement
        # de laisser le titre seul tout en bas.
        story.append(CondPageBreak(4 * cm))
        story += bloc

    story += _titre("3.2. Travaux techniques réalisés", S, 2)
    for etiquette, cle in (
        ("Inventaire du matériel", "inventaire_materiel"),
        ("Configuration technique", "configuration_technique"),
        ("Tests de connectivité et de sécurité", "tests_securite"),
    ):
        story.append(Paragraph(_p(etiquette), S["etiquette"]))
        story += _bloc_texte(d.get(cle), S, police)

    story += _titre("3.3. Renforcement de capacités", S, 2)
    nb = d.get("nb_participants_formes")
    story.append(Paragraph(f"<b>Participants formés :</b> {nb if nb is not None else '—'}", S["texte"]))
    story.append(Paragraph(f"<b>Profil des participants :</b> {_p(d.get('profil_participants') or '—')}", S["texte"]))
    story.append(Paragraph("Thèmes abordés", S["etiquette"]))
    story += _bloc_texte(d.get("themes_formation"), S, police)
    story.append(Paragraph("Évaluation de la formation", S["etiquette"]))
    story += _bloc_texte(d.get("evaluation_formation"), S, police)

    # --- 4. Résultats ---
    story += _titre("4. Résultats obtenus et performance", S)
    if d["resultats"]:
        lignes = [[Paragraph(f"<b>{t}</b>", S["cellule"]) for t in ("Résultat attendu", "Indicateur", "Cible", "Réalisé", "Taux")]]
        for r in d["resultats"]:
            taux = f"{r['taux']:g} %" if r.get("taux") is not None else "—"
            lignes.append(
                [Paragraph(_p(r.get(k) or "—"), S["cellule"]) for k in ("resultat_attendu", "indicateur_mesure", "cible", "realise")]
                + [Paragraph(_p(taux), S["cellule_gras"])]
            )
        reste = largeur_page - 2 * 2.2 * cm - 2.2 * cm
        story.append(_tableau(lignes, [reste * 0.55, reste * 0.45, 2.2 * cm, 2.2 * cm, 2.2 * cm]))
    else:
        story.append(Paragraph("<i>Aucun indicateur défini pour cette mission.</i>", S["vide"]))

    # --- 5. Difficultés ---
    story += _titre("5. Difficultés rencontrées et solutions apportées", S)
    if d["difficultes"]:
        lignes = [[Paragraph(f"<b>{t}</b>", S["cellule"]) for t in ("Catégorie", "Difficulté", "Solution apportée")]]
        for x in d["difficultes"]:
            lignes.append(
                [
                    Paragraph(_p(x["categorie"]), S["cellule_gras"]),
                    Paragraph(_p(x["description"]), S["cellule"]),
                    Paragraph(_p(x.get("solution") or "—"), S["cellule"]),
                ]
            )
        story.append(_tableau(lignes, [3 * cm, (largeur_page - 3 * cm) / 2, (largeur_page - 3 * cm) / 2]))
    else:
        story.append(Paragraph("<i>Aucune difficulté signalée.</i>", S["vide"]))

    # --- 6. Bilan ---
    story += _titre("6. Points forts, leçons apprises et bonnes pratiques", S)
    for etiquette, cle in (
        ("Points forts", "points_forts"),
        ("Leçons apprises", "lecons_apprises"),
        ("Bonnes pratiques", "bonnes_pratiques"),
    ):
        story.append(Paragraph(_p(etiquette), S["etiquette"]))
        story += _bloc_texte(d.get(cle), S, police)

    # --- 7. Conclusion ---
    story += _titre("7. Conclusion et recommandations", S)
    story.append(Paragraph("Conclusion générale", S["etiquette"]))
    story += _bloc_texte(d.get("conclusion"), S, police)
    story.append(Paragraph("Recommandations", S["etiquette"]))
    recommandations = _lignes(d.get("recommandations"))
    if recommandations:
        story.append(_liste(recommandations, S))
    else:
        story.append(Paragraph("<i>Non renseigné.</i>", S["vide"]))

    # --- Photos par district ---
    photos = [p for p in d["pieces"] if p["type_piece"] == "photo"]
    if photos:
        story += _titre("Photos de la mission", S)
        for district in d["districts"]:
            du_district = [p for p in photos if p.get("id_mission_district") == district["id_mission_district"]]
            if du_district:
                story.append(Paragraph(_p(district["nom"]), S["etiquette"]))
                story.append(_grille_photos(du_district, S, largeur_page))

    # --- Annexes ---
    story += _titre("Annexes", S)
    annexes = [p for p in d["pieces"] if p["type_piece"] != "photo"]
    nb_photos = len(photos)
    if annexes or nb_photos:
        lignes = [[Paragraph(f"<b>{t}</b>", S["cellule"]) for t in ("Pièce", "Fichier", "District", "Empreinte SHA-256")]]
        for p in annexes:
            lignes.append(
                [
                    Paragraph(_p(LIBELLES_PIECES.get(p["type_piece"], p["type_piece"])), S["cellule"]),
                    Paragraph(_p(p["nom_original"]), S["cellule"]),
                    Paragraph(_p(p.get("nom_district") or "Tout l'axe"), S["cellule"]),
                    Paragraph(_p(p["empreinte_sha256"][:16] + "…"), S["cellule"]),
                ]
            )
        if nb_photos:
            lignes.append(
                [
                    Paragraph("Photos", S["cellule"]),
                    Paragraph(_p(f"{nb_photos} photo(s), reproduites ci-dessus"), S["cellule"]),
                    Paragraph("Par district", S["cellule"]),
                    Paragraph("—", S["cellule"]),
                ]
            )
        story.append(_tableau(lignes, [4 * cm, largeur_page - 4 * cm - 4.2 * cm - 3.4 * cm, 4.2 * cm, 3.4 * cm]))
    else:
        story.append(Paragraph("<i>Aucune annexe jointe.</i>", S["vide"]))

    # --- Validation et signatures ---
    validation = [
        Spacer(1, 14),
        Paragraph(
            _p(
                f"Rapport soumis le {_date_heure(d.get('date_soumission'))} et validé par "
                f"{d.get('nom_validateur') or '—'} le {_date_heure(d.get('date_validation'))}."
            ),
            S["texte"],
        ),
        Spacer(1, 8),
    ]
    signatures = Table(
        [
            [
                Paragraph(_p(f"Le chef de mission,\n\n\n\n{d['auteur']}"), S["signature"]),
                Paragraph(_p(f"Le validateur,\n\n\n\n{d.get('nom_validateur') or ''}"), S["signature"]),
            ]
        ],
        colWidths=[largeur_page / 2, largeur_page / 2],
    )
    validation.append(signatures)
    story.append(KeepTogether(validation))

    tampon = io.BytesIO()
    pied = f"Rapport de mission n°{d['id']}, axe {axe} – {d['titre_mission']}"
    pied = _nettoyer(pied if len(pied) <= 95 else pied[:92] + "...")
    doc = SimpleDocTemplate(
        tampon,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=2.2 * cm,
        title=_nettoyer(f"Rapport de mission – {d['titre_mission']} – axe {axe}"),
        author=_nettoyer(d["auteur"]),
        subject="Rapport de mission validé",
    )
    doc.build(story, canvasmaker=_fabrique_canvas(pied, police))
    return tampon.getvalue()