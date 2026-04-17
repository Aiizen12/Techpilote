import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.state.auth import AuthState
from techpilot.state.suivi_doc import SuiviDocState, CATEGORIES, PRIORITES, STATUTS_AM
from techpilot.state.models import DocPickerItem

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
                rx.match(
                    source,
                    ("Document",     rx.hstack(rx.icon("file-text", size=11, color="#a5b4fc"),
                                               rx.text("Document", color="#a5b4fc", font_size="0.7rem"),
                                               spacing="1", align="center")),
                    ("Intégrée",     rx.text("Intégrée",     color=MUTED, font_size="0.7rem")),
                    ("Personnalisée",rx.text("Personnalisée", color=MUTED, font_size="0.7rem")),
                    rx.text(source, color=MUTED, font_size="0.7rem"),
                ),
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


# ── Confirmation suppression amélioration ─────────────────────────────────────

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


# ── Modal sélection document ──────────────────────────────────────────────────

def _doc_picker_item(doc: DocPickerItem) -> rx.Component:
    return rx.hstack(
        rx.icon("file-text", size=14, color="#a5b4fc", flex_shrink="0"),
        rx.vstack(
            rx.text(doc.nom, color=TEXT, font_size="0.82rem", font_weight="500",
                    white_space="nowrap", overflow="hidden", text_overflow="ellipsis"),
            rx.text(doc.url, color=MUTED, font_size="0.68rem",
                    white_space="nowrap", overflow="hidden", text_overflow="ellipsis",
                    max_width="340px"),
            spacing="0", align="start", flex="1", min_width="0",
        ),
        rx.button(
            "Lier",
            on_click=SuiviDocState.link_doc_to_proc(doc.id, doc.nom, doc.url),
            background="rgba(99,102,241,0.15)", color="#a5b4fc",
            border="1px solid rgba(99,102,241,0.35)", border_radius="7px",
            font_size="0.75rem", font_weight="600", padding="3px 10px",
            cursor="pointer", flex_shrink="0",
            _hover={"background": "rgba(99,102,241,0.3)"},
        ),
        spacing="3", align="center", width="100%",
        padding="8px 12px",
        border_bottom=f"1px solid {BORDER}",
        _hover={"background": "rgba(255,255,255,0.025)"},
    )


def _gabarit_picker_item(g: DocPickerItem) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.icon("file-text", size=15, color="#a5b4fc"),
            flex_shrink="0", width="2rem", height="2rem",
            background="rgba(99,102,241,0.12)", border_radius="8px",
            display="flex", align_items="center", justify_content="center",
        ),
        rx.text(g["nom"], color=TEXT, font_size="0.82rem", flex="1",
                overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
        rx.button(
            "Lier",
            on_click=SuiviDocState.link_gabarit_to_proc(g["id"], g["nom"]),
            background="rgba(99,102,241,0.15)", color="#a5b4fc",
            border="1px solid rgba(99,102,241,0.3)", border_radius="6px",
            font_size="0.75rem", font_weight="600", padding="3px 10px",
            cursor="pointer", flex_shrink="0",
            _hover={"background": "rgba(99,102,241,0.3)"},
        ),
        spacing="3", align="center", width="100%",
        padding="8px 12px",
        border_bottom=f"1px solid {BORDER}",
        _hover={"background": "rgba(255,255,255,0.025)"},
    )


