import { FormEvent, useEffect, useMemo, useState } from "react";

type ActionItem = {
  id: string;
  title: string;
  completed: boolean;
  created_at: string;
};

type Day = {
  id: string;
  date: string;
  actions: ActionItem[];
};

type InboxItem = {
  id: string;
  title: string;
  created_at: string;
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

async function responseError(
  response: Response,
  fallback: string,
): Promise<Error> {
  try {
    const payload = (await response.json()) as {
      message?: string;
      detail?: { message?: string };
    };
    return new Error(payload.message ?? payload.detail?.message ?? fallback);
  } catch {
    return new Error(fallback);
  }
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
  const [pendingActionId, setPendingActionId] = useState<string | null>(null);
  const [editingActionId, setEditingActionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [inbox, setInbox] = useState<InboxItem[]>([]);
  const [inboxTitle, setInboxTitle] = useState("");
  const [isInboxLoading, setIsInboxLoading] = useState(true);
  const [pendingInboxItemId, setPendingInboxItemId] = useState<string | null>(
    null,
  );
  const [editingInboxItemId, setEditingInboxItemId] = useState<string | null>(
    null,
  );
  const [editingInboxTitle, setEditingInboxTitle] = useState("");
  const [schedulingItem, setSchedulingItem] = useState<InboxItem | null>(null);
  const [scheduleDate, setScheduleDate] = useState(selectedDate);

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

  useEffect(() => {
    const controller = new AbortController();

    fetch(`${API_BASE_URL}/inbox`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) {
          throw await responseError(response, "Не удалось загрузить Inbox");
        }
        return (await response.json()) as InboxItem[];
      })
      .then((items) => setInbox(items))
      .catch((requestError: Error) => {
        if (requestError.name !== "AbortError") {
          setError(
            readableRequestError(requestError, "Не удалось загрузить Inbox"),
          );
        }
      })
      .finally(() => setIsInboxLoading(false));

    return () => controller.abort();
  }, []);

  async function handleInboxSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!inboxTitle.trim()) return;

    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/inbox`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: inboxTitle }),
      });
      if (!response.ok) {
        throw await responseError(response, "Не удалось добавить в Inbox");
      }
      const createdItem = (await response.json()) as InboxItem;
      setInbox((items) => [...items, createdItem]);
      setInboxTitle("");
    } catch (requestError) {
      setError(
        readableRequestError(requestError, "Не удалось добавить в Inbox"),
      );
    }
  }

  async function handleInboxRename(
    event: FormEvent<HTMLFormElement>,
    itemId: string,
  ) {
    event.preventDefault();
    if (!editingInboxTitle.trim()) return;

    setPendingInboxItemId(itemId);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/inbox/${itemId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: editingInboxTitle }),
      });
      if (!response.ok) {
        throw await responseError(
          response,
          "Не удалось переименовать элемент Inbox",
        );
      }
      const updated = (await response.json()) as InboxItem;
      setInbox((items) =>
        items.map((item) => (item.id === updated.id ? updated : item)),
      );
      setEditingInboxItemId(null);
      setEditingInboxTitle("");
    } catch (requestError) {
      setError(
        readableRequestError(
          requestError,
          "Не удалось переименовать элемент Inbox",
        ),
      );
    } finally {
      setPendingInboxItemId(null);
    }
  }

  async function handleInboxDelete(item: InboxItem) {
    if (!window.confirm(`Удалить «${item.title}» из Inbox?`)) return;

    setPendingInboxItemId(item.id);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/inbox/${item.id}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw await responseError(response, "Не удалось удалить элемент Inbox");
      }
      setInbox((items) => items.filter((current) => current.id !== item.id));
    } catch (requestError) {
      setError(
        readableRequestError(requestError, "Не удалось удалить элемент Inbox"),
      );
    } finally {
      setPendingInboxItemId(null);
    }
  }

  async function handleSchedule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!schedulingItem || !scheduleDate) return;

    setPendingInboxItemId(schedulingItem.id);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE_URL}/inbox/${schedulingItem.id}/schedule`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ date: scheduleDate }),
        },
      );
      if (!response.ok) {
        throw await responseError(response, "Не удалось запланировать задачу");
      }
      const action = (await response.json()) as ActionItem;
      setInbox((items) =>
        items.filter((item) => item.id !== schedulingItem.id),
      );
      if (scheduleDate === selectedDate) {
        setDay((currentDay) =>
          currentDay
            ? { ...currentDay, actions: [...currentDay.actions, action] }
            : currentDay,
        );
      } else {
        setSelectedDate(scheduleDate);
      }
      setSchedulingItem(null);
    } catch (requestError) {
      setError(
        readableRequestError(requestError, "Не удалось запланировать задачу"),
      );
    } finally {
      setPendingInboxItemId(null);
    }
  }

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

  async function patchAction(
    actionId: string,
    updates: { title?: string; completed?: boolean },
    fallbackError: string,
  ): Promise<boolean> {
    setPendingActionId(actionId);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/actions/${actionId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
      });
      if (!response.ok) throw await responseError(response, fallbackError);
      const updatedAction = (await response.json()) as ActionItem;
      setDay((currentDay) =>
        currentDay
          ? {
              ...currentDay,
              actions: currentDay.actions.map((action) =>
                action.id === updatedAction.id ? updatedAction : action,
              ),
            }
          : currentDay,
      );
      return true;
    } catch (requestError) {
      setError(readableRequestError(requestError, fallbackError));
      return false;
    } finally {
      setPendingActionId(null);
    }
  }

  async function handleEditSubmit(
    event: FormEvent<HTMLFormElement>,
    actionId: string,
  ) {
    event.preventDefault();
    if (!editingTitle.trim()) return;

    const saved = await patchAction(
      actionId,
      { title: editingTitle },
      "Не удалось переименовать действие",
    );
    if (saved) {
      setEditingActionId(null);
      setEditingTitle("");
    }
  }

  async function handleDelete(action: ActionItem) {
    if (!window.confirm(`Удалить действие «${action.title}»?`)) return;

    setPendingActionId(action.id);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/actions/${action.id}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw await responseError(response, "Не удалось удалить действие");
      }
      setDay((currentDay) =>
        currentDay
          ? {
              ...currentDay,
              actions: currentDay.actions.filter(
                (currentAction) => currentAction.id !== action.id,
              ),
            }
          : currentDay,
      );
      if (editingActionId === action.id) {
        setEditingActionId(null);
        setEditingTitle("");
      }
    } catch (requestError) {
      setError(
        readableRequestError(requestError, "Не удалось удалить действие"),
      );
    } finally {
      setPendingActionId(null);
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

      <section className="panel inbox-panel" aria-busy={isInboxLoading}>
        <h2>Inbox</h2>
        {isInboxLoading && <p>Загрузка…</p>}
        {!isInboxLoading && inbox.length === 0 && (
          <p className="empty-state">Inbox пока пуст.</p>
        )}
        {inbox.length > 0 && (
          <ul className="inbox-list">
            {inbox.map((item) => (
              <li className="inbox-list__item" key={item.id}>
                <span aria-hidden="true">□</span>
                {editingInboxItemId === item.id ? (
                  <form
                    className="action-edit-form"
                    onSubmit={(event) => void handleInboxRename(event, item.id)}
                  >
                    <label
                      className="visually-hidden"
                      htmlFor={`inbox-edit-${item.id}`}
                    >
                      Название элемента Inbox
                    </label>
                    <input
                      id={`inbox-edit-${item.id}`}
                      value={editingInboxTitle}
                      maxLength={500}
                      onChange={(event) =>
                        setEditingInboxTitle(event.target.value)
                      }
                    />
                    <button
                      type="submit"
                      disabled={
                        pendingInboxItemId === item.id ||
                        !editingInboxTitle.trim()
                      }
                    >
                      Сохранить
                    </button>
                    <button
                      className="button-secondary"
                      type="button"
                      onClick={() => setEditingInboxItemId(null)}
                    >
                      Отмена
                    </button>
                  </form>
                ) : (
                  <span>{item.title}</span>
                )}
                {editingInboxItemId !== item.id && (
                  <div className="action-list__controls">
                    <button
                      className="button-secondary"
                      type="button"
                      disabled={pendingInboxItemId === item.id}
                      aria-label={`Запланировать «${item.title}»`}
                      onClick={() => {
                        setSchedulingItem(item);
                        setScheduleDate(selectedDate);
                      }}
                    >
                      Schedule
                    </button>
                    <button
                      className="button-secondary"
                      type="button"
                      disabled={pendingInboxItemId === item.id}
                      aria-label={`Редактировать «${item.title}» в Inbox`}
                      onClick={() => {
                        setEditingInboxItemId(item.id);
                        setEditingInboxTitle(item.title);
                      }}
                    >
                      Изменить
                    </button>
                    <button
                      className="button-danger"
                      type="button"
                      disabled={pendingInboxItemId === item.id}
                      aria-label={`Удалить «${item.title}» из Inbox`}
                      onClick={() => void handleInboxDelete(item)}
                    >
                      Удалить
                    </button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}

        <form className="action-form" onSubmit={handleInboxSubmit}>
          <label htmlFor="inbox-title">Новая задача без даты</label>
          <div className="action-form__row">
            <input
              id="inbox-title"
              value={inboxTitle}
              onChange={(event) => setInboxTitle(event.target.value)}
              placeholder="Быстро сохранить мысль"
              maxLength={500}
            />
            <button type="submit" disabled={!inboxTitle.trim()}>
              + Добавить
            </button>
          </div>
        </form>
      </section>

      <section className="panel" aria-busy={isLoading}>
        <h2>Действия</h2>
        {isLoading && <p>Загрузка…</p>}
        {!isLoading && day?.actions.length === 0 && (
          <p className="empty-state">На этот день действий пока нет.</p>
        )}
        {!isLoading && day && day.actions.length > 0 && (
          <ol className="action-list">
            {day.actions.map((action) => (
              <li
                className={
                  action.completed
                    ? "action-list__item action-list__item--completed"
                    : "action-list__item"
                }
                key={action.id}
              >
                <input
                  aria-label={
                    action.completed
                      ? `Вернуть «${action.title}» в работу`
                      : `Отметить «${action.title}» выполненным`
                  }
                  type="checkbox"
                  checked={action.completed}
                  disabled={pendingActionId === action.id}
                  onChange={(event) =>
                    void patchAction(
                      action.id,
                      { completed: event.target.checked },
                      "Не удалось изменить состояние действия",
                    )
                  }
                />

                {editingActionId === action.id ? (
                  <form
                    className="action-edit-form"
                    onSubmit={(event) =>
                      void handleEditSubmit(event, action.id)
                    }
                  >
                    <label
                      className="visually-hidden"
                      htmlFor={`edit-${action.id}`}
                    >
                      Название действия
                    </label>
                    <input
                      id={`edit-${action.id}`}
                      value={editingTitle}
                      maxLength={500}
                      onChange={(event) => setEditingTitle(event.target.value)}
                    />
                    <button
                      type="submit"
                      disabled={
                        pendingActionId === action.id || !editingTitle.trim()
                      }
                    >
                      Сохранить
                    </button>
                    <button
                      className="button-secondary"
                      type="button"
                      onClick={() => setEditingActionId(null)}
                    >
                      Отмена
                    </button>
                  </form>
                ) : (
                  <span className="action-list__title">{action.title}</span>
                )}

                {editingActionId !== action.id && (
                  <div className="action-list__controls">
                    <button
                      className="button-secondary"
                      type="button"
                      disabled={pendingActionId === action.id}
                      aria-label={`Редактировать «${action.title}»`}
                      onClick={() => {
                        setEditingActionId(action.id);
                        setEditingTitle(action.title);
                      }}
                    >
                      Изменить
                    </button>
                    <button
                      className="button-danger"
                      type="button"
                      disabled={pendingActionId === action.id}
                      aria-label={`Удалить «${action.title}»`}
                      onClick={() => void handleDelete(action)}
                    >
                      Удалить
                    </button>
                  </div>
                )}
              </li>
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

      {schedulingItem && (
        <div className="dialog-backdrop" role="presentation">
          <section className="schedule-dialog" role="dialog" aria-modal="true">
            <h2>Запланировать задачу</h2>
            <p>{schedulingItem.title}</p>
            <form className="action-form" onSubmit={handleSchedule}>
              <label htmlFor="schedule-date">Дата</label>
              <input
                id="schedule-date"
                type="date"
                value={scheduleDate}
                onChange={(event) => setScheduleDate(event.target.value)}
              />
              <div className="dialog-actions">
                <button type="submit" disabled={!scheduleDate}>
                  Запланировать
                </button>
                <button
                  className="button-secondary"
                  type="button"
                  onClick={() => setSchedulingItem(null)}
                >
                  Отмена
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </main>
  );
}
