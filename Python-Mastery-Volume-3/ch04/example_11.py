# migrations/versions/0042_add_user_tier_zero_downtime.py
"""Alembic zero-downtime migration with lock_timeout and concurrent indexing.

Revision ID: 0042_add_user_tier
Create Date: 2026-10-19 14:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0042_add_user_tier"
down_revision = "0041_previous_revision"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Set autocommit block to allow CREATE INDEX CONCURRENTLY
    connection = op.get_bind()
    
    # 1. Enforce strict 2-second lock timeout to prevent queueing behind readers
    connection.execute(sa.text("SET lock_timeout = '2000ms';"))
    
    # 2. Add column as NULLABLE first (Expand Phase)
    op.add_column(
        "users",
        sa.Column("membership_tier", sa.String(length=32), nullable=True),
    )
    
    # 3. Create index CONCURRENTLY outside standard transaction boundary
    # Must commit current transaction before concurrent index creation
    op.execute("COMMIT;")
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_users_membership_tier "
        "ON users (membership_tier);"
    )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("SET lock_timeout = '2000ms';"))
    
    # Drop index concurrently before dropping column
    op.execute("COMMIT;")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_users_membership_tier;")
    
    op.drop_column("users", "membership_tier")
