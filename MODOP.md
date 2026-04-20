# Mode Opératoire — TechPilot

> Application de gestion d'équipe helpdesk N1.
> Mise à jour : avril 2026

---

## Table des matières

1. [Accès & connexion](#1-accès--connexion)
2. [Navigation & interface](#2-navigation--interface)
3. [Recherche globale (Ctrl+K)](#3-recherche-globale-ctrlk)
4. [Dashboard](#4-dashboard)
5. [Planning](#5-planning)
6. [Escalade N1 — Matrice](#6-escalade-n1--matrice)
7. [Tickets](#7-tickets)
8. [Documents & Gabarits](#8-documents--gabarits)
9. [Suivi doc — Procédures & Améliorations](#9-suivi-doc--procédures--améliorations)
10. [Outils](#10-outils)
11. [Techniciens](#11-techniciens)
12. [Actualités](#12-actualités)
13. [Quêtes](#13-quêtes)
14. [Feedbacks](#14-feedbacks)
15. [Admin — Permissions](#15-admin--permissions)
16. [Admin — Audit](#16-admin--audit)
17. [Admin — Import Excel](#17-admin--import-excel)
18. [Profil utilisateur](#18-profil-utilisateur)

---

## 1. Accès & connexion

L'application est accessible via l'URL Railway (ou en local sur `http://localhost:3000`).

**Connexion**
- Saisir son nom d'utilisateur et son mot de passe sur la page `/login`.
- Deux rôles : **Manager** (accès à toutes les pages, y compris Admin) et **Technicien** (accès restreint aux pages opérationnelles).
- La session est maintenue jusqu'à déconnexion manuelle.

**Déconnexion**
- Cliquer sur l'icône de déconnexion en bas de la sidebar (⇢ à côté de l'avatar).

---

## 2. Navigation & interface

La sidebar à gauche liste toutes les pages. Elle peut être **réduite** (icônes seules) via le bouton `←` en haut à droite de la sidebar — utile sur petit écran.

**Sections sidebar**
| Section | Pages |
|---|---|
| Navigation | Dashboard, Planning, Escalade N1, Tickets, Documents, Outils |
| Équipe | Techniciens, Actualités, Quêtes, Feedbacks |
| Admin *(Manager uniquement)* | Permissions, Audit, Import Excel |

**Header**
- Titre de la page courante.
- Bouton de recherche globale `Ctrl+K` (voir section 3).
- Cloche de notifications : tickets ouverts depuis >48h, feedbacks non traités, quêtes en attente de validation.

---

## 3. Recherche globale (Ctrl+K)

**Ouvrir la recherche**
- Raccourci clavier : `Ctrl+K` (ou `Cmd+K` sur Mac).
- Ou cliquer sur le bouton "Recherche…" dans le header.

**Utilisation**
- Taper au moins 2 caractères pour lancer la recherche en temps réel.
- La recherche couvre simultanément : **Tickets**, **Matrice d'escalade**, **Documents**, **Gabarits**.
- Maximum 5 résultats affichés par catégorie.

**Actions sur les résultats**
| Type de résultat | Action au clic |
|---|---|
| Ticket | Redirige vers la page Tickets |
| Matrice | Redirige vers la page Escalade |
| Document | Redirige vers la page Documents |
| Gabarit | Copie le contenu dans le presse-papiers |

**Fermer** : touche `Échap` ou clic sur le fond sombre.

---

## 4. Dashboard

Page d'accueil opérationnelle. Affiche une vue synthétique de l'activité en temps réel.

**Widgets disponibles**
| Widget | Contenu |
|---|---|
| KPIs | Techniciens actifs / Tickets ouverts / Entrées matrice / Semaines planning |
| Actualités | 5 dernières actualités (épinglées en premier) |
| Présence aujourd'hui | Statut de chaque tech (Présent / TT / Absent / Repos) dérivé du planning |
| Astreintes à venir | Créneaux matin (06h-08h) et soir (18h-20h) |
| Tendance tickets | Graphe linéaire des 8 dernières semaines (créés vs résolus) |
| Planning de la semaine | Tableau horaires / jours TT / Bendoc de la semaine active |
| Notes rapides | Zone de texte libre, auto-sauvegardée, ouvrable en fenêtre séparée |
| Liens rapides | Favoris avec URL, ajout/suppression en un clic |
| Stats techniciens | Barre de progression par tech : total tickets / en cours / résolus / % escaladés |

**Personnaliser les widgets**
- Cliquer sur l'icône ⚙ en haut à droite du dashboard.
- Activer/désactiver chaque widget via les toggles.
- La configuration est sauvegardée.

**Notes rapides — fenêtre dédiée**
- Cliquer sur l'icône ⧉ dans l'en-tête du widget Notes.
- Ouvre une petite fenêtre flottante indépendante, pratique en multi-écran.

---

## 5. Planning

Gestion des plannings hebdomadaires et des astreintes.

**Sélection de la semaine**
- Menu déroulant en haut pour choisir la semaine à afficher (ex. S14, S15…).
- La semaine sélectionnée est mémorisée et réutilisée à la prochaine ouverture.

**Tableau planning**
Colonnes : Technicien | Horaire | Jours télétravail | Bendoc/Pause.

**Astreintes**
- Section dédiée sous le planning.
- Chaque créneau liste : période, slot matin, slot soir.

**Import via Excel**
- Les plannings sont importés depuis le fichier Excel source (voir section 17).
- L'import ne supprime pas les modifications manuelles faites sur d'autres données (tickets, procédures, etc.).

---

## 6. Escalade N1 — Matrice

Matrice de routage N1/N2/N3 — 401 entrées issues du fichier Excel source.

**Recherche / filtres**
- Barre de recherche dans le header (ou via `Ctrl+K`).
- Filtres par : Périmètre, Typologie, Catégorie Freshservice.
- La recherche est instantanée.

**Détail d'une entrée (modale)**
Cliquer sur une ligne ouvre la modale avec :

- **Traitement N1** : procédure à suivre.
- **Escalade N2/N3** : interlocuteur, WP N2, référents, conditions d'escalade.
- **Note Excel** : note importée depuis le fichier source (non modifiable).
- **Procédure N1** : liste d'étapes éditables, avec numéro de version et historique.
- **Document lié** : un document ou gabarit associé à cette entrée.

**Modifier la procédure N1**
1. Cliquer sur "Modifier" dans la section Procédure N1.
2. Ajouter / supprimer / réordonner les étapes.
3. Sauvegarder → une nouvelle version est créée automatiquement.

**Historique des versions**
- Cliquer sur l'icône 🕐 à côté du numéro de version.
- Voir toutes les versions précédentes avec date et auteur.
- Cliquer "Restaurer" pour revenir à une version antérieure.

**Lier un document**
1. Cliquer "Lier un document" dans la section Document lié.
2. Onglet **Documents** : chercher dans la base documentaire et sélectionner.
3. Onglet **Gabarits** : sélectionner un gabarit prédéfini ou personnalisé.
4. Ou saisir manuellement un nom + URL personnalisés.
5. Le lien est affiché dans la modale et cliquable directement.

---

## 7. Tickets

Suivi des tickets N1 en cours et résolus.

**Liste des tickets**
- Filtres : par état (En cours / Résolu), par technicien, par périmètre.
- Recherche textuelle sur le titre et la description.

**Créer un ticket**
1. Bouton "Nouveau ticket".
2. Renseigner : titre, description, impact, périmètre, technicien assigné.
3. Le ticket est créé à l'état "En cours".

**Détail d'un ticket (modale)**
- Modifier les informations.
- Changer l'état (En cours → Résolu).
- Ajouter des notes internes.
- Renseigner une escalade (interlocuteur N2, WP N2, périmètre/typologie).

**Gabarits rapides (dans la zone Notes)**
- Cliquer sur le bouton "Gabarit" à côté du champ Notes.
- Rechercher un gabarit par titre ou contenu.
- Cliquer "Copier" pour insérer le contenu dans le presse-papiers.

---

## 8. Documents & Gabarits

Deux onglets sur la même page `/documents`.

### Onglet Documents

Base de documents (procédures, guides, liens externes…).

- **Recherche** : barre de recherche filtre sur le nom et la description.
- **Ajouter un document** : bouton "+", renseigner nom, URL, catégorie, sous-catégorie, description.
- **Modifier / Supprimer** : icônes sur chaque ligne (droits requis).
- **Ouvrir** : cliquer sur le nom du document ouvre l'URL dans un nouvel onglet.

### Onglet Gabarits

Gabarits de texte organisés en colonnes par catégorie (kanban).

- **Recherche** : barre de recherche en haut, filtre en temps réel sur toutes les colonnes.
- **Gabarits prédéfinis** : fournis par défaut, non modifiables mais masquables.
- **Gabarits personnalisés** : créés via le bouton "+", éditables et supprimables.
- **Copier un gabarit** : cliquer sur "Copier" → contenu copié dans le presse-papiers + toast de confirmation.
- **Masquer un gabarit prédéfini** : icône 🙈 sur la carte.

---

## 9. Suivi doc — Procédures & Améliorations

Page `/suivi_doc` — vue croisée procédures N1 vs améliorations signalées.

### Tableau de suivi des procédures

- Liste toutes les entrées de la matrice.
- Colonnes : Périmètre | Typologie | Catégorie | Procédure (Intégrée / Personnalisée / Document / —).
- Filtres par périmètre et présence de procédure.

**Lier un document à une procédure**
1. Cliquer sur l'icône 📎 de la ligne.
2. Onglet **Documents** : chercher et sélectionner.
3. Onglet **Gabarits** : sélectionner un gabarit (stocké comme référence).
4. Le lien est visible dans la colonne "Procédure".

### Améliorations

- Signaler un problème ou une suggestion liée à une procédure.
- Champs : titre, description, catégorie (Process / UX / Technique / Formation / Autre), priorité, statut.
- Statuts : Ouvert → En cours → Résolu → Fermé.
- Filtres par catégorie, priorité et statut.

---

## 10. Outils

Page `/outils` — intègre l'outil de **diagnostic réseau** en iframe.

- Permet d'effectuer des diagnostics rapides (ping, traceroute, etc.) sans quitter l'application.
- L'outil est chargé depuis `/diagnostic.html` (fichier statique).

---

## 11. Techniciens

Gestion de l'équipe (droits requis).

**Liste des techniciens**
- Cards avec avatar couleur, nom, matricule, email, statut actif/inactif.

**Ajouter un technicien**
- Bouton "+ Nouveau technicien".
- Renseigner : nom, matricule, email, couleur avatar.

**Modifier un technicien**
- Cliquer sur la card → modale d'édition.
- Modifier les informations, activer/désactiver le compte.

**Désactiver un technicien**
- Toggle "Actif" dans la modale.
- Le technicien n'apparaît plus dans les plannings et les nouvelles assignations.

---

## 12. Actualités

Tableau de bord d'équipe pour partager des informations.

**Créer une actualité**
- Bouton "+ Nouvelle actualité".
- Champs : titre, contenu, type (Info / Succès / Avertissement / Alerte), épinglée ou non.

**Types d'actualités**
| Type | Couleur | Icône |
|---|---|---|
| Info | Indigo | ℹ |
| Succès | Vert | ✓ |
| Avertissement | Ambre | ⚠ |
| Alerte | Rouge | 🔔 |

**Épingler une actualité**
- Cocher "Épinglée" lors de la création ou de l'édition.
- Les actualités épinglées apparaissent en premier (widget dashboard + page complète).

**Modifier / Supprimer**
- Icônes sur chaque carte (droits requis).

---

## 13. Quêtes

Système de gamification pour encourager les bonnes pratiques.

**Fonctionnement**
- Chaque technicien a un profil avec des XP, un niveau et un rang (E → D → C → B → A → S).
- Les quêtes représentent des objectifs à atteindre (ex. : résoudre N tickets, documenter une procédure, etc.).

**Types de quêtes**
- Automatiques : progression calculée depuis les tickets (ex. "Résoudre 10 tickets réseau").
- Manuelles : à valider par le manager.

**Valider une quête (Manager)**
- Onglet "Validations en attente" → liste des demandes.
- Approuver ou rejeter avec commentaire optionnel.

**Leaderboard**
- Classement de l'équipe par XP total.
- Affiché sur la page Quêtes.

---

## 14. Feedbacks

Remontée de suggestions et anomalies par les techniciens.

**Créer un feedback**
- Bouton "+ Nouveau feedback".
- Champs : titre, description, type (Bug / Suggestion / Amélioration), priorité.

**Suivi des feedbacks (Manager)**
- Changer le statut : Ouvert → En cours → Résolu → Fermé.
- Voter pour un feedback existant (compteur de votes).

**Filtres**
- Par type, statut, priorité.

---

## 15. Admin — Permissions

*(Accès Manager uniquement)*

Gestion fine des droits par utilisateur.

**Permissions disponibles**
| Permission | Description |
|---|---|
| planning_edit | Modifier le planning |
| matrix_edit | Modifier la matrice d'escalade |
| technicians_edit | Ajouter / modifier les techniciens |
| tickets_manage | Créer / clôturer des tickets |
| import_excel | Importer des fichiers Excel |
| permissions_manage | Modifier les droits des autres |
| escalade_proc_edit | Éditer les procédures N1 |
| doc_edit | Ajouter / modifier les documents |

**Modifier les droits d'un utilisateur**
1. Cliquer sur l'utilisateur dans la liste.
2. Activer/désactiver chaque permission via les toggles.
3. Sauvegarder.

---

## 16. Admin — Audit

*(Accès Manager uniquement)*

Journal des actions effectuées dans l'application.

- Colonnes : Date/heure | Utilisateur | Action | Entité | Détail.
- Filtre par période et par utilisateur.
- Les actions auditées incluent : connexion, création/modification/suppression de tickets, plannings, documents, permissions.

---

## 17. Admin — Import Excel

*(Accès Manager uniquement — ou permission `import_excel`)*

Importation des données depuis les fichiers Excel sources.

**Fichiers supportés**
| Fichier | Données importées |
|---|---|
| `planning_final.xlsm` | Planning hebdomadaire (6 techs × semaines) + astreintes |
| `Matrice d'escalade et de routage - Helpdesk.xlsx` | Matrice N1/N2/N3 (401 entrées) |

**Procédure d'import**
1. Glisser-déposer le fichier Excel dans la zone d'import (ou cliquer pour parcourir).
2. Vérifier le prévisualisation des données détectées.
3. Cliquer "Importer".

**Important — ce qui est remplacé vs conservé**
| Données | Comportement à l'import |
|---|---|
| `escalation_matrix` | **Remplacé** par les nouvelles données Excel |
| `planning`, `astreintes` | **Remplacé** par les nouvelles données Excel |
| Procédures N1, liaisons documents | **Conservés** (stockés séparément dans `procedures`, `proc_doc_links`) |
| Tickets, techniciens, gabarits, actualités | **Non touchés** |

---

## 18. Profil utilisateur

Page `/profil` — accessible en cliquant sur son nom en bas de la sidebar.

- Affichage du nom, rôle, matricule.
- Modification du mot de passe.
- Historique de ses propres actions (si activé).

---

## Annexe — Raccourcis clavier

| Raccourci | Action |
|---|---|
| `Ctrl+K` | Ouvrir la recherche globale |
| `Échap` | Fermer la recherche globale / une modale |
| `Entrée` (dans la recherche matrice) | Aller sur la page Escalade |

---

## Annexe — Statuts et codes couleur

**Statut technicien (présence)**
| Statut | Couleur | Signification |
|---|---|---|
| Présent | 🟢 Vert | En présentiel selon le planning |
| TT | 🔵 Cyan | Télétravail ce jour |
| Absent | 🔴 Rouge | Congé / absence |
| Repos | ⚫ Gris | Non planifié cette semaine |

**État ticket**
| État | Signification |
|---|---|
| En cours | Ticket ouvert, en traitement |
| Résolu | Ticket clôturé |

---

*Ce document est versionné avec le code source. Mettre à jour la section concernée à chaque ajout de fonctionnalité.*
