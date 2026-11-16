# PDIF — Plateforme de Données de l'Inclusion Financière

Plateforme interne de l'Unité d'Inclusion Financière (UIF) de la BRH : collecte des données de l'inclusion
financière (FMI, Banque mondiale, IHSI, puis directions de la BRH), contrôle qualité, entrepôt historisé,
tableaux de bord des KPI de la SNIF et du PNEF, exports.

La fiche de mise en œuvre est dans [`CLAUDE.md`](CLAUDE.md).

> **Règles de base :** aucune donnée de la BRH et aucun secret dans ce dépôt. Phase 1 = données publiques uniquement.
> Pas de déploiement sans le feu vert de Krystofia.

## État d'avancement

| Étape | Contenu | État |
| --- | --- | --- |
| 1 | Dépôt, structure, environnement | ✅ |
| 2 | Modèle de données et migrations (16 tables) | ✅ |
| 3 | Référentiel KPI (19 KPI + 3 séries auxiliaires), modifiable sans code | ✅ |
| 4 | Connecteur Banque mondiale (HTI + DOM, JAM, NIC, BRA, FRA, CAN) | ✅ valeurs de contrôle retrouvées |
| 5 | Connecteur FMI FAS (SDMX 3.0) | ✅ valeurs de contrôle retrouvées |
| 6 | Import IHSI (population) | ✅ testé sur un fichier **fictif** |
| 7 | Moteur de contrôle qualité (6 règles) | ✅ |
| 8 | API FastAPI | ✅ documentée sur `/docs` |
| 9 | Authentification et 3 rôles | ✅ |
| 10–13 | Interface : connexion, menu, tableau de bord, connexions, qualité, dépôt, catalogue, rapports | ✅ |
| 14 | Mises à jour planifiées, retards signalés | ✅ |
| 15 | Exports, documentation, procédure d'installation BRH | ✅ procédure rédigée, **non appliquée** |

Tests : 88 tests backend (pytest) et 4 tests interface (Vitest).

## Prérequis

- Python 3.11 ou plus récent, Node.js 20 ou plus récent.

## Installation (une seule fois)

```bash
cp .env.example .env
```

Dans `.env`, remplacer `SECRET_KEY` par une clé générée avec :

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

```bash
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
```

```bash
cd backend && .venv/bin/alembic upgrade head && .venv/bin/python -m app.cli init
```

```bash
cd backend && .venv/bin/python -m app.cli creer-utilisateur krystofia "Krystofia K. Elien" admin_uif
```

```bash
cd frontend && npm install
```

Sous Windows, remplacer `.venv/bin/` par `.venv\Scripts\`.

## Lancement (deux terminaux)

**Terminal 1 — API** :

```bash
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000
```

- http://localhost:8000/api/sante doit afficher `"statut":"ok"` ; documentation de l'API : http://localhost:8000/docs

**Terminal 2 — interface** :

```bash
cd frontend && npm run dev
```

- Ouvrir http://localhost:5173 et se connecter.

**Charger les données publiques** (ou bouton « Lancer une mise à jour » de l'écran Connexions) :

```bash
cd backend && .venv/bin/python -m app.cli maj FMI
```

```bash
cd backend && .venv/bin/python -m app.cli maj WB
```

Le premier chargement attend une validation (écran Contrôle qualité) : il contient des variations inhabituelles
historiques à confirmer.

## Tests

```bash
cd backend && .venv/bin/pytest
```

```bash
cd frontend && npm test
```

Les tests n'appellent jamais les API : ils rejouent de vraies réponses enregistrées dans `backend/tests/fixtures/`.

## Organisation du dépôt

```
backend/app/
  config.py, db.py, main.py   réglages (.env), base, application FastAPI
  models/                     les 16 tables
  data/*.csv                  référentiels initiaux (KPI, séries vérifiées, pays, départements, sources)
  connectors/                 worldbank.py, imf.py, ihsi.py, depot.py (interface commune : base.py)
  quality/                    modeles.py (modèles de fichiers), regles.py (les 6 règles)
  services/                   chargement.py (circuit de chargement), calculs.py (KPI calculés), sécurité, comptes…
  api/                        routes : auth, kpi, sources, chargements, depots, exports, admin
  scheduler.py, cli.py        planification ; commandes d'exploitation
backend/migrations/           migrations Alembic
backend/tests/                tests ; fixtures/ = réponses API réelles + fichier IHSI fictif
frontend/src/                 interface React (pages/, components/, theme.ts)
templates/                    modèles Excel de transmission (générés par « app.cli init »)
docs/                         sources.md, dictionnaire.md, kpi.md, procedures.md (dont installation serveur BRH)
```

## Configuration (`.env`)

| Variable | Rôle | Valeur par défaut |
| --- | --- | --- |
| `DATABASE_URL` | Base de données | `sqlite:///./pdif.db` (PostgreSQL sur le serveur BRH) |
| `SECRET_KEY` | Signature des sessions (obligatoire, 32 caractères au moins) | — |
| `PAYS_COMPARAISON` | Pays comparés à Haïti | `DOM,JAM,NIC,BRA,FRA,CAN` |
| `HTTP_TIMEOUT_SECONDES`, `HTTP_ESSAIS` | Patience envers les API | 25 s, 5 essais |
| `PLANIFICATION_ACTIVE` | Mises à jour automatiques | `false` |
| `DEPOTS_DIRECTIONS_OUVERTS` | Ouvre le dépôt des directions (seulement sur le serveur BRH) | `false` |

## En cas de problème

- **« Backend injoignable » / pages vides** : le terminal 1 tourne-t-il ? Ouvrir http://localhost:8000/api/sante.
- **`secret_key` … Field required** au démarrage : `SECRET_KEY` manque dans `.env`.
- **`no such table`** : lancer `alembic upgrade head` puis `python -m app.cli init`.
- **Mise à jour en « erreur »** : lire le message dans l'historique (délai dépassé = API lente : relancer).
- **Envoi « rejeté »** : l'écran Contrôle qualité donne la règle en échec et les lignes en cause.
