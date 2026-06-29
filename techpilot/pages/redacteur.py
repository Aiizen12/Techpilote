import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.state.auth import AuthState
from techpilot.state.redacteur import RedacteurState, PROC_TYPES, PROC_STATUTS

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
CARD_BG = "#111524"
BORDER  = "#1c2138"
PRIMARY = "#6366f1"
GREEN   = "#22c55e"
AMBER   = "#f59e0b"
RED     = "#ef4444"


# ── Helpers UI ────────────────────────────────────────────────────────────────

def _label(text: str) -> rx.Component:
    return rx.text(text, color=MUTED, font_size="0.73rem", font_weight="600", margin_bottom="4px")


def _input(value, on_change, placeholder: str = "", **kwargs) -> rx.Component:
    return rx.input(
        value=value, on_change=on_change, placeholder=placeholder,
        style={
            "background": "#0d1117", "color": TEXT,
            "border": f"1px solid {BORDER}", "border_radius": "8px",
            "padding": "7px 10px", "width": "100%", "font_size": "0.85rem",
        },
        **kwargs,
    )


def _textarea(value, on_change, placeholder: str = "", rows: str = "4") -> rx.Component:
    return rx.text_area(
        value=value, on_change=on_change, placeholder=placeholder, rows=rows,
        style={
            "background": "#0d1117", "color": TEXT,
            "border": f"1px solid {BORDER}", "border_radius": "8px",
            "padding": "8px 10px", "width": "100%",
            "font_size": "0.85rem", "resize": "vertical",
            "line_height": "1.6",
        },
    )


def _select(value, on_change, options: list[str], placeholder: str = "") -> rx.Component:
    return rx.select.root(
        rx.select.trigger(
            placeholder=placeholder,
            style={
                "background": "#0d1117", "color": TEXT,
                "border": f"1px solid {BORDER}", "border_radius": "8px",
                "padding": "7px 10px", "width": "100%", "font_size": "0.85rem",
            },
        ),
        rx.select.content(
            *[rx.select.item(o, value=o) for o in options],
            background=CARD_BG,
        ),
        value=value,
        on_change=on_change,
        width="100%",
    )


def _statut_color(s: str) -> str:
    colors = {
        "Brouillon":               "#64748b",
        "En attente de validation": "#f59e0b",
        "Relecture N1":            "#06b6d4",
        "Relecture N2":            "#8b5cf6",
        "Validé":                  "#22c55e",
        "Publié":                  "#10b981",
    }
    return colors.get(s, "#64748b")


def _statut_badge(s: str) -> rx.Component:
    color = _statut_color(s)
    return rx.box(
        rx.text(s, color=color, font_size="0.7rem", font_weight="600"),
        background=f"rgba({_hex_to_rgb(color)},0.1)",
        border=f"1px solid {color}44",
        border_radius="6px", padding="2px 8px", display="inline-flex",
    )


def _hex_to_rgb(h: str) -> str:
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b}"


# ── Panneau gauche : éditeur ──────────────────────────────────────────────────

