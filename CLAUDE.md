# PDIF — Plateforme de Données de l'Inclusion Financière (UIF, BRH)

> Fiche de mise en œuvre pour Claude Code. À placer à la racine du dépôt sous le nom `CLAUDE.md`.
> Cheffe de projet : Krystofia K. Elien, chargée de gestion et d'analyse de données, Unité d'Inclusion Financière (UIF), Banque de la République d'Haïti (BRH).
> Version 1 — 16 novembre 2026.

---

## 1. Ce qu'on construit

Une plateforme web interne qui :

1. **se connecte** aux sources de données de l'inclusion financière :
   - FMI (Financial Access Survey) par API ;
   - Banque mondiale (WDI, Global Findex) par API ;
   - IHSI par import de fichiers ;
   - plus tard, les directions de la BRH par dépôt de fichiers standardisés ;
2. **contrôle la qualité** de chaque envoi avant de l'enregistrer ;
3. **stocke** les données dans un entrepôt unique et historisé ;
4. **restitue** les KPI de la SNIF et du PNEF dans des tableaux de bord, des rapports et des exports.

Documents de référence :
- **Fiche de projet** (objectifs, périmètre, KPI, risques) : https://claude.ai/artifact/Ce4R5H1b5thsDyYyHSh58q
- **Maquettes des écrans** : https://claude.ai/artifact/PcrfhriGi7oMtwsmaV2re3

---

## 2. Règles non négociables

1. **Aucune donnée de la BRH dans le dépôt, sur un service gratuit externe ou sur un compte personnel.** La phase 1 n'utilise que des données publiques (FMI, Banque mondiale, IHSI). Les données des directions n'arrivent qu'une fois la plateforme hébergée sur un serveur de la BRH.
2. **Aucun déploiement sans le feu vert explicite de Krystofia.** Ni mise en ligne, ni hébergement, ni partage de lien sans son accord écrit dans la conversation.
3. **Ne jamais inventer un code d'indicateur, un identifiant de jeu de données ou une URL d'API.** Les trouver en interrogeant les métadonnées de l'API, les noter dans `docs/sources.md` avec la date de vérification, puis seulement les utiliser.
4. **Aucun secret dans le code** (mots de passe, clés). Ils vont dans un fichier `.env`, avec `.env.example` comme modèle et `.env` dans `.gitignore`.
5. **Données agrégées uniquement.** Aucune donnée nominative de client ne doit pouvoir être chargée, et les contrôles doivent refuser un fichier qui en contient.
6. **Tout est tracé.** Chaque chargement porte une source, une date, un statut et un auteur. Une valeur publiée doit toujours pouvoir être retrouvée.

---

## 3. Façon de travailler avec Krystofia

