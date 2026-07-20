"""Create commitment day experiment tables.

Revision ID: 20260720_04
Revises: 20260720_03
Create Date: 2026-07-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260720_04"
down_revision: str | Sequence[str] | None = "20260720_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "daily_plans",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("capacity", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date"),
    )
    op.create_table(
        "daily_commitments",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("daily_plan_id", sa.String(36), nullable=False),
        sa.Column("text", sa.String(500), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["daily_plan_id"], ["daily_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_daily_commitments_plan_position",
        "daily_commitments",
        ["daily_plan_id", "position"],
    )
    op.create_table(
        "commitment_resolutions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("commitment_id", sa.String(36), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("reason", sa.String(64), nullable=True),
        sa.Column("comment", sa.String(1000), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("successor_commitment_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["commitment_id"], ["daily_commitments.id"]),
        sa.ForeignKeyConstraint(["successor_commitment_id"], ["daily_commitments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("commitment_id"),
    )


def downgrade() -> None:
    op.drop_table("commitment_resolutions")
    op.drop_index("ix_daily_commitments_plan_position", table_name="daily_commitments")
    op.drop_table("daily_commitments")
    op.drop_table("daily_plans")
