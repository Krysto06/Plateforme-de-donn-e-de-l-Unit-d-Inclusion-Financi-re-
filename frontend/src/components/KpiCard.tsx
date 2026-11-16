import type { Carte } from "../api";
import { nombre } from "../format";
import StatusBadge, { tonDe } from "./StatusBadge";

export default function KpiCard({ carte, onClick, actif }: { carte: Carte; onClick?: () => void; actif?: boolean }) {
  const vide = carte.valeur === null;
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={actif}
      className={`flex min-h-[44px] flex-col gap-2 rounded-xl border bg-white p-5 text-left transition hover:border-marine ${actif ? "border-marine ring-2 ring-marine/20" : "border-bordure"}`}
    >
      <span className="text-[13px] text-discret">{carte.libelle}</span>
      <span className={`text-[32px] font-semibold leading-tight ${vide ? "text-[#8a95a8]" : "text-marine"}`}>
        {nombre(carte.valeur, carte.unite)}
      </span>
      <span className="text-xs text-discret">
        {vide ? (carte.source_attendue ?? "Source à définir") : carte.source_nom} · {carte.code}
      </span>
      {carte.autres_sources.length > 0 && (
        <span className="text-xs text-discret">
          Autre source : {carte.autres_sources.map((a) => `${a.source} ${nombre(a.valeur, carte.unite)}`).join(", ")}
        </span>
      )}
      <StatusBadge texte={carte.anciennete.libelle} ton={vide ? "info" : tonDe(carte.anciennete.code)} />
    </button>
  );
}
