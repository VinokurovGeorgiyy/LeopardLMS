"""added solutions to lesson

Revision ID: 79e149e55aef
Revises: dc07c3323fca
Create Date: 2020-04-24 22:12:40.436644

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '79e149e55aef'
down_revision = 'dc07c3323fca'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('lessons', sa.Column('solutions', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('lessons', 'solutions')
    # ### end Alembic commands ###
