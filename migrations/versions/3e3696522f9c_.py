"""empty message

Revision ID: 3e3696522f9c
Revises: 
Create Date: 2018-05-28 16:59:08.020871

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3e3696522f9c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('carga', sa.Column('descricao', sa.String(length=100), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('carga', 'descricao')
    # ### end Alembic commands ###
