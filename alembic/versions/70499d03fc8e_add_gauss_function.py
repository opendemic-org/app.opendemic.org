"""add gauss function

Revision ID: 70499d03fc8e
Revises: b280b8245d31
Create Date: 2020-04-23 20:57:14.913554

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '70499d03fc8e'
down_revision = 'b280b8245d31'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        """
        DROP FUNCTION IF EXISTS gauss;
        CREATE FUNCTION gauss(mean float, stdev float) RETURNS float
        BEGIN
        set @x=rand(), @y=rand();
        set @gaus = ((sqrt(-2*log(@x))*cos(2*pi()*@y))*stdev)+mean;
        return @gaus;
        END;
        """
    )
    pass


def downgrade():
    pass
