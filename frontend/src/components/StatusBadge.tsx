// Badge de statut : couleur + texte (jamais la couleur seule)
const TONS = {
  succes: "bg-[#e3f4e8] text-[#1d6b3a]",
  attention: "bg-[#fff1d1] text-[#7a4f00]",
  danger: "bg-[#fde7e2] text-[#a1260f]",
  info: "bg-[#e3ebf6] text-marine",
  neutre: "bg-[#eceff4] text-discret",
} as const;

export type Ton = keyof typeof TONS;

const PAR_STATUT: Record<string, Ton> = {
  "chargé": "succes", "réussi": "succes", "à jour": "succes", recente: "succes",
  "en contrôle": "attention", "alerte": "attention", "en attente": "attention", "en retard": "attention",
  a_surveiller: "attention", "en cours": "info", "reçu": "info", "accepté": "info", a_collecter: "info",
  "rejeté": "danger", "échec": "danger", "erreur": "danger", "en erreur": "danger", ancienne: "danger",
  "jamais chargée": "neutre",
};

export function tonDe(statut: string): Ton {
  return PAR_STATUT[statut] ?? "neutre";
}

export default function StatusBadge({ texte, ton }: { texte: string; ton?: Ton }) {
  return (
    <span className={`inline-flex items-center self-start whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold ${TONS[ton ?? tonDe(texte)]}`}>
      {texte}
    </span>
  );
}
