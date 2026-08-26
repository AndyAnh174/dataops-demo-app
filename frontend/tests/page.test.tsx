import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import Home from "../app/page";


afterEach(() => {
  vi.restoreAllMocks();
});

test("shows the deployed API status and revision", async () => {
  vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          status: "ok",
          service: "dataops-demo-api",
          revision: "abc123",
        }),
      ),
    )
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          message: "Next.js + FastAPI deployed by a self-hosted runner",
        }),
      ),
    );

  render(<Home />);

  expect(screen.getByRole("heading", { name: /dataops demo/i })).toBeInTheDocument();
  await waitFor(() => {
    expect(screen.getByText("Online")).toBeInTheDocument();
    expect(screen.getByText("abc123")).toBeInTheDocument();
    expect(
      screen.getByText("Next.js + FastAPI deployed by a self-hosted runner"),
    ).toBeInTheDocument();
  });
});

test("shows an explicit degraded state when the API is unavailable", async () => {
  vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("network down"));

  render(<Home />);

  await waitFor(() => {
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
  });
});
