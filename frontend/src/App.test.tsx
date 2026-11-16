import { render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import App from "./App";

afterEach(() => vi.restoreAllMocks());

test("affiche le titre et l'état du backend", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ statut: "ok", environnement: "test" })),
  );
  render(<App />);
  expect(screen.getByRole("heading", { name: "PDIF" })).toBeInTheDocument();
  expect(await screen.findByText("Backend : ok (test)")).toBeInTheDocument();
});
