"""Benchmarking du risque d'accès entre services (3e volet du module d'audit).

Les deux premiers volets répondent à « cette trace est-elle fiable ? » (journal
chaîné) et « cet accès est-il anormal pour cet agent ? » (score d'anomalie).
Celui-ci change d'échelle : il agrège les accès et les alertes **par service**
sur un mois, puis classe les services entre eux pour dire à l'auditeur par où
commencer.

Méthode (volontairement simple et explicable) :

1. Période = un mois calendaire, en heure de Madagascar (UTC+3). Un accès du
   1er novembre à 01h00 locale appartient à novembre, pas à octobre : les bornes
   sont donc calculées en heure locale puis comparées à l'horodatage (stocké
   avec son fuseau).

2. Deux indicateurs par service, jamais un seul :
   - `taux_alertes` = alertes retenues / accès journalisés x 100. Normalisé par
     le volume : sans cela un district à fort trafic serait toujours classé plus
     risqué qu'une petite commune, ce qui serait un biais de volume.
   - `score_risque_moyen` = moyenne des |z-score| des accès analysés. Accompagné
     de `nb_scores`, car tous les accès ne sont pas scorés : une moyenne sur
     3 accès ne vaut pas une moyenne sur 300.
   Les alertes classées « fausse_alerte » sont exclues des deux indicateurs :
   une alerte infirmée par une investigation n'est pas du risque.

3. Comparaison entre services de **même type** (commune avec commune, district
   avec district). Comparer une commune au ministère n'aurait pas de sens.

4. Un service n'est classé que s'il atteint MIN_ACCES_CLASSEMENT accès sur la
   période. En dessous, les deux indicateurs sont trop instables (une seule
   alerte sur 3 accès donne un taux de 33 %) : la ligne est conservée mais son
   rang reste NULL, et le rapport d'audit le dit explicitement.

5. Le résultat est une photographie (snapshot) enregistrée dans
   `benchmarking_services` : on peut donc suivre l'évolution d'un service d'un
   mois sur l'autre. Recalculer une période remplace sa photographie.
"""

import re
from datetime import datetime, timedelta, timezone
from statistics import mean, median

from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload

from app.models.analyse import ScoreAnomalie
from app.models.audit import JournalAcces
from app.models.identity import ServiceCommune, Utilisateur
from app.models.reporting import BenchmarkingService, RapportAudit
from app.models.securite import AlerteSecurite

# Heure de Madagascar : fuseau de référence pour découper les mois.
MADA = timezone(timedelta(hours=3))

# En dessous de ce nombre d'accès sur la période, un service n'est pas classé.
MIN_ACCES_CLASSEMENT = 10

MOTIF_PERIODE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

# Au-delà de ce rapport au taux médian de son type, le service est signalé
# comme nettement au-dessus des autres dans la synthèse d'audit.
FACTEUR_CONTROLE_APPROFONDI = 1.5

# En dessous de ce nombre de services classés dans un type, la médiane du type
# se confond avec le service lui-même : aucune lecture comparative n'est émise.
MIN_SERVICES_COMPARAISON = 2


class PeriodeInvalide(ValueError):
    """Format de période attendu : AAAA-MM (ex. 2026-11)."""


def valider_periode(periode: str) -> str:
    if not MOTIF_PERIODE.match(periode or ""):
        raise PeriodeInvalide(
            "Période attendue au format AAAA-MM (par exemple 2026-11)."
        )
    return periode


