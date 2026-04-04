"""Convert timestamp columns to timezone-aware

Revision ID: PLACEHOLDER
Revises: 7b411a8c01ff
Create Date: 2026-04-04 04:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'PLACEHOLDER_REV'
down_revision = '7b411a8c01ff'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert kiosk_sessions timestamp columns to TIMESTAMP WITH TIME ZONE
    op.execute('ALTER TABLE kiosk_sessions ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE')
    op.execute('ALTER TABLE kiosk_sessions ALTER COLUMN expires_at TYPE TIMESTAMP WITH TIME ZONE')
    op.execute('ALTER TABLE kiosk_sessions ALTER COLUMN completed_at TYPE TIMESTAMP WITH TIME ZONE')


def downgrade() -> None:
    # Revert to TIMESTAMP WITHOUT TIME ZONE
    op.execute('ALTER TABLE kiosk_sessions ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE')
    op.execute('ALTER TABLE kiosk_sessions ALTER COLUMN expires_at TYPE TIMESTAMP WITHOUT TIME ZONE')
    op.execute('ALTER TABLE kiosk_sessions ALTER COLUMN completed_at TYPE TIMESTAMP WITHOUT TIME ZONE')
