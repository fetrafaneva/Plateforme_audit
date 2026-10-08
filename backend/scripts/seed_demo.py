"""Réinitialise la base `audit_comportemental` et y insère un jeu de données de démonstration.

Usage, depuis le dossier backend/ avec le venv activé :
    python -m scripts.seed_demo

ATTENTION : efface TOUTES les données des tables de l'application, y compris
celles du module d'audit. Les mots de passe ci-dessous sont des mots de passe
de démonstration : à ne jamais utiliser sur une plateforme déployée en ligne.
Les noms de personnes et les valeurs de résultats sont fictifs.
"""
from datetime import date, datetime

from sqlalchemy import text

import app.models  # noqa: F401  (enregistre toutes les tables sur Base.metadata)
from app.core.security import hash_password
from app.db.base import Base, SessionLocal, engine
from app.models.identity import Role, ServiceCommune, Utilisateur
from app.models.missions import (
    Axe,
    District,
    Equipe,
    IndicateurPerformance,
    Journee,
    Livrable,
    Mission,
    MissionDistrict,
    Participant,
    Phase,
    TypeActivite,
)

BASE_ATTENDUE = "audit_comportemental"
MOT_DE_PASSE_DEMO = "Demo2026!"


def effacer(db):
    """Vide toutes les tables déclarées dans les modèles (alembic_version n'est pas touchée)."""
    noms = [t.name for t in Base.metadata.sorted_tables]
    liste = ", ".join(f'"{nom}"' for nom in noms)
    db.execute(text(f"TRUNCATE TABLE {liste} RESTART IDENTITY CASCADE"))


def ajouter(db, objet):
    db.add(objet)
    db.flush()
    return objet


