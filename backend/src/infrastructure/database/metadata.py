from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    false,
)

metadata = MetaData()

days = Table(
    "days",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("date", Date, nullable=False, unique=True),
)

actions = Table(
    "actions",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("day_id", String(36), ForeignKey("days.id", ondelete="CASCADE"), nullable=False),
    Column("title", String(500), nullable=False),
    Column("completed", Boolean, nullable=False, server_default=false()),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

inbox_items = Table(
    "inbox_items",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("title", String(500), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

daily_plans = Table(
    "daily_plans",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("date", Date, nullable=False, unique=True),
    Column("capacity", String(16), nullable=False),
    Column("status", String(16), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("closed_at", DateTime(timezone=True), nullable=True),
)

daily_commitments = Table(
    "daily_commitments",
    metadata,
    Column("id", String(36), primary_key=True),
    Column(
        "daily_plan_id",
        String(36),
        ForeignKey("daily_plans.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("text", String(500), nullable=False),
    Column("kind", String(16), nullable=False),
    Column("status", String(16), nullable=False),
    Column("position", Integer, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

commitment_resolutions = Table(
    "commitment_resolutions",
    metadata,
    Column("id", String(36), primary_key=True),
    Column(
        "commitment_id",
        String(36),
        ForeignKey("daily_commitments.id"),
        nullable=False,
        unique=True,
    ),
    Column("outcome", String(16), nullable=False),
    Column("reason", String(64), nullable=True),
    Column("comment", String(1000), nullable=True),
    Column("target_date", Date, nullable=True),
    Column(
        "successor_commitment_id",
        String(36),
        ForeignKey("daily_commitments.id"),
        nullable=True,
    ),
    Column("created_at", DateTime(timezone=True), nullable=False),
)
