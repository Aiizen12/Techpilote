import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.state.escalade import EscaladeState
from techpilot.state.models import EscaladeEntry
from techpilot.state.auth import AuthState

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
CARD_BG = "#111524"
BORDER  = "#1c2138"
PRIMARY = "#6366f1"


# ── Tab button ────────────────────────────────────────────────────────────────

def _tab_btn(label: str, icon_name: str, val: str) -> rx.Component:
    is_active = EscaladeState.mode == val
    return rx.box(
        rx.hstack(
            rx.icon(icon_name, size=14, color=rx.cond(is_active, "white", MUTED)),
            rx.text(
                label,
                color=rx.cond(is_active, "white", MUTED),
                font_size="0.82rem",
                font_weight=rx.cond(is_active, "600", "400"),
            ),
            spacing="2",
            align="center",
        ),
        padding="7px 14px",
        border_radius="8px",
        background=rx.cond(is_active, PRIMARY, "transparent"),
        cursor="pointer",
        on_click=EscaladeState.set_mode(val),
        transition="all 0.15s",
        white_space="nowrap",
        _hover={"background": rx.cond(is_active, PRIMARY, "rgba(255,255,255,0.06)")},
    )


# ── Header banner ─────────────────────────────────────────────────────────────

def header_banner() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text("Matrice d'escalade", color=TEXT, font_size="1.6rem", font_weight="800"),
                rx.text(
                    EscaladeState.total_count.to_string() + " procédures de routage N1 → N2/N3",
                    color="rgba(241,245,249,0.6)",
                    font_size="0.875rem",
                ),
                spacing="1",
                align="start",
                flex="1",
            ),
            rx.button(
                rx.icon("download", size=15),
                "Exporter CSV",
                on_click=EscaladeState.export_csv,
                background="rgba(99,102,241,0.15)",
                color=PRIMARY,
                border=f"1px solid rgba(99,102,241,0.35)",
                border_radius="8px",
                padding="8px 16px",
                font_size="0.82rem",
                font_weight="600",
                cursor="pointer",
                spacing="2",
                _hover={"background": "rgba(99,102,241,0.28)"},
            ),
            align="center",
            width="100%",
        ),
        background="linear-gradient(135deg, rgba(99,102,241,0.28) 0%, rgba(139,92,246,0.18) 50%, transparent 100%)",
        border=f"1px solid rgba(99,102,241,0.3)",
        border_radius="16px",
        padding="1.5rem 2rem",
        width="100%",
    )


# ── Mode tabs ─────────────────────────────────────────────────────────────────

