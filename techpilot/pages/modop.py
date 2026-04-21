import reflex as rx
from techpilot.components.layout import page_layout

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
CARD_BG = "#111524"
BORDER  = "#1c2138"
PRIMARY = "#6366f1"

# ── Contenu du mode opératoire ────────────────────────────────────────────────
# Mettre à jour ce contenu à chaque ajout de fonctionnalité.

MODOP_CONTENT = """
## 1. Accès & connexion

L'application est accessible via l'URL Railway (ou en local sur `http://localhost:3000`).

**Connexion**
- Saisir son nom d'utilisateur et son mot de passe sur la page `/login`.
- Deux rôles : **Manager** (accès à toutes les pages, y compris Admin) et **Technicien** (accès restreint).
- La session est maintenue jusqu'à déconnexion manuelle.

**Déconnexion** : icône en bas de la sidebar à côté de l'avatar.

---

## 2. Navigation & interface

La sidebar à gauche liste toutes les pages. Elle peut être **réduite** (icônes seules) via le bouton `←` en haut à droite.

| Section | Pages |
|---|---|
| Navigation | Dashboard, Planning, Escalade N1, Tickets, Documents, Outils |
| Équipe | Techniciens, Actualités, Quêtes, Feedbacks |
| Admin *(Manager)* | Permissions, Audit, Import Excel |

**Header** : titre de la page, bouton recherche globale `Ctrl+K`, cloche de notifications.

---

## 3. Recherche globale (Ctrl+K)

- Raccourci clavier `Ctrl+K` ou clic sur le bouton "Recherche…" dans le header.
- Recherche en temps réel sur : **Tickets**, **Matrice d'escalade**, **Documents**, **Gabarits** (5 résultats max par catégorie).
- Cliquer sur un résultat → navigation directe. Gabarit → copie dans le presse-papiers.
- Fermer : `Échap` ou clic sur le fond sombre.

---

## 4. Dashboard

Vue synthétique de l'activité. Widgets disponibles :

| Widget | Contenu |
|---|---|
| KPIs | Techniciens actifs / Tickets ouverts / Entrées matrice / Semaines planning |
| Actualités | 5 dernières actualités (épinglées en premier) |
| Présence aujourd'hui | Statut de chaque tech (Présent / TT / Absent / Repos) |
| Astreintes à venir | Créneaux matin (06h-08h) et soir (18h-20h) |
| Tendance tickets | Graphe 8 dernières semaines (créés vs résolus) |
| Planning de la semaine | Horaires / jours TT / Bendoc — filtre par technicien |
| Notes rapides | Zone de texte libre, auto-sauvegardée, ouvrable en fenêtre séparée |
| Liens rapides | Favoris avec URL, ajout/suppression en un clic |
| Stats techniciens | Barre de progression par tech : total / en cours / résolus / % escaladés |
| Mises à jour | Historique des évolutions de l'application (changelog) |

**Personnaliser** : icône ⚙ en haut à droite → activer/désactiver chaque widget.

**Widget Planning** : affiche par défaut uniquement votre propre ligne. Cliquez sur les badges de techniciens en haut du widget pour afficher/masquer d'autres techs. Bouton "Tous" pour tout afficher.

**Widget Mises à jour** : bouton "+ Nouvelle entrée" → renseigner version, type (Nouveauté / Amélioration / Correction), titre, détails (une ligne par item).

---

## 5. Planning

- Sélecteur de semaine en haut (ex. S14, S15…) — mémorisé à la prochaine ouverture.
- Tableau : Technicien | Horaire | Jours télétravail | Bendoc/Pause.
- Section Astreintes : période, slot matin et soir.
- Les plannings sont importés depuis Excel (voir section 17).

---

## 6. Escalade N1 — Matrice

Matrice de routage N1/N2/N3 — 401 entrées.

**Recherche** : barre dans le header ou `Ctrl+K`. Filtres par Périmètre, Typologie, Catégorie Freshservice.

**Détail d'une entrée (modale)** :
- Traitement N1, escalade N2/N3 (interlocuteur, WP N2, référents, conditions).
- Note Excel (importée, non modifiable).
- **Procédure N1** : liste d'étapes éditables avec numéro de version.
  - Icône 🕐 → historique de toutes les versions (date, auteur) avec bouton "Restaurer".
- **Document lié** : lier un document de la base, un gabarit, ou une URL personnalisée.

---

## 7. Tickets

**Créer** : bouton "Nouveau ticket" → titre, description, impact, périmètre, technicien.

**Détail** : modifier, changer l'état (En cours → Résolu), ajouter des notes, renseigner une escalade N2.

**Gabarits rapides** : bouton "Gabarit" dans la zone Notes → chercher et copier un gabarit en un clic.

---

## 8. Documents & Gabarits

**Onglet Documents** : base documentaire avec recherche, ajout, modification, suppression (droits requis).

**Onglet Gabarits** : kanban par catégorie.
- Recherche en temps réel sur toutes les colonnes.
- Gabarits prédéfinis (masquables) et personnalisés (éditables).
- Bouton "Copier" → contenu dans le presse-papiers.

---

## 9. Suivi doc — Procédures & Améliorations

**Tableau de suivi** : liste toutes les entrées matrice avec statut procédure (Intégrée / Personnalisée / Document / —).
- Icône 📎 → lier un document ou gabarit à la procédure.

**Améliorations** : signaler un problème ou suggestion (catégorie, priorité, statut).
- Statuts : Ouvert → En cours → Résolu → Fermé.

---

## 10. Outils

Outil de **diagnostic réseau** intégré en iframe (ping, traceroute…).

---

## 11. Techniciens

- Ajouter : bouton "+ Nouveau technicien" (nom, matricule, email, couleur).
- Modifier : bouton "Modifier" sur la carte → modale d'édition.
- Désactiver / Activer : bascule le statut — un tech désactivé n'apparaît plus dans les plannings et assignations.
- **Supprimer** : icône 🗑️ rouge sur la carte — suppression définitive (Manager ou permission `technicians_edit`).

---

## 12. Actualités

**Créer** : bouton "+ Nouvelle actualité" → titre, contenu, type, épinglée ou non.

| Type | Couleur | Icône |
|---|---|---|
| Info | Indigo | ℹ |
| Succès | Vert | ✓ |
| Avertissement | Ambre | ⚠ |
| Alerte | Rouge | 🔔 |

Les actualités épinglées apparaissent en premier (widget dashboard + page complète).

---

## 13. Quêtes

Gamification pour encourager les bonnes pratiques.
- Chaque tech : XP, niveau, rang (E → D → C → B → A → S).
- Quêtes automatiques (progression depuis les tickets) et manuelles (validation manager).
- **Valider une quête** (Manager) : onglet "Validations en attente" → approuver / rejeter.
- **Leaderboard** : classement de l'équipe par XP total.

---

## 14. Feedbacks

- Créer : titre, description, type (Bug / Suggestion / Amélioration), priorité.
- Suivi (Manager) : changer le statut, voter pour un feedback.

---

## 15. Admin — Permissions *(Manager uniquement)*

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

---

## 16. Admin — Audit *(Manager uniquement)*

Journal de toutes les actions (Date/heure | Utilisateur | Action | Entité | Détail). Filtrable par période et utilisateur.

---

## 17. Admin — Import Excel *(Manager ou permission `import_excel`)*

| Fichier | Données importées |
|---|---|
| `planning_final.xlsm` | Planning hebdomadaire + astreintes |
| `Matrice d'escalade et de routage - Helpdesk.xlsx` | Matrice N1/N2/N3 (401 entrées) |

**Ce qui est remplacé vs conservé à l'import** :

| Données | Comportement |
|---|---|
| `escalation_matrix`, `planning`, `astreintes` | **Remplacé** |
| Procédures N1, liaisons documents | **Conservés** |
| Tickets, techniciens, gabarits, actualités | **Non touchés** |

---

## 18. Profil utilisateur

Accessible en cliquant sur son nom en bas de la sidebar. Modification du mot de passe.

---

## Raccourcis clavier

| Raccourci | Action |
|---|---|
| `Ctrl+K` | Ouvrir la recherche globale |
| `Échap` | Fermer la recherche / une modale |

---

## Statuts présence techniciens

| Statut | Couleur | Signification |
|---|---|---|
| Présent | 🟢 Vert | En présentiel selon le planning |
| TT | 🔵 Cyan | Télétravail ce jour |
| Absent | 🔴 Rouge | Congé / absence |
| Repos | ⚫ Gris | Non planifié cette semaine |
"""


