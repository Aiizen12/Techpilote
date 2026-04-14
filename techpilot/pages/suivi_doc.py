import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.state.auth import AuthState
from techpilot.state.suivi_doc import SuiviDocState, CATEGORIES, PRIORITES, STATUTS_AM

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
CARD_BG = "#111524"
BORDER  = "#1c2138"
PRIMARY = "#6366f1"


# ── Badges couleur ────────────────────────────────────────────────────────────

def _badge(label: str, color: str, bg: str) -> rx.Component:
    return rx.box(
        rx.text(label, color=color, font_size="0.72rem", font_weight="600"),
        background=bg, border=f"1px solid {color}33",
        border_radius="6px", padding="2px 8px", display="inline-flex",
    )


def _priorite_badge(p: str) -> rx.Component:
    return rx.match(
        p,
        ("Critique", _badge("Critique", "#ef4444", "rgba(239,68,68,0.1)")),
        ("Haute",    _badge("Haute",    "#f97316", "rgba(249,115,22,0.1)")),
        ("Normale",  _badge("Normale",  "#6366f1", "rgba(99,102,241,0.1)")),
        ("Basse",    _badge("Basse",    "#94a3b8", "rgba(148,163,184,0.1)")),
        _badge(p, MUTED, "transparent"),
    )


def _statut_badge(s: str) -> rx.Component:
    return rx.match(
        s,
        ("Ouvert",    _badge("Ouvert",    "#f59e0b", "rgba(245,158,11,0.1)")),
        ("En cours",  _badge("En cours",  "#06b6d4", "rgba(6,182,212,0.1)")),
        ("Résolu",    _badge("Résolu",    "#22c55e", "rgba(34,197,94,0.1)")),
        ("Fermé",     _badge("Fermé",     "#64748b", "rgba(100,116,139,0.1)")),
        _badge(s, MUTED, "transparent"),
    )


def _categorie_badge(c: str) -> rx.Component:
    return rx.match(
        c,
        ("Process",    _badge("Process",    "#8b5cf6", "rgba(139,92,246,0.1)")),
        ("UX",         _badge("UX",         "#ec4899", "rgba(236,72,153,0.1)")),
        ("Technique",  _badge("Technique",  "#06b6d4", "rgba(6,182,212,0.1)")),
        ("Formation",  _badge("Formation",  "#f59e0b", "rgba(245,158,11,0.1)")),
        ("Autre",      _badge("Autre",      "#64748b", "rgba(100,116,139,0.1)")),
        _badge(c, MUTED, "transparent"),
    )


def _proc_badge(has_proc: bool, source: str) -> rx.Component:
    return rx.cond(
        has_proc,
        rx.hstack(
            _badge("Oui", "#22c55e", "rgba(34,197,94,0.1)"),
            rx.cond(
                source != "",
                rx.text(source, color=MUTED, font_size="0.7rem"),
            ),
            spacing="2", align="center",
        ),
        _badge("Non", "#64748b", "rgba(100,116,139,0.08)"),
    )


# ── Onglets ────────────────────────────────────────────────────────────────────

def _tab_btn(label: str, icon_name: str, val: str) -> rx.Component:
    is_active = SuiviDocState.tab == val
    return rx.button(
        rx.hstack(
            rx.icon(icon_name, size=14),
            rx.text(label, font_size="0.82rem", font_weight="600"),
            spacing="2", align="center",
        ),
        on_click=SuiviDocState.set_tab(val),
        style={
            "background": rx.cond(is_active, "rgba(99,102,241,0.15)", "transparent"),
            "color": rx.cond(is_active, PRIMARY, MUTED),
            "border": rx.cond(is_active, f"1px solid rgba(99,102,241,0.3)", f"1px solid {BORDER}"),
            "border_radius": "8px",
            "padding": "6px 14px",
            "cursor": "pointer",
        },
    )


# ── Formulaire Amélioration (modal) ──────────────────────────────────────────

def _select(value, on_change, options: list[str], placeholder: str = "") -> rx.Component:
    return rx.select.root(
        rx.select.trigger(
            placeholder=placeholder,
            style={
                "background": "#0d1117",
                "color": TEXT,
                "border": f"1px solid {BORDER}",
                "border_radius": "8px",
                "padding": "6px 10px",
                "width": "100%",
                "font_size": "0.85rem",
            },
        ),
        rx.select.content(
            *[rx.select.item(o, value=o) for o in options],
            background=CARD_BG,
        ),
        value=value,
        on_change=on_change,
    )


