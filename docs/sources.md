# Sources de données — codes vérifiés

Règle n° 3 : aucun code d'indicateur, identifiant de jeu de données ou URL d'API n'est utilisé sans avoir été
vérifié auprès de l'API et noté ici avec sa date. Les correspondances sont en base (table `serie_source`) et dans
`backend/app/data/series_sources.csv`.

## Banque mondiale — API Indicators v2 (sans clé)

- Adresse : `https://api.worldbank.org/v2/country/{pays;pays;...}/indicator/{code}?format=json&per_page=1000&date=AAAA:AAAA&page=n`
- Vérifié le **16/11/2026** en interrogeant `https://api.worldbank.org/v2/indicator/{code}?format=json`.
- Pays demandés : HTI, DOM, JAM, NIC, BRA, FRA, CAN (réglable : `PAYS_COMPARAISON` dans `.env`).
- Agrégat régional disponible si besoin : `LCN` (Amérique latine et Caraïbes), vérifié le 16/11/2026 ; **non activé**.

| Code | Libellé renvoyé par l'API | KPI | Vérifié le |
| --- | --- | --- | --- |
| `FB.CBK.BRCH.P5` | Commercial bank branches (per 100,000 adults) | ACC-01 | 2026-11-16 |
| `FB.ATM.TOTL.P5` | Automated teller machines (ATMs) (per 100,000 adults) | ACC-02 | 2026-11-16 |
| `FB.CBK.DPTR.P3` | Depositors with commercial banks (per 1,000 adults) | USA-01 | 2026-11-16 |
| `FB.CBK.BRWR.P3` | Borrowers from commercial banks (per 1,000 adults) | USA-02 | 2026-11-16 |
| `FX.OWN.TOTL.ZS` | Account ownership at a financial institution or with a mobile-money-service provider (% of population ages 15+) | USA-04 (Total) | 2026-11-16 |
| `FX.OWN.TOTL.FE.ZS` | … female (% of population ages 15+) | USA-04 (F) → GEN-01 | 2026-11-16 |
| `FX.OWN.TOTL.MA.ZS` | … male (% of population ages 15+) | USA-04 (H) → GEN-01 | 2026-11-16 |

**Comportement observé** : l'API est lente et irrégulière (requêtes bloquées 30 à 60 s puis réponse en moins
d'une seconde à l'essai suivant). D'où un délai court (25 s) et 5 essais avec attente croissante (`.env`).

## FMI — Financial Access Survey, API SDMX 3.0

- Base : `https://api.imf.org/external/sdmx/3.0`
- Jeu de données trouvé par `structure/dataflow/*/*/+` le **16/11/2026** : `IMF.STA:FAS` version 9.0.0,
  « Financial Access Survey (FAS) », structure `IMF.STA:DSD_FAS` 10.0.0.
