import { useState, type ButtonHTMLAttributes, type ReactNode } from "react";
import { Outlet } from "react-router-dom";
import { DEMO } from "../api";
import { IconeMenu } from "./Icones";
import Sidebar from "./Sidebar";

export default function Layout() {
  const [menuOuvert, setMenuOuvert] = useState(false);
  return (
    <div className="flex min-h-screen">
      <Sidebar ouvert={menuOuvert} fermer={() => setMenuOuvert(false)} />
      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-20 flex items-center gap-3 bg-marine px-4 py-2 text-white lg:hidden">
          <button type="button" onClick={() => setMenuOuvert(true)} aria-label="Ouvrir le menu" aria-controls="menu-principal"
            aria-expanded={menuOuvert} className="flex h-11 w-11 items-center justify-center rounded-lg">
            <IconeMenu />
          </button>
          <span className="text-lg font-bold">PDIF</span>
        </header>
        {DEMO && (
          <div role="note" className="border-b border-[#e8c879] bg-[#fff6e0] px-4 py-2.5 text-[13px] text-[#5c4300] sm:px-6 lg:px-10">
            <strong>Prototype de démonstration non officiel</strong> — lecture seule, données publiques du FMI et de la
            Banque mondiale figées. Les actions (mises à jour, validation, dépôt) demandent la version installée sur un serveur.
          </div>
        )}
        <div className="px-4 py-6 sm:px-6 lg:px-10 lg:py-8">
          <main className="mx-auto flex max-w-[1160px] flex-col gap-6">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}

export function EnTete({ titre, sousTitre, children }: { titre: string; sousTitre?: string; children?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div className="flex flex-col gap-1">
        <h1 className="m-0 text-[26px] font-semibold text-marine sm:text-[28px]">{titre}</h1>
        {sousTitre && <p className="m-0 text-[15px] text-discret">{sousTitre}</p>}
      </div>
      {children}
    </div>
  );
}

export function Section({ titre, sousTitre, children, action, className = "" }:
  { titre: string; sousTitre?: string; children: ReactNode; action?: ReactNode; className?: string }) {
  return (
    <section className={`flex min-w-0 flex-col gap-4 rounded-xl border border-bordure bg-white p-5 ${className}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex flex-col gap-0.5">
          <h2 className="m-0 text-[17px] font-semibold text-marine">{titre}</h2>
          {sousTitre && <span className="text-[13px] text-discret">{sousTitre}</span>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

export function Bandeau({ children, ton = "attention" }: { children: ReactNode; ton?: "attention" | "danger" | "info" | "succes" }) {
  const styles = {
    attention: "bg-[#fff6e0] border-[#e8c879] text-[#5c4300]",
    danger: "bg-[#fde7e2] border-[#efb1a3] text-[#7d1d0b]",
    info: "bg-[#e9f0f9] border-[#b9c6d8] text-marine",
    succes: "bg-[#e3f4e8] border-[#a9d8b7] text-[#1d5b33]",
  }[ton];
  return (
    <div role="status" className={`flex items-start gap-3 rounded-xl border px-4 py-3.5 text-sm ${styles}`}>
      {children}
    </div>
  );
}

export function Bouton({ children, variante = "principal", ...props }:
  ButtonHTMLAttributes<HTMLButtonElement> & { variante?: "principal" | "secondaire" | "or" | "danger" }) {
  const styles = {
    principal: "bg-marine text-white hover:bg-marine-fonce",
    secondaire: "bg-white text-marine border border-champ hover:border-marine",
    or: "bg-or text-marine hover:brightness-95",
    danger: "bg-white text-[#a1260f] border border-[#efb1a3] hover:bg-[#fde7e2]",
  }[variante];
  return (
    <button type="button" {...props}
      className={`inline-flex min-h-[44px] items-center justify-center gap-2 rounded-lg px-[18px] text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50 ${styles} ${props.className ?? ""}`}>
      {children}
    </button>
  );
}
