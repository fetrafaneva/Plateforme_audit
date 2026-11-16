"""Benchmarking : indicateurs par service et unicite des periodes

Revision ID: b7f3a9c15d42
Revises: f0b649b0b6b6
Create Date: 2026-11-15

La table benchmarking_services ne gardait qu'un seul chiffre (score_risque_moyen).
Le module de benchmarking en stocke deux, plus les effectifs qui servent a les
interpreter : un taux d'alertes pour 100 acces (normalise par le volume) et la
moyenne des |z-score| des acces effectivement analyses.

L'unicite (id_service, periode) garantit qu'un recalcul remplace la photographie
de la periode au lieu d'en empiler une seconde ; idem pour rapports_audit.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7f3a9c15d42"
down_revision: Union[str, Sequence[str], None] = "f0b649b0b6b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


COLONNES_ENTIERES = (
    "nb_agents",
    "nb_acces",
    "nb_scores",
    "nb_alertes",
    "nb_alertes_critiques",
)


def upgrade() -> None:
    for nom in COLONNES_ENTIERES:
        op.add_column(
            "benchmarking_services",
            sa.Column(nom, sa.Integer(), nullable=False, server_default="0"),
        )
    op.add_column(
        "benchmarking_services",
        sa.Column("taux_alertes", sa.Float(), nullable=False, server_default="0"),
    )

    # Le server_default n'etait la que pour remplir d'eventuelles lignes existantes :
    # les valeurs sont toujours calculees par l'application.
    for nom in COLONNES_ENTIERES:
        op.alter_column(
            "benchmarking_services",
            nom,
            existing_type=sa.Integer(),
            server_default=None,
        )
    op.alter_column(
        "benchmarking_services",
        "taux_alertes",
        existing_type=sa.Float(),
        server_default=None,
    )

    op.create_index(
        "ix_benchmarking_services_periode", "benchmarking_services", ["periode"]
    )
    op.create_unique_constraint(
        "uq_benchmarking_services_service_periode",
        "benchmarking_services",
        ["id_service", "periode"],
    )
    op.create_unique_constraint(
        "uq_rapports_audit_service_periode",
        "rapports_audit",
        ["id_service", "periode_couverte"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_rapports_audit_service_periode", "rapports_audit", type_="unique"
    )
    op.drop_constraint(
        "uq_benchmarking_services_service_periode",
        "benchmarking_services",
        type_="unique",
    )
    op.drop_index(
        "ix_benchmarking_services_periode", table_name="benchmarking_services"
    )
    op.drop_column("benchmarking_services", "taux_alertes")
    for nom in reversed(COLONNES_ENTIERES):
        op.drop_column("benchmarking_services", nom)