def semer(db):
    # ---------- Rôles ----------
    roles = {}
    for nom, niveau in [
        ("administrateur", "total"),
        ("chef_mission", "mission"),
        ("technicien", "mission"),
        ("agent", "standard"),
        ("auditeur", "audit"),
        ("responsable_hierarchique", "supervision"),
    ]:
        roles[nom] = ajouter(db, Role(nom_role=nom, niveau_acces=niveau))

    # ---------- Services ----------
    mid = ajouter(db, ServiceCommune(
        nom_service="Ministère de l'Intérieur et de la Décentralisation", type="ministere"))
    dsid = ajouter(db, ServiceCommune(
        nom_service="Direction du Système d'Information et de la Digitalisation",
        type="ministere", id_service_parent=mid.id_service))
    dgddl = ajouter(db, ServiceCommune(
        nom_service="Direction Générale de la Décentralisation et du Développement Local",
        type="ministere", id_service_parent=mid.id_service))
    dist_ambovombe = ajouter(db, ServiceCommune(
        nom_service="District d'Ambovombe", type="district",
        id_service_parent=dgddl.id_service))

    # ---------- Utilisateurs ----------
    mdp_hash = hash_password(MOT_DE_PASSE_DEMO)
    definitions = [
        ("Faneva", "Fetra", "faneva@gmail.com", "1174 H-F", "administrateur", dsid),
        ("Rakoto", "Hery", "chef@test.mg", "CHEF001", "chef_mission", dsid),
        ("Randria", "Mamy", "tech@test.mg", "TECH001", "technicien", dsid),
        ("Razafy", "Tiana", "agent@test.mg", "AGT001", "agent", dist_ambovombe),
        ("Rabe", "Fanja", "auditeur@test.mg", "AUD001", "auditeur", dsid),
        ("Ravelo", "Mahefa", "responsable@test.mg", "RESP001", "responsable_hierarchique", dgddl),
    ]
    utilisateurs = {}
    for nom, prenom, email, matricule, role, service in definitions:
        utilisateurs[role] = ajouter(db, Utilisateur(
            nom=nom, prenom=prenom, email=email, matricule=matricule,
            mot_de_passe_hash=mdp_hash,
            id_service=service.id_service, id_role=roles[role].id_role,
            statut="actif",
        ))
    chef = utilisateurs["chef_mission"]
    tech = utilisateurs["technicien"]

    # ---------- Types d'activité ----------
    types = {}
    for libelle in [
        "Installation du serveur",
        "Formation à l'administration serveur",
        "Formation SII CSB et gestion des documents",
        "Déploiement du logiciel",
        "Installation de générateur solaire",
    ]:
        types[libelle] = ajouter(db, TypeActivite(libelle=libelle))

    # ---------- Districts (les 16 districts cibles du TDR SII CSB) ----------
    # La région d'Antanimora n'est pas renseignée : à vérifier avant publication.
    districts = {}
    for nom, region in [
        ("Toliara I", "Atsimo-Andrefana"), ("Toliara II", "Atsimo-Andrefana"),
        ("Morombe", "Atsimo-Andrefana"), ("Ankazoabo", "Atsimo-Andrefana"),
        ("Beroroha", "Atsimo-Andrefana"), ("Betioky", "Atsimo-Andrefana"),
        ("Ampanihy", "Atsimo-Andrefana"), ("Benenitra", "Atsimo-Andrefana"),
        ("Taolagnaro", "Anosy"), ("Amboasary", "Anosy"), ("Betroka", "Anosy"),
        ("Antanimora", None),
        ("Ambovombe", "Androy"), ("Tsihombe", "Androy"),
        ("Beloha", "Androy"), ("Bekily", "Androy"),
    ]:
        districts[nom] = ajouter(db, District(nom=nom, region=region, province="Toliara"))

    # ---------- Mission 1 : déploiement SII CSB (terminée) ----------
    m1 = ajouter(db, Mission(
        titre="Opérationnalisation des serveurs districts et déploiement du SII CSB",
        type_mission="deploiement_serveur",
        date_debut=datetime(2026, 9, 5), date_fin_prevue=datetime(2026, 10, 4),
        statut="terminee"))

    axes_m1 = [
        (1, "Tanà → Toliara → Morombe → Ankazoabo → Beroroha → Tanà",
         ["Toliara II", "Morombe", "Ankazoabo", "Beroroha"],
         [("DSID", [
             ("Rakoto Hery", "Chef de mission / Coordinateur technique", chef),
             ("Randria Mamy", "Technicien infrastructure serveur", tech),
             ("Rasoanaivo Lova", "Technicien réseau", None)]),
          ("SI CSB", [("Andrianina Solo", "Formateur certifié SII CSB", None)])]),
        (2, "Tanà → Toliara → Betioky → Ampanihy → Benenitra → Tanà",
         ["Toliara I", "Betioky", "Ampanihy", "Benenitra"],
         [("DSID", [
             ("Rakotomalala Njaka", "Chef de mission / Coordinateur technique", None),
             ("Rasolofo Tahiry", "Technicien infrastructure serveur", None),
             ("Ranaivo Lalaina", "Technicien réseau", None)])]),
        (3, "Tanà → Taolagnaro → Amboasary → Antanimora → Betroka → Tanà",
         ["Taolagnaro", "Amboasary", "Antanimora", "Betroka"],
         [("DSID", [
             ("Randrianasolo Fidy", "Chef de mission", None),
             ("Razanakoto Nirina", "Technicien réseau", None)]),
          ("MATSF", [("Rabemanana Tsiory", "Technicien infrastructure serveur", None)])]),
        (4, "Tanà → Ambovombe → Tsihombe → Beloha → Bekily → Tanà",
         ["Ambovombe", "Tsihombe", "Beloha", "Bekily"],
         [("DSID", [
             ("Rasamimanana Hanta", "Chef de mission", None),
             ("Ratsimba Koloina", "Technicien réseau", None)]),
          ("INDDL", [("Randriamihaja Zo", "Formateur", None)])]),
    ]

    md_ambovombe = None
    for numero, itineraire, noms_districts, equipes in axes_m1:
        axe = ajouter(db, Axe(
            mission_id=m1.id, numero_axe=numero, itineraire_principal=itineraire))
        for ordre, nom_district in enumerate(noms_districts, start=1):
            md = ajouter(db, MissionDistrict(
                axe_id=axe.id, district_id=districts[nom_district].id,
                ordre_visite=ordre, statut="termine"))
            if nom_district == "Ambovombe":
                md_ambovombe = md
        for type_equipe, participants in equipes:
            equipe = ajouter(db, Equipe(axe_id=axe.id, type_equipe=type_equipe))
            for nom, fonction, compte in participants:
                ajouter(db, Participant(
                    equipe_id=equipe.id, nom=nom, fonction=fonction,
                    id_utilisateur=compte.id_utilisateur if compte else None))

    # Séquence d'intervention détaillée pour Ambovombe (phases, journées, livrables)
    phases = []
    for ordre, (type_libelle, duree, livrable) in enumerate([
        ("Installation du serveur", "J1-J2", "Serveur branché, alimenté, configuré et sécurisé"),
        ("Formation à l'administration serveur", "J3-J4", "PV de formation signé"),
        ("Déploiement du logiciel", "J5", "Logiciel déployé et fonctionnel"),
    ], start=1):
        phases.append(ajouter(db, Phase(
            mission_district_id=md_ambovombe.id,
            type_activite_id=types[type_libelle].id,
            numero_ordre=ordre, duree_prevue=duree,
            livrable_attendu=livrable, statut="terminee")))

    for jour in range(1, 6):
        ajouter(db, Journee(
            mission_district_id=md_ambovombe.id, numero_jour=jour,
            date=date(2026, 9, 9 + jour), lieu="Ambovombe", statut="realisee"))

    ajouter(db, Livrable(
        phase_id=phases[0].id, type_livrable="PV d'installation du serveur",
        date_production=datetime(2026, 9, 11), signe=True))
    ajouter(db, Livrable(
        phase_id=phases[1].id, type_livrable="PV de formation signé",
        date_production=datetime(2026, 9, 13), signe=True))

    for resultat, indicateur, cible, realise in [
        ("Serveurs installés et opérationnels",
         "Nombre de serveurs configurés / total prévu", "16/16 (100%)", "16/16"),
        ("SII CSB déployé et fonctionnel",
         "Nombre de logiciels actifs / total districts", "16/16 (100%)", "15/16"),
        ("Agents formés et certifiés",
         "Nombre d'agents formés par district", "≥ 1 SI CSB / district", "≥ 1 dans 14 districts"),
        ("Rapports d'intervention produits",
         "Nombre de PV signés / districts visités", "16/16 (100%)", "16/16"),
        ("Mission réalisée dans les délais",
         "Date de retour effective vs. planifiée", "≤ J+29", "J+28"),
    ]:
        ajouter(db, IndicateurPerformance(
            mission_id=m1.id, resultat_attendu=resultat,
            indicateur_mesure=indicateur, cible=cible, valeur_realisee=realise))

    # ---------- Mission 2 : formation (en cours) ----------
    m2 = ajouter(db, Mission(
        titre="Formation des agents à l'administration des serveurs",
        type_mission="formation",
        date_debut=datetime(2026, 10, 1), date_fin_prevue=datetime(2026, 11, 13),
        statut="en_cours"))
    axe_m2 = ajouter(db, Axe(
        mission_id=m2.id, numero_axe=1, itineraire_principal="Tanà → Toliara → Tanà"))
    md_t1 = ajouter(db, MissionDistrict(
        axe_id=axe_m2.id, district_id=districts["Toliara I"].id,
        ordre_visite=1, statut="en_cours"))
    ajouter(db, MissionDistrict(
        axe_id=axe_m2.id, district_id=districts["Toliara II"].id,
        ordre_visite=2, statut="planifie"))
    equipe_m2 = ajouter(db, Equipe(axe_id=axe_m2.id, type_equipe="DSID"))
    ajouter(db, Participant(
        equipe_id=equipe_m2.id, nom="Randria Mamy",
        fonction="Formateur", id_utilisateur=tech.id_utilisateur))
    ajouter(db, Participant(
        equipe_id=equipe_m2.id, nom="Rasoanaivo Lova", fonction="Technicien réseau"))
    phase_m2 = ajouter(db, Phase(
        mission_district_id=md_t1.id,
        type_activite_id=types["Formation à l'administration serveur"].id,
        numero_ordre=1, duree_prevue="J1-J2",
        livrable_attendu="PV de formation signé", statut="en_cours"))
    ajouter(db, Journee(
        mission_district_id=md_t1.id, numero_jour=1, date=date(2026, 10, 6),
        lieu="Toliara", statut="realisee"))
    ajouter(db, Journee(
        mission_district_id=md_t1.id, numero_jour=2, date=date(2026, 10, 9),
        lieu="Toliara", statut="prevue"))
    ajouter(db, Livrable(
        phase_id=phase_m2.id, type_livrable="PV de formation signé", signe=False))
    ajouter(db, IndicateurPerformance(
        mission_id=m2.id, resultat_attendu="Agents formés et certifiés",
        indicateur_mesure="Nombre d'agents formés par district",
        cible="≥ 1 par district", valeur_realisee="1/2"))

    # ---------- Mission 3 : équipement solaire (planifiée, sans district) ----------
    m3 = ajouter(db, Mission(
        titre="Installation de générateurs solaires dans les districts non électrifiés",
        type_mission="equipement",
        date_debut=datetime(2026, 11, 16), date_fin_prevue=datetime(2026, 12, 18),
        statut="planifiee"))
    axe_m3 = ajouter(db, Axe(
        mission_id=m3.id, numero_axe=1, itineraire_principal="Tanà → Taolagnaro → Tanà"))
    equipe_m3 = ajouter(db, Equipe(axe_id=axe_m3.id, type_equipe="DSID"))
    ajouter(db, Participant(
        equipe_id=equipe_m3.id, nom="Rakoto Hery",
        fonction="Chef de mission", id_utilisateur=chef.id_utilisateur))
    ajouter(db, Participant(
        equipe_id=equipe_m3.id, nom="Rasolofo Tahiry", fonction="Technicien installation"))

    # ---------- Mission 4 : audit pilote (annulée, sans axe) ----------
    ajouter(db, Mission(
        titre="Audit de conformité des accès, phase pilote",
        type_mission="audit_terrain",
        date_debut=datetime(2026, 9, 14), date_fin_prevue=datetime(2026, 9, 25),
        statut="annulee"))

    return definitions


def main():
    base = engine.url.database
    if base != BASE_ATTENDUE:
        raise SystemExit(
            f'Arrêt : la base ciblée est "{base}", pas "{BASE_ATTENDUE}". '
            "Rien n'a été modifié."
        )

    reponse = input(
        f'Cette opération efface TOUTES les données de "{base}". '
        "Tape OUI pour continuer : "
    )
    if reponse.strip() != "OUI":
        raise SystemExit("Annulé. Rien n'a été modifié.")

    db = SessionLocal()
    try:
        effacer(db)
        comptes = semer(db)
        db.commit()  # tout ou rien : en cas d'erreur, l'ancien contenu est conservé
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print("\nBase réinitialisée. Comptes de démonstration "
          f"(mot de passe : {MOT_DE_PASSE_DEMO}) :")
    for nom, prenom, email, _matricule, role, _service in comptes:
        print(f"  {email:<24} {role}")


if __name__ == "__main__":
    main()