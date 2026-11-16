# Dictionnaire des données

Toutes les tables sont créées par les migrations Alembic (`backend/migrations/`). Le même schéma fonctionne sous
SQLite (développement) et PostgreSQL (serveur BRH). Données **agrégées uniquement** : aucune table ne contient de
donnée de client.

## Référentiels

**pays** — pays suivis. `code_iso3` (unique, ex. HTI), `nom`, `region`.

**departement** — 10 départements d'Haïti. `code` (ISO 3166-2:HT, ex. HT-OU), `nom`.

**periode** — `annee`, `trimestre` (1–4, vide si annuelle), `type` (annuelle | trimestrielle). Unique sur (année, trimestre). Créée automatiquement au chargement.

**direction** — directions de la BRH (noms à confirmer). `code` (unique), `nom`, `actif`.

**type_institution** — `code` (BANQUE, COOP, IMF, MOBILE, GARANTIE), `libelle`.

**institution** — `nom` (unique), `type_institution_id`, `actif`.

**source** — `code` (WB, FMI, IHSI, UIF, DIR), `nom`, `mode` (api | fichier | formulaire | depot), `url`,
`calendrier_cron` (mise à jour automatique, ex. `0 3 1 * *` = le 1er du mois à 3 h), `delai_alerte_jours`
(au-delà sans mise à jour réussie : « en retard »), `actif`.

**indicateur** — référentiel des KPI (modifiable sans code).
| Colonne | Contenu |
| --- | --- |
| `code` | Code unique (ACC-01…) |
| `libelle`, `dimension`, `unite`, `formule` | Description lisible |
| `calcul` | Formule automatique pour un KPI calculé, ex. `USA-04[H] - USA-04[F]` (nombres, `+ - * /`, parenthèses, références `CODE[F|H|Total]`) |
| `source_attendue`, `source_preferee` | Source prévue ; source affichée en premier quand plusieurs existent |
| `frequence`, `phase` | Fréquence ; phase du projet (1, 2, 3) |
| `est_kpi` | 0 = série auxiliaire (population, emprunteurs) |
| `additif` | 1 si femmes + hommes doivent égaler le total (règle 4) |
| `seuil_variation_pct` | Seuil de la règle 5 (variation d'une année sur l'autre) |
| `actif`, `ordre` | Retrait sans suppression ; ordre d'affichage |

**serie_source** — correspondance indicateur ↔ code de série chez une source. `indicateur_id`, `source_id`,
`code_serie`, `sexe` (F | H | Total), `verifie_le` (date de vérification par l'API, règle 3), `actif`.

## Faits et suivi

**observation** — une valeur publiée.
| Colonne | Contenu |
| --- | --- |
| `cle` | Clé lisible `indicateur|pays|département|sexe|période|institution|source` (`-` si vide) |
| `version`, `est_courante` | Historique : une nouvelle valeur crée la version suivante, l'ancienne passe `est_courante = false` sans être effacée |
| `indicateur_id`, `pays_id`, `departement_id` (facultatif), `sexe`, `periode_id`, `institution_id` (facultatif) | Dimensions |
| `valeur` | Nombre |
| `source_id`, `chargement_id`, `cree_le` | Traçabilité : d'où vient la valeur et par quel chargement |

Unicité : (`cle`, `version`). Relancer un chargement identique ne crée rien (valeurs « inchangées »).

**chargement** — un envoi (API, fichier, dépôt). `source_id`, `cree_le`, `termine_le`, `declencheur`
(automatique | manuel), `auteur`, `fichier_nom`, `nb_lignes`, `nb_nouvelles`, `nb_modifiees`, `nb_inchangees`,
`statut` (reçu | en contrôle | accepté | rejeté | chargé | erreur), `message`, `donnees_json` (valeurs normalisées en
attente de validation, vidé après chargement), `decision_par`, `decision_le`, `decision_commentaire`.

**controle** — résultat d'une règle pour un chargement. `chargement_id`, `regle`, `resultat` (réussi | alerte | échec), `detail`.

**depot** — envoi d'une direction. `direction_id`, `type_institution_id`, `institution_id`, `type_donnees`,
`version_modele`, `periode` (AAAA ou AAAA-Tn), `fichier_nom`, `commentaire`, `certifie_agrege`, `statut`, `auteur`,
`cree_le`, `chargement_id`.

**role** — admin_uif (administratrice UIF), cadre_uif (lecture), point_focal (dépôt).

**utilisateur** — `identifiant` (unique, minuscules), `nom`, `mot_de_passe_hash` (PBKDF2-SHA256, 390 000 itérations ;
jamais le mot de passe en clair), `role_id`, `direction_id` (point focal), `actif`, `cree_le`.

**journal** — `horodatage`, `utilisateur`, `action` (connexion, chargement, validation:accepter, kpi:modification…), `objet`, `detail`.

## Format normalisé (toutes sources)

Avant chargement, chaque source est ramenée aux colonnes : `indicateur`, `pays`, `departement` (vide = national),
`sexe`, `annee`, `trimestre` (0 = annuel), `institution` (vide = ensemble), `valeur`, `source`.
