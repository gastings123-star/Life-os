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

## Commitment Day: dogfood-эксперимент

В экспериментальной ветке главным экраном является цикл «утренний договор → работа с выбранными
результатами → вечернее закрытие». После запуска откройте <http://localhost:5173>, выберите дату,
capacity, один главный и до двух дополнительных результатов, подтвердите план и закройте день.

Итоги эксперимента доступны без dashboard:

```bash
curl "http://localhost:8000/api/v1/experiments/commitment-day/summary"
```

Подробности гипотезы, ограничений и критериев описаны в
[`docs/product-experiments/commitment-day.md`](docs/product-experiments/commitment-day.md).

## Хранение данных

Backend использует локальную SQLite. Адрес подключения задается переменной `LIFE_OS_DATABASE_URL`. По умолчанию база располагается в `data/life-os.sqlite3`.

Подготовить каталог данных и проверить состояние миграций локально:

```bash
mkdir -p data
cd backend
uv run alembic current
```

Применить доступные миграции:

```bash
cd backend
uv run alembic upgrade head
```

До появления первой реальной миграции список ревизий остается пустым. Команды Alembic при этом выполняются без ошибки и не создают бизнес-таблиц.

## Запуск через Docker

```bash
docker compose up --build
```

В Docker каталог проекта `./data` подключается к backend как `/data`, поэтому файл SQLite сохраняется между перезапусками контейнера.

Проверить состояние миграций через Docker:

```bash
docker compose run --rm backend uv run --no-dev alembic current
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

## Architecture

Backend сохраняет слоистую структуру с направленными зависимостями:

- **Domain** содержит предметные данные, правила и инварианты без зависимости от HTTP и базы данных.
- **Application** координирует пользовательские сценарии и зависит от интерфейсов репозиториев.
- **Infrastructure** реализует доступ к SQLite и другие технические адаптеры.
- **API** описывает HTTP-контракт, собирает зависимости и преобразует ошибки в единый JSON-формат.

Dependency Injection выполняется средствами FastAPI `Depends`: API получает прикладной сервис,
репозиторий и SQLAlchemy engine через явную цепочку зависимостей. Repository Pattern отделяет
прикладные сценарии от конкретного способа хранения данных. Подготовительный интерфейс
`UnitOfWork` фиксирует будущую точку транзакционной координации, но в текущей итерации не
управляет транзакциями и не меняет поведение сервисов.
