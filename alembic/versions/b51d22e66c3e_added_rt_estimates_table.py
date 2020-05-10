"""added Rt estimates table

Revision ID: b51d22e66c3e
Revises: 5291a3c95c9a
Create Date: 2020-05-09 22:47:35.899284

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b51d22e66c3e'
down_revision = '5291a3c95c9a'
branch_labels = None
depends_on = None


def upgrade():
	conn = op.get_bind()
	conn.execute("""
	CREATE TABLE `rt_estimates` (
		`date` date NOT NULL,
		`rt_estimate` decimal(14,4) DEFAULT NULL,
		`rt_low` decimal(14,4) DEFAULT NULL,
		`rt_high` decimal(14,4) DEFAULT NULL,
		`country_code` varchar(254) NOT NULL,
		`first_administrative_division_name` varchar(254) NOT NULL,
		`region_code` varchar(254) NOT NULL,
		`region_name` varchar(254) NOT NULL,
		`modified` timestamp NOT NULL,
		PRIMARY KEY (`date`,`country_code`,`first_administrative_division_name`,`region_code`,`region_name`)
	) ENGINE=InnoDB DEFAULT CHARSET=latin1;
    """)


def downgrade():
	pass
