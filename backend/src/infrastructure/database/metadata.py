from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, MetaData, String, Table, false

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
