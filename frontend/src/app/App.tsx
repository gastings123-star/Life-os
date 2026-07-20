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

const API_BASE_URL = "http://localhost:8000/api/v1";

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
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const formattedDate = useMemo(
    () => new Intl.DateTimeFormat("ru-RU", { dateStyle: "full" }).format(new Date(`${selectedDate}T12:00:00`)),
    [selectedDate],
  );

  useEffect(() => {
    const controller = new AbortController();
    setIsLoading(true);
    setError(null);

    fetch(`${API_BASE_URL}/days/${selectedDate}`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("Не удалось загрузить день");
        return (await response.json()) as Day;
      })
      .then(setDay)
      .catch((requestError: Error) => {
        if (requestError.name !== "AbortError") setError(requestError.message);
      })
      .finally(() => setIsLoading(false));

    return () => controller.abort();
  }, [selectedDate]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim()) return;

    setIsSaving(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/days/${selectedDate}/actions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
      if (!response.ok) throw new Error("Не удалось сохранить действие");
      setDay((await response.json()) as Day);
      setTitle("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Неизвестная ошибка");
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
          <input type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} />
        </label>
      </header>

      <section className="panel" aria-busy={isLoading}>
        <h2>Действия</h2>
        {isLoading && <p>Загрузка…</p>}
        {!isLoading && day?.actions.length === 0 && <p className="empty-state">На этот день действий пока нет.</p>}
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

        {error && <p className="error" role="alert">{error}</p>}
      </section>
    </main>
  );
}
