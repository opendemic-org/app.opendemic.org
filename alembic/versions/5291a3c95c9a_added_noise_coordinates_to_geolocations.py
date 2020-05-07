"""added noise coordinates to geolocations

Revision ID: 5291a3c95c9a
Revises: 70499d03fc8e
Create Date: 2020-05-06 21:19:52.848211

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5291a3c95c9a'
down_revision = '70499d03fc8e'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute("""
            SET @AddLatitudeNoiseColumnIfExist = 
            (
                SELECT IF
                (
                    (
                        SELECT COUNT(1)
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE table_name = 'geolocations'
                        AND column_name = 'latitude_noise'
                    ) = 0,
                    "ALTER TABLE geolocations ADD COLUMN latitude_noise DECIMAL(14,10) DEFAULT 0;",
                    /* Personalize your message if the column doesn't exist or already dropped */
                    "SELECT 'latitude_noise does exist in humans table.'"
                )
            );
            PREPARE alterIfNotExists FROM @AddLatitudeNoiseColumnIfExist;
            EXECUTE alterIfNotExists;
            DEALLOCATE PREPARE alterIfNotExists;
            
            SET @AddLongitudeNoiseColumnIfExist = 
            (
                SELECT IF
                (
                    (
                        SELECT COUNT(1)
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE table_name = 'geolocations'
                        AND column_name = 'longitude_noise'
                    ) = 0,
                    "ALTER TABLE geolocations ADD COLUMN longitude_noise DECIMAL(14,10) DEFAULT 0;",
                    /* Personalize your message if the column doesn't exist or already dropped */
                    "SELECT 'longitude_noise does exist in humans table.'"
                )
            );
            PREPARE alterIfNotExists FROM @AddLongitudeNoiseColumnIfExist;
            EXECUTE alterIfNotExists;
            DEALLOCATE PREPARE alterIfNotExists;
            
            UPDATE `geolocations`
            SET `latitude_noise` = gauss(0,0.001)
            WHERE `latitude_noise` = 0;
            
            UPDATE `geolocations`
            SET `longitude_noise` = gauss(0,0.001)
            WHERE `longitude_noise` = 0;

        """)


def downgrade():
    pass
