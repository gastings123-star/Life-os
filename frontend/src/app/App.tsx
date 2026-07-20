import { FormEvent, useEffect, useMemo, useState } from "react";

type Capacity = "low" | "normal" | "high";
type Status = "empty" | "draft" | "active" | "closed";
type Outcome = "completed" | "dropped" | "renegotiated";
type Reason =
  | "overestimated_capacity"
  | "not_enough_time"
  | "higher_priority_appeared"
  | "scope_was_too_large"
  | "lost_relevance"
  | "blocked_by_external_dependency"
  | "other";
type Commitment = {
  id: string;
  text: string;
  kind: "primary" | "secondary";
  status: "active" | Outcome;
  position: number;
};
type CommitmentDay = {
  date: string;
  status: Status;
  capacity: Capacity | null;
  commitments: Commitment[];
  closed_at: string | null;
};
type Resolution = {
  outcome: Outcome | "";
  reason: Reason | "";
  comment: string;
  target_date: string;
};

const API = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/$/, "");
const NETWORK_ERROR =
  "Не удалось связаться с сервером. Проверьте, что backend запущен.";
const reasonLabels: Record<Reason, string> = {
  overestimated_capacity: "Переоценил(а) ёмкость дня",
  not_enough_time: "Не хватило времени",
  higher_priority_appeared: "Появился более важный приоритет",
  scope_was_too_large: "Объём оказался слишком большим",
  lost_relevance: "Потеряло актуальность",
  blocked_by_external_dependency: "Заблокировано внешней зависимостью",
  other: "Другое",
};

function localToday() {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60_000)
    .toISOString()
    .slice(0, 10);
}
async function apiError(response: Response, fallback: string) {
  try {
    const body = (await response.json()) as { message?: string };
    return new Error(body.message ?? fallback);
  } catch {
    return new Error(fallback);
  }
}
function message(error: unknown, fallback: string) {
  return error instanceof TypeError
    ? NETWORK_ERROR
    : error instanceof Error
      ? error.message
      : fallback;
}

