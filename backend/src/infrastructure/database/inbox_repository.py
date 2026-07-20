from datetime import UTC, date
from uuid import UUID, uuid4

from sqlalchemy import Engine, delete, insert, select, update

from src.application.repositories import InboxRepository
from src.domain.daily_planning import Action
from src.domain.inbox import InboxItem
from src.infrastructure.database.metadata import actions, days, inbox_items


def inbox_item_from_row(row) -> InboxItem:
    created_at = row["created_at"]
    return InboxItem(
        id=UUID(row["id"]),
        title=row["title"],
        created_at=(created_at.replace(tzinfo=UTC) if created_at.tzinfo is None else created_at),
    )


class SqlAlchemyInboxRepository(InboxRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_all(self) -> list[InboxItem]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(inbox_items).order_by(inbox_items.c.created_at, inbox_items.c.id)
            ).mappings()
            return [inbox_item_from_row(row) for row in rows]

    def add(self, item: InboxItem) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                insert(inbox_items).values(
                    id=str(item.id),
                    title=item.title,
                    created_at=item.created_at,
                )
            )

    def get(self, item_id: UUID) -> InboxItem | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(select(inbox_items).where(inbox_items.c.id == str(item_id)))
                .mappings()
                .one_or_none()
            )
            return None if row is None else inbox_item_from_row(row)

    def update(self, item: InboxItem) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                update(inbox_items).where(inbox_items.c.id == str(item.id)).values(title=item.title)
            )

    def delete(self, item_id: UUID) -> bool:
        with self._engine.begin() as connection:
            result = connection.execute(delete(inbox_items).where(inbox_items.c.id == str(item_id)))
            return result.rowcount > 0

    def schedule(self, item_id: UUID, day_date: date) -> Action | None:
        with self._engine.begin() as connection:
            item_row = (
                connection.execute(select(inbox_items).where(inbox_items.c.id == str(item_id)))
                .mappings()
                .one_or_none()
            )
            if item_row is None:
                return None

            day_id = connection.execute(
                select(days.c.id).where(days.c.date == day_date)
            ).scalar_one_or_none()
            if day_id is None:
                day_id = str(uuid4())
                connection.execute(insert(days).values(id=day_id, date=day_date))

            action = Action(day_id=UUID(day_id), title=item_row["title"])
            connection.execute(
                insert(actions).values(
                    id=str(action.id),
                    day_id=day_id,
                    title=action.title,
                    completed=action.completed,
                    created_at=action.created_at,
                )
            )
            connection.execute(delete(inbox_items).where(inbox_items.c.id == str(item_id)))
            return action