def _editor_panel() -> rx.Component:
    return rx.vstack(
        # Header
        rx.hstack(
            rx.hstack(
                rx.icon("file-text", size=16, color=PRIMARY),
                rx.text(
                    rx.cond(RedacteurState.edit_id != "", "Modifier la procédure", "Nouvelle procédure"),
                    color=TEXT, font_size="0.95rem", font_weight="700",
                ),
                spacing="2", align="center",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=14),
                "Nouvelle",
                on_click=RedacteurState.new_procedure,
                background="transparent", color=MUTED,
                border=f"1px solid {BORDER}", border_radius="8px",
                font_size="0.78rem", padding="5px 12px", cursor="pointer",
                _hover={"background": "rgba(255,255,255,0.05)", "color": TEXT},
            ),
            width="100%",
        ),

        rx.divider(border_color=BORDER),

        # Titre
        rx.vstack(
            _label("Titre *"),
            _input(RedacteurState.titre, RedacteurState.set_titre,
                   placeholder="Ex : N1 - Citrix – le bureau virtuel ne se lance pas"),
            spacing="0", width="100%",
        ),

        # Type + Périmètre
        rx.hstack(
            rx.vstack(
                _label("Type"),
                _select(RedacteurState.type_proc, RedacteurState.set_type_proc, PROC_TYPES),
                spacing="0", width="100%",
            ),
            rx.vstack(
                _label("Application / Périmètre"),
                _input(RedacteurState.perimetre, RedacteurState.set_perimetre,
                       placeholder="Ex : Citrix, Gmail, AD..."),
                spacing="0", width="100%",
            ),
            spacing="3", width="100%",
        ),

        # Description (pour Claude)
        rx.vstack(
            _label("Description courte (contexte pour Claude)"),
            _textarea(RedacteurState.description_brief, RedacteurState.set_description_brief,
                      placeholder="Décris en quelques mots le cas : symptôme, usage, population concernée…",
                      rows="2"),
            spacing="0", width="100%",
        ),

        rx.divider(border_color=BORDER, margin_y="2px"),

        # Objectif
        rx.vstack(
            _label("Objectif"),
            _textarea(RedacteurState.objectif, RedacteurState.set_objectif,
                      placeholder="Objectif de la procédure…", rows="2"),
            spacing="0", width="100%",
        ),

        # Pré-requis
        rx.vstack(
            _label("Pré-requis"),
            _textarea(RedacteurState.prerequis, RedacteurState.set_prerequis,
                      placeholder="• Accès X\n• Droits Y", rows="3"),
            spacing="0", width="100%",
        ),

        # Étapes
        rx.vstack(
            _label("Étapes"),
            _textarea(RedacteurState.steps_text, RedacteurState.set_steps_text,
                      placeholder="1. Première étape\n2. Deuxième étape\n3. …",
                      rows="8"),
            spacing="0", width="100%",
        ),

        # Résultat attendu
        rx.vstack(
            _label("Résultat attendu"),
            _textarea(RedacteurState.resultat_attendu, RedacteurState.set_resultat_attendu,
                      placeholder="Ce qui doit se produire après les étapes…", rows="2"),
            spacing="0", width="100%",
        ),

        # Escalade
        rx.vstack(
            _label("Escalade"),
            _textarea(RedacteurState.escalade_info, RedacteurState.set_escalade_info,
                      placeholder="Si non résolu → Escalader à [N2] via [WP]…", rows="2"),
            spacing="0", width="100%",
        ),

        # Statut + URL Doc
        rx.hstack(
            rx.vstack(
                _label("Statut"),
                _select(RedacteurState.statut, RedacteurState.set_statut, PROC_STATUTS),
                spacing="0", width="100%",
            ),
            rx.vstack(
                _label("Lien Google Doc (optionnel)"),
                _input(RedacteurState.google_doc_url, RedacteurState.set_google_doc_url,
                       placeholder="https://docs.google.com/…"),
                spacing="0", width="100%",
            ),
            spacing="3", width="100%",
        ),

        # Boutons action
        rx.hstack(
            rx.button(
                rx.icon("save", size=15),
                rx.text("Enregistrer", font_size="0.88rem"),
                on_click=RedacteurState.save_procedure,
                background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                color="white", border="none", border_radius="9px",
                padding="8px 20px", cursor="pointer", font_weight="700",
                display="flex", align_items="center", gap="6px",
                _hover={"opacity": "0.88"},
            ),
            rx.button(
                rx.icon("send", size=14),
                "Soumettre à validation",
                on_click=[RedacteurState.submit_for_validation, RedacteurState.save_procedure],
                background="rgba(245,158,11,0.12)", color=AMBER,
                border=f"1px solid {AMBER}55", border_radius="9px",
                padding="8px 16px", cursor="pointer", font_size="0.82rem",
                font_weight="600",
                _hover={"background": "rgba(245,158,11,0.22)"},
            ),
            # Feedback succès
            rx.cond(
                RedacteurState.save_success,
                rx.hstack(
                    rx.icon("check-circle", size=14, color=GREEN),
                    rx.text("Enregistré !", color=GREEN, font_size="0.8rem", font_weight="600"),
                    spacing="1", align="center",
                ),
            ),
            spacing="3", align="center", width="100%",
        ),

        spacing="4", width="100%",
        background=CARD_BG, border=f"1px solid {BORDER}",
        border_radius="14px", padding="1.25rem",
    )


