from sqlalchemy import Column, Date, DateTime, ForeignKey, MetaData, String, Table

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
    Column("created_at", DateTime(timezone=True), nullable=False),
)