def mode_tabs() -> rx.Component:
    return rx.box(
        rx.hstack(
            _tab_btn("Recherche",            "search",     "recherche"),
            _tab_btn("Assistant guidé",      "sparkles",   "assistant"),
            _tab_btn("Arbre",                "git-branch", "arbre"),
            _tab_btn("Par interlocuteur N2", "users",      "interlocuteur"),
            _tab_btn("Recherche libre",      "filter",     "libre"),
            spacing="1",
            wrap="wrap",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="12px",
        padding="5px",
        width="100%",
    )


# ── Modale détail ─────────────────────────────────────────────────────────────

def _info_block(label: str, value, color: str = "") -> rx.Component:
    return rx.box(
        rx.text(label, color=MUTED, font_size="0.72rem", font_weight="600", margin_bottom="3px"),
        rx.text(
            rx.cond(value, value, "—"),
            color=color if color else TEXT,
            font_size="0.85rem",
            font_weight="500" if color else "400",
        ),
        background="#1c2138",
        border_radius="8px",
        padding="8px 12px",
    )


def entry_modal() -> rx.Component:
    e = EscaladeState.selected_entry
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.vstack(
                        rx.text(e["perimetre"], color=TEXT, font_weight="700", font_size="1rem"),
                        rx.text(e["typologie"], color=MUTED, font_size="0.85rem"),
                        spacing="1", align="start",
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("star", size=16),
                        on_click=EscaladeState.toggle_favori,
                        background=rx.cond(EscaladeState.is_selected_favori, "rgba(245,158,11,0.15)", "rgba(255,255,255,0.07)"),
                        color=rx.cond(EscaladeState.is_selected_favori, "#fcd34d", MUTED),
                        border="none", border_radius="8px", cursor="pointer", size="2",
                        _hover={"background": "rgba(245,158,11,0.1)", "color": "#fcd34d"},
                    ),
                    rx.dialog.close(
                        rx.icon_button(
                            rx.icon("x", size=16),
                            background="rgba(255,255,255,0.07)", color=MUTED,
                            border="none", cursor="pointer", size="2",
                            _hover={"background": "rgba(239,68,68,0.15)", "color": "#f87171"},
                        ),
                        on_click=EscaladeState.close_modal,
                    ),
                    width="100%", align="center", spacing="2",
                ),
            ),
            rx.divider(border_color=BORDER, margin_y="0.8rem"),
            rx.box(
                rx.text("Catégorie FRESH", color=MUTED, font_size="0.72rem", font_weight="600", margin_bottom="3px"),
                rx.hstack(
                    rx.text(rx.cond(e["categorie_fresh"], e["categorie_fresh"], "—"), color=TEXT, font_size="0.85rem", flex="1"),
                    rx.button(
                        rx.icon("copy", size=11), "Copier",
                        on_click=EscaladeState.copy_fresh_cat,
                        background="rgba(255,255,255,0.07)", color=MUTED,
                        border="none", border_radius="6px",
                        font_size="0.7rem", font_weight="600", padding="2px 8px",
                        cursor="pointer", spacing="1",
                        _hover={"background": "rgba(16,185,129,0.2)", "color": "#6ee7b7"},
                    ),
                    align="center", spacing="2",
                ),
                background="#1c2138", border_radius="8px", padding="8px 12px", margin_bottom="0.75rem",
            ),
            rx.grid(
                _info_block("Traitement N1",    e["traitement_n1"],    "#22c55e"),
                _info_block("WP N1",            e["wp"]),
                _info_block("Interlocuteur",    e["interlocuteur"]),
                _info_block("Traitement N2/N3", e["traitement_n2n3"],  "#f59e0b"),
                _info_block("WP N2",            e["wp_n2"]),
                columns="2", spacing="3", width="100%",
            ),
            rx.cond(
                e["conditions_escalade"] != "",
                rx.box(
                    rx.text("Conditions d'escalade", color=MUTED, font_size="0.75rem", font_weight="600", margin_bottom="4px"),
                    rx.text(e["conditions_escalade"], color=TEXT, font_size="0.85rem"),
                    background="#1a1a2a", border=f"1px solid {BORDER}",
                    border_radius="8px", padding="10px 14px", margin_top="0.5rem",
                ),
            ),
            rx.cond(
                e["referents"] != "",
                rx.box(
                    rx.text("Référents", color=MUTED, font_size="0.75rem", font_weight="600", margin_bottom="4px"),
                    rx.text(e["referents"], color=TEXT, font_size="0.85rem"),
                    background="#1a1a2a", border=f"1px solid {BORDER}",
                    border_radius="8px", padding="10px 14px", margin_top="0.5rem",
                ),
            ),

            # ── Procédure N1 ──────────────────────────────────────────────
            rx.box(
                # En-tête avec bouton édition
                rx.hstack(
                    rx.box(
                        rx.icon("clipboard-list", size=13, color="#22c55e"),
                        background="rgba(34,197,94,0.12)", border_radius="6px",
                        padding="4px", display="flex",
                        align_items="center", justify_content="center",
                    ),
                    rx.text("Procédure N1", color="#22c55e", font_size="0.8rem", font_weight="700"),
                    rx.spacer(),
                    rx.cond(
                        AuthState.can_edit_procedure,
                        rx.cond(
                            EscaladeState.editing_procedure,
                            # Boutons save / annuler
                            rx.hstack(
                                rx.button(
                                    rx.icon("check", size=12), "Sauvegarder",
                                    on_click=EscaladeState.save_procedure,
                                    size="1",
                                    style={
                                        "background": "rgba(34,197,94,0.15)",
                                        "color": "#22c55e",
                                        "border": "1px solid rgba(34,197,94,0.3)",
                                        "border_radius": "6px",
                                        "cursor": "pointer",
                                        "font_size": "0.72rem",
                                        "padding": "3px 8px",
                                    },
                                ),
                                rx.button(
                                    rx.icon("x", size=12), "Annuler",
                                    on_click=EscaladeState.cancel_edit_procedure,
                                    size="1",
                                    style={
                                        "background": "rgba(148,163,184,0.1)",
                                        "color": MUTED,
                                        "border": f"1px solid {BORDER}",
                                        "border_radius": "6px",
                                        "cursor": "pointer",
                                        "font_size": "0.72rem",
                                        "padding": "3px 8px",
                                    },
                                ),
                                spacing="1",
                            ),
                            # Bouton crayon (lecture)
                            rx.button(
                                rx.icon("pencil", size=12),
                                rx.cond(
                                    EscaladeState.has_procedure,
                                    "Modifier",
                                    "Ajouter",
                                ),
                                on_click=EscaladeState.start_edit_procedure,
                                size="1",
                                style={
                                    "background": "rgba(99,102,241,0.12)",
                                    "color": "#6366f1",
                                    "border": "1px solid rgba(99,102,241,0.25)",
                                    "border_radius": "6px",
                                    "cursor": "pointer",
                                    "font_size": "0.72rem",
                                    "padding": "3px 8px",
                                },
                            ),
                        ),
                    ),
                    align="center", width="100%", margin_bottom="0.65rem",
                ),
                # Mode édition : textarea
                rx.cond(
                    EscaladeState.editing_procedure,
                    rx.vstack(
                        rx.text(
                            "Une étape par ligne",
                            color=MUTED, font_size="0.7rem", margin_bottom="4px",
                        ),
                        rx.text_area(
                            value=EscaladeState.edit_steps_text,
                            on_change=EscaladeState.set_edit_steps_text,
                            placeholder="Étape 1\nÉtape 2\n...",
                            rows="10",
                            style={
                                "width": "100%",
                                "background": "#0d1117",
                                "color": TEXT,
                                "border": "1px solid rgba(99,102,241,0.35)",
                                "border_radius": "8px",
                                "padding": "10px 12px",
                                "font_size": "0.82rem",
                                "line_height": "1.6",
                                "resize": "vertical",
                                "font_family": "inherit",
                            },
                        ),
                        width="100%", spacing="1",
                    ),
                    # Mode lecture : liste des étapes (ou vide)
                    rx.cond(
                        EscaladeState.has_procedure,
                        rx.vstack(
                            rx.foreach(
                                EscaladeState.selected_entry.procedure_n1,
                                lambda step: rx.hstack(
                                    rx.box(
                                        rx.icon("circle-check", size=13, color="#22c55e"),
                                        min_width="18px", flex_shrink="0", padding_top="2px",
                                    ),
                                    rx.text(
                                        step,
                                        color=TEXT,
                                        font_size="0.82rem",
                                        line_height="1.55",
                                    ),
                                    spacing="2", align="start", width="100%",
                                ),
                            ),
                            spacing="2", width="100%",
                        ),
                        # Pas de procédure + pas en édition → message vide (visible seulement manager/perm)
                        rx.cond(
                            AuthState.can_edit_procedure,
                            rx.text(
                                "Aucune procédure N1 pour cette fiche. Cliquez sur « Ajouter » pour en créer une.",
                                color=MUTED, font_size="0.78rem", font_style="italic",
                            ),
                        ),
                    ),
                ),
                background="rgba(34,197,94,0.04)",
                border="1px solid rgba(34,197,94,0.18)",
                border_left="3px solid #22c55e",
                border_radius="10px",
                padding="12px 14px",
                margin_top="0.75rem",
                # Masquer le bloc entier si pas de procédure ET pas de droit d'édition
                display=rx.cond(
                    EscaladeState.has_procedure | AuthState.can_edit_procedure,
                    "block",
                    "none",
                ),
            ),

            # ── Document lié ─────────────────────────────────────────────
            rx.cond(
                e["doc_url"] != "",
                rx.box(
                    rx.hstack(
                        rx.box(
                            rx.icon("file-text", size=13, color="#60a5fa"),
                            min_width="18px", flex_shrink="0",
                            display="flex", align_items="center", justify_content="center",
                        ),
                        rx.link(
                            e["doc_name"],
                            href=e["doc_url"],
                            is_external=True,
                            color="#60a5fa",
                            font_size="0.82rem",
                            font_weight="600",
                            text_decoration="underline",
                            _hover={"color": "#93c5fd"},
                        ),
                        spacing="2", align="center",
                    ),
                    background="rgba(59,130,246,0.05)",
                    border="1px solid rgba(59,130,246,0.2)",
                    border_left="3px solid #60a5fa",
                    border_radius="10px",
                    padding="10px 14px",
                    margin_top="0.75rem",
                ),
            ),

            # ── Notes Excel ───────────────────────────────────────────────
            rx.cond(
                e["notes"] != "",
                rx.box(
                    rx.text("Notes", color=MUTED, font_size="0.72rem", font_weight="600", margin_bottom="4px"),
                    rx.text(e["notes"], color="#94a3b8", font_size="0.78rem", line_height="1.5",
                            font_style="italic"),
                    background="rgba(148,163,184,0.05)", border=f"1px solid {BORDER}",
                    border_radius="8px", padding="10px 14px", margin_top="0.5rem",
                ),
            ),

            background="#111524", border=f"1px solid {BORDER}",
            border_radius="16px", max_width="600px", width="90vw", padding="1.5rem",
        ),
        open=EscaladeState.show_modal,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Mode RECHERCHE
