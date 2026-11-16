import { StrictMode, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/ibm-plex-sans/700.css";
import "./index.css";
import { FournisseurAuth, useAuth } from "./auth";
import Layout from "./components/Layout";
import Catalogue from "./pages/Catalogue";
import Connexions from "./pages/Connexions";
import Dashboard from "./pages/Dashboard";
import Depot from "./pages/Depot";
import Login from "./pages/Login";
import Qualite from "./pages/Qualite";
import Rapports from "./pages/Rapports";

// Garde : il faut être connecté ; l'espace UIF est fermé aux points focaux
function Protege({ children, uif = false }: { children: ReactNode; uif?: boolean }) {
  const { utilisateur, pret } = useAuth();
  if (!pret) return <p className="p-8 text-discret">Chargement…</p>;
  if (!utilisateur) return <Navigate to="/connexion" replace />;
  if (uif && utilisateur.espace !== "uif") return <Navigate to="/depot" replace />;
  return <>{children}</>;
}

export function Application() {
  return (
    <Routes>
      <Route path="/connexion" element={<Login />} />
      <Route element={<Protege><Layout /></Protege>}>
        <Route index element={<Protege uif><Dashboard /></Protege>} />
        <Route path="connexions" element={<Protege uif><Connexions /></Protege>} />
        <Route path="qualite" element={<Protege uif><Qualite /></Protege>} />
        <Route path="catalogue" element={<Protege uif><Catalogue /></Protege>} />
        <Route path="rapports" element={<Protege uif><Rapports /></Protege>} />
        <Route path="depot" element={<Depot />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

const racine = document.getElementById("root");
if (racine) {
  createRoot(racine).render(
    <StrictMode>
      <BrowserRouter>
        <FournisseurAuth>
          <Application />
        </FournisseurAuth>
      </BrowserRouter>
    </StrictMode>,
  );
}
