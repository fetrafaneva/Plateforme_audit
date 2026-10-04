"""Évalue la détection d'anomalies : précision, rappel, F1-score, en
comparant les jours prédits comme anormaux à ceux réellement injectés par
generate_synthetic_data.py (chapitre 9.4 du mémoire).

Inclut une analyse de sensibilité au seuil z (le seuil est un compromis :
plus bas = plus de rappel mais plus de faux positifs, plus haut = l'inverse).

Usage : python evaluer_detection.py
Prérequis : avoir lancé generate_synthetic_data.py pour ID_UTILISATEUR_CIBLE.
"""

from datetime import datetime, timedelta, timezone

import pandas as pd

from app import models  # noqa: F401 — enregistre les modèles sur Base
from app.core.analytics import calculer_baseline_robuste
from app.db.base import SessionLocal
from app.models.audit import JournalAcces

ID_UTILISATEUR_CIBLE = 1
NB_JOURS_HISTORIQUE = 20
# Doit correspondre exactement à JOURS_ANOMALIE dans generate_synthetic_data.py
JOURS_ANOMALIE_INJECTES = {19, 11, 15, 8, 3}
SEUILS_A_TESTER = [2.0, 2.5, 3.0, 3.5]


def calculer_metriques(volumes_par_offset, moyenne, ecart_type, seuil_z):
    vp = fp = vn = fn = 0
    for jour_offset, volume in volumes_par_offset.items():
        z = (volume - moyenne) / ecart_type
        predit_anormal = abs(z) > seuil_z
        reel_anormal = jour_offset in JOURS_ANOMALIE_INJECTES

        if predit_anormal and reel_anormal:
            vp += 1
        elif predit_anormal and not reel_anormal:
            fp += 1
        elif not predit_anormal and reel_anormal:
            fn += 1
        else:
            vn += 1

    precision = vp / (vp + fp) if (vp + fp) > 0 else 0.0
    rappel = vp / (vp + fn) if (vp + fn) > 0 else 0.0
    f1 = 2 * precision * rappel / (precision + rappel) if (precision + rappel) > 0 else 0.0
    return vp, fp, fn, vn, precision, rappel, f1


def evaluer():
    db = SessionLocal()
    try:
        lignes = (
            db.query(JournalAcces)
            .filter(JournalAcces.id_utilisateur == ID_UTILISATEUR_CIBLE)
            .all()
        )
        if not lignes:
            raise SystemExit(
                f"Aucun historique pour l'utilisateur {ID_UTILISATEUR_CIBLE} — "
                "lance generate_synthetic_data.py d'abord."
            )

        df = pd.DataFrame([{"date": ligne.horodatage.date()} for ligne in lignes])
        volume_par_jour = df.groupby("date").size()

        moyenne, ecart_type = calculer_baseline_robuste(volume_par_jour)

        aujourdhui = datetime.now(timezone.utc).date()
        volumes_par_offset = {
            jour_offset: int(volume_par_jour.get(aujourdhui - timedelta(days=jour_offset), 0))
            for jour_offset in range(NB_JOURS_HISTORIQUE, 0, -1)
        }

        print(f"Baseline robuste : moyenne={moyenne:.2f}  écart-type={ecart_type:.2f}\n")

        # --- Détail jour par jour, au seuil par défaut (3.0) ---
        print(f"{'Jour':<8}{'Volume':<8}{'Z-score':<10}{'Prédit (seuil 3.0)':<22}{'Réel':<10}")
        for jour_offset, volume in volumes_par_offset.items():
            z = (volume - moyenne) / ecart_type
            predit_anormal = abs(z) > 3.0
            reel_anormal = jour_offset in JOURS_ANOMALIE_INJECTES
            marqueur = " <-- injecté" if reel_anormal else ""
            print(
                f"J-{jour_offset:<6}{volume:<8}{z:<10.2f}"
                f"{str(predit_anormal):<22}{str(reel_anormal):<10}{marqueur}"
            )

        # --- Sensibilité au seuil ---
        print("\nSensibilité au seuil z :")
        print(f"{'Seuil':<8}{'VP':<5}{'FP':<5}{'FN':<5}{'VN':<5}{'Précision':<12}{'Rappel':<10}{'F1':<6}")
        for seuil in SEUILS_A_TESTER:
            vp, fp, fn, vn, precision, rappel, f1 = calculer_metriques(
                volumes_par_offset, moyenne, ecart_type, seuil
            )
            print(
                f"{seuil:<8}{vp:<5}{fp:<5}{fn:<5}{vn:<5}"
                f"{precision:<12.2f}{rappel:<10.2f}{f1:<6.2f}"
            )
    finally:
        db.close()


if __name__ == "__main__":
    evaluer()