# ══════════════════════════════════════════════════════════════════════════════

def entry_row(entry: EscaladeEntry, idx) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.badge(entry["perimetre"], color_scheme="indigo", variant="soft", radius="full"),
            padding="8px 12px",
        ),
        rx.table.cell(rx.text(entry["typologie"], color=TEXT, font_size="0.85rem"), padding="8px 12px"),
        rx.table.cell(rx.text(entry["categorie_fresh"], color=MUTED, font_size="0.82rem"), padding="8px 12px"),
        rx.table.cell(rx.text(entry["traitement_n1"], color="#86efac", font_size="0.82rem"), padding="8px 12px"),
        rx.table.cell(
            rx.icon(
                "eye", size=14, color=PRIMARY,
            ),
            padding="8px 12px", text_align="center",
        ),
        _hover={"background": "rgba(255,255,255,0.02)"},
        cursor="pointer",
        on_click=EscaladeState.open_entry_at(idx),
    )


def recherche_mode() -> rx.Component:
    return rx.vstack(
        rx.cond(
            EscaladeState.favoris.length() > 0,
            rx.box(
                rx.hstack(
                    rx.icon("star", size=13, color="#fcd34d"),
                    rx.text("Favoris", color="#fcd34d", font_size="0.7rem", font_weight="700", letter_spacing="0.08em"),
                    spacing="2", align="center",
                ),
                rx.flex(
                    rx.foreach(
                        EscaladeState.favoris,
                        lambda e: rx.badge(
                            e["perimetre"] + " — " + e["typologie"],
                            on_click=EscaladeState.open_favori(e["perimetre"], e["typologie"]),
                            cursor="pointer", color_scheme="amber", variant="soft",
                            radius="full", font_size="0.72rem",
                        ),
                    ),
                    wrap="wrap", gap="6px", margin_top="0.5rem",
                ),
                background=CARD_BG, border=f"1px solid rgba(245,158,11,0.25)",
                border_radius="12px", padding="0.75rem 1rem", width="100%",
            ),
        ),
        rx.hstack(
            rx.box(
                rx.icon("search", size=16, color=MUTED,
                        position="absolute", left="12px", top="50%", transform="translateY(-50%)"),
                rx.input(
                    placeholder="Rechercher (périmètre, typologie, traitement, interlocuteur…)",
                    value=EscaladeState.search,
                    on_change=EscaladeState.set_search,
                    background="#1c2138", border=f"1px solid {BORDER}",
                    style={"color": TEXT}, border_radius="10px",
                    padding_left="36px", padding_right="12px", padding_y="9px",
                    width="100%",
                    _focus={"border_color": PRIMARY, "outline": "none"},
                    _placeholder={"color": MUTED},
                ),
                position="relative", flex="1",
            ),
            rx.cond(
                (EscaladeState.search != "") | (EscaladeState.selected_perimetres.length() > 0),
                rx.button(
                    rx.icon("x", size=14), "Effacer",
                    on_click=EscaladeState.clear_filters,
                    background="transparent", color=MUTED,
                    border=f"1px solid {BORDER}", border_radius="8px",
                    padding="8px 12px", font_size="0.8rem",
                    cursor="pointer", spacing="1", _hover={"color": TEXT},
                ),
            ),
            rx.text(EscaladeState.total.to_string() + " résultats", color=MUTED, font_size="0.82rem", white_space="nowrap"),
            spacing="3", width="100%", align="center",
        ),
        rx.box(
            rx.hstack(
                rx.text("Périmètre :", color=MUTED, font_size="0.8rem", white_space="nowrap"),
                rx.flex(
                    rx.foreach(
                        EscaladeState.perimetres,
                        lambda p: rx.badge(
                            p,
                            on_click=EscaladeState.toggle_perimetre(p),
                            cursor="pointer",
                            color_scheme=rx.cond(EscaladeState.selected_perimetres.contains(p), "indigo", "gray"),
                            variant=rx.cond(EscaladeState.selected_perimetres.contains(p), "solid", "soft"),
                            radius="full", font_size="0.72rem",
                        ),
                    ),
                    wrap="wrap", gap="6px",
                ),
                spacing="3", align="center", wrap="wrap",
            ),
            background=CARD_BG, border=f"1px solid {BORDER}",
            border_radius="10px", padding="0.7rem 1rem", width="100%",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Périmètre",     color=MUTED, font_size="0.75rem", padding="10px 12px"),
                        rx.table.column_header_cell("Typologie",     color=MUTED, font_size="0.75rem", padding="10px 12px"),
                        rx.table.column_header_cell("Catégorie",     color=MUTED, font_size="0.75rem", padding="10px 12px"),
                        rx.table.column_header_cell("Traitement N1", color=MUTED, font_size="0.75rem", padding="10px 12px"),
                        rx.table.column_header_cell("",              padding="10px 12px"),
                    ),
                    background="#0d1021",
                ),
                rx.table.body(rx.foreach(EscaladeState.entries, lambda e, i: entry_row(e, i))),
                width="100%",
            ),
            background=CARD_BG, border=f"1px solid {BORDER}",
            border_radius="14px", overflow="hidden", width="100%",
        ),
        rx.hstack(
            rx.icon_button(
                rx.icon("chevron-left", size=14),
                on_click=EscaladeState.go_page(EscaladeState.page - 1),
                disabled=EscaladeState.page <= 1,
                background="#1c2138", color=TEXT, border=f"1px solid {BORDER}",
                border_radius="8px", size="2",
            ),
            rx.text(
                "Page " + EscaladeState.page.to_string() + " / " + EscaladeState.total_pages.to_string(),
                color=MUTED, font_size="0.82rem",
            ),
            rx.icon_button(
                rx.icon("chevron-right", size=14),
                on_click=EscaladeState.go_page(EscaladeState.page + 1),
                disabled=EscaladeState.page >= EscaladeState.total_pages,
                background="#1c2138", color=TEXT, border=f"1px solid {BORDER}",
                border_radius="8px", size="2",
            ),
            spacing="3", align="center",
        ),
        spacing="4", width="100%",
    )


