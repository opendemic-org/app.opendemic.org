"""removed old symptom columns in  and added source field 

Revision ID: b280b8245d31
Revises: 8a601f99b62d
Create Date: 2020-04-08 23:03:16.698607

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b280b8245d31'
down_revision = '8a601f99b62d'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute("""
        SET @DropFeverColumnIfExist = 
            (
                SELECT IF
                (
                    (
                        SELECT COUNT(1)
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE table_name = 'geolocations'
                        AND column_name = 'fever'
                    ) > 0,
                    "ALTER TABLE geolocations DROP COLUMN fever;",
                    /* Personalize your message if the column doesn't exist or already dropped */
                    "SELECT 'fever does not exist in geolocations table.'"
                )
            );
            PREPARE alterIfNotExists FROM @DropFeverColumnIfExist;
            EXECUTE alterIfNotExists;
            DEALLOCATE PREPARE alterIfNotExists;
            
        SET @DropSOFBreathColumnIfExist = 
        (
            SELECT IF
            (
                (
                    SELECT COUNT(1)
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE table_name = 'geolocations'
                    AND column_name = 'shortness_of_breath'
                ) > 0,
                "ALTER TABLE geolocations DROP COLUMN shortness_of_breath;",
                /* Personalize your message if the column doesn't exist or already dropped */
                "SELECT 'shortness_of_breath does not exist in geolocations table.'"
            )
        );
        PREPARE alterIfNotExists FROM @DropSOFBreathColumnIfExist;
        EXECUTE alterIfNotExists;
        DEALLOCATE PREPARE alterIfNotExists;
        
        SET @DropCoughColumnIfExist = 
        (
            SELECT IF
            (
                (
                    SELECT COUNT(1)
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE table_name = 'geolocations'
                    AND column_name = 'cough'
                ) > 0,
                "ALTER TABLE geolocations DROP COLUMN cough;",
                /* Personalize your message if the column doesn't exist or already dropped */
                "SELECT 'cough does not exist in geolocations table.'"
            )
        );
        PREPARE alterIfNotExists FROM @DropCoughColumnIfExist;
        EXECUTE alterIfNotExists;
        DEALLOCATE PREPARE alterIfNotExists;
        
        
        SET @AddSourceColumnIfExist = 
        (
            SELECT IF
            (
                (
                    SELECT COUNT(1)
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE table_name = 'humans'
                    AND column_name = 'source'
                ) = 0,
                "ALTER TABLE humans ADD COLUMN source VARCHAR(254) DEFAULT NULL;",
                /* Personalize your message if the column doesn't exist or already dropped */
                "SELECT 'source does exist in humans table.'"
            )
        );
        PREPARE alterIfNotExists FROM @AddSourceColumnIfExist;
        EXECUTE alterIfNotExists;
        DEALLOCATE PREPARE alterIfNotExists;
        
        SET @AddSourceIDColumnIfExist = 
        (
            SELECT IF
            (
                (
                    SELECT COUNT(1)
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE table_name = 'humans'
                    AND column_name = 'source_id'
                ) = 0,
                "ALTER TABLE humans ADD COLUMN source_id VARCHAR(254) DEFAULT NULL;",
                /* Personalize your message if the column doesn't exist or already dropped */
                "SELECT 'source_id does exist in humans table.'"
            )
        );
        PREPARE alterIfNotExists FROM @AddSourceIDColumnIfExist;
        EXECUTE alterIfNotExists;
        DEALLOCATE PREPARE alterIfNotExists;
    """)


def downgrade():
    pass
