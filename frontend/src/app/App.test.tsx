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
      .mockResolvedValueOnce(new Response(JSON.stringify(emptyDay), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(dayWithAction), { status: 201 }));

    render(<App />);

    expect(screen.getByRole("heading", { name: "План дня" })).toBeInTheDocument();
    await screen.findByText("На этот день действий пока нет.");

    fireEvent.change(screen.getByLabelText("Новое действие"), {
      target: { value: "Подготовить план встречи" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Добавить" }));

    await screen.findByText("Подготовить план встречи");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  });
});