def _doc_picker_modal() -> rx.Component:
    is_docs_tab = SuiviDocState.doc_picker_tab == "documents"
    return rx.dialog.root(
        rx.dialog.content(
            # Header
            rx.box(
                rx.hstack(
                    rx.box(
                        rx.icon("link-2", size=18, color="white"),
                        background="rgba(255,255,255,0.15)", border_radius="10px",
                        padding="8px", display="flex", align_items="center",
                        justify_content="center",
                    ),
                    rx.vstack(
                        rx.text("Lier un document", color="white", font_size="1rem", font_weight="700"),
                        rx.text("Choisir le document ou gabarit à associer",
                                color="rgba(255,255,255,0.65)", font_size="0.72rem"),
                        spacing="0", align="start",
                    ),
                    spacing="3", align="center",
                ),
                background="linear-gradient(135deg, #1e1b4b, #4338ca)",
                border_radius="12px 12px 0 0",
                padding="1.25rem 1.5rem",
                margin="-24px -24px 0 -24px",
            ),
            # Onglets
            rx.hstack(
                rx.button(
                    rx.icon("folder-open", size=13), "Documents",
                    on_click=SuiviDocState.set_doc_picker_tab("documents"),
                    background=rx.cond(is_docs_tab, "rgba(99,102,241,0.2)", "transparent"),
                    color=rx.cond(is_docs_tab, PRIMARY, MUTED),
                    border=rx.cond(is_docs_tab, "1px solid rgba(99,102,241,0.4)", f"1px solid {BORDER}"),
                    border_radius="7px", font_size="0.78rem", font_weight="600",
                    padding="4px 12px", cursor="pointer", spacing="1",
                ),
                rx.button(
                    rx.icon("file-text", size=13), "Gabarits",
                    on_click=SuiviDocState.set_doc_picker_tab("gabarits"),
                    background=rx.cond(~is_docs_tab, "rgba(99,102,241,0.2)", "transparent"),
                    color=rx.cond(~is_docs_tab, PRIMARY, MUTED),
                    border=rx.cond(~is_docs_tab, "1px solid rgba(99,102,241,0.4)", f"1px solid {BORDER}"),
                    border_radius="7px", font_size="0.78rem", font_weight="600",
                    padding="4px 12px", cursor="pointer", spacing="1",
                ),
                spacing="2", padding_top="1rem", padding_bottom="0.5rem",
            ),
            # Recherche
            rx.input(
                placeholder=rx.cond(is_docs_tab, "Rechercher un document…", "Rechercher un gabarit…"),
                value=SuiviDocState.doc_picker_search,
                on_change=SuiviDocState.set_doc_picker_search,
                background="#0d1117", style={"color": TEXT},
                border=f"1px solid {BORDER}", border_radius="8px",
                font_size="0.82rem", width="100%", margin_bottom="0.5rem",
            ),
            # Liste documents
            rx.cond(
                is_docs_tab,
                rx.cond(
                    SuiviDocState.available_proc_docs.length() == 0,
                    rx.box(
                        rx.vstack(
                            rx.icon("folder-open", size=32, color=MUTED),
                            rx.text("Aucun document trouvé.", color=MUTED, font_size="0.85rem"),
                            spacing="2", align="center",
                        ),
                        padding="2rem", text_align="center",
                    ),
                    rx.box(
                        rx.foreach(SuiviDocState.available_proc_docs, _doc_picker_item),
                        max_height="300px", overflow_y="auto", width="100%",
                    ),
                ),
                # Liste gabarits
                rx.cond(
                    SuiviDocState.available_gabarits_picker.length() == 0,
                    rx.box(
                        rx.vstack(
                            rx.icon("file-text", size=32, color=MUTED),
                            rx.text("Aucun gabarit trouvé.", color=MUTED, font_size="0.85rem"),
                            spacing="2", align="center",
                        ),
                        padding="2rem", text_align="center",
                    ),
                    rx.box(
                        rx.foreach(SuiviDocState.available_gabarits_picker, _gabarit_picker_item),
                        max_height="300px", overflow_y="auto", width="100%",
                    ),
                ),
            ),
            rx.hstack(
                rx.button(
                    "Annuler",
                    on_click=SuiviDocState.close_doc_picker,
                    background="transparent", color=MUTED,
                    border=f"1px solid {BORDER}", border_radius="8px",
                    cursor="pointer", padding="6px 14px",
                ),
                justify="end", width="100%", padding_top="0.75rem",
            ),
            background="#151728",
            border=f"1px solid rgba(255,255,255,0.1)",
            border_radius="16px",
            padding="24px",
            max_width="520px",
            overflow="hidden",
        ),
        open=SuiviDocState.show_doc_picker,
    )


# ── Modal procédure (ajout/visualisation depuis le tableau) ───────────────────

