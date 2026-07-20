import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

const emptyDay = {
  id: "3b22f5c0-bdb4-48ee-84a6-869e87a9a948",
  date: "2026-07-20",
  actions: [],
};

const dayWithAction = {
  ...emptyDay,
  actions: [
    {
      id: "836d09f0-9ab9-4e65-91e6-6b2a18f2485e",
      title: "Подготовить план встречи",
      completed: false,
      created_at: "2026-07-20T08:00:00+00:00",
    },
  ],
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App", () => {
  it("loads a day and adds an action", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(JSON.stringify(emptyDay), { status: 200 }),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify(dayWithAction), { status: 201 }),
      );

    render(<App />);

    expect(
      screen.getByRole("heading", { name: "План дня" }),
    ).toBeInTheDocument();
    await screen.findByText("На этот день действий пока нет.");

    fireEvent.change(screen.getByLabelText("Новое действие"), {
      target: { value: "Подготовить план встречи" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Добавить" }));

    await screen.findByText("Подготовить план встречи");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  });

  it("shows a clear message when the backend is unavailable", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(
      new TypeError("Failed to fetch"),
    );

    render(<App />);

    expect(
      await screen.findByText(
        "Не удалось связаться с сервером. Проверьте, что backend запущен.",
      ),
    ).toBeInTheDocument();
  });

  it("completes, renames and deletes an action", async () => {
    const completedAction = {
      ...dayWithAction.actions[0],
      completed: true,
    };
    const renamedAction = {
      ...completedAction,
      title: "Обновлённое действие",
    };
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(JSON.stringify(dayWithAction), { status: 200 }),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify(completedAction), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(renamedAction), { status: 200 }),
      )
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(<App />);
    await screen.findByText("Подготовить план встречи");

    fireEvent.click(
      screen.getByRole("checkbox", {
        name: "Отметить «Подготовить план встречи» выполненным",
      }),
    );
    await waitFor(() =>
      expect(
        screen.getByRole("checkbox", {
          name: "Вернуть «Подготовить план встречи» в работу",
        }),
      ).toBeChecked(),
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: "Редактировать «Подготовить план встречи»",
      }),
    );
    fireEvent.change(screen.getByLabelText("Название действия"), {
      target: { value: "Обновлённое действие" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Сохранить" }));
    await screen.findByText("Обновлённое действие");

    fireEvent.click(
      screen.getByRole("button", {
        name: "Удалить «Обновлённое действие»",
      }),
    );
    await waitFor(() =>
      expect(
        screen.queryByText("Обновлённое действие"),
      ).not.toBeInTheDocument(),
    );

    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      expect.stringContaining(`/actions/${dayWithAction.actions[0].id}`),
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({ completed: true }),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      4,
      expect.stringContaining(`/actions/${dayWithAction.actions[0].id}`),
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({ title: "Обновлённое действие" }),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      5,
      expect.stringContaining(`/actions/${dayWithAction.actions[0].id}`),
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("renames and schedules an Inbox item into the selected day", async () => {
    const inboxItem = {
      id: "b30cb4e8-6d7e-47cc-9abc-170747bc3a27",
      title: "Купить молоко",
      created_at: "2026-07-20T07:30:00+00:00",
    };
    const renamedInboxItem = { ...inboxItem, title: "Купить овсяное молоко" };
    const scheduledAction = {
      id: "a30cb4e8-6d7e-47cc-9abc-170747bc3a27",
      title: renamedInboxItem.title,
      completed: false,
      created_at: "2026-07-20T08:30:00+00:00",
    };
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(JSON.stringify(emptyDay), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify([inboxItem]), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(renamedInboxItem), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(scheduledAction), { status: 200 }),
      );

    render(<App />);
    await screen.findByText("Купить молоко");

    fireEvent.click(
      screen.getByRole("button", {
        name: "Редактировать «Купить молоко» в Inbox",
      }),
    );
    fireEvent.change(screen.getByLabelText("Название элемента Inbox"), {
      target: { value: renamedInboxItem.title },
    });
    fireEvent.click(screen.getByRole("button", { name: "Сохранить" }));
    await screen.findByText(renamedInboxItem.title);

    fireEvent.click(
      screen.getByRole("button", {
        name: `Запланировать «${renamedInboxItem.title}»`,
      }),
    );
    fireEvent.change(screen.getAllByLabelText("Дата")[1], {
      target: { value: emptyDay.date },
    });
    fireEvent.click(screen.getByRole("button", { name: "Запланировать" }));

    await waitFor(() =>
      expect(
        screen.queryByRole("button", {
          name: `Запланировать «${renamedInboxItem.title}»`,
        }),
      ).not.toBeInTheDocument(),
    );
    expect(screen.getByText(renamedInboxItem.title)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenNthCalledWith(
      4,
      expect.stringContaining(`/inbox/${inboxItem.id}/schedule`),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ date: emptyDay.date }),
      }),
    );
  });

  it("adds and deletes an Inbox item", async () => {
    const inboxItem = {
      id: "c30cb4e8-6d7e-47cc-9abc-170747bc3a27",
      title: "Позвонить",
      created_at: "2026-07-20T09:00:00+00:00",
    };
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(JSON.stringify(emptyDay), { status: 200 }),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify(inboxItem), { status: 201 }),
      )
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(<App />);
    await screen.findByText("Inbox пока пуст.");

    fireEvent.change(screen.getByLabelText("Новая задача без даты"), {
      target: { value: inboxItem.title },
    });
    fireEvent.click(screen.getByRole("button", { name: "+ Добавить" }));
    await screen.findByText(inboxItem.title);

    fireEvent.click(
      screen.getByRole("button", {
        name: `Удалить «${inboxItem.title}» из Inbox`,
      }),
    );

    await screen.findByText("Inbox пока пуст.");
    expect(fetchMock).toHaveBeenNthCalledWith(
      4,
      expect.stringContaining(`/inbox/${inboxItem.id}`),
      expect.objectContaining({ method: "DELETE" }),
    );
  });
});
