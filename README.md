# PDIF — Plateforme de Données de l'Inclusion Financière

Plateforme interne de l'Unité d'Inclusion Financière (UIF) de la BRH : collecte des données de l'inclusion financière (FMI, Banque mondiale, IHSI, puis directions de la BRH), contrôle qualité, entrepôt historisé, tableaux de bord des KPI de la SNIF et du PNEF.

La fiche de mise en œuvre complète est dans [`CLAUDE.md`](CLAUDE.md).

> **Règles de base :** aucune donnée de la BRH et aucun secret dans ce dépôt. Phase 1 = données publiques uniquement.

## État d'avancement

| Étape | Contenu | État |
| --- | --- | --- |
| 1 | Dépôt, structure, environnement, README | ✅ terminée (en attente de validation) |
| 2 | Modèle de données et migrations | à faire |
| 3 → 15 | voir `CLAUDE.md`, section 11 | à faire |

## Prérequis

- Python 3.11 ou plus récent (`python3 --version`)
- Node.js 20 ou plus récent (`node --version`)

## Installation (une seule fois)

```bash
cp .env.example .env
```

```bash
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
```

```bash
cd frontend && npm install
```

Sous Windows, remplacer `.venv/bin/` par `.venv\Scripts\`.

## Lancement (deux terminaux)

**Terminal 1 — backend (API)** :

```bash
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000
```

- Vérification : http://localhost:8000/api/sante doit afficher `"statut":"ok"`.
- Documentation automatique de l'API : http://localhost:8000/docs

**Terminal 2 — frontend (interface)** :

```bash
cd frontend && npm run dev
```

- Ouvrir http://localhost:5173 : la carte doit afficher « Backend : ok (developpement) ».
- Le frontend transmet tous les appels `/api/...` au backend (réglage `proxy` dans `frontend/vite.config.ts`).

## Tests

```bash
cd backend && .venv/bin/pytest
```

```bash
cd frontend && npm test
```

## Organisation du dépôt

```
backend/app/        API FastAPI (main.py), configuration (config.py), base (db.py)
  models/           tables (étape 2)
  connectors/       connecteurs FMI, Banque mondiale, IHSI, dépôt (étapes 4 à 6, 13)
  quality/          contrôles qualité (étape 7)
  api/              routes (étape 8)
backend/migrations/ migrations Alembic (étape 2)
backend/tests/      tests pytest ; fixtures/ = petits échantillons de réponses API
frontend/src/       interface React ; pages/, components/, theme.ts
templates/          modèles Excel de transmission des directions (étape 13)
docs/               sources, dictionnaire, KPI, procédures
```

## Configuration

Tous les réglages sont dans `.env` (jamais versionné). Le modèle est `.env.example`.

| Variable | Rôle | Valeur en développement |
| --- | --- | --- |
| `DATABASE_URL` | Adresse de la base | `sqlite:///./pdif.db` (PostgreSQL sur le serveur BRH) |
| `ENVIRONMENT` | Nom de l'environnement | `developpement` |
| `FRONTEND_ORIGIN` | Adresse autorisée à appeler l'API | `http://localhost:5173` |

## En cas de problème

- **« Backend injoignable » dans l'interface** : le terminal 1 est-il lancé ? Ouvrir http://localhost:8000/api/sante pour vérifier.
- **`ModuleNotFoundError`** : l'environnement Python n'est pas installé ou la commande n'a pas été lancée depuis `backend/`.
- **`address already in use`** : un serveur tourne déjà sur ce port. Le fermer ou changer de port.
