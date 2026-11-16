# Procédures d'exploitation

Toutes les commandes se lancent depuis le dossier `backend/`, environnement Python activé
(`source .venv/bin/activate`, ou préfixe `.venv/bin/`).

## 1. Démarrer en développement

Voir la section « Lancement » du `README.md`.

## 2. Gérer les comptes

- Créer un compte (le mot de passe est demandé sans s'afficher, 12 caractères au moins) :
  `python -m app.cli creer-utilisateur prenom.nom "Prénom Nom" admin_uif`
  Rôles : `admin_uif` (tout), `cadre_uif` (lecture de l'espace UIF), `point_focal` (dépôt, avec `--direction CODE`).
- Une direction doit exister avant son point focal : `POST /api/directions` (page /docs) avec un code et un nom.

## 3. Mettre à jour une source API

- Depuis l'écran **Sources et connexions** : choisir la source, « Tester la connexion » puis « Lancer une mise à jour ».
  L'état s'actualise seul ; le résultat apparaît dans l'historique.
- En ligne de commande : `python -m app.cli maj WB` ou `python -m app.cli maj FMI`.
- Si l'API ne répond pas, le chargement passe au statut **erreur** avec le message (délai dépassé, code HTTP…).
  Relancer plus tard ; la Banque mondiale est souvent lente.

## 4. Valider un envoi (écran Contrôle qualité)

1. Les envois « à valider » sont en tête de liste.
2. Lire le résultat des 6 règles et l'aperçu des valeurs.
3. **Accepter** charge les valeurs ; **Renvoyer** exige un commentaire (visible par la direction).
Un **échec** a déjà bloqué l'envoi : il faut corriger le fichier et le déposer à nouveau.

Seules les valeurs nouvelles ou modifiées sont examinées par la règle 5 : une relance identique se charge seule.

## 5. Importer un fichier IHSI

Écran Connexions → IHSI → télécharger le modèle `ihsi_population_v1.xlsx`, le remplir (une ligne par
département × sexe × tranche d'âge), puis « Importer et contrôler ». Ou : `python -m app.cli importer-ihsi fichier.xlsx`.
Le total national n'est calculé que si les 10 départements sont présents.

## 6. Modifier le référentiel des KPI

Écran **Catalogue** → « Modifier » (libellé, seuil de variation, source prioritaire, actif), ou API `/api/kpi`.
Ajouter une série source : `POST /api/kpi/{code}/series` avec la date de vérification (règle 3 : vérifier d'abord le
code auprès de l'API et le noter dans `docs/sources.md`). Toute modification est tracée dans le journal.

## 7. Mises à jour planifiées

Mettre `PLANIFICATION_ACTIVE=true` dans `.env` et redémarrer l'API. Calendrier par source (colonne
`calendrier_cron`) : Banque mondiale le 1er du mois à 3 h, FMI le 1er du mois à 4 h (heure de Port-au-Prince).
Une vérification des retards tourne chaque jour à 7 h (journal de l'API) ; l'écran Connexions affiche « en retard »
si aucune mise à jour réussie depuis `delai_alerte_jours` (45 jours pour les API).
Alternative sur le serveur : désactiver la planification interne et utiliser cron :
`0 3 1 * * cd /opt/pdif/backend && .venv/bin/python -m app.cli maj WB >> /var/log/pdif/maj.log 2>&1`

## 8. Exports

Écran **Rapports et exports** : choisir KPI, pays, années ; Excel ou CSV (séparateur `;`, virgule décimale,
s'ouvre directement dans Excel). Chaque ligne porte la source, la version et le numéro de chargement.

## 9. Retrouver l'origine d'une valeur publiée

Numéro de chargement (export ou API) → écran Contrôle qualité `?chargement=N` : date, auteur, fichier, contrôles,
décision. Les anciennes versions restent dans la table `observation` (`est_courante = false`).

---

# Installation sur un serveur de la BRH (procédure pour la direction informatique)

> **Ne pas exécuter sans le feu vert écrit de Krystofia K. Elien.** Cette procédure est préparée, pas appliquée.

## Prérequis
- Serveur Linux interne (Ubuntu 22.04+ ou RHEL 9), Python 3.11+, Node.js 20+ (pour construire l'interface seulement),
  PostgreSQL 14+, un serveur web (Nginx), un certificat TLS interne.
- Sortie HTTPS autorisée vers `api.worldbank.org` et `api.imf.org` uniquement.

## Étapes
1. **Base** : créer l'utilisateur et la base PostgreSQL `pdif` (mot de passe fort, conservé par la DSI).
2. **Code** : copier le dépôt dans `/opt/pdif` (utilisateur système dédié `pdif`, sans shell).
3. **Configuration** : `cp .env.example .env`, puis renseigner :
   `DATABASE_URL=postgresql+psycopg://pdif:MOTDEPASSE@localhost:5432/pdif`, une `SECRET_KEY` générée
   (`python3 -c "import secrets; print(secrets.token_urlsafe(48))"`), `ENVIRONMENT=production`,
   `FRONTEND_ORIGIN=https://pdif.brh.interne` (adresse réelle), `PLANIFICATION_ACTIVE=true`.
   `DEPOTS_DIRECTIONS_OUVERTS=true` seulement après accord. Droits du fichier : `chmod 600 .env`.
4. **Backend** : `cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`,
   puis `.venv/bin/alembic upgrade head` et `.venv/bin/python -m app.cli init`.
5. **Premier compte** : `.venv/bin/python -m app.cli creer-utilisateur ...` (rôle `admin_uif`).
6. **Service** : lancer l'API avec un service systemd :
   `ExecStart=/opt/pdif/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1`
   (un seul processus tant que la planification interne est active, sinon les tâches seraient doublées).
7. **Interface** : `cd frontend && npm ci && npm run build` ; Nginx sert `frontend/dist/` et transmet `/api/` à
   `http://127.0.0.1:8000`. Toute adresse inconnue renvoie `index.html` (`try_files $uri /index.html`).
8. **Sauvegardes** : `pg_dump` quotidien chiffré, conservation selon la politique de la BRH ; tester une restauration.
9. **Contrôle** : `https://…/api/sante` doit répondre `"statut":"ok"` ; se connecter ; lancer « Tester la connexion »
   pour la Banque mondiale et le FMI.

## Points à valider avec la DSI avant mise en service
- Authentification par l'annuaire de la BRH (remplacerait les comptes locaux).
- Jeton de session : actuellement conservé par le navigateur (sessionStorage) ; en production, préférer un cookie
  `HttpOnly` et `Secure`.
- Le schéma a été testé sous SQLite ; **un premier essai complet sous PostgreSQL reste à faire** sur le serveur de test.
