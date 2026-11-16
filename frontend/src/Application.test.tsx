import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { FournisseurAuth } from "./auth";
import KpiCard from "./components/KpiCard";
import { Application } from "./main";
import type { Carte } from "./api";

function profil(role: "admin_uif" | "point_focal") {
  return {
    identifiant: "x", nom: role === "admin_uif" ? "Krystofia K. Elien" : "Point Focal", role, role_libelle: "Rôle",
    espace: role === "point_focal" ? "direction" : "uif",
    direction: role === "point_focal" ? { id: 1, nom: "Direction fictive" } : null,
  };
}

function simulerApi(role: "admin_uif" | "point_focal" | null) {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (entree) => {
    const url = String(entree);
    if (url.endsWith("/api/auth/moi")) return role ? Response.json(profil(role)) : new Response("{}", { status: 401 });
    if (url.includes("/api/tableau-de-bord")) return Response.json({ cartes: [], resume: { kpi_total: 19, kpi_disponibles: 0 } });
    if (url.includes("/api/depots/parametres")) return Response.json({ depots_ouverts: false, directions: [{ id: 1, nom: "Direction fictive" }],
      types_institution: [], institutions: [], types_donnees: [] });
    if (url.includes("/api/referentiels")) return Response.json({ departements: [], pays: [] });
    return Response.json([]);
  });
}

function afficher(chemin: string) {
  return render(<MemoryRouter initialEntries={[chemin]}><FournisseurAuth><Application /></FournisseurAuth></MemoryRouter>);
}

beforeEach(() => sessionStorage.clear());
afterEach(() => vi.restoreAllMocks());

test("sans connexion, on arrive sur la page de connexion", async () => {
  simulerApi(null);
  afficher("/");
  expect(await screen.findByRole("heading", { name: "Connexion" })).toBeInTheDocument();
  expect(screen.getByLabelText("Mot de passe")).toHaveAttribute("type", "password");
});

test("l'administratrice voit l'espace UIF complet", async () => {
  sessionStorage.setItem("pdif.jeton", "jeton");
  simulerApi("admin_uif");
  afficher("/");
  const nav = await screen.findByRole("navigation", { name: "Navigation principale" });
  for (const lien of ["Tableau de bord", "Sources et connexions", "Contrôle qualité", "Dépôt de données", "Catalogue des données", "Rapports et exports"]) {
    expect(nav).toHaveTextContent(lien);
  }
  expect(await screen.findByRole("heading", { name: "Tableau de bord de l'inclusion financière" })).toBeInTheDocument();
});

test("un point focal ne voit que l'espace dépôt, même s'il tape l'adresse du tableau de bord", async () => {
  sessionStorage.setItem("pdif.jeton", "jeton");
  simulerApi("point_focal");
  afficher("/");
  expect(await screen.findByRole("heading", { name: "Dépôt de données" })).toBeInTheDocument();
  const nav = screen.getByRole("navigation", { name: "Navigation principale" });
  expect(nav).toHaveTextContent("Espace direction");
  expect(nav).not.toHaveTextContent("Tableau de bord");
  await waitFor(() => expect(screen.getByText(/ne sera ouvert qu'une fois la plateforme hébergée/)).toBeInTheDocument());
});

test("une carte KPI affiche valeur, source, année et ancienneté", () => {
  const carte: Carte = {
    code: "ACC-01", libelle: "Agences bancaires pour 100 000 adultes", dimension: "Accès", unite: "pour 100 000 adultes", phase: 1,
    source_attendue: "FMI FAS", valeur: 2.6655, annee: 2020, source: "FMI", source_nom: "FMI — Financial Access Survey (FAS)",
    chargement_id: 1, autres_sources: [{ source: "WB", valeur: 2.6655 }], anciennete: { code: "ancienne", libelle: "Donnée de 2020 (6 ans)" },
  };
  render(<KpiCard carte={carte} />);
  expect(screen.getByText("2,67")).toBeInTheDocument();
  expect(screen.getByText(/FMI — Financial Access Survey \(FAS\) · ACC-01/)).toBeInTheDocument();
  expect(screen.getByText("Donnée de 2020 (6 ans)")).toBeInTheDocument();
  expect(screen.getByText(/Autre source : WB/)).toBeInTheDocument();
});