# ── Panneau droit : Claude + Comparateur ─────────────────────────────────────

def _similar_doc_row(doc: dict) -> rx.Component:
    return rx.hstack(
        rx.icon("file-text", size=13, color="#a5b4fc", flex_shrink="0"),
        rx.vstack(
            rx.text(doc["nom"], color=TEXT, font_size="0.78rem", font_weight="500",
                    white_space="nowrap", overflow="hidden", text_overflow="ellipsis"),
            rx.text(doc["categorie"], color=MUTED, font_size="0.68rem"),
            spacing="0", align="start", flex="1", min_width="0",
        ),
        rx.cond(
            doc["url"] != "",
            rx.link(
                rx.icon("external-link", size=12),
                href=doc["url"], target="_blank",
                color=MUTED, _hover={"color": "#a5b4fc"},
            ),
        ),
        spacing="2", align="center", width="100%",
        padding="6px 8px",
        border_bottom=f"1px solid {BORDER}",
        _hover={"background": "rgba(255,255,255,0.02)"},
    )


def _assistant_panel() -> rx.Component:
    return rx.vstack(
        # ── Génération Claude ─────────────────────────────────────────────
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.text("✦", color="white", font_size="0.9rem"),
                    background="linear-gradient(135deg, #6366f1, #8b5cf6)",
                    border_radius="8px", padding="6px",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.vstack(
                    rx.text("Assistant Claude", color=TEXT, font_size="0.92rem", font_weight="700"),
                    rx.text("Génération automatique de procédures N1", color=MUTED, font_size="0.72rem"),
                    spacing="0", align="start",
                ),
                spacing="2", align="center",
            ),

            rx.hstack(
                rx.button(
                    rx.cond(
                        RedacteurState.claude_loading,
                        rx.hstack(rx.spinner(size="1"), rx.text("Génération…"), spacing="2", align="center"),
                        rx.hstack(rx.text("✦", font_size="0.9rem"), rx.text("Générer", font_size="0.85rem"),
                                  spacing="1", align="center"),
                    ),
                    on_click=RedacteurState.generate_with_claude,
                    disabled=RedacteurState.claude_loading,
                    background="linear-gradient(135deg, #6366f1, #8b5cf6)",
                    color="white", border="none", border_radius="8px",
                    padding="7px 16px", cursor="pointer", font_weight="700",
                    _hover={"opacity": "0.88"},
                ),
                rx.cond(
                    RedacteurState.claude_generated != "",
                    rx.button(
                        rx.icon("copy-check", size=14),
                        "Appliquer",
                        on_click=RedacteurState.apply_claude_result,
                        background="rgba(34,197,94,0.1)", color=GREEN,
                        border=f"1px solid {GREEN}55", border_radius="8px",
                        padding="7px 14px", cursor="pointer",
                        font_size="0.82rem", font_weight="600",
                        _hover={"background": "rgba(34,197,94,0.2)"},
                    ),
                ),
                spacing="2", align="center",
            ),

            # Erreur
            rx.cond(
                RedacteurState.claude_error != "",
                rx.hstack(
                    rx.icon("alert-triangle", size=13, color=RED),
                    rx.text(RedacteurState.claude_error, color=RED, font_size="0.78rem"),
                    spacing="2", align="center",
                    padding="6px 10px",
                    background="rgba(239,68,68,0.08)",
                    border=f"1px solid {RED}33",
                    border_radius="8px",
                ),
            ),

            # Résultat généré
            rx.cond(
                RedacteurState.claude_generated != "",
                rx.box(
                    rx.text(
                        RedacteurState.claude_generated,
                        color=TEXT, font_size="0.8rem",
                        white_space="pre-wrap", line_height="1.65",
                    ),
                    background="#0d1117",
                    border=f"1px solid rgba(99,102,241,0.25)",
                    border_radius="10px",
                    padding="12px 14px",
                    max_height="400px",
                    overflow_y="auto",
                    width="100%",
                ),
            ),

            spacing="3", width="100%",
            background=CARD_BG, border=f"1px solid {BORDER}",
            border_radius="14px", padding="1.25rem",
        ),

        # ── Comparateur ───────────────────────────────────────────────────
        rx.vstack(
            rx.hstack(
                rx.icon("search", size=14, color=AMBER),
                rx.text("Procédures similaires", color=TEXT, font_size="0.88rem", font_weight="700"),
                rx.cond(
                    RedacteurState.similar_docs.length() > 0,
                    rx.badge(
                        RedacteurState.similar_docs.length().to_string(),
                        color_scheme="amber", variant="soft", font_size="0.68rem",
                    ),
                ),
                spacing="2", align="center",
            ),
            rx.text(
                "Procédures Google Docs existantes dont le titre est proche",
                color=MUTED, font_size="0.72rem",
            ),

            rx.cond(
                RedacteurState.similar_docs.length() == 0,
                rx.hstack(
                    rx.icon("search-x", size=15, color=MUTED),
                    rx.text(
                        rx.cond(
                            RedacteurState.titre != "",
                            "Aucune procédure similaire trouvée.",
                            "Renseigne le titre pour lancer la recherche.",
                        ),
                        color=MUTED, font_size="0.8rem",
                    ),
                    spacing="2", align="center",
                    padding_y="0.5rem",
                ),
                rx.box(
                    rx.foreach(RedacteurState.similar_docs, _similar_doc_row),
                    width="100%",
                    background="#0d1117",
                    border=f"1px solid {BORDER}",
                    border_radius="10px",
                    overflow="hidden",
                ),
            ),

            spacing="3", width="100%",
            background=CARD_BG, border=f"1px solid {BORDER}",
            border_radius="14px", padding="1.25rem",
        ),

        spacing="4", width="100%",
    )


