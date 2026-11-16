// Mise en forme française des nombres et des dates
const nf = (d: number) => new Intl.NumberFormat("fr-FR", { maximumFractionDigits: d, minimumFractionDigits: 0 });

export function nombre(v: number | null | undefined, unite = ""): string {
  if (v === null || v === undefined) return "—";
  const decimales = Math.abs(v) >= 1000 ? 0 : Math.abs(v) >= 100 ? 1 : 2;
  const texte = nf(decimales).format(v);
  return unite.trim().startsWith("%") ? `${texte} %` : unite === "points de %" ? `${texte} pts` : texte;
}

export function dateHeure(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" });
}
