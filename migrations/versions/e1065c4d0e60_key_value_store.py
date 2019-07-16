"""extra_data

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
    op.rename_table('sample', 'condition')
    op.rename_table('measurement', 'sample')
    op.alter_column('sample', 'sample_id', new_column_name='condition_id')
    op.add_column('condition', sa.Column(
        'extra_data', sa.JSON(), nullable=True))


def downgrade():
    pass
    op.drop_column('condition', 'extra_data')
    op.drop_column('condition', 'key_value_store')
    op.rename_table('sample', 'measurement')
    op.rename_table('condition', 'sample')
    op.alter_column('measurement', 'condition_id', new_column_name='sample_id')
