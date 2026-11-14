"""Génération du PDF d'un rapport de mission validé (reportlab).

`construire_pdf(donnees)` reçoit un dictionnaire simple (voir `api/rapports.py`,
fonction `_donnees_pdf`) et renvoie le contenu du PDF en octets. Le module ne
touche ni à la base ni au disque, sauf pour lire les photos dont il reçoit le
chemin et les logos de l'en-tête : il se teste donc seul.

Mise en page d'après le modèle de rapport du MID (Rapport_de_mission.docx) :
en-tête avec les logos du Ministère et de la République, titre, objet, informations générales sous forme
de puces, sections numérotées séparées par un trait gris, tableaux sobres,
photos par district (une par ligne, légende « Figure n : ... »), annexes et
bloc de validation.

Les logos sont lus dans `assets/logos/` à côté de ce fichier :
`logo_ministere.png` (en haut à gauche) et `logo_republique.png` (en haut à droite).
Si un logo est absent, il est simplement omis (le PDF se génère quand même).
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
PROJET = "PROJET MIONJO"
FUSEAU_MADAGASCAR = timezone(timedelta(hours=3))

# Couleurs du modèle : texte gris très foncé, séparateurs gris moyen, tableaux noirs.
COULEUR_TEXTE = colors.HexColor("#262626")
COULEUR_TITRE = colors.HexColor("#1B1B1C")
COULEUR_TRAIT = colors.HexColor("#A6A6A6")
COULEUR_LIGNE = colors.HexColor("#D0D0D0")

MARGE = 2.5 * cm  # marges gauche, droite et bas du modèle
MARGE_HAUT = 1.25 * cm
DOSSIER_LOGOS = Path(__file__).resolve().parent / "assets" / "logos"

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

# (normal, gras, italique, gras italique). Le modèle est en Arial : sous Linux,
# Liberation Sans a exactement les mêmes dimensions. La police fournie avec
# reportlab (Vera) sert de dernier recours : elle est toujours présente.
_CANDIDATS_POLICES = [
    (
        r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\ariali.ttf", r"C:\Windows\Fonts\arialbi.ttf",
    ),
    (
        "/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf",
        "/Library/Fonts/Arial Italic.ttf", "/Library/Fonts/Arial Bold Italic.ttf",
    ),
    (
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf",
    ),
    (
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Italic.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-BoldItalic.ttf",
    ),
    (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
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
    base = dict(fontName=police, fontSize=11, leading=14.5, textColor=COULEUR_TEXTE)
    gras = police + "-Bold"
    return {
        "texte": ParagraphStyle("texte", alignment=TA_JUSTIFY, spaceAfter=7, **base),
        "item": ParagraphStyle("item", alignment=TA_JUSTIFY, spaceAfter=3, **base),
        "vide": ParagraphStyle("vide", **{**base, "textColor": colors.grey}, spaceAfter=6),
        "ministere": ParagraphStyle(
            "ministere", fontName=gras, fontSize=10.5, leading=13.5, alignment=TA_CENTER,
            textColor=COULEUR_TITRE,
        ),
        "titre": ParagraphStyle(
            "titre", fontName=gras, fontSize=11, leading=15, alignment=TA_CENTER,
            textColor=COULEUR_TITRE, spaceBefore=22, spaceAfter=12,
        ),
        "objet": ParagraphStyle(
            "objet", fontName=gras, fontSize=11, leading=15, alignment=TA_JUSTIFY,
            textColor=COULEUR_TEXTE, spaceAfter=4,
        ),
        "h1": ParagraphStyle(
            "h1", fontName=gras, fontSize=12, leading=16, textColor=COULEUR_TITRE,
            spaceAfter=8, keepWithNext=1,
        ),
        "h2": ParagraphStyle(
            "h2", fontName=gras, fontSize=11, leading=15, textColor=COULEUR_TITRE,
            spaceBefore=8, spaceAfter=6, keepWithNext=1,
        ),
        "titre_photos": ParagraphStyle(
            "titre_photos", fontName=gras, fontSize=11, leading=15, textColor=COULEUR_TITRE,
            spaceBefore=16, spaceAfter=8, keepWithNext=1,
        ),
        "cellule": ParagraphStyle(
            "cellule", fontName=police, fontSize=9, leading=11.5, textColor=COULEUR_TEXTE
        ),
        "cellule_gras": ParagraphStyle(
            "cellule_gras", fontName=gras, fontSize=9, leading=11.5, textColor=COULEUR_TEXTE
        ),
        "legende": ParagraphStyle(
            "legende", fontName=police, fontSize=9, leading=12, alignment=TA_CENTER,
            textColor=COULEUR_TEXTE, spaceBefore=4, spaceAfter=18,
        ),
        "signature": ParagraphStyle(
            "signature", fontName=police, fontSize=10, leading=13.5, alignment=TA_CENTER,
            textColor=COULEUR_TEXTE,
        ),
    }


def _tableau_grille(lignes, largeurs):
    """Tableau à bordures noires fines, sans fond (résultats, annexes)."""
    tableau = Table(lignes, colWidths=largeurs, repeatRows=1)
    tableau.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return tableau


def _tableau_leger(lignes, largeurs):
    """Tableau sans bordures verticales : un trait sous l'en-tête, un filet gris entre les lignes."""
    tableau = Table(lignes, colWidths=largeurs, repeatRows=1)
    tableau.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.black),
                ("LINEBELOW", (0, 1), (-1, -1), 0.4, COULEUR_LIGNE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return tableau


# ---------------------------------------------------------------------------
# Blocs de contenu
# ---------------------------------------------------------------------------

_PUCE = re.compile(r"^([-*•]|\d+[.)])\s+")


def _puce(police) -> str:
    glyphes = pdfmetrics.getFont(police).face.charToGlyph
    return "•" if ord("•") in glyphes else "-"


def _decouper(texte):
    """Texte libre -> [("texte", str) | ("liste", [str])] ; les lignes en « - » forment une liste."""
    blocs = []
    for bloc in re.split(r"\n\s*\n", (texte or "").replace("\r", "")):
        lignes = [ligne.strip() for ligne in bloc.split("\n") if ligne.strip()]
        if not lignes:
            continue
        if all(_PUCE.match(ligne) for ligne in lignes):
            blocs.append(("liste", [_PUCE.sub("", ligne) for ligne in lignes]))
        else:
            blocs.append(("texte", "\n".join(lignes)))
    return blocs


def _liste_puces(items, puce="•", retrait=20):
    """Liste à puces (« • » au premier niveau, « o » au second, comme le modèle)."""
    return ListFlowable(
        items,
        bulletType="bullet",
        start=puce,
        leftIndent=retrait,
        bulletFontName=_police(),
        bulletFontSize=10,
    )


def _liste(elements, S, puce="•", retrait=20):
    return _liste_puces([ListItem(Paragraph(_p(e), S["item"])) for e in elements], puce, retrait)


def _bloc_texte(texte, S, police):
    """Texte libre -> paragraphes justifiés ; les lignes commençant par « - » deviennent une liste."""
    blocs = _decouper((texte or "").strip())
    if not blocs:
        return [Paragraph("<i>Non renseigné.</i>", S["vide"])]
    puce = _puce(police)
    return [
        Paragraph(_p(valeur), S["texte"]) if genre == "texte" else _liste(valeur, S, puce)
        for genre, valeur in blocs
    ]


def _item_libelle(libelle, texte, S, police):
    """Puce « **Libellé :** texte », comme dans les sections 3.2, 3.3 et 6 du modèle."""
    etiquette = f"<b>{_p(libelle)} :</b>"
    blocs = _decouper((texte or "").strip())
    if not blocs:
        return ListItem(Paragraph(f"{etiquette} <i>Non renseigné.</i>", S["item"]))

    genre, valeur = blocs[0]
    if genre == "texte":
        contenu = [Paragraph(f"{etiquette} {_p(valeur)}", S["item"])]
        reste = blocs[1:]
    else:
        contenu = [Paragraph(etiquette, S["item"])]
        reste = blocs
    puce = "o"
    for genre, valeur in reste:
        contenu.append(
            Paragraph(_p(valeur), S["item"]) if genre == "texte" else _liste(valeur, S, puce)
        )
    return ListItem(contenu if len(contenu) > 1 else contenu[0])


def _lignes(texte):
    return [_PUCE.sub("", ligne.strip()) for ligne in (texte or "").splitlines() if ligne.strip()]


def _titre(texte, S, niveau=1):
    """Niveau 1 : trait gris puis titre en gras (comme le modèle). Niveau 2 : titre en gras."""
    if niveau == 1:
        trait = HRFlowable(width="100%", thickness=1, color=COULEUR_TRAIT, spaceBefore=6, spaceAfter=12)
        trait.keepWithNext = 1
        return [trait, Paragraph(_p(texte), S["h1"])]
    return [Paragraph(_p(texte), S["h2"])]


def _logo(nom_fichier, hauteur):
    """Logo à la hauteur voulue (largeur proportionnelle), ou None s'il est absent."""
    chemin = DOSSIER_LOGOS / nom_fichier
    try:
        with PILImage.open(chemin) as source:
            largeur_px, hauteur_px = source.size
        return Image(str(chemin), width=hauteur * largeur_px / hauteur_px, height=hauteur)
    except Exception:  # logo absent ou illisible : l'en-tête se passe de lui
        return None


def _entete(S, largeur_page):
    """Logo du Ministère en haut à gauche, logo de la République en haut à droite, texte centré dessous."""
    # Même hauteur pour les deux logos (la largeur suit les proportions de chaque image).
    hauteur_logo = 2.2 * cm
    ministere = _logo("logo_ministere.png", hauteur_logo)
    republique = _logo("logo_republique.png", hauteur_logo)

    texte = [
        Paragraph(_p(MINISTERE), S["ministere"]),
        Paragraph("-----", S["ministere"]),
        Paragraph(_p(PROJET), S["ministere"]),
    ]
    lignes = []
    style = [
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    if ministere is not None or republique is not None:
        lignes.append([ministere or "", "", republique or ""])
        style += [
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ("ALIGN", (2, 0), (2, 0), "RIGHT"),
            ("VALIGN", (0, 0), (-1, 0), "TOP"),
        ]
    ligne_texte = len(lignes)
    lignes.append([texte, "", ""])
    style += [("SPAN", (0, ligne_texte), (-1, ligne_texte)), ("ALIGN", (0, ligne_texte), (-1, ligne_texte), "CENTER")]

    tableau = Table(lignes, colWidths=[4 * cm, largeur_page - 8 * cm, 4 * cm])
    tableau.setStyle(TableStyle(style))
    return tableau


def _image(chemin, largeur_max, hauteur_max):
    """Photo redimensionnée et recompressée (corrige aussi l'orientation EXIF)."""
    try:
        with PILImage.open(chemin) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((1600, 1600))
            tampon = io.BytesIO()
            image.save(tampon, "JPEG", quality=85)
        largeur, hauteur = image.size
        echelle = min(largeur_max / largeur, hauteur_max / hauteur)
        tampon.seek(0)
        return Image(tampon, width=largeur * echelle, height=hauteur * echelle)
    except Exception:  # fichier absent ou illisible : on garde la légende seule
        return None


def _figures(photos, S, largeur_page):
    """Une photo par ligne, centrée, avec sa légende « Figure n : ... » en gras dessous."""
    flux = []
    for numero, photo in enumerate(photos, start=1):
        image = _image(photo.get("chemin"), largeur_page, 12 * cm) if photo.get("chemin") else None
        legende = photo.get("legende") or photo["nom_original"]
        flux.append(
            KeepTogether(
                [
                    image if image is not None else Paragraph("<i>Image non disponible</i>", S["legende"]),
                    Paragraph(f"<b>Figure {numero} : {_p(legende)}</b>", S["legende"]),
                ]
            )
        )
    return flux


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
                self.setFont(police, 8)
                self.setFillColor(colors.HexColor("#666666"))
                self.drawString(MARGE, 1.3 * cm, pied_gauche)
                self.drawRightString(A4[0] - MARGE, 1.3 * cm, f"Page {self._pageNumber} / {total}")
                super().showPage()
            super().save()

    return Numerote


# ---------------------------------------------------------------------------
# Construction du document
# ---------------------------------------------------------------------------


def construire_pdf(d: dict) -> bytes:
    police = _police()
    S = _styles(police)
    puce = _puce(police)
    largeur_page = A4[0] - 2 * MARGE

    axe = d.get("numero_axe") if d.get("numero_axe") is not None else d["id_axe"]
    story = []

    # --- En-tête ---
    story.append(_entete(S, largeur_page))
    if d.get("service_auteur"):
        story.append(Paragraph(_p(d["service_auteur"].upper()), S["ministere"]))
    story.append(Paragraph("RAPPORT DE MISSION", S["titre"]))
    story.append(Paragraph(_p(f"OBJET : {d['titre_mission']}"), S["objet"]))

    # --- Informations générales ---
    story += _titre("Informations générales", S)
    districts = ", ".join(x["nom"] for x in d["districts"]) or "Aucun district rattaché"
    if d.get("periode_debut"):
        periode = f"Du {_date_longue(d['periode_debut'])} au {_date_longue(d['periode_fin'])}"
    else:
        periode = "Non renseignée"

    def ligne_info(libelle, valeur):
        return ListItem(Paragraph(f"<b>{_p(libelle)} :</b> {_p(valeur)}", S["item"]))

    infos = [
        ligne_info("Axe d'intervention", f"Axe {axe}"),
        ligne_info("Districts couverts", districts),
        ligne_info("Période de la mission", periode),
    ]
    if d["membres"]:
        membres = _liste(
            [f"{m['nom']} – {m['fonction'] or 'fonction non précisée'}" for m in d["membres"]],
            S, "o",
        )
        infos.append(
            ListItem([Paragraph("<b>Membres de l'équipe de mission :</b>", S["item"]), membres])
        )
    else:
        infos.append(
            ListItem(
                Paragraph(
                    "<b>Membres de l'équipe de mission :</b> <i>Aucun participant enregistré.</i>",
                    S["item"],
                )
            )
        )
    infos.append(ligne_info("Rédigé par", d["auteur"]))
    story.append(_liste_puces(infos, puce))

    # --- 1 et 2 ---
    story += _titre("1. Contexte", S)
    story += _bloc_texte(d.get("contexte"), S, police)
    story += _titre("2. Justification de la mission", S)
    story += _bloc_texte(d.get("justification"), S, police)

    # --- 3. Déroulement ---
    story += _titre("3. Déroulement des activités et méthodologie", S)
    story += _titre("3.1. Approche organisationnelle et itinéraire suivi", S, 2)
    story.append(
        _liste_puces([ligne_info("Itinéraire réel", d.get("itineraire_reel") or "—")], puce)
    )
    for district in d["districts"]:
        journees = d.get("journees", {}).get(district["id_mission_district"], [])
        bloc = [
            Spacer(1, 6),
            _liste_puces(
                [ListItem(Paragraph(f"<b>Chronogramme réalisé à {_p(district['nom'])} :</b>", S["item"]))],
                puce,
            ),
        ]
        if journees:
            lignes = [
                [
                    Paragraph(t, S["cellule_gras"])
                    for t in (
                        "Date", "Lieu / Établissement", "Activités planifiées",
                        "Activités réellement réalisées", "Écart / Justification si modification",
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
            reste = largeur_page - 2.2 * cm - 2.5 * cm
            bloc.append(
                _tableau_leger(lignes, [2.2 * cm, 2.5 * cm, reste / 3, reste / 3, reste / 3])
            )
        else:
            bloc.append(Paragraph("<i>Aucune journée enregistrée pour ce district.</i>", S["vide"]))
        bloc.append(Spacer(1, 6))
        # Le tableau peut se couper entre deux pages (en-tête répété) ; on évite seulement
        # de laisser le titre seul tout en bas.
        story.append(CondPageBreak(4 * cm))
        story += bloc

    story += _titre("3.2. Travaux techniques réalisés (Opérationnalisation des serveurs)", S, 2)
    story.append(
        _liste_puces(
            [
                _item_libelle("Inventaire du matériel reçu et installé", d.get("inventaire_materiel"), S, police),
                _item_libelle("Configuration technique", d.get("configuration_technique"), S, police),
                _item_libelle("Tests de connectivité et de sécurité", d.get("tests_securite"), S, police),
            ],
            puce,
        )
    )

    story += _titre("3.3. Renforcement de capacités (Formations dispensées)", S, 2)
    nb = d.get("nb_participants_formes")
    story.append(
        _liste_puces(
            [
                ligne_info("Participants formés", nb if nb is not None else "—"),
                ligne_info("Profil des participants", d.get("profil_participants") or "—"),
                _item_libelle("Thèmes abordés", d.get("themes_formation"), S, police),
                _item_libelle("Évaluation de la formation", d.get("evaluation_formation"), S, police),
            ],
            puce,
        )
    )

    # --- 4. Résultats ---
    story += _titre("4. Résultats obtenus et performance", S)
    if d["resultats"]:
        lignes = [
            [
                Paragraph(t, S["cellule_gras"])
                for t in (
                    "Résultat attendu (TDR)", "Indicateur de mesure", "Cible initiale",
                    "Réalisé (réel)", "Taux de réalisation (%)",
                )
            ]
        ]
        for r in d["resultats"]:
            taux = f"{r['taux']:g} %" if r.get("taux") is not None else "—"
            lignes.append(
                [Paragraph(_p(r.get(k) or "—"), S["cellule"]) for k in ("resultat_attendu", "indicateur_mesure", "cible", "realise")]
                + [Paragraph(_p(taux), S["cellule_gras"])]
            )
        story.append(
            _tableau_grille(lignes, [4.3 * cm, 4.5 * cm, 2.1 * cm, 2.1 * cm, largeur_page - 13 * cm])
        )
    else:
        story.append(Paragraph("<i>Aucun indicateur défini pour cette mission.</i>", S["vide"]))

    # --- 5. Difficultés ---
    story += _titre("5. Principales difficultés rencontrées et solutions apportées", S)
    if d["difficultes"]:
        items = []
        for x in d["difficultes"]:
            details = _liste_puces(
                [
                    ListItem(Paragraph(f"<i>Description :</i> {_p(x['description'])}", S["item"])),
                    ListItem(Paragraph(f"<i>Solution apportée :</i> {_p(x.get('solution') or '—')}", S["item"])),
                ],
                "o",
            )
            items.append(ListItem([Paragraph(f"<b>{_p(x['categorie'])} :</b>", S["item"]), details]))
        story.append(
            ListFlowable(
                items,
                bulletType="1",
                bulletFormat="%s.",
                leftIndent=22,
                bulletFontName=police,
                bulletFontSize=10,
            )
        )
    else:
        story.append(Paragraph("<i>Aucune difficulté signalée.</i>", S["vide"]))

    # --- 6. Bilan ---
    story += _titre("6. Points forts, leçons apprises et bonnes pratiques", S)
    story.append(
        _liste_puces(
            [
                _item_libelle("Points forts", d.get("points_forts"), S, police),
                _item_libelle("Leçons apprises", d.get("lecons_apprises"), S, police),
                _item_libelle("Bonnes pratiques", d.get("bonnes_pratiques"), S, police),
            ],
            puce,
        )
    )

    # --- 7. Conclusion ---
    story += _titre("7. Conclusion et recommandations", S)
    story += _titre("7.1. Conclusion générale", S, 2)
    story += _bloc_texte(d.get("conclusion"), S, police)
    story += _titre("7.2. Recommandations à court et moyen terme", S, 2)
    recommandations = _lignes(d.get("recommandations"))
    if recommandations:
        # Dans le modèle, chaque recommandation est un paragraphe commençant par un tiret.
        story += [Paragraph(_p("- " + r), S["texte"]) for r in recommandations]
    else:
        story.append(Paragraph("<i>Non renseigné.</i>", S["vide"]))

    # --- Photos par district ---
    photos = [p for p in d["pieces"] if p["type_piece"] == "photo"]
    for district in d["districts"]:
        du_district = [p for p in photos if p.get("id_mission_district") == district["id_mission_district"]]
        if du_district:
            story.append(
                Paragraph(
                    f"<b><u>Photos de la mission pour le district {_p(district['nom'])}</u></b>",
                    S["titre_photos"],
                )
            )
            story += _figures(du_district, S, largeur_page)

    # --- Annexes ---
    story += _titre("Annexes", S)
    annexes = [p for p in d["pieces"] if p["type_piece"] != "photo"]
    nb_photos = len(photos)
    if annexes or nb_photos:
        lignes = [
            [Paragraph(t, S["cellule_gras"]) for t in ("Pièce", "Fichier", "District", "Empreinte SHA-256")]
        ]
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
        story.append(_tableau_grille(lignes, [3.4 * cm, largeur_page - 11 * cm, 3.6 * cm, 4 * cm]))
    else:
        story.append(Paragraph("<i>Aucune annexe jointe.</i>", S["vide"]))

    # --- Validation et signatures ---
    trait = HRFlowable(width="100%", thickness=1, color=COULEUR_TRAIT, spaceBefore=0, spaceAfter=10)
    validation = [
        Spacer(1, 14),
        trait,
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
    pied = _nettoyer(pied if len(pied) <= 80 else pied[:77] + "...")
    doc = SimpleDocTemplate(
        tampon,
        pagesize=A4,
        leftMargin=MARGE,
        rightMargin=MARGE,
        topMargin=MARGE_HAUT,
        bottomMargin=MARGE,
        title=_nettoyer(f"Rapport de mission – {d['titre_mission']} – axe {axe}"),
        author=_nettoyer(d["auteur"]),
        subject="Rapport de mission validé",
    )
    doc.build(story, canvasmaker=_fabrique_canvas(pied, police))
    return tampon.getvalue()