def periode_de(moment: datetime) -> str:
    """La période (AAAA-MM) à laquelle appartient un instant, en heure de Madagascar."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(MADA).strftime("%Y-%m")


def periode_courante() -> str:
    return periode_de(datetime.now(timezone.utc))


def bornes_periode(periode: str) -> tuple[datetime, datetime]:
    """Début inclus et fin exclue du mois, en heure de Madagascar."""
    valider_periode(periode)
    annee, mois = int(periode[:4]), int(periode[5:7])
    debut = datetime(annee, mois, 1, tzinfo=MADA)
    if mois == 12:
        fin = datetime(annee + 1, 1, 1, tzinfo=MADA)
    else:
        fin = datetime(annee, mois + 1, 1, tzinfo=MADA)
    return debut, fin


# --------------------------------------------------------------------------
# Agrégats par service
# --------------------------------------------------------------------------


def _agents_par_service(db: Session) -> dict[int, int]:
    """Effectif actif de chaque service (état actuel, pas historisé)."""
    lignes = (
        db.query(Utilisateur.id_service, func.count(Utilisateur.id_utilisateur))
        .filter(Utilisateur.statut == "actif")
        .group_by(Utilisateur.id_service)
        .all()
    )
    return {id_service: nb for id_service, nb in lignes}


def _acces_par_service(
    db: Session, debut: datetime, fin: datetime
) -> dict[int, int]:
    lignes = (
        db.query(Utilisateur.id_service, func.count(JournalAcces.id_entree))
        .select_from(JournalAcces)
        .join(Utilisateur, Utilisateur.id_utilisateur == JournalAcces.id_utilisateur)
        .filter(JournalAcces.horodatage >= debut, JournalAcces.horodatage < fin)
        .group_by(Utilisateur.id_service)
        .all()
    )
    return {id_service: nb for id_service, nb in lignes}


def _scores_par_service(
    db: Session, debut: datetime, fin: datetime
) -> dict[int, tuple[int, float]]:
    """Par service : (nombre d'accès scorés, somme des |z-score|).

    La période est celle de l'accès (`journal_acces.horodatage`), pas celle du
    calcul du score : un score recalculé aujourd'hui sur un accès d'octobre
    reste rattaché à octobre.
    """
    lignes = (
        db.query(
            Utilisateur.id_service,
            func.count(ScoreAnomalie.id_score),
            func.coalesce(func.sum(func.abs(ScoreAnomalie.z_score)), 0.0),
        )
        .select_from(ScoreAnomalie)
        .join(JournalAcces, JournalAcces.id_entree == ScoreAnomalie.id_entree_journal)
        .join(Utilisateur, Utilisateur.id_utilisateur == JournalAcces.id_utilisateur)
        .filter(JournalAcces.horodatage >= debut, JournalAcces.horodatage < fin)
        .group_by(Utilisateur.id_service)
        .all()
    )
    return {
        id_service: (nb, float(somme)) for id_service, nb, somme in lignes
    }


def _alertes_par_service(
    db: Session, debut: datetime, fin: datetime
) -> dict[int, tuple[int, int]]:
    """Par service : (alertes retenues, dont critiques), hors fausses alertes."""
    lignes = (
        db.query(
            Utilisateur.id_service,
            func.count(AlerteSecurite.id_alerte),
            func.count(
                case((AlerteSecurite.niveau_gravite == "critique", 1))
            ),
        )
        .select_from(AlerteSecurite)
        .join(ScoreAnomalie, ScoreAnomalie.id_score == AlerteSecurite.id_score)
        .join(JournalAcces, JournalAcces.id_entree == ScoreAnomalie.id_entree_journal)
        .join(Utilisateur, Utilisateur.id_utilisateur == JournalAcces.id_utilisateur)
        .filter(
            AlerteSecurite.statut != "fausse_alerte",
            JournalAcces.horodatage >= debut,
            JournalAcces.horodatage < fin,
        )
        .group_by(Utilisateur.id_service)
        .all()
    )
    return {
        id_service: (nb, nb_critiques)
        for id_service, nb, nb_critiques in lignes
    }


# --------------------------------------------------------------------------
# Classement
# --------------------------------------------------------------------------


def _cle_risque(ligne: BenchmarkingService) -> tuple[float, float]:
    """Ordre de risque : taux d'alertes d'abord, moyenne des |z| pour départager."""
    return (ligne.taux_alertes, ligne.score_risque_moyen)


def classer(
    lignes: list[BenchmarkingService],
    type_par_service: dict[int, str],
    min_acces: int = MIN_ACCES_CLASSEMENT,
) -> None:
    """Attribue `rang` par type de service. Rang 1 = le plus risqué.

    Les ex æquo partagent le même rang (rang dense), et les services sous le
    seuil d'accès restent sans rang.
    """
    par_type: dict[str, list[BenchmarkingService]] = {}
    for ligne in lignes:
        ligne.rang = None
        if ligne.nb_acces >= min_acces:
            type_service = type_par_service.get(ligne.id_service) or "inconnu"
            par_type.setdefault(type_service, []).append(ligne)

    for groupe in par_type.values():
        cles = {id(ligne): _cle_risque(ligne) for ligne in groupe}
        for ligne in groupe:
            ma_cle = cles[id(ligne)]
            ligne.rang = 1 + sum(
                1 for autre in groupe if cles[id(autre)] > ma_cle
            )


def reperes_par_type(
    lignes: list[BenchmarkingService], type_par_service: dict[int, str]
) -> dict[str, dict[str, float | int]]:
    """Médiane et moyenne des deux indicateurs, par type, sur les services classés.

    Ce sont les repères auxquels un responsable compare son propre service sans
    avoir à voir le détail des autres.
    """
    par_type: dict[str, list[BenchmarkingService]] = {}
    for ligne in lignes:
        if ligne.rang is None:
            continue
        type_service = type_par_service.get(ligne.id_service) or "inconnu"
        par_type.setdefault(type_service, []).append(ligne)

    reperes: dict[str, dict[str, float | int]] = {}
    for type_service, groupe in par_type.items():
        taux = [ligne.taux_alertes for ligne in groupe]
        scores = [ligne.score_risque_moyen for ligne in groupe]
        reperes[type_service] = {
            "nb_services_classes": len(groupe),
            "taux_median": round(median(taux), 2),
            "taux_moyen": round(mean(taux), 2),
            "score_median": round(median(scores), 2),
            "score_moyen": round(mean(scores), 2),
        }
    return reperes


# --------------------------------------------------------------------------
# Calcul de la période
# --------------------------------------------------------------------------


def calculer_benchmark(
    db: Session, periode: str, min_acces: int = MIN_ACCES_CLASSEMENT
) -> list[BenchmarkingService]:
    """Calcule et enregistre la photographie d'une période. Remplace l'ancienne.

    Les services sans agent actif et sans aucun accès sur la période sont
    ignorés : les stocker n'apporterait qu'une ligne vide.
    """
    debut, fin = bornes_periode(periode)

    services = db.query(ServiceCommune).all()
    type_par_service = {s.id_service: s.type for s in services}

    agents = _agents_par_service(db)
    acces = _acces_par_service(db, debut, fin)
    scores = _scores_par_service(db, debut, fin)
    alertes = _alertes_par_service(db, debut, fin)

    lignes: list[BenchmarkingService] = []
    for service in services:
        nb_agents = agents.get(service.id_service, 0)
        nb_acces = acces.get(service.id_service, 0)
        if nb_agents == 0 and nb_acces == 0:
            continue
        nb_scores, somme_z = scores.get(service.id_service, (0, 0.0))
        nb_alertes, nb_critiques = alertes.get(service.id_service, (0, 0))
        lignes.append(
            BenchmarkingService(
                id_service=service.id_service,
                periode=periode,
                nb_agents=nb_agents,
                nb_acces=nb_acces,
                nb_scores=nb_scores,
                nb_alertes=nb_alertes,
                nb_alertes_critiques=nb_critiques,
                taux_alertes=(
                    round(nb_alertes / nb_acces * 100, 2) if nb_acces else 0.0
                ),
                score_risque_moyen=(
                    round(somme_z / nb_scores, 2) if nb_scores else 0.0
                ),
            )
        )

    classer(lignes, type_par_service, min_acces)

    db.query(BenchmarkingService).filter(
        BenchmarkingService.periode == periode
    ).delete(synchronize_session=False)
    db.add_all(lignes)
    db.commit()
    return lignes


def lignes_periode(db: Session, periode: str) -> list[BenchmarkingService]:
    """Les lignes enregistrées pour une période, service chargé, du plus risqué au moins."""
    return (
        db.query(BenchmarkingService)
        .options(joinedload(BenchmarkingService.service))
        .filter(BenchmarkingService.periode == periode)
        .order_by(
            BenchmarkingService.taux_alertes.desc(),
            BenchmarkingService.score_risque_moyen.desc(),
        )
        .all()
    )


def periodes_disponibles(db: Session) -> list[tuple[str, int, datetime]]:
    """(période, nombre de services, date du dernier calcul), de la plus récente à la plus ancienne."""
    lignes = (
        db.query(
            BenchmarkingService.periode,
            func.count(BenchmarkingService.id_benchmark),
            func.max(BenchmarkingService.date_calcul),
        )
        .group_by(BenchmarkingService.periode)
        .order_by(BenchmarkingService.periode.desc())
        .all()
    )
    return [(periode, nb, date) for periode, nb, date in lignes]


# --------------------------------------------------------------------------
# Synthèses d'audit (rapports_audit)
# --------------------------------------------------------------------------


def _ligne_lecture(
    ligne: BenchmarkingService, repere: dict[str, float | int] | None
) -> tuple[str, str]:
    """Phrase de lecture et recommandation, déduites du taux et de la médiane du type."""
    if ligne.rang is None:
        return (
            f"Moins de {MIN_ACCES_CLASSEMENT} accès journalisés sur la période : "
            "les indicateurs ne sont pas assez stables pour un classement.",
            "Aucune conclusion à tirer de cette période pour ce service. "
            "Vérifier que les accès de ce service sont bien journalisés.",
        )
    if repere is None:
        return ("Aucun repère disponible pour ce type de service.", "Aucune action particulière.")

    median_taux = float(repere["taux_median"])
    nb_classes = int(repere["nb_services_classes"])

    if ligne.nb_alertes == 0:
        return ("Aucune alerte retenue sur la période.", "Aucune action particulière.")

    if nb_classes < MIN_SERVICES_COMPARAISON:
        # Un seul service classé dans son type : la médiane du type EST son propre
        # taux. Le comparer à lui-même n'aurait aucun sens.
        return (
            f"Taux d'alertes de {ligne.taux_alertes} pour 100 accès. Seul service de "
            "son type classé sur la période : aucune comparaison possible.",
            "Examiner les alertes du service sur leur seul mérite, sans conclusion "
            "comparative. Pour un classement utile, il faut que les autres services "
            "du même type journalisent aussi leurs accès.",
        )

    # À partir d'ici : le service a des alertes et son type compte au moins deux
    # services classés. Deux situations font qu'il se détache nettement :
    #   - la médiane de son type est nulle, donc la majorité des services
    #     comparables n'a aucune alerte retenue (possible seulement à partir de
    #     trois services classés) ;
    #   - son taux atteint FACTEUR_CONTROLE_APPROFONDI fois la médiane du type.
    median_nulle = median_taux == 0 and nb_classes >= 3
    se_detache = median_nulle or (
        median_taux > 0
        and ligne.taux_alertes >= median_taux * FACTEUR_CONTROLE_APPROFONDI
    )

    # Formulation de la position : sur deux services, la médiane est le milieu des
    # deux valeurs, que ni l'un ni l'autre n'atteint. On compare donc directement.
    if median_nulle:
        position = (
            f"Taux d'alertes de {ligne.taux_alertes} pour 100 accès, alors que la "
            "majorité des services classés de son type n'a aucune alerte retenue."
        )
    elif nb_classes == MIN_SERVICES_COMPARAISON:
        rang_dit = "le plus exposé" if ligne.rang == 1 else "le moins exposé"
        position = (
            f"Taux d'alertes de {ligne.taux_alertes} pour 100 accès : {rang_dit} des "
            f"{nb_classes} services classés de son type."
        )
    elif se_detache:
        position = (
            f"Taux d'alertes de {ligne.taux_alertes} pour 100 accès, soit nettement "
            f"au-dessus de la médiane de son type ({median_taux})."
        )
    elif ligne.taux_alertes > median_taux:
        position = (
            f"Taux d'alertes de {ligne.taux_alertes} pour 100 accès, au-dessus de la "
            f"médiane de son type ({median_taux})."
        )
    else:
        position = (
            f"Taux d'alertes de {ligne.taux_alertes} pour 100 accès, au niveau de la "
            f"médiane de son type ({median_taux}) ou en dessous."
        )

    if se_detache:
        recommandation = "Contrôle approfondi recommandé : examiner les alertes du service"
        recommandation += (
            " et ouvrir une investigation sur les accès critiques."
            if ligne.nb_alertes_critiques
            else " et vérifier si l'écart se confirme à la période suivante."
        )
    elif ligne.taux_alertes > median_taux:
        recommandation = (
            "Surveillance renforcée : à comparer avec la période suivante avant "
            "toute conclusion."
        )
    else:
        recommandation = (
            "Aucune action particulière : des alertes existent mais le service reste "
            "dans la norme de son type."
        )
    return position, recommandation


def texte_synthese(
    ligne: BenchmarkingService,
    type_service: str,
    repere: dict[str, float | int] | None,
) -> str:
    """Synthèse d'audit d'un service, en texte brut (stockée dans rapports_audit.contenu)."""
    nom = ligne.service.nom_service if ligne.service else f"service {ligne.id_service}"
    lecture, recommandation = _ligne_lecture(ligne, repere)

    if ligne.rang is not None and repere is not None:
        nb_classes = int(repere["nb_services_classes"])
        if nb_classes < MIN_SERVICES_COMPARAISON:
            classement = (
                f"Seul service de type « {type_service} » classé sur la période : "
                "le rang n'a pas de valeur comparative."
            )
        else:
            classement = (
                f"Rang {ligne.rang} sur {nb_classes} services "
                f"de type « {type_service} » classés sur la période "
                "(rang 1 = service le plus exposé)."
            )
    else:
        classement = "Service non classé sur cette période."

    moyenne_z = (
        f"{ligne.score_risque_moyen} (moyenne des |z-score| sur {ligne.nb_scores} "
        "accès analysés)"
        if ligne.nb_scores
        else "non calculable (aucun accès analysé sur la période)"
    )

    return "\n".join(
        [
            f"Synthèse d'audit — {nom} ({type_service})",
            f"Période couverte : {ligne.periode}",
            "",
            f"Effectif suivi : {ligne.nb_agents} agent(s) actif(s)",
            f"Accès journalisés : {ligne.nb_acces}",
            f"Alertes retenues : {ligne.nb_alertes}, dont {ligne.nb_alertes_critiques} "
            "critique(s) (fausses alertes exclues)",
            f"Taux d'alertes : {ligne.taux_alertes} pour 100 accès",
            f"Écart comportemental moyen : {moyenne_z}",
            "",
            classement,
            f"Lecture : {lecture}",
            f"Recommandation : {recommandation}",
            "",
            "Document généré automatiquement à partir du journal d'accès chaîné et "
            "des scores d'anomalie de la période. Les indicateurs ne constituent pas "
            "une preuve : ils désignent les services à examiner en priorité.",
        ]
    )


def generer_rapports_audit(db: Session, periode: str) -> list[RapportAudit]:
    """(Re)génère une synthèse d'audit par service pour la période calculée."""
    valider_periode(periode)
    lignes = lignes_periode(db, periode)
    if not lignes:
        return []

    type_par_service = {
        ligne.id_service: (ligne.service.type if ligne.service else "inconnu")
        for ligne in lignes
    }
    reperes = reperes_par_type(lignes, type_par_service)

    db.query(RapportAudit).filter(
        RapportAudit.periode_couverte == periode
    ).delete(synchronize_session=False)

    rapports = [
        RapportAudit(
            id_service=ligne.id_service,
            periode_couverte=periode,
            contenu=texte_synthese(
                ligne,
                type_par_service.get(ligne.id_service) or "inconnu",
                reperes.get(type_par_service.get(ligne.id_service) or "inconnu"),
            ),
        )
        for ligne in lignes
    ]
    db.add_all(rapports)
    db.commit()
    return rapports
