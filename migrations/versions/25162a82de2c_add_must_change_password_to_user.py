"""Add must_change_password to User

Revision ID: 25162a82de2c
Revises: 5d4a832a0a4c
Create Date: 2025-06-24 13:44:10.084529

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '25162a82de2c'
down_revision = '5d4a832a0a4c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('must_change_password', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('must_change_password')

    # ### end Alembic commands ###
