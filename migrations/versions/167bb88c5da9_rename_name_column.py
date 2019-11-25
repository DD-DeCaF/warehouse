"""rename name column

Revision ID: 167bb88c5da9
Revises: 0941fbfaa16c
Create Date: 2019-11-25 10:27:25.658812

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '167bb88c5da9'
down_revision = '0941fbfaa16c'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('proteomics', 'name', new_column_name='full_name')
    # ### end Alembic commands ###


def downgrade():
    op.alter_column('proteomics', 'full_name', new_column_name='name')
    # ### end Alembic commands ###
