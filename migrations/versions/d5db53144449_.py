"""empty message

Revision ID: d5db53144449
Revises: b11dc26220c0
Create Date: 2019-12-20 13:21:21.813680

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd5db53144449'
down_revision = 'b11dc26220c0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('proteomics', 'gene',
               existing_type=sa.TEXT(),
               type_=postgresql.JSON(astext_type=sa.Text()),
               existing_nullable=False,
               postgresql_using="gene::json")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('proteomics', 'gene',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               type_=sa.TEXT(),
               existing_nullable=False)
    # ### end Alembic commands ###
