import { FormEvent, useEffect, useMemo, useState } from "react";

type ActionItem = {
  id: string;
  title: string;
  created_at: string;
};

type Day = {
  id: string;
  date: string;
  actions: ActionItem[];
};

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/$/, "");

const NETWORK_ERROR_MESSAGE =
  "Не удалось связаться с сервером. Проверьте, что backend запущен.";

function readableRequestError(error: unknown, fallback: string): string {
  if (error instanceof TypeError) return NETWORK_ERROR_MESSAGE;
  return error instanceof Error ? error.message : fallback;
}

function localToday(): string {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60_000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

export function App() {
  const [selectedDate, setSelectedDate] = useState(localToday);
  const [day, setDay] = useState<Day | null>(null);
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<{
    date: string;
    message: string;
  } | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const isLoading =
    day?.date !== selectedDate && loadError?.date !== selectedDate;
  const displayedError =
    loadError?.date === selectedDate ? loadError.message : error;

  const formattedDate = useMemo(
    () =>
      new Intl.DateTimeFormat("ru-RU", { dateStyle: "full" }).format(
        new Date(`${selectedDate}T12:00:00`),
      ),
    [selectedDate],
  );

  useEffect(() => {
    const controller = new AbortController();
    const requestedDate = selectedDate;

    fetch(`${API_BASE_URL}/days/${requestedDate}`, {
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error("Не удалось загрузить день");
        return (await response.json()) as Day;
      })
      .then((loadedDay) => {
        setDay(loadedDay);
        setLoadError(null);
      })
      .catch((requestError: Error) => {
        if (requestError.name !== "AbortError") {
          setLoadError({
            date: requestedDate,
            message: readableRequestError(
              requestError,
              "Не удалось загрузить день",
            ),
          });
        }
      });

    return () => controller.abort();
  }, [selectedDate]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim()) return;

    setIsSaving(true);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE_URL}/days/${selectedDate}/actions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title }),
        },
      );
      if (!response.ok) throw new Error("Не удалось сохранить действие");
      setDay((await response.json()) as Day);
      setTitle("");
    } catch (requestError) {
      setError(
        readableRequestError(requestError, "Не удалось сохранить действие"),
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <main className="workspace">
      <header className="workspace__header">
        <div>
          <p className="eyebrow">Life OS</p>
          <h1>План дня</h1>
          <p className="date-label">{formattedDate}</p>
        </div>
        <label className="date-picker">
          <span>Дата</span>
          <input
            type="date"
            value={selectedDate}
            onChange={(event) => setSelectedDate(event.target.value)}
          />
        </label>
      </header>

      <section className="panel" aria-busy={isLoading}>
        <h2>Действия</h2>
        {isLoading && <p>Загрузка…</p>}
        {!isLoading && day?.actions.length === 0 && (
          <p className="empty-state">На этот день действий пока нет.</p>
        )}
        {!isLoading && day && day.actions.length > 0 && (
          <ol className="action-list">
            {day.actions.map((action) => (
              <li key={action.id}>{action.title}</li>
            ))}
          </ol>
        )}

        <form className="action-form" onSubmit={handleSubmit}>
          <label htmlFor="action-title">Новое действие</label>
          <div className="action-form__row">
            <input
              id="action-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Например, подготовить план встречи"
              maxLength={500}
            />
            <button type="submit" disabled={isSaving || !title.trim()}>
              {isSaving ? "Сохраняем…" : "Добавить"}
            </button>
          </div>
        </form>

        {displayedError && (
          <p className="error" role="alert">
            {displayedError}
          </p>
        )}
      </section>
    </main>
  );
}
