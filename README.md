# Life OS

Локальное веб-приложение для управления целями, результатами дня, привычками, метриками и обзорами.

## Статус

Создан технический каркас backend и frontend. Бизнес-функции пока не реализованы.

## Базовая концепция

В центре системы находится `Day`. Долгосрочный контекст задают Identity, Domains, Vision, Goals, Projects и Outcomes. На конкретный день выбираются Actions, Events, Habits и Metrics.

## Требования

- Python 3.13;
- [uv](https://docs.astral.sh/uv/);
- Node.js и npm;
- Docker с Docker Compose — для запуска в контейнерах.

## Локальный запуск

Установить зависимости:

```bash
cd backend && uv sync
cd ../frontend && npm install
```

Запустить backend и frontend одной командой из корня проекта:

```bash
./scripts/dev.sh
```

После запуска доступны:

- frontend: <http://localhost:5173>;
- проверка backend: <http://localhost:8000/health>.

## Запуск через Docker

```bash
docker compose up --build
```

## Проверки

```bash
cd backend
uv run pytest
uv run ruff check .
uv run ruff format --check .

cd ../frontend
npm test
npm run lint
npm run format:check
npm run build
```