def _form_modal() -> rx.Component:
    is_edit = SuiviDocState.edit_id != ""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(is_edit, "Modifier la fiche", "Nouvelle fiche"),
                color=TEXT, font_weight="700", font_size="1.05rem",
            ),
            rx.vstack(
                # Titre
                rx.vstack(
                    rx.text("Titre *", color=MUTED, font_size="0.75rem", font_weight="600"),
                    rx.input(
                        value=SuiviDocState.form_titre,
                        on_change=SuiviDocState.set_form_titre,
                        placeholder="Ex : Améliorer la procédure VPN",
                        style={
                            "background": "#0d1117", "color": TEXT,
                            "border": f"1px solid {BORDER}", "border_radius": "8px",
                            "padding": "6px 10px", "width": "100%", "font_size": "0.85rem",
                        },
                    ),
                    spacing="1", width="100%",
                ),
                # Description
                rx.vstack(
                    rx.text("Description", color=MUTED, font_size="0.75rem", font_weight="600"),
                    rx.text_area(
                        value=SuiviDocState.form_description,
                        on_change=SuiviDocState.set_form_description,
                        placeholder="Détaillez l'amélioration souhaitée…",
                        rows="4",
                        style={
                            "background": "#0d1117", "color": TEXT,
                            "border": f"1px solid {BORDER}", "border_radius": "8px",
                            "padding": "8px 10px", "width": "100%",
                            "font_size": "0.85rem", "resize": "vertical",
                        },
                    ),
                    spacing="1", width="100%",
                ),
                # Catégorie + Priorité
                rx.hstack(
                    rx.vstack(
                        rx.text("Catégorie", color=MUTED, font_size="0.75rem", font_weight="600"),
                        _select(SuiviDocState.form_categorie, SuiviDocState.set_form_categorie, CATEGORIES),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text("Priorité", color=MUTED, font_size="0.75rem", font_weight="600"),
                        _select(SuiviDocState.form_priorite, SuiviDocState.set_form_priorite, PRIORITES),
                        spacing="1", width="100%",
                    ),
                    spacing="3", width="100%",
                ),
                # Statut (visible en édition seulement)
                rx.cond(
                    is_edit,
                    rx.vstack(
                        rx.text("Statut", color=MUTED, font_size="0.75rem", font_weight="600"),
                        _select(SuiviDocState.form_statut, SuiviDocState.set_form_statut, STATUTS_AM),
                        spacing="1", width="100%",
                    ),
                ),
                # Boutons
                rx.hstack(
                    rx.button(
                        rx.cond(is_edit, "Mettre à jour", "Ajouter"),
                        on_click=SuiviDocState.save_form,
                        style={
                            "background": PRIMARY, "color": "white",
                            "border_radius": "8px", "padding": "6px 18px",
                            "font_size": "0.85rem", "cursor": "pointer",
                            "border": "none",
                        },
                    ),
                    rx.dialog.close(
                        rx.button(
                            "Annuler",
                            on_click=SuiviDocState.close_form,
                            style={
                                "background": "transparent", "color": MUTED,
                                "border": f"1px solid {BORDER}", "border_radius": "8px",
                                "padding": "6px 18px", "font_size": "0.85rem", "cursor": "pointer",
                            },
                        ),
                    ),
                    spacing="2", justify="end", width="100%",
                ),
                spacing="4", width="100%",
            ),
            background=CARD_BG, border=f"1px solid {BORDER}",
            border_radius="16px", max_width="520px", width="90vw", padding="1.5rem",
        ),
        open=SuiviDocState.show_form,
    )


# ── Confirmation suppression (mini dialog) ────────────────────────────────────

def _confirm_delete_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Supprimer cette fiche ?", color=TEXT, font_size="1rem"),
            rx.text("Cette action est irréversible.", color=MUTED, font_size="0.85rem"),
            rx.hstack(
                rx.button(
                    "Supprimer", on_click=SuiviDocState.confirm_delete,
                    style={
                        "background": "rgba(239,68,68,0.15)", "color": "#ef4444",
                        "border": "1px solid rgba(239,68,68,0.3)",
                        "border_radius": "8px", "padding": "5px 14px",
                        "font_size": "0.82rem", "cursor": "pointer",
                    },
                ),
                rx.dialog.close(
                    rx.button(
                        "Annuler", on_click=SuiviDocState.cancel_delete,
                        style={
                            "background": "transparent", "color": MUTED,
                            "border": f"1px solid {BORDER}",
                            "border_radius": "8px", "padding": "5px 14px",
                            "font_size": "0.82rem", "cursor": "pointer",
                        },
                    ),
                ),
                spacing="2", justify="end", margin_top="1rem",
            ),
            background=CARD_BG, border=f"1px solid {BORDER}",
            border_radius="12px", padding="1.2rem", max_width="360px",
        ),
        open=SuiviDocState.confirm_delete_id != "",
    )


