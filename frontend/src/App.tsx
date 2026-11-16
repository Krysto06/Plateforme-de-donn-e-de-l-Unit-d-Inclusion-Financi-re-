import { useEffect, useState } from "react";

type Sante = { statut: string; environnement: string };

// Écran provisoire de l'étape 1 : il vérifie seulement que l'interface parle au backend.
export default function App() {
  const [sante, setSante] = useState<Sante | null>(null);
  const [erreur, setErreur] = useState(false);

  useEffect(() => {
    fetch("/api/sante")
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(setSante)
      .catch(() => setErreur(true));
  }, []);

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow p-8 max-w-md w-full border-t-4 border-or">
        <h1 className="text-2xl font-semibold text-marine">PDIF</h1>
        <p className="mt-1">Plateforme de Données de l'Inclusion Financière — UIF, BRH</p>
        <p className="mt-6" role="status">
          {sante && `Backend : ${sante.statut} (${sante.environnement})`}
          {erreur && "Backend injoignable : vérifiez qu'il tourne sur le port 8000."}
          {!sante && !erreur && "Vérification du backend…"}
        </p>
      </div>
    </main>
  );
}