- Dimensions (dans l'ordre de la clé) : `COUNTRY`, `INDICATOR`, `SECTOR`, `COUNTERPARTY_SECTOR`, `SEX`,
  `TYPE_OF_TRANSFORMATION`, `FREQUENCY`.
- Listes de codes : `CL_FAS_INDICATOR` 4.1.0 (31 codes), `CL_FAS_TYPE_OF_TRANSFORMATION` 4.0.0 (7 codes) ;
  copie dans `backend/tests/fixtures/imf/codelists_fas.json`.
- Requête de données (un seul appel pour tous les pays) :
  `{base}/data/dataflow/IMF.STA/FAS/+/HTI+DOM+JAM+NIC+BRA+FRA+CAN.*.*.*.*.*.A` avec l'en-tête `Accept: application/json`.
  La virgule entre pays est refusée (code 400) ; le `+` fonctionne.
- Une pause d'une seconde suit chaque appel (limites de requêtes).

Code de série enregistré = `INDICATOR.SECTOR.COUNTERPARTY_SECTOR.SEX.TYPE_OF_TRANSFORMATION`.

| Code de série | Signification | KPI | Vérifié le |
| --- | --- | --- | --- |
| `FA22.COMBANK._Z._T.PHTADLT_NUM` | Agences hors siège, banques commerciales, pour 100 000 adultes | ACC-01 | 2026-11-16 |
| `FA18._Z._Z._T.PHTADLT_NUM` | Distributeurs automatiques pour 100 000 adultes | ACC-02 | 2026-11-16 |
| `FA5._Z._Z._T.PHTADLT_NUM` | Points d'agents mobile money **actifs** pour 100 000 adultes | ACC-03 | 2026-11-16 |
| `FA29.COMBANK._Z._T.PTADLT_NUM` | Déposants, banques commerciales, pour 1 000 adultes | USA-01 | 2026-11-16 |
| `FA21.COMBANK._Z._T.PTADLT_NUM` | Emprunteurs, banques commerciales, pour 1 000 adultes | USA-02 | 2026-11-16 |
| `FA63._Z._Z._T.PTADLT_NUM` | Comptes mobile money actifs pour 1 000 adultes | USA-03 | 2026-11-16 |
| `OUTD.COMBANK._Z._T.POGDP` | Encours des dépôts, banques commerciales, % du PIB | PRO-01 | 2026-11-16 |
| `OUTL.COMBANK._Z._T.POGDP` | Encours des crédits, banques commerciales, % du PIB | PRO-02 | 2026-11-16 |
| `FA21.COMBANK.S14.F.NUM` | Emprunteurs ménages, femmes (nombre) | AUX-EMP (F) → GEN-02 | 2026-11-16 |
| `FA21.COMBANK.S14.M.NUM` | Emprunteurs ménages, hommes (nombre) | AUX-EMP (H) → GEN-02 | 2026-11-16 |
| `FA21.COMBANK.S14._T.NUM` | Emprunteurs ménages, total (nombre) | AUX-EMP (Total) | 2026-11-16 |

**Constat sur les données** : pour Haïti, emprunteuses + emprunteurs ≠ total (2020 : 76 180 contre 79 812),
car le total compte les emprunteurs de sexe non déclaré. AUX-EMP n'est donc pas soumis à la règle F + H = Total,
et GEN-02 se calcule parmi les emprunteurs de sexe connu : `100 × F / (F + H)`.

## Valeurs de contrôle (fiche, section 8.5) — retrouvées le 16/11/2026

| Indicateur | Année | Source | Fiche | Valeur chargée | Écart |
| --- | --- | --- | --- | --- | --- |
| Agences pour 100 000 adultes | 2020 | FMI FAS | 2,67 | 2,6655 | 0,005 ✅ |
| Agences pour 100 000 adultes | 2020 | Banque mondiale | 2,62 | 2,6655 | 0,046 ✅ (tolérance 0,05) |
| Déposants pour 1 000 adultes | 2020 | FMI FAS | 257,05 | 257,0460 | 0,004 ✅ |
| Dépôts des banques commerciales, % du PIB | 2020 | FMI FAS | 20,25 | 20,2499 | 0,000 ✅ |

La Banque mondiale publie désormais la même valeur que le FMI pour les agences (2,67) : elle reprend les
données FAS et a intégré une révision. Les deux sources restent stockées séparément.

## IHSI

Pas d'API publique connue au 16/11/2026 : import de fichiers (modèle `templates/ihsi_population_v1.xlsx`).
Départements identifiés par leur code ISO 3166-2:HT (HT-AR, HT-CE, HT-GA, HT-NI, HT-ND, HT-NE, HT-NO, HT-OU, HT-SD,
HT-SE). **À confirmer** : la correspondance avec la codification propre de l'IHSI, si ses fichiers l'utilisent.

## Échantillons de test (`backend/tests/fixtures/`)

- `worldbank/*.json`, `imf/fas_comparateurs.json` : vraies réponses des API enregistrées le 16/11/2026 (données publiques).
- `ihsi/population_FICTIVE_2024.csv` : **valeurs inventées** pour les tests, ne pas utiliser comme donnée.

## Journal

- **16/11/2026** : accès réseau à `api.worldbank.org` et `api.imf.org` ouvert dans l'environnement de développement
  (approuvé par Krystofia). Codes vérifiés, premiers chargements réels effectués.