# ── Liste des procédures ──────────────────────────────────────────────────────

def _proc_list_row(p: dict) -> rx.Component:
    return rx.hstack(
        # Titre + périmètre
        rx.vstack(
            rx.text(p["titre"], color=TEXT, font_size="0.85rem", font_weight="600",
                    white_space="nowrap", overflow="hidden", text_overflow="ellipsis",
                    max_width="300px"),
            rx.hstack(
                rx.text(p["type_proc"], color=MUTED, font_size="0.72rem"),
                rx.cond(
                    p["perimetre"] != "",
                    rx.text("·", color=MUTED, font_size="0.72rem"),
                ),
                rx.text(p["perimetre"], color=MUTED, font_size="0.72rem"),
                spacing="1", align="center",
            ),
            spacing="0", align="start", flex="1", min_width="0",
        ),

        # Statut badge (construit statiquement pour éviter les vars dynamiques)
        rx.match(
            p["statut"],
            ("Brouillon",
             rx.box(rx.text("Brouillon", color="#64748b", font_size="0.7rem", font_weight="600"),
                    background="rgba(100,116,139,0.1)", border="1px solid #64748b44",
                    border_radius="6px", padding="2px 8px", display="inline-flex")),
            ("En attente de validation",
             rx.box(rx.text("En attente", color=AMBER, font_size="0.7rem", font_weight="600"),
                    background="rgba(245,158,11,0.1)", border=f"1px solid {AMBER}44",
                    border_radius="6px", padding="2px 8px", display="inline-flex")),
            ("Relecture N1",
             rx.box(rx.text("Relecture N1", color="#06b6d4", font_size="0.7rem", font_weight="600"),
                    background="rgba(6,182,212,0.1)", border="1px solid #06b6d444",
                    border_radius="6px", padding="2px 8px", display="inline-flex")),
            ("Relecture N2",
             rx.box(rx.text("Relecture N2", color="#8b5cf6", font_size="0.7rem", font_weight="600"),
                    background="rgba(139,92,246,0.1)", border="1px solid #8b5cf644",
                    border_radius="6px", padding="2px 8px", display="inline-flex")),
            ("Validé",
             rx.box(rx.text("Validé", color=GREEN, font_size="0.7rem", font_weight="600"),
                    background="rgba(34,197,94,0.1)", border=f"1px solid {GREEN}44",
                    border_radius="6px", padding="2px 8px", display="inline-flex")),
            ("Publié",
             rx.box(rx.text("Publié", color="#10b981", font_size="0.7rem", font_weight="600"),
                    background="rgba(16,185,129,0.1)", border="1px solid #10b98144",
                    border_radius="6px", padding="2px 8px", display="inline-flex")),
            rx.box(rx.text(p["statut"], color=MUTED, font_size="0.7rem"),
                   border_radius="6px", padding="2px 8px", display="inline-flex"),
        ),

        # Auteur + date
        rx.text(p["auteur_nom"], color=MUTED, font_size="0.75rem", min_width="80px",
                overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
        rx.text(p["date_maj"], color=MUTED, font_size="0.72rem", min_width="72px"),

        # Actions
        rx.hstack(
            rx.cond(
                p["google_doc_url"] != "",
                rx.link(
                    rx.icon_button(
                        rx.icon("external-link", size=13),
                        background="transparent", color="#a5b4fc",
                        border=f"1px solid rgba(99,102,241,0.3)", size="1",
                        cursor="pointer", border_radius="6px",
                        title="Ouvrir le Google Doc",
                        _hover={"background": "rgba(99,102,241,0.15)"},
                    ),
                    href=p["google_doc_url"], target="_blank",
                ),
            ),
            rx.icon_button(
                rx.icon("pencil", size=13),
                on_click=RedacteurState.edit_procedure(p["id"]),
                background="rgba(99,102,241,0.08)", color=PRIMARY,
                border=f"1px solid rgba(99,102,241,0.2)", size="1",
                cursor="pointer", border_radius="6px",
                title="Modifier",
                _hover={"background": "rgba(99,102,241,0.2)"},
            ),
            rx.icon_button(
                rx.icon("trash-2", size=13),
                on_click=RedacteurState.ask_delete(p["id"]),
                background="rgba(239,68,68,0.06)", color=RED,
                border=f"1px solid rgba(239,68,68,0.2)", size="1",
                cursor="pointer", border_radius="6px",
                title="Supprimer",
                _hover={"background": "rgba(239,68,68,0.18)"},
            ),
            spacing="1",
        ),

        spacing="3", align="center", width="100%",
        padding="9px 14px",
        border_bottom=f"1px solid {BORDER}",
        _hover={"background": "rgba(255,255,255,0.015)"},
    )


def _procedures_list() -> rx.Component:
    return rx.vstack(
        # Header + filtres
        rx.hstack(
            rx.hstack(
                rx.icon("list", size=15, color=PRIMARY),
                rx.text("Procédures rédigées", color=TEXT, font_size="0.95rem", font_weight="700"),
                rx.cond(
                    RedacteurState.pending_count > 0,
                    rx.badge(
                        RedacteurState.pending_count.to_string() + " en attente",
                        color_scheme="amber", variant="soft", font_size="0.68rem",
                    ),
                ),
                spacing="2", align="center",
            ),
            rx.spacer(),
            # Filtres
            rx.hstack(
                rx.input(
                    value=RedacteurState.search_list,
                    on_change=RedacteurState.set_search_list,
                    placeholder="Rechercher…",
                    style={
                        "background": CARD_BG, "color": TEXT,
                        "border": f"1px solid {BORDER}", "border_radius": "8px",
                        "padding": "5px 10px", "font_size": "0.8rem", "width": "180px",
                    },
                ),
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Statut",
                        style={
                            "background": CARD_BG, "color": MUTED,
                            "border": f"1px solid {BORDER}", "border_radius": "8px",
                            "padding": "5px 10px", "font_size": "0.78rem",
                        },
                    ),
                    rx.select.content(
                        rx.select.item("Tous", value=""),
                        *[rx.select.item(s, value=s) for s in PROC_STATUTS],
                        background=CARD_BG,
                    ),
                    value=RedacteurState.filter_statut,
                    on_change=RedacteurState.set_filter_statut,
                ),
                rx.cond(
                    (RedacteurState.filter_statut != "") | (RedacteurState.search_list != ""),
                    rx.button(
                        rx.icon("x", size=12), "Effacer",
                        on_click=RedacteurState.clear_filters,
                        background="transparent", color=MUTED,
                        border=f"1px solid {BORDER}", border_radius="7px",
                        font_size="0.75rem", padding="4px 10px", cursor="pointer",
                    ),
                ),
                spacing="2", align="center",
            ),
            align="center", width="100%",
        ),

        # Tableau
        rx.cond(
            RedacteurState.filtered_procedures.length() == 0,
            rx.box(
                rx.vstack(
                    rx.icon("file-x", size=28, color=MUTED),
                    rx.text("Aucune procédure rédigée.", color=MUTED, font_size="0.88rem"),
                    rx.text("Crée ta première procédure avec l'éditeur ci-dessus.",
                            color=MUTED, font_size="0.78rem"),
                    spacing="2", align="center",
                ),
                width="100%", text_align="center", padding="2.5rem 0",
            ),
            rx.box(
                # En-tête colonnes
                rx.hstack(
                    rx.text("Titre / Périmètre", color=MUTED, font_size="0.71rem", font_weight="700",
                            flex="1", min_width="0"),
                    rx.text("Statut",  color=MUTED, font_size="0.71rem", font_weight="700", min_width="120px"),
                    rx.text("Auteur",  color=MUTED, font_size="0.71rem", font_weight="700", min_width="80px"),
                    rx.text("Modifié", color=MUTED, font_size="0.71rem", font_weight="700", min_width="72px"),
                    rx.box(width="90px"),
                    spacing="3", width="100%",
                    padding="7px 14px",
                    border_bottom=f"1px solid {BORDER}",
                ),
                rx.foreach(RedacteurState.filtered_procedures, _proc_list_row),
                background=CARD_BG, border=f"1px solid {BORDER}",
                border_radius="12px", overflow_x="auto",
            ),
        ),

        spacing="4", width="100%",
    )


