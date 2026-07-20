from datetime import UTC, date
from uuid import UUID

from sqlalchemy import Engine, delete, insert, select, update

from src.domain.daily_planning import Action, Day
from src.infrastructure.database.metadata import actions, days


class SqlAlchemyDayRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_by_date(self, day_date: date) -> Day | None:
        with self._engine.connect() as connection:
            day_row = (
                connection.execute(select(days).where(days.c.date == day_date))
                .mappings()
                .one_or_none()
            )
            if day_row is None:
                return None

            action_rows = connection.execute(
                select(actions)
                .where(actions.c.day_id == day_row["id"])
                .order_by(actions.c.created_at, actions.c.id)
            ).mappings()

            return Day(
                id=UUID(day_row["id"]),
                date=day_row["date"],
                actions=[
                    Action(
                        id=UUID(row["id"]),
                        day_id=UUID(row["day_id"]),
                        title=row["title"],
                        completed=row["completed"],
                        created_at=(
                            row["created_at"].replace(tzinfo=UTC)
                            if row["created_at"].tzinfo is None
                            else row["created_at"]
                        ),
                    )
                    for row in action_rows
                ],
            )

    def save(self, day: Day) -> None:
        with self._engine.begin() as connection:
            existing_day = connection.execute(
                select(days.c.id).where(days.c.id == str(day.id))
            ).scalar_one_or_none()
            if existing_day is None:
                connection.execute(insert(days).values(id=str(day.id), date=day.date))

            existing_action_ids = set(
                connection.execute(
                    select(actions.c.id).where(actions.c.day_id == str(day.id))
                ).scalars()
            )
            new_actions = [
                action for action in day.actions if str(action.id) not in existing_action_ids
            ]
            if new_actions:
                connection.execute(
                    insert(actions),
                    [
                        {
                            "id": str(action.id),
                            "day_id": str(action.day_id),
                            "title": action.title,
                            "completed": action.completed,
                            "created_at": action.created_at,
                        }
                        for action in new_actions
                    ],
                )

    def get_action(self, action_id: UUID) -> Action | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(select(actions).where(actions.c.id == str(action_id)))
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            return Action(
                id=UUID(row["id"]),
                day_id=UUID(row["day_id"]),
                title=row["title"],
                completed=row["completed"],
                created_at=(
                    row["created_at"].replace(tzinfo=UTC)
                    if row["created_at"].tzinfo is None
                    else row["created_at"]
                ),
            )

    def update_action(self, action: Action) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                update(actions)
                .where(actions.c.id == str(action.id))
                .values(title=action.title, completed=action.completed)
            )

    def delete_action(self, action_id: UUID) -> bool:
        with self._engine.begin() as connection:
            result = connection.execute(delete(actions).where(actions.c.id == str(action_id)))
            return result.rowcount > 0