def _proc_form_modal() -> rx.Component:
    can_edit = AuthState.can_edit_procedure
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Titre du modal
                rx.hstack(
                    rx.icon("list-checks", size=16, color="#22c55e"),
                    rx.vstack(
                        rx.text(
                            SuiviDocState.proc_form_perimetre + " — " + SuiviDocState.proc_form_typologie,
                            color=TEXT, font_weight="700", font_size="0.95rem",
                        ),
                        rx.text("Procédure N1", color=MUTED, font_size="0.72rem"),
                        spacing="0",
                    ),
                    spacing="2", align="center",
                ),
                rx.divider(border_color=BORDER),
                # Zone étapes
                rx.cond(
                    can_edit,
                    # Mode édition
                    rx.vstack(
                        rx.hstack(
                            rx.icon("pencil", size=12, color=MUTED),
                            rx.text(
                                "Une étape par ligne",
                                color=MUTED, font_size="0.72rem",
                            ),
                            spacing="1", align="center",
                        ),
                        rx.text_area(
                            value=SuiviDocState.proc_form_steps_text,
                            on_change=SuiviDocState.set_proc_form_steps_text,
                            placeholder="Étape 1 : Vérifier la connexion réseau\nÉtape 2 : Relancer le service\n...",
                            rows="14",
                            style={
                                "background": "#0d1117", "color": TEXT,
                                "border": f"1px solid {BORDER}", "border_radius": "8px",
                                "padding": "10px 12px", "width": "100%",
                                "font_size": "0.83rem", "resize": "vertical",
                                "line_height": "1.6", "font_family": "monospace",
                            },
                        ),
                        spacing="2", width="100%",
                    ),
                    # Mode lecture seule
                    rx.box(
                        rx.cond(
                            SuiviDocState.proc_form_steps_text != "",
                            rx.text(
                                SuiviDocState.proc_form_steps_text,
                                color=TEXT, font_size="0.85rem",
                                white_space="pre-wrap", line_height="1.7",
                            ),
                            rx.hstack(
                                rx.icon("circle-slash", size=16, color=MUTED),
                                rx.text("Aucune procédure définie.", color=MUTED, font_size="0.85rem"),
                                spacing="2", align="center",
                            ),
                        ),
                        background="#0d1117",
                        border=f"1px solid {BORDER}",
                        border_radius="8px",
                        padding="12px 14px",
                        width="100%",
                        min_height="120px",
                    ),
                ),
                # Boutons
                rx.hstack(
                    rx.cond(
                        can_edit,
                        rx.button(
                            rx.icon("save", size=14),
                            rx.text("Sauvegarder", font_size="0.85rem"),
                            on_click=SuiviDocState.save_proc_form,
                            style={
                                "background": PRIMARY, "color": "white",
                                "border": "none", "border_radius": "8px",
                                "padding": "6px 16px", "cursor": "pointer",
                                "display": "flex", "align_items": "center", "gap": "6px",
                            },
                        ),
                    ),
                    rx.dialog.close(
                        rx.button(
                            "Fermer",
                            on_click=SuiviDocState.close_proc_form,
                            style={
                                "background": "transparent", "color": MUTED,
                                "border": f"1px solid {BORDER}", "border_radius": "8px",
                                "padding": "6px 16px", "font_size": "0.85rem", "cursor": "pointer",
                            },
                        ),
                    ),
                    spacing="2", justify="end", width="100%",
                ),
                spacing="4", width="100%",
            ),
            background=CARD_BG, border=f"1px solid {BORDER}",
            border_radius="16px", max_width="600px", width="90vw", padding="1.5rem",
        ),
        open=SuiviDocState.show_proc_form,
    )


# ── Sheet 1 : Amélioration Desk (tableau) ────────────────────────────────────

def _amelioration_header() -> rx.Component:
    return rx.hstack(
        rx.text("Titre / Description", color=MUTED, font_size="0.72rem", font_weight="700",
                flex="1", min_width="0"),
        rx.text("Catégorie",  color=MUTED, font_size="0.72rem", font_weight="700", min_width="95px"),
        rx.text("Priorité",   color=MUTED, font_size="0.72rem", font_weight="700", min_width="80px"),
        rx.text("Statut",     color=MUTED, font_size="0.72rem", font_weight="700", min_width="85px"),
        rx.text("Auteur",     color=MUTED, font_size="0.72rem", font_weight="700",
                min_width="80px", max_width="90px"),
        rx.text("Date",       color=MUTED, font_size="0.72rem", font_weight="700", min_width="72px"),
        # Espace actions (affiché ou non selon le droit)
        rx.cond(
            AuthState.can_edit_doc,
            rx.box(width="68px"),
        ),
        spacing="3", width="100%",
        padding="7px 14px",
        border_bottom=f"1px solid {BORDER}",
    )


