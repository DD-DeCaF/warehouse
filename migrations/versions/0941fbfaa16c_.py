"""empty message

Revision ID: 0941fbfaa16c
Revises: 7a18bfd606ee
Create Date: 2019-10-23 11:03:27.893835

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0941fbfaa16c'
down_revision = '7a18bfd606ee'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('proteomics',
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sample_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('identifier', sa.Text(), nullable=False),
    sa.Column('gene', sa.Text(), nullable=False),
    sa.Column('measurement', sa.Float(), nullable=False),
    sa.Column('uncertainty', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['sample_id'], ['sample.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('proteomics')
    # ### end Alembic commands ###
