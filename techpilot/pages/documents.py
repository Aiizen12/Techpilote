import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.state.documents import DocumentsState, CATEGORIES, SOUS_CATEGORIES
from techpilot.state.models import DocumentItem, DocGroup, GabaritItem, GabaritColumn
from techpilot.state.suivi_doc import SuiviDocState
from techpilot.pages.suivi_doc import suivi_tab_content

TEXT = "#e2e8f0"
MUTED = "#64748b"
CARD_BG = "#0d1117"
BORDER = "rgba(255,255,255,0.07)"
PRIMARY = "#6366f1"


def doc_row(doc: DocumentItem) -> rx.Component:
    is_link = doc["type"] == "lien"
    return rx.hstack(
        rx.box(
            rx.cond(
                is_link,
                rx.icon("link-2", size=16, color="#a5b4fc"),
                rx.icon("file", size=16, color=MUTED),
            ),
            flex_shrink="0",
            width="2.25rem",
            height="2.25rem",
            background=rx.cond(is_link, "rgba(99,102,241,0.15)", "rgba(255,255,255,0.05)"),
            border_radius="8px",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
        rx.box(
            rx.cond(
                is_link,
                rx.link(
                    doc["nom_original"],
                    href=doc["url"],
                    color="#a5b4fc",
                    font_weight="600",
                    font_size="0.875rem",
                    target="_blank",
                    display="block",
                    white_space="nowrap",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    _hover={"text_decoration": "underline"},
                ),
                rx.text(
                    doc["nom_original"],
                    color=TEXT,
                    font_weight="600",
                    font_size="0.875rem",
                    white_space="nowrap",
                    overflow="hidden",
                    text_overflow="ellipsis",
                ),
            ),
            rx.cond(
                doc["description"] != "",
                rx.text(doc["description"], color=MUTED, font_size="0.75rem", white_space="nowrap", overflow="hidden", text_overflow="ellipsis"),
            ),
            rx.cond(
                is_link & (doc["url"] != ""),
                rx.text(doc["url"], color="#334155", font_size="0.7rem", white_space="nowrap", overflow="hidden", text_overflow="ellipsis"),
            ),
            flex="1",
            min_width="0",
        ),
        rx.spacer(),
        rx.cond(
            is_link,
            rx.badge("Lien", color_scheme="violet", variant="soft", radius="full", font_size="0.65rem"),
        ),
        rx.icon_button(
            rx.icon("trash-2", size=14),
            on_click=DocumentsState.delete_doc(doc["id"]),
            background="transparent",
            color=MUTED,
            border="none",
            border_radius="6px",
            size="1",
            cursor="pointer",
            _hover={"background": "rgba(239,68,68,0.15)", "color": "#ef4444"},
        ),
        spacing="3",
        align="center",
        width="100%",
        padding="0.75rem 1.25rem",
        border_bottom=f"1px solid {BORDER}",
        _hover={"background": "rgba(255,255,255,0.025)"},
        transition="background 0.1s",
    )


def group_section(group: DocGroup) -> rx.Component:
    return rx.vstack(
        rx.text(
            group["name"],
            color=MUTED,
            font_size="0.7rem",
            font_weight="700",
            text_transform="uppercase",
            letter_spacing="0.07em",
            padding_left="0.25rem",
        ),
        rx.box(
            rx.foreach(group["docs"], doc_row),
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="14px",
            overflow="hidden",
            width="100%",
        ),
        spacing="2",
        width="100%",
        align="start",
    )


def internal_sources_section() -> rx.Component:
    return rx.vstack(
        rx.text("Données internes", color=MUTED, font_size="0.7rem", font_weight="700", text_transform="uppercase", letter_spacing="0.07em", padding_left="0.25rem"),
        rx.box(
            rx.hstack(
                rx.box(
                    rx.icon("git-branch", size=18, color="#a5b4fc"),
                    flex_shrink="0", width="2.25rem", height="2.25rem",
                    background="rgba(99,102,241,0.15)", border_radius="8px",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.vstack(
                    rx.text("Matrice d'escalade", color=TEXT, font_weight="600", font_size="0.875rem"),
                    rx.text(DocumentsState.escalade_count.to_string() + " règles de routage N1/N2/N3", color=MUTED, font_size="0.75rem"),
                    spacing="0", align="start",
                ),
                rx.spacer(),
                rx.badge("Interne", color_scheme="indigo", variant="soft", font_size="0.72rem"),
                rx.icon("external-link", size=14, color=MUTED),
                spacing="3", align="center", width="100%",
                padding="0.875rem 1.25rem",
                border_bottom=f"1px solid {BORDER}",
                cursor="pointer",
                _hover={"background": "rgba(255,255,255,0.03)"},
                on_click=rx.redirect("/escalade"),
            ),
            rx.hstack(
                rx.box(
                    rx.icon("calendar", size=18, color="#7dd3fc"),
                    flex_shrink="0", width="2.25rem", height="2.25rem",
                    background="rgba(14,165,233,0.15)", border_radius="8px",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.vstack(
                    rx.text("Planning", color=TEXT, font_weight="600", font_size="0.875rem"),
                    rx.text("Planning hebdomadaire de l'équipe", color=MUTED, font_size="0.75rem"),
                    spacing="0", align="start",
                ),
                rx.spacer(),
                rx.badge("Interne", color_scheme="cyan", variant="soft", font_size="0.72rem"),
                rx.icon("external-link", size=14, color=MUTED),
                spacing="3", align="center", width="100%",
                padding="0.875rem 1.25rem",
                cursor="pointer",
                _hover={"background": "rgba(255,255,255,0.03)"},
                on_click=rx.redirect("/planning"),
            ),
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="14px",
            overflow="hidden",
            width="100%",
        ),
        spacing="2", width="100%", align="start",
    )


def _gabarit_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.box(
                rx.hstack(
                    rx.box(
                        rx.cond(
                            DocumentsState.editing_gabarit_id != "",
                            rx.icon("pencil", size=18, color="white"),
                            rx.icon("file-plus", size=18, color="white"),
                        ),
                        background="rgba(255,255,255,0.2)", border_radius="10px", padding="8px",
                        display="flex", align_items="center", justify_content="center",
                    ),
                    rx.vstack(
                        rx.cond(
                            DocumentsState.editing_gabarit_id != "",
                            rx.text("Modifier le gabarit", color="white", font_size="1rem", font_weight="700"),
                            rx.text("Nouveau gabarit", color="white", font_size="1rem", font_weight="700"),
                        ),
                        rx.text("Titre · Catégorie · Contenu", color="rgba(255,255,255,0.65)", font_size="0.72rem"),
                        spacing="0", align="start",
                    ),
                    spacing="3", align="center",
                ),
                background="linear-gradient(135deg, #1e1b4b, #4338ca)",
                border_radius="12px 12px 0 0",
                padding="1.25rem 1.5rem",
                margin="-24px -24px 0 -24px",
            ),
            rx.vstack(
                # Titre
                rx.vstack(
                    rx.hstack(
                        rx.text("TITRE", color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.07em"),
                        rx.text("*", color="#ef4444", font_size="0.75rem"),
                        spacing="1",
                    ),
                    rx.input(
                        placeholder="Ex : Mail – Confirmation prise en charge",
                        value=DocumentsState.gabarit_form["titre"],
                        on_change=lambda v: DocumentsState.set_gabarit_field("titre", v),
                        background="#1e2035", color=TEXT,
                        border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px", width="100%",
                    ),
                    spacing="1", align="start", width="100%",
                ),
                # Catégorie — texte libre + chips rapides
                rx.vstack(
                    rx.text("CATÉGORIE", color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.07em"),
                    rx.input(
                        placeholder="Ticket, Mail, Note, Escalade ou nouvelle catégorie…",
                        value=DocumentsState.gabarit_form["categorie"],
                        on_change=lambda v: DocumentsState.set_gabarit_field("categorie", v),
                        background="#1e2035", color=TEXT,
                        border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px", width="100%",
                    ),
                    rx.flex(
                        rx.foreach(DocumentsState.gabarit_categories, _cat_chip),
                        flex_wrap="wrap",
                        gap="2",
                    ),
                    spacing="2", align="start", width="100%",
                ),
                # Contenu
                rx.vstack(
                    rx.hstack(
                        rx.text("CONTENU", color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.07em"),
                        rx.text("*", color="#ef4444", font_size="0.75rem"),
                        spacing="1",
                    ),
                    rx.text_area(
                        placeholder="Coller ici le texte du gabarit…",
                        value=DocumentsState.gabarit_form["contenu"],
                        on_change=lambda v: DocumentsState.set_gabarit_field("contenu", v),
                        background="#1e2035", color=TEXT,
                        border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px", width="100%",
                        rows="10",
                        font_family="'Courier New', monospace",
                        font_size="0.8rem",
                    ),
                    spacing="1", align="start", width="100%",
                ),
                # Actions
                rx.hstack(
                    rx.button(
                        "Annuler",
                        on_click=DocumentsState.close_gabarit_form,
                        background="transparent", color=MUTED,
                        border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px", cursor="pointer",
                    ),
                    rx.button(
                        rx.icon("save", size=15),
                        rx.cond(
                            DocumentsState.editing_gabarit_id != "",
                            "Mettre à jour",
                            "Enregistrer",
                        ),
                        on_click=DocumentsState.save_gabarit,
                        background="linear-gradient(135deg, #1e1b4b, #4338ca)",
                        color="white", border_radius="8px", cursor="pointer",
                        font_weight="700", spacing="2",
                    ),
                    spacing="3", justify="end", width="100%",
                ),
                spacing="4", width="100%", padding_top="1.25rem",
            ),
            background="#151728",
            border=f"1px solid rgba(255,255,255,0.1)",
            border_radius="16px",
            padding="24px",
            max_width="540px",
            overflow="hidden",
        ),
        open=DocumentsState.show_gabarit_form,
    )


def gabarit_kanban_card(g: GabaritItem) -> rx.Component:
    return rx.box(
        rx.hstack(
            # Titre cliquable → ouvre l'édition
            rx.text(
                g["titre"],
                font_size="0.82rem",
                font_weight="500",
                color=TEXT,
                flex="1",
                min_width="0",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
                line_height="1.4",
                cursor="pointer",
                on_click=DocumentsState.open_edit_gabarit_form(
                    g["id"], g["titre"], g["categorie"], g["contenu"]
                ),
                _hover={"color": "#a5b4fc"},
            ),
            # × discret pour suppression
            rx.icon_button(
                rx.icon("x", size=11),
                on_click=DocumentsState.delete_gabarit(g["id"]),
                background="transparent",
                color="rgba(148,163,184,0.25)",
                border="none",
                size="1",
                cursor="pointer",
                flex_shrink="0",
                _hover={"color": "#ef4444", "background": "rgba(239,68,68,0.12)"},
            ),
            spacing="1",
            align="center",
            width="100%",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="8px",
        padding="0.55rem 0.7rem",
        width="100%",
        transition="all 0.12s",
        _hover={"border_color": "rgba(99,102,241,0.45)", "background": "rgba(99,102,241,0.04)"},
    )


def _cat_chip(cat: str) -> rx.Component:
    return rx.button(
        cat,
        on_click=DocumentsState.set_gabarit_field("categorie", cat),
        background=rx.cond(
            DocumentsState.gabarit_form["categorie"] == cat,
            "rgba(99,102,241,0.3)", "rgba(255,255,255,0.05)",
        ),
        color=rx.cond(
            DocumentsState.gabarit_form["categorie"] == cat, "#a5b4fc", MUTED,
        ),
        border=rx.cond(
            DocumentsState.gabarit_form["categorie"] == cat,
            "1px solid rgba(99,102,241,0.5)", f"1px solid {BORDER}",
        ),
        border_radius="999px",
        font_size="0.72rem",
        font_weight="600",
        padding="0.2rem 0.65rem",
        cursor="pointer",
        _hover={"background": "rgba(99,102,241,0.2)", "color": "#a5b4fc"},
    )


def add_category_column() -> rx.Component:
    return rx.box(
        rx.cond(
            DocumentsState.show_add_cat_input,
            rx.vstack(
                rx.text("Nouvelle catégorie", color=MUTED, font_size="0.75rem", font_weight="700",
                        text_transform="uppercase", letter_spacing="0.05em"),
                rx.input(
                    placeholder="Nom de la catégorie…",
                    value=DocumentsState.new_cat_name,
                    on_change=DocumentsState.set_new_cat_name,
                    background="#1e2035", color=TEXT,
                    border="1px solid rgba(99,102,241,0.4)", border_radius="8px",
                    font_size="0.82rem", width="100%",
                ),
                rx.hstack(
                    rx.button(
                        "Annuler",
                        on_click=DocumentsState.toggle_add_cat,
                        background="transparent", color=MUTED,
                        border=f"1px solid {BORDER}", border_radius="7px",
                        font_size="0.75rem", cursor="pointer",
                    ),
                    rx.button(
                        rx.icon("plus", size=13), "Créer",
                        on_click=DocumentsState.add_category,
                        background="rgba(99,102,241,0.2)", color="#a5b4fc",
                        border="1px solid rgba(99,102,241,0.4)", border_radius="7px",
                        font_size="0.75rem", font_weight="700", spacing="1", cursor="pointer",
                        _hover={"background": "rgba(99,102,241,0.35)"},
                    ),
                    spacing="2", justify="end", width="100%",
                ),
                spacing="3",
                background="rgba(255,255,255,0.015)",
                border=f"1px solid rgba(99,102,241,0.3)",
                border_radius="12px",
                padding="0.875rem",
                width="190px",
                min_width="190px",
            ),
            rx.box(
                rx.vstack(
                    rx.icon("plus", size=20, color=MUTED),
                    rx.text("Nouvelle catégorie", color=MUTED, font_size="0.78rem", font_weight="600"),
                    spacing="2", align="center",
                ),
                on_click=DocumentsState.toggle_add_cat,
                background="transparent",
                border=f"2px dashed {BORDER}",
                border_radius="12px",
                padding="1.5rem 1rem",
                width="160px",
                min_width="160px",
                display="flex",
                align_items="center",
                justify_content="center",
                cursor="pointer",
                transition="all 0.15s",
                _hover={"border_color": "rgba(99,102,241,0.4)", "color": "#a5b4fc"},
            ),
        ),
        flex_shrink="0",
    )


def gabarit_kanban_column(col: GabaritColumn) -> rx.Component:
    return rx.vstack(
        # En-tête : mode normal ou mode édition
        rx.cond(
            DocumentsState.editing_col_cat == col["category"],
            # Mode édition
            rx.hstack(
                rx.input(
                    value=DocumentsState.editing_col_new_name,
                    on_change=DocumentsState.set_edit_col_name,
                    background="#1e2035", color=TEXT,
                    border="1px solid rgba(99,102,241,0.5)",
                    border_radius="6px", font_size="0.82rem", font_weight="700",
                    flex="1", size="1",
                ),
                rx.icon_button(
                    rx.icon("check", size=12),
                    on_click=DocumentsState.save_col_rename,
                    background="rgba(34,197,94,0.12)", color="#22c55e",
                    border="1px solid rgba(34,197,94,0.3)",
                    size="1", border_radius="6px", cursor="pointer",
                ),
                rx.icon_button(
                    rx.icon("x", size=12),
                    on_click=DocumentsState.cancel_col_edit,
                    background="transparent", color=MUTED, border="none",
                    size="1", cursor="pointer",
                ),
                spacing="1", align="center", width="100%",
                padding_bottom="0.6rem", border_bottom=f"1px solid {BORDER}",
            ),
            # Mode normal
            rx.hstack(
                rx.text(col["category"], font_weight="700", font_size="0.82rem", color=TEXT),
                rx.box(
                    rx.text(col["items"].length().to_string(),
                            font_size="0.7rem", font_weight="700", color=MUTED),
                    background="rgba(255,255,255,0.06)",
                    border_radius="999px", padding="1px 8px",
                ),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("plus", size=13),
                    on_click=DocumentsState.open_gabarit_form_with_cat(col["category"]),
                    background="transparent", color=MUTED, border=f"1px solid {BORDER}",
                    size="1", border_radius="6px", cursor="pointer",
                    _hover={"background": "rgba(99,102,241,0.15)", "color": "#a5b4fc",
                            "border_color": "rgba(99,102,241,0.4)"},
                ),
                rx.icon_button(
                    rx.icon("pencil", size=12),
                    on_click=DocumentsState.start_edit_col(col["category"]),
                    background="transparent", color=MUTED, border="none",
                    size="1", cursor="pointer",
                    _hover={"color": "#a5b4fc", "background": "rgba(99,102,241,0.1)"},
                ),
                spacing="1", align="center", width="100%",
                padding_bottom="0.6rem", border_bottom=f"1px solid {BORDER}",
            ),
        ),
        rx.vstack(
            rx.foreach(col["items"], gabarit_kanban_card),
            spacing="2",
            width="100%",
        ),
        background="rgba(255,255,255,0.015)",
        border=f"1px solid {BORDER}",
        border_radius="12px",
        padding="0.875rem",
        spacing="3",
        width="0",
        flex="1",
        min_width="190px",
        align="start",
    )


def gabarits_tab_view() -> rx.Component:
    return rx.vstack(
        # Header avec bouton d'ajout
        rx.hstack(
            rx.vstack(
                rx.text("Gabarits", color=TEXT, font_weight="700", font_size="1rem"),
                rx.text("Modèles de tickets, mails et notes prêts à copier",
                        color=MUTED, font_size="0.78rem"),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.input(
                placeholder="Rechercher un gabarit…",
                value=DocumentsState.gabarit_search,
                on_change=DocumentsState.set_gabarit_search,
                style={
                    "background": CARD_BG, "color": TEXT,
                    "border": f"1px solid {BORDER}", "border_radius": "8px",
                    "padding": "5px 10px", "font_size": "0.8rem", "width": "200px",
                },
            ),
            rx.button(
                rx.icon("plus", size=15),
                "Nouveau gabarit",
                on_click=DocumentsState.open_gabarit_form,
                background="rgba(99,102,241,0.15)",
                color="#a5b4fc",
                border="1.5px solid rgba(99,102,241,0.35)",
                border_radius="10px",
                font_size="0.82rem",
                font_weight="600",
                padding="0.5rem 1.1rem",
                cursor="pointer",
                spacing="2",
                _hover={"background": "rgba(99,102,241,0.28)", "border_color": "rgba(99,102,241,0.6)"},
            ),
            width="100%",
            align="center",
            padding_bottom="0.75rem",
            border_bottom=f"1px solid {BORDER}",
        ),
        # Kanban board
        rx.hstack(
            rx.foreach(DocumentsState.filtered_gabarit_columns, gabarit_kanban_column),
            rx.cond(DocumentsState.gabarit_search == "", add_category_column()),
            spacing="3",
            align="start",
            width="100%",
            overflow_x="auto",
            padding_bottom="0.5rem",
        ),
        _gabarit_dialog(),
        spacing="4",
        width="100%",
    )


def _tab_btn(key: str, icon: str, label: str, extra_on_click=None) -> rx.Component:
    click = [DocumentsState.set_tab(key), extra_on_click] if extra_on_click else DocumentsState.set_tab(key)
    return rx.button(
        rx.icon(icon, size=14),
        label,
        on_click=click,
        background=rx.cond(DocumentsState.current_tab == key, "rgba(99,102,241,0.18)", "transparent"),
        color=rx.cond(DocumentsState.current_tab == key, "#a5b4fc", MUTED),
        border=rx.cond(DocumentsState.current_tab == key, "1px solid rgba(99,102,241,0.4)", f"1px solid {BORDER}"),
        border_radius="8px",
        font_size="0.8rem",
        font_weight="600",
        padding="0.35rem 0.875rem",
        cursor="pointer",
        spacing="2",
        _hover={"background": "rgba(99,102,241,0.1)", "color": "#a5b4fc"},
    )


def tab_bar() -> rx.Component:
    return rx.hstack(
        _tab_btn("documents", "folder-open", "Documents"),
        _tab_btn("gabarits", "file-text", "Gabarits"),
        _tab_btn("suivi", "book-open", "Suivi de Doc", SuiviDocState.load),
        spacing="2",
        padding_bottom="0.5rem",
        border_bottom=f"1px solid {BORDER}",
        width="100%",
    )


def documents_content() -> rx.Component:
    return rx.vstack(
        # Barre d'onglets
        tab_bar(),
        # Vue Gabarits
        rx.cond(
            DocumentsState.current_tab == "gabarits",
            gabarits_tab_view(),
        ),
        # Vue Suivi de Doc
        rx.cond(
            DocumentsState.current_tab == "suivi",
            suivi_tab_content(),
        ),
        # Vue Documents
        rx.cond(
            DocumentsState.current_tab == "documents",
            rx.vstack(
        # Header
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.icon("folder-open", size=22, color="#7dd3fc"),
                    rx.heading("Documents partagés", size="5", color=TEXT, font_weight="800"),
                    spacing="2", align="center",
                ),
                rx.text(
                    DocumentsState.total_count.to_string() + " document(s) disponible(s)",
                    color=MUTED, font_size="0.875rem",
                ),
                spacing="1", align="start",
            ),
            rx.spacer(),
            rx.input(
                placeholder="Rechercher un document…",
                value=DocumentsState.doc_search,
                on_change=DocumentsState.set_doc_search,
                style={
                    "background": CARD_BG, "color": TEXT,
                    "border": f"1px solid {BORDER}", "border_radius": "8px",
                    "padding": "6px 12px", "font_size": "0.82rem", "width": "220px",
                },
            ),
            rx.button(
                rx.icon("link-2", size=16),
                "Ajouter un lien",
                on_click=DocumentsState.open_link_form,
                background="rgba(99,102,241,0.15)",
                color="#a5b4fc",
                border="1.5px solid rgba(99,102,241,0.3)",
                border_radius="10px",
                font_size="0.875rem",
                font_weight="600",
                padding="0.6rem 1.25rem",
                cursor="pointer",
                spacing="2",
                _hover={"background": "rgba(99,102,241,0.25)", "border_color": "rgba(99,102,241,0.5)"},
            ),
            width="100%", align="center",
        ),
        # Filtres catégorie (pills)
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text("Catégorie", color=MUTED, font_size="0.72rem", font_weight="700", text_transform="uppercase", letter_spacing="0.05em"),
                    *[
                        rx.button(
                            cat or "Tous",
                            on_click=DocumentsState.set_cat(cat),
                            background=rx.cond(DocumentsState.filter_cat == cat, "#2563eb", "rgba(255,255,255,0.05)"),
                            color=rx.cond(DocumentsState.filter_cat == cat, "white", MUTED),
                            border="none",
                            border_radius="999px",
                            font_size="0.8rem",
                            font_weight="600",
                            padding="0.3rem 0.875rem",
                            cursor="pointer",
                            _hover={"background": rx.cond(DocumentsState.filter_cat == cat, "#1d4ed8", "rgba(255,255,255,0.1)")},
                        )
                        for cat in ["", *CATEGORIES]
                    ],
                    spacing="2",
                    align="center",
                    wrap="wrap",
                ),
                rx.cond(
                    DocumentsState.filter_cat == "Procédures",
                    rx.hstack(
                        rx.text("Dossier", color="#334155", font_size="0.7rem", font_weight="700", text_transform="uppercase", letter_spacing="0.05em"),
                        *[
                            rx.button(
                                sc or "Tous",
                                on_click=DocumentsState.set_sous_cat(sc),
                                background=rx.cond(DocumentsState.filter_sous_cat == sc, "rgba(99,102,241,0.8)", "rgba(255,255,255,0.04)"),
                                color=rx.cond(DocumentsState.filter_sous_cat == sc, "white", MUTED),
                                border="none",
                                border_radius="999px",
                                font_size="0.75rem",
                                font_weight="600",
                                padding="0.2rem 0.7rem",
                                cursor="pointer",
                                white_space="nowrap",
                                _hover={"background": rx.cond(DocumentsState.filter_sous_cat == sc, "rgba(99,102,241,0.9)", "rgba(255,255,255,0.08)")},
                            )
                            for sc in ["", *SOUS_CATEGORIES]
                        ],
                        spacing="2",
                        align="center",
                        wrap="wrap",
                        padding_top="0.5rem",
                        border_top=f"1px solid {BORDER}",
                    ),
                ),
                spacing="3", align="start",
            ),
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="12px",
            padding="0.75rem 1rem",
            width="100%",
        ),
        # Données internes (seulement sans filtre catégorie)
        rx.cond(
            DocumentsState.filter_cat == "",
            internal_sources_section(),
        ),
        # Documents groupés
        rx.cond(
            DocumentsState.doc_groups.length() == 0,
            rx.box(
                rx.vstack(
                    rx.icon("folder-open", size=48, color=MUTED),
                    rx.text("Aucun document disponible", color=MUTED, font_size="0.875rem"),
                    spacing="3", align="center",
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="14px",
                padding="5rem",
                display="flex",
                justify_content="center",
                width="100%",
            ),
            rx.vstack(
                rx.foreach(DocumentsState.doc_groups, group_section),
                spacing="4",
                width="100%",
            ),
        ),
        # Dialog ajout lien
        rx.dialog.root(
            rx.dialog.content(

                # Header gradient
                rx.box(
                    rx.hstack(
                        rx.box(
                            rx.icon("link-2", size=18, color="white"),
                            background="rgba(255,255,255,0.2)",
                            border_radius="10px",
                            padding="8px",
                            display="flex", align_items="center", justify_content="center",
                        ),
                        rx.vstack(
                            rx.text("Ajouter un lien", color="white", font_size="1rem", font_weight="700"),
                            rx.text("Référencer une ressource externe",
                                    color="rgba(255,255,255,0.7)", font_size="0.72rem"),
                            spacing="0", align="start",
                        ),
                        spacing="3", align="center",
                    ),
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    border_radius="12px 12px 0 0",
                    padding="1.25rem 1.5rem",
                    margin="-24px -24px 0 -24px",
                ),

                rx.vstack(
                    rx.vstack(
                        rx.hstack(
                            rx.text("NOM", color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.07em"),
                            rx.text("*", color="#ef4444", font_size="0.75rem"),
                            spacing="1",
                        ),
                        rx.input(
                            placeholder="Nom du document ou lien…",
                            value=DocumentsState.link_form["nom"],
                            on_change=lambda v: DocumentsState.set_link_field("nom", v),
                            background="#1e2035", color=TEXT,
                            border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px", width="100%",
                        ),
                        spacing="1", align="start", width="100%",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.text("URL", color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.07em"),
                            rx.text("*", color="#ef4444", font_size="0.75rem"),
                            spacing="1",
                        ),
                        rx.input(
                            placeholder="https://…",
                            value=DocumentsState.link_form["url"],
                            on_change=lambda v: DocumentsState.set_link_field("url", v),
                            background="#1e2035", color=TEXT,
                            border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px", width="100%",
                        ),
                        spacing="1", align="start", width="100%",
                    ),
                    rx.hstack(
                        rx.vstack(
                            rx.text("CATÉGORIE", color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.07em"),
                            rx.select(
                                CATEGORIES,
                                value=DocumentsState.link_form["categorie"],
                                on_change=lambda v: DocumentsState.set_link_field("categorie", v),
                                background="#1e2035", color=TEXT,
                                border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px",
                            ),
                            spacing="1", align="start", flex="1",
                        ),
                        rx.vstack(
                            rx.text("DOSSIER", color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.07em"),
                            rx.select(
                                SOUS_CATEGORIES,
                                placeholder="Optionnel",
                                value=DocumentsState.link_form["sous_categorie"],
                                on_change=lambda v: DocumentsState.set_link_field("sous_categorie", v),
                                background="#1e2035", color=TEXT,
                                border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px",
                            ),
                            spacing="1", align="start", flex="1",
                        ),
                        spacing="3", width="100%",
                    ),
                    rx.vstack(
                        rx.text("DESCRIPTION", color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.07em"),
                        rx.text_area(
                            placeholder="Description optionnelle…",
                            value=DocumentsState.link_form["description"],
                            on_change=lambda v: DocumentsState.set_link_field("description", v),
                            background="#1e2035", color=TEXT,
                            border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px", width="100%",
                            rows="2",
                        ),
                        spacing="1", align="start", width="100%",
                    ),
                    rx.hstack(
                        rx.button("Annuler", on_click=DocumentsState.close_link_form,
                                  background="transparent", color=MUTED,
                                  border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px", cursor="pointer"),
                        rx.button(
                            rx.icon("plus", size=15),
                            "Ajouter",
                            on_click=DocumentsState.create_link,
                            background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                            color="white", border_radius="8px", cursor="pointer",
                            font_weight="700", spacing="2",
                        ),
                        spacing="3", justify="end", width="100%",
                    ),
                    spacing="4", width="100%", padding_top="1.25rem",
                ),

                background="#151728",
                border=f"1px solid rgba(255,255,255,0.1)",
                border_radius="16px",
                padding="24px",
                max_width="480px",
                overflow="hidden",
            ),
            open=DocumentsState.show_link_form,
        ),
            spacing="5",
            width="100%",
            align="start",
        ),  # fin rx.vstack documents
        ),  # fin rx.cond documents
        spacing="5",
        width="100%",
        on_mount=[DocumentsState.load, SuiviDocState.load],
    )


def documents_page() -> rx.Component:
    return page_layout(documents_content(), "Documents")