# ══════════════════════════════════════════════════════════════════════════════
# Mode ASSISTANT GUIDÉ
# ══════════════════════════════════════════════════════════════════════════════

def perimetre_card(p: dict) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(p["name"], color=TEXT, font_size="0.88rem", font_weight="600", line_height="1.3"),
            rx.text(p["count_str"], font_size="0.75rem", color=p["color"]),
            spacing="2", align="start",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_top=p["border_accent"],
        border_radius="10px",
        padding="1rem",
        cursor="pointer",
        min_height="80px",
        on_click=EscaladeState.assistant_select_perimetre(p["name"]),
        transition="all 0.15s",
        _hover={"box_shadow": "0 4px 20px rgba(0,0,0,0.4)", "transform": "translateY(-2px)"},
    )


def assistant_entry_row(entry: EscaladeEntry, idx) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(entry["typologie"], color=TEXT, font_size="0.85rem"), padding="8px 12px"),
        rx.table.cell(rx.text(entry["categorie_fresh"], color=MUTED, font_size="0.82rem"), padding="8px 12px"),
        rx.table.cell(rx.text(entry["traitement_n1"], color="#86efac", font_size="0.82rem"), padding="8px 12px"),
        rx.table.cell(rx.text(entry["interlocuteur"], color=MUTED, font_size="0.82rem"), padding="8px 12px"),
        rx.table.cell(rx.icon("eye", size=14, color=PRIMARY), padding="8px 12px"),
        _hover={"background": "rgba(255,255,255,0.02)"},
        cursor="pointer",
        on_click=EscaladeState.open_assistant_entry_at(idx),
    )


