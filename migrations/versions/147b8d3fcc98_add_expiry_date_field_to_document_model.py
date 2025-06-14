"""Add expiry_date field to Document model

Revision ID: 147b8d3fcc98
Revises: 6595d902ab35
Create Date: 2025-06-10 00:03:56.212380

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '147b8d3fcc98'
down_revision = '6595d902ab35'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('document', schema=None) as batch_op:
        batch_op.add_column(sa.Column('expiry_date', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('document', schema=None) as batch_op:
        batch_op.drop_column('expiry_date')

    # ### end Alembic commands ###
