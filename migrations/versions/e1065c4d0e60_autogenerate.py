"""--autogenerate

Revision ID: e1065c4d0e60
Revises: ce0b8c0ec29d
Create Date: 2018-07-25 13:26:10.009931

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1065c4d0e60'
down_revision = 'ce0b8c0ec29d'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('biological_entity', 'namespace_id',
                    existing_type=sa.INTEGER(),
                    nullable=False)


def downgrade():
    pass