export function App() {
  const today = localToday();
  const [selectedDate, setSelectedDate] = useState(today);
  const [day, setDay] = useState<CommitmentDay | null>(null);
  const [capacity, setCapacity] = useState<Capacity>("normal");
  const [primary, setPrimary] = useState("");
  const [secondary, setSecondary] = useState<string[]>([]);
  const [closing, setClosing] = useState(false);
  const [resolutions, setResolutions] = useState<Record<string, Resolution>>(
    {},
  );
  const [unclosed, setUnclosed] = useState<CommitmentDay[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const formattedDate = useMemo(
    () =>
      new Intl.DateTimeFormat("ru-RU", { dateStyle: "full" }).format(
        new Date(`${selectedDate}T12:00:00`),
      ),
    [selectedDate],
  );

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API}/commitment-days/${selectedDate}`, {
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok)
          throw await apiError(response, "Не удалось загрузить день");
        return response.json() as Promise<CommitmentDay>;
      })
      .then((loaded) => {
        setDay(loaded);
        setCapacity(loaded.capacity ?? "normal");
        setPrimary(
          loaded.commitments.find((item) => item.kind === "primary")?.text ??
            "",
        );
        setSecondary(
          loaded.commitments
            .filter((item) => item.kind === "secondary")
            .map((item) => item.text),
        );
        setClosing(false);
      })
      .catch((requestError: Error) => {
        if (requestError.name !== "AbortError")
          setError(message(requestError, "Не удалось загрузить день"));
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [selectedDate]);

  useEffect(() => {
    fetch(`${API}/commitment-days/unclosed?before=${today}`)
      .then((response) => (response.ok ? response.json() : []))
      .then((items: CommitmentDay[]) => setUnclosed(items))
      .catch(() => undefined);
  }, [today]);

  function chooseDate(value: string) {
    setLoading(true);
    setError(null);
    setSelectedDate(value);
  }

  async function confirmPlan(event: FormEvent) {
    event.preventDefault();
    if (!primary.trim()) {
      setError("Сформулируйте главный результат дня");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const saved = await fetch(`${API}/commitment-days/${selectedDate}/plan`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          capacity,
          primary,
          secondary: secondary.filter((value) => value.trim()),
        }),
      });
      if (!saved.ok) throw await apiError(saved, "Не удалось сохранить план");
      const activated = await fetch(
        `${API}/commitment-days/${selectedDate}/activate`,
        { method: "POST" },
      );
      if (!activated.ok)
        throw await apiError(activated, "Не удалось подтвердить план");
      setDay((await activated.json()) as CommitmentDay);
    } catch (requestError) {
      setError(message(requestError, "Не удалось подтвердить план"));
    } finally {
      setSaving(false);
    }
  }

  async function complete(id: string) {
    setSaving(true);
    setError(null);
    try {
      const response = await fetch(`${API}/commitments/${id}/complete`, {
        method: "POST",
      });
      if (!response.ok)
        throw await apiError(response, "Не удалось отметить результат");
      setDay((await response.json()) as CommitmentDay);
    } catch (requestError) {
      setError(message(requestError, "Не удалось отметить результат"));
    } finally {
      setSaving(false);
    }
  }

  function beginClose() {
    if (!day) return;
    setResolutions(
      Object.fromEntries(
        day.commitments.map((item) => [
          item.id,
          {
            outcome: item.status === "completed" ? "completed" : "",
            reason: "",
            comment: "",
            target_date: "",
          },
        ]),
      ),
    );
    setClosing(true);
  }
  function updateResolution(id: string, update: Partial<Resolution>) {
    setResolutions((current) => ({
      ...current,
      [id]: { ...current[id], ...update },
    }));
  }

  async function closeDay(event: FormEvent) {
    event.preventDefault();
    if (!day) return;
    const values = day.commitments.map((item) => ({
      commitment_id: item.id,
      ...resolutions[item.id],
      reason: resolutions[item.id].reason || null,
      comment: resolutions[item.id].comment || null,
      target_date: resolutions[item.id].target_date || null,
    }));
    if (values.some((item) => !item.outcome)) {
      setError("Выберите итог для каждого результата");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const response = await fetch(
        `${API}/commitment-days/${selectedDate}/close`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ resolutions: values }),
        },
      );
      if (!response.ok)
        throw await apiError(response, "Не удалось закрыть день");
      setDay((await response.json()) as CommitmentDay);
      setClosing(false);
      setUnclosed((items) =>
        items.filter((item) => item.date !== selectedDate),
      );
    } catch (requestError) {
      setError(message(requestError, "Не удалось закрыть день"));
    } finally {
      setSaving(false);
    }
  }

  const counts = Object.values(resolutions).reduce(
    (result, item) => ({
      ...result,
      [item.outcome]: (result[item.outcome] ?? 0) + 1,
    }),
    {} as Record<string, number>,
  );
  const pastUnclosed =
    day &&
    selectedDate < today &&
    day.status !== "closed" &&
    day.status !== "empty";
  return (
    <main className="commitment-workspace">
      <header className="commitment-header">
        <div>
          <p className="eyebrow">Life OS · 7-дневный эксперимент</p>
          <h1>Мои договорённости на сегодня</h1>
          <p className="date-label">{formattedDate}</p>
        </div>
        <label className="date-picker">
          <span>Дата</span>
          <input
            type="date"
            value={selectedDate}
            onChange={(event) => chooseDate(event.target.value)}
          />
        </label>
      </header>
      {unclosed.length > 0 && (
        <aside className="unclosed-banner">
          <strong>Есть незакрытые дни:</strong>
          {unclosed.map((item) => (
            <button
              key={item.date}
              type="button"
              onClick={() => chooseDate(item.date)}
            >
              {item.date}
            </button>
          ))}
        </aside>
      )}
      {pastUnclosed && (
        <p className="warning">
          День не закрыт. Его можно честно пересмотреть сейчас.
        </p>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {loading && (
        <section className="commitment-card">
          <p>Загрузка…</p>
        </section>
      )}
      {!loading &&
        day &&
        (day.status === "empty" || day.status === "draft") && (
          <form className="commitment-card morning-plan" onSubmit={confirmPlan}>
            <div>
              <p className="step-label">Утренний договор</p>
              <h2>Что должно стать правдой к концу дня?</h2>
              <p className="prompt-example">
                Не «Поработать над презентацией», а «Черновик презентации готов
                и отправлен на проверку».
              </p>
            </div>
            <fieldset className="capacity-picker">
              <legend>Реальная ёмкость дня</legend>
              {(["low", "normal", "high"] as Capacity[]).map((value) => (
                <label key={value}>
                  <input
                    type="radio"
                    name="capacity"
                    checked={capacity === value}
                    onChange={() => setCapacity(value)}
                  />
                  {{ low: "Низкая", normal: "Обычная", high: "Высокая" }[value]}
                </label>
              ))}
            </fieldset>
            <label className="result-field primary-field">
              <span>Главный результат</span>
              <textarea
                value={primary}
                maxLength={500}
                onChange={(event) => setPrimary(event.target.value)}
              />
            </label>
            {secondary.map((value, index) => (
              <label className="result-field" key={index}>
                <span>Дополнительный результат {index + 1}</span>
                <textarea
                  value={value}
                  maxLength={500}
                  onChange={(event) =>
                    setSecondary((items) =>
                      items.map((item, itemIndex) =>
                        itemIndex === index ? event.target.value : item,
                      ),
                    )
                  }
                />
              </label>
            ))}
            <div className="plan-actions">
              <span>1 главный + {secondary.length} дополнительных</span>
              {secondary.length < 2 && (
                <button
                  className="button-secondary"
                  type="button"
                  onClick={() => setSecondary((items) => [...items, ""])}
                >
                  + Дополнительный
                </button>
              )}
              <button type="submit" disabled={saving}>
                Подтвердить план дня
              </button>
            </div>
          </form>
        )}
      {!loading && day?.status === "active" && !closing && (
        <section className="commitment-card active-day">
          <div className="capacity-badge">Ёмкость: {day.capacity}</div>
          {day.commitments.map((item) => (
            <article
              className={
                item.kind === "primary"
                  ? "commitment commitment--primary"
                  : "commitment"
              }
              key={item.id}
            >
              <p>
                {item.kind === "primary"
                  ? "Главный результат"
                  : "Дополнительный результат"}
              </p>
              <h2>{item.text}</h2>
              {item.status === "completed" ? (
                <span className="completed-mark">Выполнено</span>
              ) : (
                <button
                  type="button"
                  disabled={saving}
                  onClick={() => void complete(item.id)}
                >
                  Отметить выполненным
                </button>
              )}
            </article>
          ))}
          <button
            className="close-day-button"
            type="button"
            onClick={beginClose}
          >
            Начать вечернее закрытие
          </button>
        </section>
      )}
      {!loading && day?.status === "active" && closing && (
        <form className="commitment-card evening-close" onSubmit={closeDay}>
          <p className="step-label">Вечерний пересмотр</p>
          <h2>Закрыть день честно</h2>
          {day.commitments.map((item) => {
            const draft = resolutions[item.id];
            return (
              <fieldset className="resolution" key={item.id}>
                <legend>{item.text}</legend>
                {(["completed", "dropped", "renegotiated"] as Outcome[]).map(
                  (outcome) => (
                    <label key={outcome}>
                      <input
                        type="radio"
                        name={`outcome-${item.id}`}
                        checked={draft?.outcome === outcome}
                        onChange={() =>
                          updateResolution(item.id, {
                            outcome,
                            reason: outcome === "completed" ? "" : draft.reason,
                            target_date:
                              outcome === "renegotiated"
                                ? draft.target_date
                                : "",
                          })
                        }
                      />
                      {
                        {
                          completed: "Выполнено",
                          dropped: "Снято",
                          renegotiated: "Пересмотрено",
                        }[outcome]
                      }
                    </label>
                  ),
                )}
                {(draft?.outcome === "dropped" ||
                  draft?.outcome === "renegotiated") && (
                  <label className="resolution-detail">
                    <span>Причина</span>
                    <select
                      aria-label={`Причина: ${item.text}`}
                      value={draft.reason}
                      onChange={(event) =>
                        updateResolution(item.id, {
                          reason: event.target.value as Reason,
                        })
                      }
                    >
                      <option value="">Выберите причину</option>
                      {Object.entries(reasonLabels).map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </label>
                )}
                {draft?.reason === "other" && (
                  <label className="resolution-detail">
                    <span>Комментарий</span>
                    <textarea
                      aria-label={`Комментарий: ${item.text}`}
                      value={draft.comment}
                      onChange={(event) =>
                        updateResolution(item.id, {
                          comment: event.target.value,
                        })
                      }
                    />
                  </label>
                )}
                {draft?.outcome === "renegotiated" && (
                  <label className="resolution-detail">
                    <span>Новая дата</span>
                    <input
                      aria-label={`Новая дата: ${item.text}`}
                      type="date"
                      min={selectedDate}
                      value={draft.target_date}
                      onChange={(event) =>
                        updateResolution(item.id, {
                          target_date: event.target.value,
                        })
                      }
                    />
                  </label>
                )}
              </fieldset>
            );
          })}
          <p className="close-summary">
            Выполнено: {counts.completed ?? 0} · Снято: {counts.dropped ?? 0} ·
            Пересмотрено: {counts.renegotiated ?? 0}
          </p>
          <div className="dialog-actions">
            <button
              className="button-secondary"
              type="button"
              onClick={() => setClosing(false)}
            >
              Вернуться
            </button>
            <button type="submit" disabled={saving}>
              Закрыть день
            </button>
          </div>
        </form>
      )}
      {!loading && day?.status === "closed" && (
        <section className="commitment-card closed-day">
          <p className="step-label">День закрыт</p>
          <h2>Договор пересмотрен</h2>
          <p className="date-label">
            Закрыт{" "}
            {day.closed_at
              ? new Date(day.closed_at).toLocaleString("ru-RU")
              : ""}
          </p>
          {day.commitments.map((item) => (
            <article className="closed-result" key={item.id}>
              <span>{item.status}</span>
              <strong>{item.text}</strong>
            </article>
          ))}
        </section>
      )}
    </main>
  );
}
