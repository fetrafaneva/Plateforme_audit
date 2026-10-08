"""lien participant vers utilisateur

Revision ID: 55a85c0485fd
Revises: e939075e7644
Create Date: 2026-10-05 15:06:46.872703

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55a85c0485fd'
down_revision: Union[str, Sequence[str], None] = 'e939075e7644'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('participants', sa.Column('id_utilisateur', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_participants_id_utilisateur_utilisateurs',
        'participants', 'utilisateurs',
        ['id_utilisateur'], ['id_utilisateur']
    )


def downgrade() -> None:
    op.drop_constraint('fk_participants_id_utilisateur_utilisateurs', 'participants', type_='foreignkey')
    op.drop_column('participants', 'id_utilisateur')