# ── Modal confirmation suppression ────────────────────────────────────────────

def _confirm_delete_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Supprimer cette procédure ?", color=TEXT, font_size="1rem"),
            rx.text("Cette action est irréversible.", color=MUTED, font_size="0.85rem"),
            rx.hstack(
                rx.button(
                    "Supprimer",
                    on_click=RedacteurState.confirm_delete,
                    background="rgba(239,68,68,0.14)", color=RED,
                    border=f"1px solid {RED}44", border_radius="8px",
                    padding="5px 14px", font_size="0.82rem", cursor="pointer",
                ),
                rx.dialog.close(
                    rx.button(
                        "Annuler",
                        on_click=RedacteurState.cancel_delete,
                        background="transparent", color=MUTED,
                        border=f"1px solid {BORDER}", border_radius="8px",
                        padding="5px 14px", font_size="0.82rem", cursor="pointer",
                    ),
                ),
                spacing="2", justify="end", margin_top="1rem",
            ),
            background=CARD_BG, border=f"1px solid {BORDER}",
            border_radius="12px", padding="1.25rem", max_width="360px",
        ),
        open=RedacteurState.confirm_delete_id != "",
    )


# ── Page principale ───────────────────────────────────────────────────────────

def redacteur_page() -> rx.Component:
    return page_layout(
        rx.vstack(
            # Titre page
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.icon("notebook-pen", size=20, color=PRIMARY),
                        rx.heading("Rédacteur de Procédures", color=TEXT, size="5"),
                        spacing="2", align="center",
                    ),
                    rx.text(
                        "Rédige et gère les procédures N1 avec l'aide de Claude",
                        color=MUTED, font_size="0.82rem",
                    ),
                    spacing="1",
                ),
                spacing="3", align="start", width="100%",
            ),

            # Layout 2 colonnes
            rx.flex(
                # Gauche : éditeur (60 %)
                rx.box(_editor_panel(), flex="0 0 58%", min_width="0"),

                # Droite : Claude + comparateur (40 %)
                rx.box(_assistant_panel(), flex="0 0 40%", min_width="0"),

                gap="1.25rem",
                width="100%",
                align_items="start",
                flex_wrap="wrap",
            ),

            # Liste procédures
            _procedures_list(),

            # Modals
            _confirm_delete_modal(),

            spacing="5", width="100%",
            on_mount=[AuthState.require_manager, RedacteurState.load],
        ),
        title="Rédacteur Procédures",
    )