def assistant_mode() -> rx.Component:
    return rx.cond(
        EscaladeState.assistant_step == 1,
        # Step 1 : cartes périmètre
        rx.vstack(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.badge("Étape 1 sur 2", color_scheme="violet", variant="soft", radius="full"),
                        justify="center", width="100%",
                    ),
                    rx.text(
                        "Quel est le périmètre concerné ?",
                        color=TEXT, font_size="1.2rem", font_weight="700", text_align="center",
                    ),
                    rx.text(
                        "Sélectionne le domaine applicatif du ticket",
                        color=MUTED, font_size="0.85rem", text_align="center",
                    ),
                    spacing="2", width="100%",
                ),
                background=CARD_BG, border=f"1px solid {BORDER}",
                border_radius="14px", padding="1.5rem", width="100%",
            ),
            rx.grid(
                rx.foreach(EscaladeState.perimetre_counts, perimetre_card),
                columns="5",
                spacing="3",
                width="100%",
            ),
            spacing="4", width="100%",
        ),
        # Step 2 : typologies du périmètre sélectionné
        rx.vstack(
            rx.hstack(
                rx.button(
                    rx.icon("arrow-left", size=14), "Retour",
                    on_click=EscaladeState.assistant_back,
                    background="transparent", color=MUTED,
                    border=f"1px solid {BORDER}", border_radius="8px",
                    padding="6px 12px", font_size="0.82rem",
                    cursor="pointer", spacing="2",
                ),
                rx.badge("Étape 2 sur 2", color_scheme="violet", variant="soft", radius="full"),
                rx.text("Périmètre :", color=MUTED, font_size="0.85rem"),
                rx.text(EscaladeState.assistant_perimetre, color=PRIMARY, font_size="0.85rem", font_weight="600"),
                spacing="3", align="center",
            ),
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Typologie",     color=MUTED, font_size="0.75rem", padding="10px 12px"),
                            rx.table.column_header_cell("Catégorie",     color=MUTED, font_size="0.75rem", padding="10px 12px"),
                            rx.table.column_header_cell("Traitement N1", color=MUTED, font_size="0.75rem", padding="10px 12px"),
                            rx.table.column_header_cell("Interlocuteur", color=MUTED, font_size="0.75rem", padding="10px 12px"),
                            rx.table.column_header_cell("",              padding="10px 12px"),
                        ),
                        background="#0d1021",
                    ),
                    rx.table.body(rx.foreach(EscaladeState.assistant_entries, lambda e, i: assistant_entry_row(e, i))),
                    width="100%",
                ),
                background=CARD_BG, border=f"1px solid {BORDER}",
                border_radius="14px", overflow="hidden", width="100%",
            ),
            spacing="4", width="100%",
        ),
    )