- **Une étape à la fois.** Suivre le plan de la section 11. À la fin de chaque étape, s'arrêter, montrer le résultat et attendre sa validation avant de passer à la suivante.
- **Le code d'abord, l'explication ensuite.** Donner le code de l'étape, puis expliquer simplement en français ce qu'il fait, sans jargon, avec une image concrète si c'est utile.
- **Elle veut comprendre et savoir déboguer.** Quand une erreur survient, expliquer la cause en une ou deux phrases, puis montrer comment la trouver soi-même (message d'erreur, log, test).
- **Être direct.** Signaler franchement un choix discutable, un risque ou une meilleure option, avant d'exécuter.
- **Documenter au fil de l'eau.** `README.md` et le dossier `docs/` sont à jour à la fin de chaque étape.
- Si l'environnement bloque l'accès réseau aux API, le dire tout de suite. Proposer alors de travailler sur un petit échantillon enregistré dans `tests/fixtures/`, sans contourner le blocage.

---

## 4. Choix techniques

| Couche | Choix | Pourquoi |
| --- | --- | --- |
| Langage des connecteurs et de l'API | Python 3.11+ | Analyse de données, écosystème riche |
| API web | FastAPI | Simple et documenté automatiquement |
| Accès base | SQLAlchemy 2 + Alembic (migrations) | Le même code tourne sur SQLite et PostgreSQL |
| Base de données | **SQLite en développement**, **PostgreSQL en production (serveur BRH)** | Démarrer sans installation, viser PostgreSQL |
| Traitement | pandas, requests (ou httpx) | Nettoyage et appels API |
| Interface | React + TypeScript + Tailwind CSS + Recharts (Vite) | Stack déjà utilisée par l'UIF pour SPS-UIF |
| Planification | APScheduler (ou cron sur le serveur) | Mises à jour automatiques |
| Tests | pytest (back), Vitest (front) | Chaque connecteur est testé |
| Authentification | Comptes locaux et rôles en phase 1 ; annuaire de la BRH plus tard | Pas de dépendance externe |

Si un autre choix paraît nettement meilleur, le proposer avec ses avantages et ses inconvénients **avant** de l'appliquer.

---

## 5. Structure du dépôt

```
pdif/
├── CLAUDE.md                 ← cette fiche
├── README.md                 ← installation, lancement, commandes
├── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py           ← FastAPI
│   │   ├── config.py         ← lecture du .env
│   │   ├── db.py             ← moteur SQLAlchemy
│   │   ├── models/           ← tables
│   │   ├── connectors/       ← imf.py, worldbank.py, ihsi.py, depot.py
│   │   ├── quality/          ← contrôles qualité
│   │   ├── api/              ← routes (auth, kpi, sources, depots, qualite)
│   │   └── scheduler.py
│   ├── migrations/           ← Alembic
│   └── tests/
│       └── fixtures/         ← petits échantillons de réponses API
├── frontend/
│   └── src/
│       ├── pages/            ← Login, Dashboard, Connexions, Qualite, Depot, Catalogue, Rapports
│       ├── components/       ← Sidebar, KpiCard, StatusBadge, …
│       └── theme.ts          ← palette et typographie
├── templates/                ← modèles de transmission Excel des directions
└── docs/
    ├── sources.md            ← codes vérifiés, URL, date de vérification
    ├── dictionnaire.md       ← chaque table et chaque variable
    ├── kpi.md                ← fiche de chaque KPI
    └── procedures.md         ← procédures d'exploitation
```

---

## 6. Modèle de données (à affiner à l'étape 2)

**Tables de référence**
- `pays` : code ISO3, nom, région
- `departement` : code, nom
- `periode` : année, trimestre éventuel, type (annuelle ou trimestrielle)
- `direction` : directions de la BRH (noms à confirmer)
- `type_institution` : banque commerciale, caisse populaire ou coopérative, IMF, opérateur de mobile money, fonds de garantie
- `institution` : nom, type
- `source` : FMI, Banque mondiale, IHSI, direction X, UIF
- `indicateur` : référentiel des KPI (section 7), avec code, libellé, dimension, unité, formule, source attendue, fréquence

**Tables de faits et de suivi**
- `observation` : indicateur, pays, département (facultatif), sexe (F / H / Total), période, institution (facultatif), valeur, source, id de chargement. Unicité sur (indicateur, pays, département, sexe, période, institution, source).
- `chargement` : source, date, déclencheur (automatique ou manuel), auteur, nombre de lignes, statut (reçu / en contrôle / accepté / rejeté / chargé)
- `controle` : chargement, règle, résultat (réussi / alerte / échec), détail
- `depot` : direction, type d'institution, institution, type de données, période, fichier, commentaire, statut
- `utilisateur`, `role` : administratrice UIF, cadre UIF (lecture), point focal de direction (dépôt)
- `journal` : qui a fait quoi et quand (connexions, chargements, validations)

Une nouvelle valeur pour une même clé n'écrase jamais l'ancienne : l'historique est conservé.

---

## 7. Référentiel initial des KPI

| Code | Indicateur | Source |
| --- | --- | --- |
| ACC-01 | Agences bancaires pour 100 000 adultes | FMI FAS / Banque mondiale |
| ACC-02 | Distributeurs automatiques pour 100 000 adultes | FMI FAS / Banque mondiale |
| ACC-03 | Agents mobile money pour 100 000 adultes | FMI FAS |
| ACC-04 | Part des communes ayant au moins un point d'accès | Données BRH (phase 2) |
| USA-01 | Déposants des banques commerciales pour 1 000 adultes | FMI FAS / Banque mondiale |
| USA-02 | Emprunteurs des banques commerciales pour 1 000 adultes | FMI FAS / Banque mondiale |
| USA-03 | Comptes mobile money actifs pour 1 000 adultes | FMI FAS |
| USA-04 | Part des adultes ayant un compte | Global Findex |
| PRO-01 | Dépôts des banques commerciales (% du PIB) | FMI FAS |
| PRO-02 | Crédits des banques commerciales (% du PIB) | FMI FAS |
| GEN-01 | Écart femmes-hommes dans la détention de compte | FMI FAS / Findex |
| GEN-02 | Part des femmes parmi les emprunteurs | FMI FAS |
| MPM-01 | Part des MPME ayant un compte | FinScope MPME 2023 (saisie manuelle) |
| MPM-02 | Crédits garantis aux MPME | Fonds de garantie (phase 3) |
| EF-01 | Supports PNEF distribués | UIF (formulaire) |
| EF-02 | Personnes touchées par l'éducation financière | UIF (formulaire) |
| EF-03 | Score de culture financière | Enquête (saisie manuelle) |
| CON-01 | Plaintes reçues et traitées dans les délais | Données BRH (phase 3) |
| VER-01 | Part du crédit vert dans le portefeuille | Pilote finance verte (phase 3) |

Ce référentiel est provisoire : il sera validé avec le cadre de l'UIF chargé des KPI. Le code doit donc permettre d'ajouter, de renommer ou de retirer un KPI sans toucher au code des connecteurs (le référentiel est une table, pas du code en dur).

---

## 8. Connecteurs

### 8.1 Banque mondiale (à faire en premier : c'est le plus simple)
- API Indicators v2, sans clé : `https://api.worldbank.org/v2/country/{pays}/indicator/{code}?format=json&per_page=1000`
- Pays : Haïti (HTI), plus les comparateurs République dominicaine (DOM), Jamaïque (JAM), Nicaragua (NIC), Brésil (BRA), France (FRA) et Canada (CAN), plus l'agrégat régional Amérique latine et Caraïbes (LCN, Banque mondiale seulement) (décisions de Krystofia du 16/11/2026 ; réglables dans `.env`, variables `PAYS_COMPARAISON` et `AGREGATS_REGIONAUX`).
- Codes repérés, **à vérifier par l'API avant usage** : `FB.CBK.BRCH.P5` (agences pour 100 000 adultes), `FB.ATM.TOTL.P5` (distributeurs), `FB.CBK.DPTR.P3` (déposants pour 1 000 adultes), `FB.CBK.BRWR.P3` (emprunteurs), `FX.OWN.TOTL.ZS` (détention de compte, Findex).
- Gérer la pagination, les valeurs nulles, les erreurs réseau (3 essais avec attente) et l'idempotence (relancer ne crée pas de doublons).

### 8.2 FMI — Financial Access Survey
- API SDMX 3.0 du FMI. Base indiquée par la documentation publique : `https://api.imf.org/external/sdmx/3.0`. Le portail https://data.imf.org/en/Resource-Pages/IMF-API mentionne aussi SDMX 2.1.
- **D'abord** interroger l'API de structure pour trouver l'identifiant exact du jeu de données FAS, ses dimensions et ses codes d'indicateurs. Les documenter dans `docs/sources.md`, puis écrire le connecteur.
- Respecter les limites de requêtes de l'API (temporisation entre les appels).

### 8.3 IHSI
- Pas d'API publique connue à ce jour : **import de fichiers** (Excel, CSV ; tableaux extraits de PDF si nécessaire) depuis l'écran Connexions, par l'administratrice.
- Premier besoin : population par département, sexe et âge (dénominateurs pour les taux par département).
- Prévoir une interface `Connector` commune, pour pouvoir ajouter plus tard un connecteur API si l'IHSI en ouvre une (sa plateforme de données est en développement).

### 8.4 Dépôt par les directions (phase 2, après accord et hébergement BRH)
- Le point focal choisit : **direction**, **type d'institution**, **institution**, **type de données**, **période**. La plateforme lui propose ensuite le modèle Excel correspondant au type de données.
- Les modèles vivent dans `templates/`, avec un modèle par type de données et une version par modèle.
- Le fichier déposé passe obligatoirement par les contrôles qualité (section 9) avant tout chargement.

### 8.5 Valeurs de contrôle pour les tests
Le connecteur doit retrouver ces valeurs publiées pour Haïti (tolérance ±0,05) :

| Indicateur | Année | Source | Valeur |
| --- | --- | --- | --- |
| Agences pour 100 000 adultes | 2020 | FMI FAS | 2,67 |
| Agences pour 100 000 adultes | 2020 | Banque mondiale | 2,62 |
| Déposants pour 1 000 adultes | 2020 | FMI FAS | 257,05 |
| Dépôts des banques commerciales, % du PIB | 2020 | FMI FAS | 20,25 |

Les deux valeurs différentes pour les agences sont normales (deux sources) : la plateforme doit les garder séparées par source, sans en écraser une.

---

## 9. Contrôles qualité

Chaque chargement passe ces règles. Chacune donne **réussi**, **alerte** ou **échec** :

1. **Format** : colonnes, types et codes (pays, département, période) conformes au modèle.
2. **Complétude** : part de cellules vides par colonne obligatoire.
3. **Doublons** : une seule ligne par clé.
4. **Cohérence** : femmes + hommes = total, et aucun pourcentage hors de 0–100.
5. **Variation inhabituelle** : écart à la période précédente au-delà d'un seuil réglable par indicateur.
6. **Données nominatives** : refus si une colonne ressemble à un nom, un NIF ou un numéro de compte.

Un échec bloque le chargement. Une alerte demande une validation humaine (accepter ou renvoyer avec un commentaire). Tous les résultats sont enregistrés dans la table `controle`.

---

## 10. Écrans (voir les maquettes)

Le design suit les maquettes :
- palette bleu marine `#1a365d`, or `#b8860b`, fond `#eef3f9`, texte `#1b2433` ;
- police IBM Plex Sans ;
- **menu latéral bleu marine sur toute la hauteur**, qui passe au-dessus du contenu sur téléphone.

0. **Connexion** : page séparée. L'espace (UIF ou direction) dépend du rôle.
1. **Tableau de bord** :
   - cartes KPI avec la valeur, la source, l'année et un badge d'ancienneté ;
   - évolution dans le temps ;
   - comparaison régionale ;
   - état du référentiel ;
   - filtres par période, département et sexe.
2. **Sources et connexions** :
   - cartes FMI, Banque mondiale et IHSI ;
   - liste de toutes les sources et de leur statut ;
   - détail d'une connexion : tester, lancer une mise à jour, voir l'historique.
3. **Contrôle qualité** : envoi à valider, résultat de chaque règle, commentaire, boutons accepter ou renvoyer, historique.
4. **Dépôt (espace direction)** : les champs de la section 8.4, un récapitulatif de l'envoi, le téléchargement du modèle, le dépôt du fichier et la case « données agrégées uniquement ».
5. **Catalogue des données** et **Rapports et exports** (CSV et Excel ; questionnaire FAS plus tard).

Accessibilité : vrais `<button>`, `<label>`, contraste suffisant, zones cliquables de 44 px minimum.

---

## 11. Plan de travail (une étape = une validation)

| Étape | Contenu | Critère de fin |
| --- | --- | --- |
| 1 | Dépôt, structure, environnement, README | `backend` et `frontend` démarrent ; les tests vides passent |
| 2 | Modèle de données et migrations | Les tables sont créées ; `docs/dictionnaire.md` est rédigé |
| 3 | Chargement du référentiel KPI | Les 19 KPI sont en base et modifiables sans code |
| 4 | Connecteur Banque mondiale | Données de Haïti et des comparateurs chargées ; valeurs de contrôle retrouvées ; relance sans doublon |
| 5 | Connecteur FMI FAS | Codes documentés ; données chargées ; valeurs de contrôle retrouvées |
| 6 | Import IHSI | Un fichier de population par département importé et contrôlé |
| 7 | Moteur de contrôle qualité | Les 6 règles sont testées sur des fichiers bons et mauvais |
| 8 | API FastAPI | Routes kpi, sources, chargements, contrôles, dépôts, documentées |
| 9 | Authentification et rôles | 3 rôles ; chaque rôle ne voit que son espace |
| 10 | Interface : connexion et menu latéral | Conformes aux maquettes ; navigation complète |
| 11 | Tableau de bord | Les KPI réels s'affichent avec leur source et leur année |
| 12 | Écrans Connexions et Contrôle qualité | Mise à jour lancée depuis l'écran ; validation possible |
| 13 | Écran Dépôt et modèles Excel | Un dépôt fictif fait tout le parcours, du dépôt au chargement |
| 14 | Mises à jour planifiées | Banque mondiale et FMI se relancent selon leur calendrier, retards signalés |
| 15 | Exports et documentation finale | Exports CSV et Excel ; `docs/` complet ; procédure d'installation sur serveur BRH rédigée |

**Ne pas déployer.** À l'étape 15, préparer seulement la procédure d'installation pour la direction informatique de la BRH. Le déploiement attend le feu vert de Krystofia.

---

## 12. Définition de « terminé » pour chaque étape

- Le code tourne et les tests passent.
- Le README et `docs/` sont à jour.
- Krystofia a reçu une explication simple de ce qui a été fait, de comment le vérifier elle-même et de ce qui reste à décider.
- Aucune donnée réelle de la BRH ni aucun secret dans le dépôt.
