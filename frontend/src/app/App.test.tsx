import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

const emptyDay = {
  date: "2026-07-20",
  status: "empty",
  capacity: null,
  commitments: [],
  closed_at: null,
};
const commitments = [
  {
    id: "11111111-1111-4111-8111-111111111111",
    text: "Главный результат готов",
    kind: "primary",
    status: "active",
    position: 0,
  },
  {
    id: "22222222-2222-4222-8222-222222222222",
    text: "Дополнительный готов",
    kind: "secondary",
    status: "active",
    position: 1,
  },
];
const activeDay = {
  ...emptyDay,
  status: "active",
  capacity: "normal",
  commitments,
};

function mockApi(dayResponse: object, handlers: Record<string, object> = {}) {
  return vi
    .spyOn(globalThis, "fetch")
    .mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/unclosed"))
        return new Response(JSON.stringify([]), { status: 200 });
      const key = `${init?.method ?? "GET"} ${url.split("/api/v1")[1]}`;
      const body = handlers[key] ?? dayResponse;
      return new Response(JSON.stringify(body), {
        status: key.startsWith("PUT") ? 200 : 200,
      });
    });
}

afterEach(() => vi.restoreAllMocks());

describe("Commitment Day", () => {
  it("renders planning, capacity and activates a morning plan", async () => {
    const fetchMock = mockApi(emptyDay, {
      "PUT /commitment-days/2026-07-20/plan": { ...activeDay, status: "draft" },
      "POST /commitment-days/2026-07-20/activate": activeDay,
    });
    render(<App />);
    await screen.findByText("Что должно стать правдой к концу дня?");
    fireEvent.click(screen.getByLabelText("Низкая"));
    fireEvent.change(screen.getByLabelText("Главный результат"), {
      target: { value: "Главный результат готов" },
    });
    fireEvent.click(screen.getByRole("button", { name: "+ Дополнительный" }));
    fireEvent.change(screen.getByLabelText("Дополнительный результат 1"), {
      target: { value: "Дополнительный готов" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Подтвердить план дня" }),
    );
    await screen.findByRole("button", { name: "Начать вечернее закрытие" });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/plan"),
      expect.objectContaining({
        body: JSON.stringify({
          capacity: "low",
          primary: "Главный результат готов",
          secondary: ["Дополнительный готов"],
        }),
      }),
    );
  });

  it("marks completed and closes with conditional resolution fields", async () => {
    const completedDay = {
      ...activeDay,
      commitments: [{ ...commitments[0], status: "completed" }, commitments[1]],
    };
    const closedDay = {
      ...completedDay,
      status: "closed",
      closed_at: "2026-07-20T20:00:00Z",
      commitments: [
        { ...commitments[0], status: "completed" },
        { ...commitments[1], status: "renegotiated" },
      ],
    };
    const fetchMock = mockApi(activeDay, {
      [`POST /commitments/${commitments[0].id}/complete`]: completedDay,
      "POST /commitment-days/2026-07-20/close": closedDay,
    });
    render(<App />);
    await screen.findByText("Главный результат готов");
    fireEvent.click(
      screen.getAllByRole("button", { name: "Отметить выполненным" })[0],
    );
    await screen.findByText("Выполнено");
    fireEvent.click(
      screen.getByRole("button", { name: "Начать вечернее закрытие" }),
    );
    fireEvent.click(screen.getAllByLabelText("Пересмотрено")[1]);
    fireEvent.change(screen.getByLabelText("Причина: Дополнительный готов"), {
      target: { value: "not_enough_time" },
    });
    fireEvent.change(
      screen.getByLabelText("Новая дата: Дополнительный готов"),
      { target: { value: "2026-07-22" } },
    );
    expect(screen.getByText(/Выполнено: 1/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Закрыть день" }));
    await screen.findByText("Договор пересмотрен");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/close"),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("shows past-unclosed warning and an understandable network error", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (String(input).includes("/unclosed"))
        return new Response(JSON.stringify([]));
      throw new TypeError("Failed to fetch");
    });
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Не удалось связаться с сервером",
    );
  });

  it("shows a past unclosed day", async () => {
    mockApi({ ...activeDay, date: "2026-07-19" });
    render(<App />);
    fireEvent.change(screen.getByLabelText("Дата"), {
      target: { value: "2026-07-19" },
    });
    await waitFor(() =>
      expect(screen.getByText(/День не закрыт/)).toBeInTheDocument(),
    );
  });
});