# ── Sheet 1 : Amélioration Desk ───────────────────────────────────────────────

def _amelioration_row(item) -> rx.Component:
    return rx.box(
        rx.hstack(
            # Titre + description
            rx.vstack(
                rx.text(item.titre, color=TEXT, font_size="0.88rem", font_weight="600"),
                rx.cond(
                    item.description != "",
                    rx.text(
                        item.description, color=MUTED, font_size="0.78rem",
                        line_height="1.45",
                        style={"display": "-webkit-box", "WebkitLineClamp": "2",
                               "WebkitBoxOrient": "vertical", "overflow": "hidden"},
                    ),
                ),
                spacing="1", align="start", flex="1",
            ),
            # Badges
            rx.vstack(
                _categorie_badge(item.categorie),
                _priorite_badge(item.priorite),
                spacing="1", align="end",
            ),
            # Statut
            rx.box(_statut_badge(item.statut), min_width="80px"),
            # Auteur + date
            rx.vstack(
                rx.text(item.auteur_nom, color=TEXT, font_size="0.78rem"),
                rx.text(item.date_creation, color=MUTED, font_size="0.7rem"),
                spacing="0", align="end", min_width="90px",
            ),
            # Actions (si droit)
            rx.cond(
                AuthState.can_edit_doc,
                rx.hstack(
                    rx.button(
                        rx.icon("pencil", size=13),
                        on_click=SuiviDocState.open_edit_form(item.id),
                        style={
                            "background": "rgba(99,102,241,0.1)", "color": PRIMARY,
                            "border": "1px solid rgba(99,102,241,0.2)",
                            "border_radius": "6px", "padding": "4px 8px",
                            "cursor": "pointer",
                        },
                    ),
                    rx.button(
                        rx.icon("trash-2", size=13),
                        on_click=SuiviDocState.ask_delete(item.id),
                        style={
                            "background": "rgba(239,68,68,0.08)", "color": "#ef4444",
                            "border": "1px solid rgba(239,68,68,0.2)",
                            "border_radius": "6px", "padding": "4px 8px",
                            "cursor": "pointer",
                        },
                    ),
                    spacing="1",
                ),
            ),
            spacing="4", align="center", width="100%",
        ),
        background=CARD_BG, border=f"1px solid {BORDER}",
        border_radius="10px", padding="12px 16px",
    )


def _sheet_amelioration() -> rx.Component:
    return rx.vstack(
        # En-tête
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.icon("notebook-pen", size=16, color="#f97316"),
                    rx.text("Amélioration Desk", color=TEXT, font_size="1rem", font_weight="700"),
                    spacing="2", align="center",
                ),
                rx.text(
                    "Fiches d'amélioration du helpdesk — modifiables par le tech référent",
                    color=MUTED, font_size="0.78rem",
                ),
                spacing="1",
            ),
            rx.spacer(),
            rx.hstack(
                # Filtre statut
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Tous statuts",
                        style={
                            "background": CARD_BG, "color": TEXT,
                            "border": f"1px solid {BORDER}", "border_radius": "8px",
                            "padding": "5px 10px", "font_size": "0.8rem",
                        },
                    ),
                    rx.select.content(
                        rx.select.item("Tous", value=""),
                        *[rx.select.item(s, value=s) for s in STATUTS_AM],
                        background=CARD_BG,
                    ),
                    value=SuiviDocState.filter_statut,
                    on_change=SuiviDocState.set_filter_statut,
                ),
                # Bouton ajouter (si droit)
                rx.cond(
                    AuthState.can_edit_doc,
                    rx.button(
                        rx.icon("plus", size=14),
                        rx.text("Nouvelle fiche", font_size="0.82rem"),
                        on_click=SuiviDocState.open_new_form,
                        style={
                            "background": PRIMARY, "color": "white",
                            "border": "none", "border_radius": "8px",
                            "padding": "6px 14px", "cursor": "pointer",
                            "display": "flex", "align_items": "center", "gap": "6px",
                        },
                    ),
                ),
                spacing="2", align="center",
            ),
            align="start", width="100%",
        ),

        # Liste des fiches
        rx.cond(
            SuiviDocState.items.length() > 0,
            rx.vstack(
                rx.foreach(SuiviDocState.items, _amelioration_row),
                spacing="2", width="100%",
            ),
            rx.box(
                rx.vstack(
                    rx.icon("notebook-pen", size=32, color=MUTED),
                    rx.text(
                        "Aucune fiche d'amélioration.",
                        color=MUTED, font_size="0.9rem",
                    ),
                    rx.cond(
                        AuthState.can_edit_doc,
                        rx.text(
                            "Cliquez sur « Nouvelle fiche » pour en créer une.",
                            color=MUTED, font_size="0.8rem",
                        ),
                    ),
                    spacing="2", align="center",
                ),
                width="100%", text_align="center", padding="3rem 0",
            ),
        ),

        spacing="4", width="100%",
    )