# ══════════════════════════════════════════════════════════════════════════════
# Mode ARBRE
# ══════════════════════════════════════════════════════════════════════════════

def arbre_entry_row(entry: EscaladeEntry, idx) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(entry["typologie"], color=TEXT, font_size="0.82rem", flex="1"),
            rx.text(entry["traitement_n1"], color="#86efac", font_size="0.75rem", max_width="260px"),
            rx.icon("eye", size=13, color=PRIMARY),
            spacing="3", align="center", width="100%",
        ),
        background="#0a0d1a",
        border_left=f"2px solid rgba(99,102,241,0.3)",
        padding="7px 12px",
        margin_left="16px",
        border_radius="6px",
        cursor="pointer",
        on_click=EscaladeState.open_arbre_entry_at(idx),
        _hover={"background": "rgba(99,102,241,0.08)"},
    )


def arbre_perimetre_item(p: dict) -> rx.Component:
    is_open = EscaladeState.arbre_expanded == p["name"]
    return rx.box(
        # Header cliquable pour ouvrir/fermer
        rx.hstack(
            rx.icon(
                rx.cond(is_open, "folder-open", "folder"),
                size=16, color=p["color"],
            ),
            rx.text(p["name"], color=TEXT, font_size="0.9rem", font_weight="600", flex="1"),
            rx.badge(p["count_str"], color_scheme="gray", variant="soft", radius="full", font_size="0.7rem"),
            rx.icon(rx.cond(is_open, "chevron-up", "chevron-down"), size=14, color=MUTED),
            spacing="3", align="center", padding="10px 14px", width="100%",
            cursor="pointer",
            on_click=EscaladeState.toggle_arbre_perimetre(p["name"]),
            _hover={"opacity": "0.9"},
        ),
        # Entrées — cliques isolés du header
        rx.cond(
            is_open,
            rx.vstack(
                rx.foreach(EscaladeState.arbre_entries, lambda e, i: arbre_entry_row(e, i)),
                spacing="1",
                padding="0 12px 12px 12px",
                width="100%",
            ),
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_left=p["border_accent"],
        border_radius="10px",
        overflow="hidden",
        width="100%",
        transition="all 0.15s",
    )


def arbre_mode() -> rx.Component:
    return rx.vstack(
        rx.foreach(EscaladeState.perimetre_counts, arbre_perimetre_item),
        spacing="2",
        width="100%",
    )


# ══════════════════════════════════════════════════════════════════════════════
# Mode PAR INTERLOCUTEUR N2
# ══════════════════════════════════════════════════════════════════════════════

def interlocuteur_entry_row(entry: EscaladeEntry, idx) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.badge(entry["perimetre"], color_scheme="indigo", variant="soft", radius="full", font_size="0.7rem"),
                    rx.text(entry["typologie"], color=TEXT, font_size="0.82rem"),
                    spacing="2", align="center",
                ),
                rx.text(
                    rx.cond(entry["traitement_n1"] != "", "N1 : " + entry["traitement_n1"], ""),
                    color="#86efac", font_size="0.75rem",
                ),
                spacing="1", align="start", flex="1",
            ),
            rx.icon("eye", size=13, color=PRIMARY),
            spacing="3", align="center", width="100%",
        ),
        background="#0a0d1a",
        border_left=f"2px solid rgba(99,102,241,0.3)",
        padding="8px 12px",
        margin_left="16px",
        border_radius="6px",
        cursor="pointer",
        on_click=EscaladeState.open_interlocuteur_entry_at(idx),
        _hover={"background": "rgba(99,102,241,0.08)"},
    )