def _amelioration_table_row(item) -> rx.Component:
    return rx.hstack(
        # Titre + description
        rx.vstack(
            rx.text(item.titre, color=TEXT, font_size="0.85rem", font_weight="600"),
            rx.cond(
                item.description != "",
                rx.text(
                    item.description, color=MUTED, font_size="0.75rem",
                    style={"display": "-webkit-box", "WebkitLineClamp": "1",
                           "WebkitBoxOrient": "vertical", "overflow": "hidden"},
                ),
            ),
            spacing="0", align="start", flex="1", min_width="0",
        ),
        # Catégorie
        rx.box(_categorie_badge(item.categorie), min_width="95px"),
        # Priorité
        rx.box(_priorite_badge(item.priorite), min_width="80px"),
        # Statut
        rx.box(_statut_badge(item.statut), min_width="85px"),
        # Auteur
        rx.text(item.auteur_nom, color=MUTED, font_size="0.75rem",
                min_width="80px", max_width="90px",
                style={"overflow": "hidden", "text_overflow": "ellipsis", "white_space": "nowrap"}),
        # Date
        rx.text(item.date_creation, color=MUTED, font_size="0.72rem", min_width="72px"),
        # Actions
        rx.cond(
            AuthState.can_edit_doc,
            rx.hstack(
                rx.button(
                    rx.icon("pencil", size=13),
                    on_click=SuiviDocState.open_edit_form(item.id),
                    style={
                        "background": "rgba(99,102,241,0.1)", "color": PRIMARY,
                        "border": "1px solid rgba(99,102,241,0.2)",
                        "border_radius": "6px", "padding": "4px 8px", "cursor": "pointer",
                    },
                ),
                rx.button(
                    rx.icon("trash-2", size=13),
                    on_click=SuiviDocState.ask_delete(item.id),
                    style={
                        "background": "rgba(239,68,68,0.08)", "color": "#ef4444",
                        "border": "1px solid rgba(239,68,68,0.2)",
                        "border_radius": "6px", "padding": "4px 8px", "cursor": "pointer",
                    },
                ),
                spacing="1",
            ),
        ),
        spacing="3", align="center", width="100%",
        padding="9px 14px",
        border_bottom=f"1px solid {BORDER}",
        _hover={"background": "rgba(255,255,255,0.02)"},
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
                # Filtre statut (pills)
                rx.button(
                    "Tous",
                    on_click=SuiviDocState.clear_filter_statut,
                    style={
                        "background": rx.cond(SuiviDocState.filter_statut == "", "rgba(99,102,241,0.2)", "transparent"),
                        "color": rx.cond(SuiviDocState.filter_statut == "", PRIMARY, MUTED),
                        "border": rx.cond(SuiviDocState.filter_statut == "", "1px solid rgba(99,102,241,0.4)", f"1px solid {BORDER}"),
                        "border_radius": "20px", "padding": "3px 12px",
                        "font_size": "0.75rem", "cursor": "pointer", "white_space": "nowrap",
                    },
                ),
                *[
                    rx.button(
                        s,
                        on_click=SuiviDocState.set_filter_statut(s),
                        style={
                            "background": rx.cond(SuiviDocState.filter_statut == s, "rgba(99,102,241,0.2)", "transparent"),
                            "color": rx.cond(SuiviDocState.filter_statut == s, PRIMARY, MUTED),
                            "border": rx.cond(SuiviDocState.filter_statut == s, "1px solid rgba(99,102,241,0.4)", f"1px solid {BORDER}"),
                            "border_radius": "20px", "padding": "3px 12px",
                            "font_size": "0.75rem", "cursor": "pointer", "white_space": "nowrap",
                        },
                    )
                    for s in STATUTS_AM
                ],
                # Bouton ajouter
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
                spacing="2", align="center", flex_wrap="wrap",
            ),
            align="start", width="100%",
        ),

        # Tableau
        rx.cond(
            SuiviDocState.items.length() > 0,
            rx.box(
                _amelioration_header(),
                rx.vstack(
                    rx.foreach(SuiviDocState.items, _amelioration_table_row),
                    spacing="0", width="100%",
                ),
                background=CARD_BG, border=f"1px solid {BORDER}",
                border_radius="12px", overflow_x="auto",
            ),
            rx.box(
                rx.vstack(
                    rx.icon("notebook-pen", size=32, color=MUTED),
                    rx.text("Aucune fiche d'amélioration.", color=MUTED, font_size="0.9rem"),
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
                min_width="110px", max_width="130px",
                style={"white_space": "nowrap", "overflow": "hidden",
                       "text_overflow": "ellipsis"}),
        # Typologie (cliquable pour ouvrir le formulaire procédure)
        rx.text(
            row.typologie, color=TEXT, font_size="0.82rem",
            flex="1", line_height="1.4", cursor="pointer",
            _hover={"color": "#a5b4fc", "text_decoration": "underline"},
            on_click=SuiviDocState.open_proc_form(row.perimetre, row.typologie),
        ),
        # Catégorie FRESH
        rx.text(row.categorie_fresh, color=MUTED, font_size="0.75rem",
                min_width="100px", max_width="120px",
                style={"white_space": "nowrap", "overflow": "hidden",
                       "text_overflow": "ellipsis"}),
        # Procédure
        rx.box(
            _proc_badge(row.has_procedure, row.procedure_source),
            min_width="120px",
        ),
        # Document lié
        rx.box(
            rx.cond(
                row.doc_url != "",
                # Doc lié → afficher le lien + bouton unlink
                rx.hstack(
                    rx.link(
                        rx.hstack(
                            rx.icon("file-text", size=13, color="#a5b4fc"),
                            rx.text(
                                row.doc_name,
                                color="#a5b4fc", font_size="0.75rem",
                                max_width="140px",
                                style={"white_space": "nowrap", "overflow": "hidden",
                                       "text_overflow": "ellipsis"},
                            ),
                            spacing="1", align="center",
                        ),
                        href=row.doc_url, target="_blank",
                        text_decoration="none",
                        _hover={"opacity": "0.8"},
                    ),
                    rx.icon_button(
                        rx.icon("x", size=11),
                        on_click=SuiviDocState.unlink_doc_from_proc(row.perimetre, row.typologie),
                        background="transparent", color=MUTED, border="none",
                        size="1", cursor="pointer",
                        _hover={"color": "#ef4444"},
                    ),
                    spacing="1", align="center",
                ),
                # Pas de doc → bouton lier
                rx.button(
                    rx.icon("link-2", size=12),
                    "Lier",
                    on_click=SuiviDocState.open_doc_picker(row.perimetre, row.typologie),
                    background="transparent",
                    color=MUTED,
                    border=f"1px solid {BORDER}",
                    border_radius="6px",
                    font_size="0.72rem",
                    padding="2px 8px",
                    cursor="pointer",
                    spacing="1",
                    _hover={"background": "rgba(99,102,241,0.1)", "color": "#a5b4fc",
                            "border_color": "rgba(99,102,241,0.4)"},
                ),
            ),
            min_width="160px",
        ),
        spacing="3", align="center", width="100%",
        padding="9px 14px",
        border_bottom=f"1px solid {BORDER}",
        _hover={"background": "rgba(255,255,255,0.015)"},
    )


def _proc_header() -> rx.Component:
    return rx.hstack(
        rx.text("Périmètre",       color=MUTED, font_size="0.72rem", font_weight="700",
                min_width="110px", max_width="130px"),
        rx.text("Typologie",       color=MUTED, font_size="0.72rem", font_weight="700", flex="1"),
        rx.text("Catégorie FRESH", color=MUTED, font_size="0.72rem", font_weight="700",
                min_width="100px", max_width="120px"),
        rx.text("Procédure N1",    color=MUTED, font_size="0.72rem", font_weight="700",
                min_width="120px"),
        rx.text("Document lié",    color=MUTED, font_size="0.72rem", font_weight="700",
                min_width="160px"),
        spacing="3", width="100%",
        padding="7px 14px",
        border_bottom=f"1px solid {BORDER}",
    )


def _pill_btn(label: str, val: str, current_val, on_click_event) -> rx.Component:
    is_active = current_val == val
    return rx.button(
        label,
        on_click=on_click_event,
        style={
            "background": rx.cond(is_active, "rgba(99,102,241,0.2)", "transparent"),
            "color": rx.cond(is_active, PRIMARY, MUTED),
            "border": rx.cond(is_active, "1px solid rgba(99,102,241,0.4)", f"1px solid {BORDER}"),
            "border_radius": "20px", "padding": "3px 12px",
            "font_size": "0.75rem", "cursor": "pointer",
            "white_space": "nowrap", "font_weight": "500",
        },
    )


def _sheet_procedures() -> rx.Component:
    return rx.vstack(
        # En-tête + compteurs
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.icon("list-checks", size=16, color="#22c55e"),
                    rx.text("Suivi des Procédures", color=TEXT, font_size="1rem", font_weight="700"),
                    spacing="2", align="center",
                ),
                rx.text(
                    "Cliquez sur une ligne pour voir ou modifier la procédure associée",
                    color=MUTED, font_size="0.78rem",
                ),
                spacing="1",
            ),
            rx.spacer(),
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
                        SuiviDocState.proc_count_without.to_string() + " sans procédure",
                        color=MUTED, font_size="0.75rem", font_weight="600",
                    ),
                    background="rgba(100,116,139,0.08)",
                    border=f"1px solid {BORDER}",
                    border_radius="6px", padding="3px 8px",
                ),
                rx.cond(
                    AuthState.can_edit_procedure,
                    rx.button(
                        rx.icon("wand-sparkles", size=14),
                        "Détecter les correspondances",
                        on_click=SuiviDocState.detect_matches,
                        background="rgba(99,102,241,0.1)",
                        color=PRIMARY,
                        border=f"1px solid rgba(99,102,241,0.3)",
                        border_radius="8px",
                        font_size="0.78rem",
                        font_weight="600",
                        cursor="pointer",
                        spacing="2",
                        _hover={"background": "rgba(99,102,241,0.2)"},
                    ),
                ),
                spacing="2",
            ),
            align="start", width="100%",
        ),

        # Barre filtres
        rx.hstack(
            rx.input(
                value=SuiviDocState.proc_search,
                on_change=SuiviDocState.set_proc_search,
                placeholder="Rechercher dans la matrice…",
                style={
                    "background": CARD_BG, "color": TEXT,
                    "border": f"1px solid {BORDER}", "border_radius": "8px",
                    "padding": "5px 10px", "font_size": "0.82rem", "width": "240px",
                },
            ),
            rx.button(
                rx.icon("x", size=13), "Tout effacer",
                on_click=SuiviDocState.clear_proc_filter,
                style={
                    "background": "transparent", "color": MUTED,
                    "border": f"1px solid {BORDER}", "border_radius": "8px",
                    "padding": "5px 10px", "cursor": "pointer",
                    "font_size": "0.78rem", "display": "flex",
                    "align_items": "center", "gap": "4px",
                },
            ),
            spacing="2", align="center",
        ),

        # Filtre : Procédure Oui/Non
        rx.hstack(
            rx.text("Procédure :", color=MUTED, font_size="0.75rem", font_weight="600"),
            _pill_btn("Toutes", "", SuiviDocState.proc_filter_has_proc,
                      SuiviDocState.set_proc_filter_has_proc("_all")),
            _pill_btn("Avec procédure", "oui", SuiviDocState.proc_filter_has_proc,
                      SuiviDocState.set_proc_filter_has_proc("oui")),
            _pill_btn("Sans procédure", "non", SuiviDocState.proc_filter_has_proc,
                      SuiviDocState.set_proc_filter_has_proc("non")),
            spacing="2", align="center",
        ),

        # Pills périmètres
        rx.box(
            rx.flex(
                rx.button(
                    "Tous",
                    on_click=SuiviDocState.clear_proc_filter,
                    style={
                        "background": rx.cond(
                            SuiviDocState.proc_filter_perimetre == "",
                            "rgba(99,102,241,0.2)", "transparent"
                        ),
                        "color": rx.cond(
                            SuiviDocState.proc_filter_perimetre == "",
                            PRIMARY, MUTED
                        ),
                        "border": rx.cond(
                            SuiviDocState.proc_filter_perimetre == "",
                            "1px solid rgba(99,102,241,0.4)", f"1px solid {BORDER}"
                        ),
                        "border_radius": "20px", "padding": "3px 12px",
                        "font_size": "0.75rem", "cursor": "pointer",
                        "white_space": "nowrap", "font_weight": "500",
                    },
                ),
                rx.foreach(
                    SuiviDocState.proc_perimetres,
                    lambda p: rx.button(
                        p,
                        on_click=SuiviDocState.set_proc_filter_perimetre(p),
                        style={
                            "background": rx.cond(
                                SuiviDocState.proc_filter_perimetre == p,
                                "rgba(99,102,241,0.2)", "transparent"
                            ),
                            "color": rx.cond(
                                SuiviDocState.proc_filter_perimetre == p,
                                PRIMARY, MUTED
                            ),
                            "border": rx.cond(
                                SuiviDocState.proc_filter_perimetre == p,
                                "1px solid rgba(99,102,241,0.4)", f"1px solid {BORDER}"
                            ),
                            "border_radius": "20px", "padding": "3px 12px",
                            "font_size": "0.75rem", "cursor": "pointer",
                            "white_space": "nowrap", "font_weight": "500",
                        },
                    ),
                ),
                flex_wrap="wrap", gap="6px",
            ),
            width="100%",
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

        # ── Modale auto-match ─────────────────────────────────────────────
        rx.dialog.root(
            rx.dialog.content(
                # Header
                rx.hstack(
                    rx.box(
                        rx.icon("wand-sparkles", size=16, color="white"),
                        background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                        border_radius="8px", padding="8px",
                        display="flex", align_items="center", justify_content="center",
                    ),
                    rx.vstack(
                        rx.text("Correspondances détectées", color=TEXT,
                                font_size="1rem", font_weight="700"),
                        rx.text(
                            SuiviDocState.auto_match_proposals.length().to_string()
                            + " proposition(s) — confirmez ou rejetez chacune",
                            color=MUTED, font_size="0.75rem",
                        ),
                        spacing="0", align="start",
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=16),
                        on_click=SuiviDocState.close_auto_match,
                        background="transparent", color=MUTED,
                        size="2", cursor="pointer",
                        _hover={"background": "rgba(255,255,255,0.08)"},
                    ),
                    spacing="3", align="center", width="100%",
                ),

                rx.divider(border_color=BORDER, margin_y="0.75rem"),

                # Liste des propositions
                rx.cond(
                    SuiviDocState.auto_match_proposals.length() > 0,
                    rx.vstack(
                        rx.foreach(
                            SuiviDocState.auto_match_proposals,
                            lambda p, i: rx.vstack(
                                # Ligne résumée — clic pour développer
                                rx.hstack(
                                    rx.icon(
                                        rx.cond(
                                            SuiviDocState.expanded_proposal_idx == i,
                                            "chevron-down", "chevron-right",
                                        ),
                                        size=13, color=MUTED, flex_shrink="0",
                                    ),
                                    rx.text(
                                        p["doc_name"],
                                        color=TEXT, font_size="0.8rem", font_weight="600",
                                        overflow="hidden", text_overflow="ellipsis",
                                        white_space="nowrap", flex="1", min_width="0",
                                    ),
                                    rx.badge(
                                        p["score"].to_string() + " pts",
                                        color_scheme="indigo", variant="soft",
                                        font_size="0.68rem", flex_shrink="0",
                                    ),
                                    rx.icon_button(
                                        rx.icon("check", size=14),
                                        on_click=SuiviDocState.confirm_match_at(i),
                                        background="rgba(34,197,94,0.12)",
                                        color="#22c55e",
                                        border="1px solid rgba(34,197,94,0.3)",
                                        size="1", cursor="pointer", border_radius="6px",
                                        title="Confirmer",
                                        _hover={"background": "rgba(34,197,94,0.25)"},
                                    ),
                                    rx.icon_button(
                                        rx.icon("x", size=14),
                                        on_click=SuiviDocState.reject_match_at(i),
                                        background="transparent", color=MUTED,
                                        size="1", cursor="pointer", border_radius="6px",
                                        title="Rejeter",
                                        _hover={"color": "#ef4444"},
                                    ),
                                    spacing="2", align="center", width="100%",
                                    padding="0.45rem 0.75rem",
                                    cursor="pointer",
                                    on_click=SuiviDocState.toggle_proposal(i),
                                    _hover={"background": "rgba(255,255,255,0.03)"},
                                ),
                                # Détail dépliable
                                rx.cond(
                                    SuiviDocState.expanded_proposal_idx == i,
                                    rx.vstack(
                                        rx.hstack(
                                            rx.icon("file-text", size=12, color="#60a5fa", flex_shrink="0"),
                                            rx.text(p["doc_name"], color=TEXT,
                                                    font_size="0.78rem", font_weight="600",
                                                    white_space="normal", line_height="1.5"),
                                            spacing="2", align="start",
                                        ),
                                        rx.hstack(
                                            rx.icon("arrow-right", size=11, color=MUTED, flex_shrink="0"),
                                            rx.text(
                                                p["perimetre"] + " · " + p["typologie"],
                                                color=MUTED, font_size="0.72rem",
                                                white_space="normal", line_height="1.5",
                                            ),
                                            spacing="2", align="start",
                                        ),
                                        spacing="1", align="start", width="100%",
                                        padding="0.4rem 0.75rem 0.6rem 2rem",
                                        background="rgba(99,102,241,0.05)",
                                    ),
                                ),
                                spacing="0", width="100%",
                                border_bottom=f"1px solid {BORDER}",
                            ),
                        ),
                        spacing="0", width="100%",
                        max_height="55vh", overflow_y="auto",
                    ),
                    rx.text("Aucune proposition.", color=MUTED,
                            font_size="0.82rem", text_align="center",
                            padding_y="1rem"),
                ),

                # Footer
                rx.hstack(
                    rx.button(
                        "Fermer",
                        on_click=SuiviDocState.close_auto_match,
                        background="transparent", color=MUTED,
                        border=f"1px solid {BORDER}", border_radius="8px",
                        cursor="pointer",
                    ),
                    rx.cond(
                        SuiviDocState.auto_match_proposals.length() > 0,
                        rx.button(
                            rx.icon("check-check", size=15),
                            "Tout confirmer",
                            on_click=SuiviDocState.confirm_all_matches,
                            background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                            color="white", border_radius="8px", cursor="pointer",
                            font_weight="700", spacing="2",
                        ),
                    ),
                    spacing="3", justify="end", width="100%",
                    margin_top="0.75rem",
                ),

                background="#111524", border=f"1px solid {BORDER}",
                border_radius="16px", padding="1.5rem",
                max_width="600px", overflow_y="auto", max_height="90vh",
            ),
            open=SuiviDocState.show_auto_match,
        ),

        spacing="4", width="100%",
    )


# ── Contenu onglet (réutilisable dans Documents) ──────────────────────────────

def suivi_tab_content() -> rx.Component:
    """Contenu de l'onglet Suivi, sans page_layout — à intégrer dans documents_page."""
    return rx.vstack(
        # Sous-onglets
        rx.hstack(
            _tab_btn("Amélioration Desk",    "notebook-pen",  "amelioration"),
            _tab_btn("Suivi des Procédures", "list-checks",   "procedures"),
            spacing="2",
        ),

        # Contenu sous-onglet
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
        _proc_form_modal(),
        _doc_picker_modal(),

        spacing="5", width="100%",
    )


# ── Page principale ────────────────────────────────────────────────────────────

def suivi_doc_page() -> rx.Component:
    return page_layout(
        rx.vstack(
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
            suivi_tab_content(),
            spacing="5", width="100%",
            on_mount=SuiviDocState.load,
        ),
        title="Suivi de Doc",
    )