# ── Sheet 2 : Suivi des Procédures ────────────────────────────────────────────

def _proc_row(row) -> rx.Component:
    return rx.hstack(
        # Périmètre
        rx.text(row.perimetre, color=MUTED, font_size="0.78rem",
                min_width="120px", max_width="140px",
                style={"white_space": "nowrap", "overflow": "hidden",
                       "text_overflow": "ellipsis"}),
        # Typologie
        rx.text(row.typologie, color=TEXT, font_size="0.82rem",
                flex="1", line_height="1.4"),
        # Catégorie FRESH
        rx.text(row.categorie_fresh, color=MUTED, font_size="0.75rem",
                min_width="120px", max_width="140px",
                style={"white_space": "nowrap", "overflow": "hidden",
                       "text_overflow": "ellipsis"}),
        # Procédure
        rx.box(
            _proc_badge(row.has_procedure, row.procedure_source),
            min_width="130px",
        ),
        spacing="3", align="center", width="100%",
        padding="8px 14px",
        border_bottom=f"1px solid {BORDER}",
        _hover={"background": "rgba(255,255,255,0.02)"},
    )


def _proc_header() -> rx.Component:
    return rx.hstack(
        rx.text("Périmètre",       color=MUTED, font_size="0.72rem", font_weight="700",
                min_width="120px", max_width="140px"),
        rx.text("Typologie",       color=MUTED, font_size="0.72rem", font_weight="700", flex="1"),
        rx.text("Catégorie FRESH", color=MUTED, font_size="0.72rem", font_weight="700",
                min_width="120px", max_width="140px"),
        rx.text("Procédure N1",    color=MUTED, font_size="0.72rem", font_weight="700",
                min_width="130px"),
        spacing="3", width="100%",
        padding="6px 14px",
        border_bottom=f"1px solid {BORDER}",
    )