def interlocuteur_row(item: dict) -> rx.Component:
    is_expanded = EscaladeState.expanded_interlocuteur == item["nom"]
    return rx.box(
        rx.hstack(
            rx.box(
                rx.icon("user", size=13, color=MUTED),
                background="rgba(148,163,184,0.1)",
                border_radius="6px",
                padding="5px",
                display="flex",
                align_items="center",
                justify_content="center",
                flex_shrink="0",
            ),
            rx.text(item["nom"], color=TEXT, font_size="0.875rem", font_weight="500", flex="1"),
            rx.badge(item["count_str"], color_scheme="indigo", variant="soft", radius="full", font_size="0.7rem"),
            rx.text(
                item["tags"], color=MUTED, font_size="0.72rem",
                max_width="360px", overflow="hidden",
                text_overflow="ellipsis", white_space="nowrap",
            ),
            rx.icon_button(
                rx.icon(rx.cond(is_expanded, "chevron-up", "chevron-down"), size=14),
                on_click=EscaladeState.toggle_expand_interlocuteur(item["nom"]),
                background="transparent", color=MUTED,
                border_radius="6px", size="1", cursor="pointer",
                _hover={"color": TEXT},
            ),
            spacing="3", align="center", padding="10px 14px", width="100%",
        ),
        rx.cond(
            is_expanded,
            rx.vstack(
                rx.foreach(EscaladeState.interlocuteur_entries, lambda e, i: interlocuteur_entry_row(e, i)),
                spacing="1",
                padding="0 12px 12px 12px",
                width="100%",
            ),
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="10px",
        overflow="hidden",
        width="100%",
        transition="all 0.15s",
        _hover={"border_color": "rgba(99,102,241,0.3)"},
    )


def interlocuteur_mode() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.box(
                rx.icon("search", size=14, color=MUTED,
                        position="absolute", left="10px", top="50%", transform="translateY(-50%)"),
                rx.input(
                    placeholder="Rechercher un interlocuteur N2…",
                    value=EscaladeState.interlocuteur_search,
                    on_change=EscaladeState.set_interlocuteur_search,
                    background="#1c2138", border=f"1px solid {BORDER}",
                    style={"color": TEXT}, border_radius="10px",
                    padding_left="32px", padding_y="9px",
                    width="100%",
                    _focus={"border_color": PRIMARY, "outline": "none"},
                    _placeholder={"color": MUTED},
                ),
                position="relative", flex="1",
            ),
            rx.badge(
                EscaladeState.filtered_interlocuteurs_list.length().to_string() + " interlocuteurs",
                color_scheme="indigo", variant="soft", radius="full",
            ),
            spacing="3", align="center", width="100%",
        ),
        rx.vstack(
            rx.foreach(EscaladeState.filtered_interlocuteurs_list, interlocuteur_row),
            spacing="2",
            width="100%",
        ),
        spacing="4", width="100%",
    )