def modop_page() -> rx.Component:
    return page_layout(
        rx.box(
            # Script CSS d'impression
            rx.script("""
(function() {
  var s = document.createElement('style');
  s.setAttribute('media', 'print');
  s.textContent = `
    #tp-sidebar, #tp-main > div:first-child { display: none !important; }
    #tp-main { margin-left: 0 !important; }
    body { background: white !important; color: black !important; }
    .modop-card { background: white !important; border: 1px solid #ccc !important; }
    a { color: #4f46e5 !important; }
  `;
  document.head.appendChild(s);
})();
"""),

            # Barre d'actions
            rx.hstack(
                rx.hstack(
                    rx.icon("book-open", size=15, color=PRIMARY),
                    rx.text("Mode Opératoire — TechPilot", color=MUTED, font_size="0.8rem"),
                    spacing="2", align="center",
                ),
                rx.spacer(),
                rx.text("Avril 2026", color=MUTED, font_size="0.75rem"),
                rx.button(
                    rx.icon("printer", size=14), "Imprimer / Exporter PDF",
                    on_click=rx.call_script("window.print()"),
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    color="white",
                    border_radius="8px",
                    font_size="0.8rem",
                    padding="6px 14px",
                    cursor="pointer",
                    spacing="2",
                    _hover={"opacity": "0.9"},
                ),
                width="100%", align="center",
                padding="0.75rem 1.25rem",
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="12px",
                margin_bottom="1.5rem",
            ),

            # Contenu Markdown
            rx.box(
                rx.box(
                    rx.heading(
                        "Mode Opératoire TechPilot",
                        size="7", color=TEXT, font_weight="800",
                        margin_bottom="0.25rem",
                    ),
                    rx.text(
                        "Guide complet d'utilisation de l'application",
                        color=MUTED, font_size="0.9rem",
                    ),
                    padding="1.5rem 2rem 1.25rem",
                    background=f"linear-gradient(135deg, {PRIMARY}22, #8b5cf622)",
                    border_bottom=f"1px solid {BORDER}",
                ),
                rx.box(
                    rx.markdown(MODOP_CONTENT),
                    padding="1.5rem 2rem 2rem",
                    style={
                        "h2": {"color": TEXT, "font_weight": "700", "margin_top": "2rem",
                               "margin_bottom": "0.75rem", "font_size": "1.15rem"},
                        "h3": {"color": TEXT, "font_weight": "600", "margin_top": "1.25rem"},
                        "p":  {"color": MUTED, "font_size": "0.875rem", "line_height": "1.7"},
                        "li": {"color": MUTED, "font_size": "0.875rem"},
                        "code": {"background": "rgba(99,102,241,0.15)", "color": "#a5b4fc",
                                 "border_radius": "4px", "padding": "1px 6px"},
                        "table": {"width": "100%", "border_collapse": "collapse",
                                  "font_size": "0.82rem", "margin_bottom": "1rem"},
                        "th": {"color": MUTED, "font_size": "0.72rem", "font_weight": "600",
                               "padding": "6px 12px", "text_align": "left",
                               "border_bottom": f"1px solid {BORDER}"},
                        "td": {"color": MUTED, "padding": "6px 12px",
                               "border_bottom": f"1px solid {BORDER}33"},
                        "strong": {"color": TEXT},
                    },
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="14px",
                overflow="hidden",
                class_name="modop-card",
            ),

            max_width="860px",
            margin="0 auto",
        ),
        title="Mode Opératoire",
    )