def _sheet_procedures() -> rx.Component:
    return rx.vstack(
        # En-tête + filtres
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.icon("list-checks", size=16, color="#22c55e"),
                    rx.text("Suivi des Procédures", color=TEXT, font_size="1rem", font_weight="700"),
                    spacing="2", align="center",
                ),
                rx.text(
                    "Toutes les lignes de la matrice d'escalade avec l'état de couverture procédurale",
                    color=MUTED, font_size="0.78rem",
                ),
                spacing="1",
            ),
            rx.spacer(),
            rx.hstack(
                # Compteurs
                rx.hstack(
                    rx.box(
                        rx.text(
                            SuiviDocState.proc_count_with.to_string() + " couvertes",
                            color="#22c55e", font_size="0.75rem", font_weight="600",
                        ),
                        background="rgba(34,197,94,0.08)",
                        border="1px solid rgba(34,197,94,0.2)",
                        border_radius="6px", padding="3px 8px",
                    ),
                    rx.box(
                        rx.text(
                            SuiviDocState.proc_count_without.to_string() + " sans",
                            color=MUTED, font_size="0.75rem", font_weight="600",
                        ),
                        background="rgba(100,116,139,0.08)",
                        border=f"1px solid {BORDER}",
                        border_radius="6px", padding="3px 8px",
                    ),
                    spacing="2",
                ),
                spacing="2", align="center",
            ),
            align="start", width="100%",
        ),

        # Filtres
        rx.hstack(
            rx.input(
                value=SuiviDocState.proc_search,
                on_change=SuiviDocState.set_proc_search,
                placeholder="Rechercher…",
                style={
                    "background": CARD_BG, "color": TEXT,
                    "border": f"1px solid {BORDER}", "border_radius": "8px",
                    "padding": "5px 10px", "font_size": "0.82rem", "width": "200px",
                },
            ),
            rx.select.root(
                rx.select.trigger(
                    placeholder="Tous périmètres",
                    style={
                        "background": CARD_BG, "color": TEXT,
                        "border": f"1px solid {BORDER}", "border_radius": "8px",
                        "padding": "5px 10px", "font_size": "0.8rem",
                    },
                ),
                rx.select.content(
                    rx.select.item("Tous", value=""),
                    rx.foreach(
                        SuiviDocState.proc_perimetres,
                        lambda p: rx.select.item(p, value=p),
                    ),
                    background=CARD_BG,
                ),
                value=SuiviDocState.proc_filter_perimetre,
                on_change=SuiviDocState.set_proc_filter_perimetre,
            ),
            rx.button(
                rx.icon("x", size=13),
                on_click=SuiviDocState.clear_proc_filter,
                style={
                    "background": "transparent", "color": MUTED,
                    "border": f"1px solid {BORDER}", "border_radius": "8px",
                    "padding": "5px 9px", "cursor": "pointer",
                },
            ),
            spacing="2", align="center",
        ),

        # Tableau
        rx.box(
            _proc_header(),
            rx.vstack(
                rx.foreach(SuiviDocState.proc_rows, _proc_row),
                spacing="0", width="100%",
            ),
            background=CARD_BG, border=f"1px solid {BORDER}",
            border_radius="12px", overflow_x="auto",
        ),

        # Pagination
        rx.hstack(
            rx.text(
                "Page " + SuiviDocState.proc_page.to_string()
                + " / " + SuiviDocState.proc_total_pages.to_string()
                + " — " + SuiviDocState.proc_total.to_string() + " lignes",
                color=MUTED, font_size="0.78rem",
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.icon("chevron-left", size=14),
                    on_click=SuiviDocState.proc_go_page(SuiviDocState.proc_page - 1),
                    disabled=SuiviDocState.proc_page <= 1,
                    style={
                        "background": "transparent", "color": MUTED,
                        "border": f"1px solid {BORDER}", "border_radius": "6px",
                        "padding": "4px 8px", "cursor": "pointer",
                    },
                ),
                rx.button(
                    rx.icon("chevron-right", size=14),
                    on_click=SuiviDocState.proc_go_page(SuiviDocState.proc_page + 1),
                    disabled=SuiviDocState.proc_page >= SuiviDocState.proc_total_pages,
                    style={
                        "background": "transparent", "color": MUTED,
                        "border": f"1px solid {BORDER}", "border_radius": "6px",
                        "padding": "4px 8px", "cursor": "pointer",
                    },
                ),
                spacing="1",
            ),
        ),

        spacing="4", width="100%",
    )


# ── Page principale ────────────────────────────────────────────────────────────

def suivi_doc_page() -> rx.Component:
    return page_layout(
        rx.vstack(
            # Titre
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.icon("book-open", size=20, color=PRIMARY),
                        rx.heading("Suivi de Doc", color=TEXT, size="5"),
                        spacing="2", align="center",
                    ),
                    rx.text(
                        "Documentation interne et couverture procédurale de la matrice d'escalade",
                        color=MUTED, font_size="0.82rem",
                    ),
                    spacing="1",
                ),
                spacing="3", align="start", width="100%",
            ),

            # Onglets
            rx.hstack(
                _tab_btn("Amélioration Desk",    "notebook-pen",  "amelioration"),
                _tab_btn("Suivi des Procédures", "list-checks",   "procedures"),
                spacing="2",
            ),

            # Contenu onglet
            rx.box(
                rx.cond(
                    SuiviDocState.tab == "amelioration",
                    _sheet_amelioration(),
                    _sheet_procedures(),
                ),
                background="#0d1117",
                border=f"1px solid {BORDER}",
                border_radius="14px",
                padding="1.25rem",
                width="100%",
            ),

            # Modals
            _form_modal(),
            _confirm_delete_modal(),

            spacing="5", width="100%",
            on_mount=SuiviDocState.load,
        ),
        title="Suivi de Doc",
    )
