# Fiches des KPI

Référentiel initial (provisoire, à valider avec le cadre de l'UIF chargé des KPI). Il est chargé en base depuis
`backend/app/data/indicateurs.csv` puis se modifie **sans code** : écran Catalogue (libellé, seuil, source prioritaire,
actif) ou API `PATCH /api/kpi/{code}`, `POST /api/kpi`, `DELETE /api/kpi/{code}` (retrait : les valeurs restent en base).

Ce fichier est généré à partir du CSV initial : la base peut avoir été modifiée depuis (voir l'écran Catalogue).

## ACC-01 — Agences bancaires pour 100 000 adultes

| Champ | Valeur |
| --- | --- |
| Dimension | Accès |
| Unité | pour 100 000 adultes |
| Définition | Agences des banques commerciales (hors siège) / population adulte × 100 000 |
| Source attendue | FMI FAS / Banque mondiale |
| Source affichée en priorité | FMI |
| Fréquence | annuelle |
| Phase | 1 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±30 % d'une année sur l'autre |
| Séries suivies | WB `FB.CBK.BRCH.P5` (Total), vérifié le 2026-11-16<br>FMI `FA22.COMBANK._Z._T.PHTADLT_NUM` (Total), vérifié le 2026-11-16 |

## ACC-02 — Distributeurs automatiques pour 100 000 adultes

| Champ | Valeur |
| --- | --- |
| Dimension | Accès |
| Unité | pour 100 000 adultes |
| Définition | Distributeurs automatiques (GAB) / population adulte × 100 000 |
| Source attendue | FMI FAS / Banque mondiale |
| Source affichée en priorité | FMI |
| Fréquence | annuelle |
| Phase | 1 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±30 % d'une année sur l'autre |
| Séries suivies | WB `FB.ATM.TOTL.P5` (Total), vérifié le 2026-11-16<br>FMI `FA18._Z._Z._T.PHTADLT_NUM` (Total), vérifié le 2026-11-16 |

## ACC-03 — Agents mobile money pour 100 000 adultes

| Champ | Valeur |
| --- | --- |
| Dimension | Accès |
| Unité | pour 100 000 adultes |
| Définition | Points d'agents mobile money actifs / population adulte × 100 000 |
| Source attendue | FMI FAS |
| Source affichée en priorité | FMI |
| Fréquence | annuelle |
| Phase | 1 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±50 % d'une année sur l'autre |
| Séries suivies | FMI `FA5._Z._Z._T.PHTADLT_NUM` (Total), vérifié le 2026-11-16 |

## ACC-04 — Part des communes ayant au moins un point d'accès

| Champ | Valeur |
| --- | --- |
| Dimension | Accès |
| Unité | % |
| Définition | Communes avec au moins un point d'accès / nombre total de communes × 100 |
| Source attendue | Données BRH (phase 2) |
| Source affichée en priorité | — |
| Fréquence | annuelle |
| Phase | 2 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±20 % d'une année sur l'autre |

## USA-01 — Déposants des banques commerciales pour 1 000 adultes

| Champ | Valeur |
| --- | --- |
| Dimension | Usage |
| Unité | pour 1 000 adultes |
| Définition | Déposants des banques commerciales / population adulte × 1 000 |
| Source attendue | FMI FAS / Banque mondiale |
| Source affichée en priorité | FMI |
| Fréquence | annuelle |
| Phase | 1 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±30 % d'une année sur l'autre |
| Séries suivies | WB `FB.CBK.DPTR.P3` (Total), vérifié le 2026-11-16<br>FMI `FA29.COMBANK._Z._T.PTADLT_NUM` (Total), vérifié le 2026-11-16 |

## USA-02 — Emprunteurs des banques commerciales pour 1 000 adultes

| Champ | Valeur |
| --- | --- |
| Dimension | Usage |
| Unité | pour 1 000 adultes |
| Définition | Emprunteurs des banques commerciales / population adulte × 1 000 |
| Source attendue | FMI FAS / Banque mondiale |
| Source affichée en priorité | FMI |
| Fréquence | annuelle |
| Phase | 1 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±30 % d'une année sur l'autre |
| Séries suivies | WB `FB.CBK.BRWR.P3` (Total), vérifié le 2026-11-16<br>FMI `FA21.COMBANK._Z._T.PTADLT_NUM` (Total), vérifié le 2026-11-16 |

## USA-03 — Comptes mobile money actifs pour 1 000 adultes

| Champ | Valeur |
| --- | --- |
| Dimension | Usage |
| Unité | pour 1 000 adultes |
| Définition | Comptes mobile money actifs / population adulte × 1 000 |
| Source attendue | FMI FAS |
| Source affichée en priorité | FMI |
| Fréquence | annuelle |
| Phase | 1 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±50 % d'une année sur l'autre |
| Séries suivies | FMI `FA63._Z._Z._T.PTADLT_NUM` (Total), vérifié le 2026-11-16 |

## USA-04 — Part des adultes ayant un compte

| Champ | Valeur |
| --- | --- |
| Dimension | Usage |
| Unité | % |
| Définition | Adultes (15 ans et plus) ayant un compte dans une institution financière ou de mobile money / adultes × 100 |
| Source attendue | Global Findex |
| Source affichée en priorité | WB |
| Fréquence | triennale |
| Phase | 1 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±30 % d'une année sur l'autre |
| Séries suivies | WB `FX.OWN.TOTL.ZS` (Total), vérifié le 2026-11-16<br>WB `FX.OWN.TOTL.FE.ZS` (F), vérifié le 2026-11-16<br>WB `FX.OWN.TOTL.MA.ZS` (H), vérifié le 2026-11-16 |

## PRO-01 — Dépôts des banques commerciales (% du PIB)

| Champ | Valeur |
| --- | --- |
| Dimension | Profondeur |
| Unité | % du PIB |
| Définition | Encours des dépôts des banques commerciales / PIB × 100 |
| Source attendue | FMI FAS |
| Source affichée en priorité | FMI |
| Fréquence | annuelle |
| Phase | 1 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±30 % d'une année sur l'autre |
| Séries suivies | FMI `OUTD.COMBANK._Z._T.POGDP` (Total), vérifié le 2026-11-16 |

## PRO-02 — Crédits des banques commerciales (% du PIB)

| Champ | Valeur |
| --- | --- |
| Dimension | Profondeur |
| Unité | % du PIB |
| Définition | Encours des crédits des banques commerciales / PIB × 100 |
| Source attendue | FMI FAS |
| Source affichée en priorité | FMI |
| Fréquence | annuelle |
| Phase | 1 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±30 % d'une année sur l'autre |
| Séries suivies | FMI `OUTL.COMBANK._Z._T.POGDP` (Total), vérifié le 2026-11-16 |

## GEN-01 — Écart femmes-hommes dans la détention de compte

| Champ | Valeur |
| --- | --- |
| Dimension | Genre |
| Unité | points de % |
| Définition | Part des hommes ayant un compte − part des femmes ayant un compte |
| Calcul automatique | `USA-04[H] - USA-04[F]` |
| Source attendue | FMI FAS / Findex |
| Source affichée en priorité | WB |
| Fréquence | triennale |
| Phase | 1 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±100 % d'une année sur l'autre |

## GEN-02 — Part des femmes parmi les emprunteurs

| Champ | Valeur |
| --- | --- |
| Dimension | Genre |
| Unité | % |
| Définition | Emprunteuses (ménages) des banques commerciales / (emprunteuses + emprunteurs) × 100, parmi les emprunteurs dont le sexe est connu |
| Calcul automatique | `100 * AUX-EMP[F] / (AUX-EMP[F] + AUX-EMP[H])` |
| Source attendue | FMI FAS |
| Source affichée en priorité | FMI |
| Fréquence | annuelle |
| Phase | 1 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±30 % d'une année sur l'autre |

## MPM-01 — Part des MPME ayant un compte

| Champ | Valeur |
| --- | --- |
| Dimension | MPME |
| Unité | % |
| Définition | MPME ayant un compte / total des MPME × 100 |
| Source attendue | FinScope MPME 2023 (saisie manuelle) |
| Source affichée en priorité | — |
| Fréquence | ponctuelle |
| Phase | 1 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±50 % d'une année sur l'autre |

## MPM-02 — Crédits garantis aux MPME

| Champ | Valeur |
| --- | --- |
| Dimension | MPME |
| Unité | HTG |
| Définition | Encours des crédits garantis aux MPME |
| Source attendue | Fonds de garantie (phase 3) |
| Source affichée en priorité | — |
| Fréquence | annuelle |
| Phase | 3 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±50 % d'une année sur l'autre |

## EF-01 — Supports PNEF distribués

| Champ | Valeur |
| --- | --- |
| Dimension | Éducation financière |
| Unité | nombre |
| Définition | Nombre de supports d'éducation financière distribués |
| Source attendue | UIF (formulaire) |
| Source affichée en priorité | UIF |
| Fréquence | annuelle |
| Phase | 1 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±100 % d'une année sur l'autre |

## EF-02 — Personnes touchées par l'éducation financière

| Champ | Valeur |
| --- | --- |
| Dimension | Éducation financière |
| Unité | nombre |
| Définition | Nombre de personnes touchées par les actions d'éducation financière |
| Source attendue | UIF (formulaire) |
| Source affichée en priorité | UIF |
| Fréquence | annuelle |
| Phase | 1 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±100 % d'une année sur l'autre |

## EF-03 — Score de culture financière

| Champ | Valeur |
| --- | --- |
| Dimension | Éducation financière |
| Unité | score |
| Définition | Score moyen de culture financière de l'enquête |
| Source attendue | Enquête (saisie manuelle) |
| Source affichée en priorité | — |
| Fréquence | ponctuelle |
| Phase | 1 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±50 % d'une année sur l'autre |

## CON-01 — Plaintes reçues et traitées dans les délais

| Champ | Valeur |
| --- | --- |
| Dimension | Protection du consommateur |
| Unité | % |
| Définition | Plaintes traitées dans les délais / plaintes reçues × 100 |
| Source attendue | Données BRH (phase 3) |
| Source affichée en priorité | — |
| Fréquence | annuelle |
| Phase | 3 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±50 % d'une année sur l'autre |

## VER-01 — Part du crédit vert dans le portefeuille

| Champ | Valeur |
| --- | --- |
| Dimension | Finance verte |
| Unité | % |
| Définition | Encours du crédit vert / encours total des crédits × 100 |
| Source attendue | Pilote finance verte (phase 3) |
| Source affichée en priorité | — |
| Fréquence | annuelle |
| Phase | 3 |
| KPI ou série auxiliaire | KPI |
| Seuil de variation inhabituelle | ±50 % d'une année sur l'autre |

## AUX-EMP — Emprunteurs ménages des banques commerciales (nombre)

| Champ | Valeur |
| --- | --- |
| Dimension | Auxiliaire |
| Unité | nombre |
| Définition | Série auxiliaire servant au calcul de GEN-02. Non additive : le total inclut les emprunteurs de sexe non déclaré |
| Source attendue | FMI FAS |
| Source affichée en priorité | FMI |
| Fréquence | annuelle |
| Phase | 1 |
| KPI ou série auxiliaire | auxiliaire |
| Seuil de variation inhabituelle | ±50 % d'une année sur l'autre |
| Séries suivies | FMI `FA21.COMBANK.S14.F.NUM` (F), vérifié le 2026-11-16<br>FMI `FA21.COMBANK.S14.M.NUM` (H), vérifié le 2026-11-16<br>FMI `FA21.COMBANK.S14._T.NUM` (Total), vérifié le 2026-11-16 |

## POP-TOT — Population totale

| Champ | Valeur |
| --- | --- |
| Dimension | Auxiliaire |
| Unité | nombre |
| Définition | Population résidente (dénominateur) |
| Source attendue | IHSI |
| Source affichée en priorité | IHSI |
| Fréquence | annuelle |
| Phase | 1 |
| KPI ou série auxiliaire | auxiliaire |
| Seuil de variation inhabituelle | ±20 % d'une année sur l'autre |

## POP-ADU — Population adulte (15 ans et plus)

| Champ | Valeur |
| --- | --- |
| Dimension | Auxiliaire |
| Unité | nombre |
| Définition | Population de 15 ans et plus (dénominateur des taux par adulte) |
| Source attendue | IHSI |
| Source affichée en priorité | IHSI |
| Fréquence | annuelle |
| Phase | 1 |
| KPI ou série auxiliaire | auxiliaire |
| Seuil de variation inhabituelle | ±20 % d'une année sur l'autre |
