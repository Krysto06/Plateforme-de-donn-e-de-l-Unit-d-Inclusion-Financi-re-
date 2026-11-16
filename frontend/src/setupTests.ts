import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Retire l'affichage d'un test avant le suivant
afterEach(() => cleanup());
