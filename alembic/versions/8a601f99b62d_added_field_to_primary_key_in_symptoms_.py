"""added field to primary key in symptoms table

Revision ID: 8a601f99b62d
Revises: 4aecad6ba879
Create Date: 2020-04-06 16:55:47.501855

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a601f99b62d'
down_revision = '4aecad6ba879'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        """
        ALTER TABLE `symptoms` DROP PRIMARY KEY, ADD PRIMARY KEY(`human_id`, `created`, `symptom`);
        """
    )


def downgrade():
    pass