# ══════════════════════════════════════════════════════════════════════════════
# Mode RECHERCHE LIBRE
# ══════════════════════════════════════════════════════════════════════════════

def libre_mode() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("filter", size=16, color=PRIMARY),
                    rx.text("Recherche plein texte", color=TEXT, font_size="0.9rem", font_weight="600"),
                    spacing="2", align="center",
                ),
                rx.text(
                    "Recherche dans tous les champs : périmètre, typologie, traitement N1/N2, interlocuteur, conditions…",
                    color=MUTED, font_size="0.8rem",
                ),
                rx.box(
                    rx.icon("search", size=16, color=MUTED,
                            position="absolute", left="12px", top="50%", transform="translateY(-50%)"),
                    rx.input(
                        placeholder="Saisissez votre recherche…",
                        value=EscaladeState.search,
                        on_change=EscaladeState.set_search,
                        background="#1c2138", border=f"1px solid {BORDER}",
                        color=TEXT, border_radius="10px",
                        padding_left="36px", padding_y="10px",
                        width="100%", font_size="0.9rem",
                        _focus={"border_color": PRIMARY, "outline": "none"},
                        _placeholder={"color": MUTED},
                    ),
                    position="relative", width="100%",
                ),
                spacing="3", width="100%",
            ),
            background=CARD_BG, border=f"1px solid {BORDER}",
            border_radius="14px", padding="1.5rem", width="100%",
        ),
        rx.cond(
            EscaladeState.search != "",
            rx.vstack(
                rx.text(EscaladeState.total.to_string() + " résultats", color=MUTED, font_size="0.82rem"),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Périmètre",     color=MUTED, font_size="0.75rem", padding="10px 12px"),
                                rx.table.column_header_cell("Typologie",     color=MUTED, font_size="0.75rem", padding="10px 12px"),
                                rx.table.column_header_cell("Traitement N1", color=MUTED, font_size="0.75rem", padding="10px 12px"),
                                rx.table.column_header_cell("",              padding="10px 12px"),
                            ),
                            background="#0d1021",
                        ),
                        rx.table.body(rx.foreach(EscaladeState.entries, lambda e, i: entry_row(e, i))),
                        width="100%",
                    ),
                    background=CARD_BG, border=f"1px solid {BORDER}",
                    border_radius="14px", overflow="hidden", width="100%",
                ),
                rx.hstack(
                    rx.icon_button(
                        rx.icon("chevron-left", size=14),
                        on_click=EscaladeState.go_page(EscaladeState.page - 1),
                        disabled=EscaladeState.page <= 1,
                        background="#1c2138", color=TEXT, border=f"1px solid {BORDER}",
                        border_radius="8px", size="2",
                    ),
                    rx.text(
                        "Page " + EscaladeState.page.to_string() + " / " + EscaladeState.total_pages.to_string(),
                        color=MUTED, font_size="0.82rem",
                    ),
                    rx.icon_button(
                        rx.icon("chevron-right", size=14),
                        on_click=EscaladeState.go_page(EscaladeState.page + 1),
                        disabled=EscaladeState.page >= EscaladeState.total_pages,
                        background="#1c2138", color=TEXT, border=f"1px solid {BORDER}",
                        border_radius="8px", size="2",
                    ),
                    spacing="3", align="center",
                ),
                spacing="3", width="100%",
            ),
        ),
        spacing="4", width="100%",
    )


# ══════════════════════════════════════════════════════════════════════════════
# Page
# ══════════════════════════════════════════════════════════════════════════════

def escalade_content() -> rx.Component:
    return rx.vstack(
        header_banner(),
        mode_tabs(),
        rx.match(
            EscaladeState.mode,
            ("recherche",     recherche_mode()),
            ("assistant",     assistant_mode()),
            ("arbre",         arbre_mode()),
            ("interlocuteur", interlocuteur_mode()),
            ("libre",         libre_mode()),
            rx.box(),
        ),
        entry_modal(),
        spacing="4",
        width="100%",
        on_mount=EscaladeState.load_data,
    )


def escalade_page() -> rx.Component:
    return page_layout(escalade_content(), "")
