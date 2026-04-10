import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.state.escalade import EscaladeState

TEXT = "#e2e8f0"
MUTED = "#64748b"
CARD_BG = "#151728"
BORDER = "#1e2235"
PRIMARY = "#6366f1"


def _info_block(label: str, value, color: str = "") -> rx.Component:
    return rx.box(
        rx.text(label, color=MUTED, font_size="0.72rem", font_weight="600", margin_bottom="3px"),
        rx.text(
            rx.cond(value, value, "—"),
            color=color if color else TEXT,
            font_size="0.85rem",
            font_weight="500" if color else "400",
        ),
        background="#1e2035",
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
                        spacing="1",
                        align="start",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.icon_button(
                            rx.icon("x", size=16),
                            background="transparent",
                            color=MUTED,
                            cursor="pointer",
                            _hover={"color": TEXT},
                            size="2",
                        ),
                        on_click=EscaladeState.close_modal,
                    ),
                    width="100%",
                    align="center",
                ),
            ),
            rx.divider(border_color=BORDER, margin_y="0.8rem"),
            rx.grid(
                _info_block("Catégorie FRESH", e["categorie_fresh"]),
                _info_block("Traitement N1",   e["traitement_n1"],   "#22c55e"),
                _info_block("WP N1",           e["wp"]),
                _info_block("Interlocuteur",   e["interlocuteur"]),
                _info_block("Traitement N2/N3",e["traitement_n2n3"], "#f59e0b"),
                _info_block("WP N2",           e["wp_n2"]),
                columns="2",
                spacing="3",
                width="100%",
            ),
            rx.cond(
                e["conditions_escalade"] != "",
                rx.box(
                    rx.text("Conditions d'escalade", color=MUTED, font_size="0.75rem", font_weight="600", margin_bottom="4px"),
                    rx.text(e["conditions_escalade"], color=TEXT, font_size="0.85rem"),
                    background="#1a1a2a",
                    border=f"1px solid {BORDER}",
                    border_radius="8px",
                    padding="10px 14px",
                    margin_top="0.5rem",
                ),
            ),
            rx.cond(
                e["referents"] != "",
                rx.box(
                    rx.text("Référents", color=MUTED, font_size="0.75rem", font_weight="600", margin_bottom="4px"),
                    rx.text(e["referents"], color=TEXT, font_size="0.85rem"),
                    background="#1a1a2a",
                    border=f"1px solid {BORDER}",
                    border_radius="8px",
                    padding="10px 14px",
                    margin_top="0.5rem",
                ),
            ),
            background="#151728",
            border=f"1px solid {BORDER}",
            border_radius="16px",
            max_width="600px",
            width="90vw",
            padding="1.5rem",
        ),
        open=EscaladeState.show_modal,
    )


def entry_row(entry: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.badge(entry["perimetre"], color_scheme="indigo", variant="soft", radius="full"),
            padding="8px 12px",
        ),
        rx.table.cell(
            rx.text(entry["typologie"], color=TEXT, font_size="0.85rem"),
            padding="8px 12px",
        ),
        rx.table.cell(
            rx.text(entry["categorie_fresh"], color=MUTED, font_size="0.82rem"),
            padding="8px 12px",
        ),
        rx.table.cell(
            rx.text(entry["traitement_n1"], color="#86efac", font_size="0.82rem"),
            padding="8px 12px",
        ),
        rx.table.cell(
            rx.icon_button(
                rx.icon("eye", size=14),
                on_click=EscaladeState.open_entry(entry),
                background="rgba(99,102,241,0.1)",
                color=PRIMARY,
                border=f"1px solid rgba(99,102,241,0.3)",
                border_radius="6px",
                size="1",
                _hover={"background": "rgba(99,102,241,0.2)"},
                cursor="pointer",
            ),
            padding="8px 12px",
            text_align="center",
        ),
        _hover={"background": "rgba(255,255,255,0.02)"},
        cursor="pointer",
        on_click=EscaladeState.open_entry(entry),
    )


def escalade_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.box(
                rx.icon("search", size=16, color=MUTED, position="absolute", left="12px", top="50%", transform="translateY(-50%)"),
                rx.input(
                    placeholder="Rechercher dans la matrice...",
                    value=EscaladeState.search,
                    on_change=EscaladeState.set_search,
                    background="#1e2035",
                    border=f"1px solid {BORDER}",
                    color=TEXT,
                    border_radius="10px",
                    padding_left="36px",
                    padding_right="12px",
                    padding_y="9px",
                    width="100%",
                    _focus={"border_color": PRIMARY, "outline": "none"},
                    _placeholder={"color": MUTED},
                ),
                position="relative",
                flex="1",
            ),
            rx.cond(
                (EscaladeState.search != "") | (EscaladeState.selected_perimetres.length() > 0),
                rx.button(
                    rx.icon("x", size=14),
                    "Effacer",
                    on_click=EscaladeState.clear_filters,
                    background="transparent",
                    color=MUTED,
                    border=f"1px solid {BORDER}",
                    border_radius="8px",
                    padding="8px 12px",
                    font_size="0.8rem",
                    cursor="pointer",
                    spacing="1",
                    _hover={"color": TEXT},
                ),
            ),
            rx.text(
                EscaladeState.total.to_string() + " résultats",
                color=MUTED,
                font_size="0.82rem",
                white_space="nowrap",
            ),
            spacing="3",
            width="100%",
            align="center",
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
                            radius="full",
                            font_size="0.72rem",
                        ),
                    ),
                    wrap="wrap",
                    gap="6px",
                ),
                spacing="3",
                align="center",
                wrap="wrap",
            ),
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="10px",
            padding="0.7rem 1rem",
            width="100%",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Périmètre",    color=MUTED, font_size="0.75rem", padding="10px 12px"),
                        rx.table.column_header_cell("Typologie",    color=MUTED, font_size="0.75rem", padding="10px 12px"),
                        rx.table.column_header_cell("Catégorie",    color=MUTED, font_size="0.75rem", padding="10px 12px"),
                        rx.table.column_header_cell("Traitement N1",color=MUTED, font_size="0.75rem", padding="10px 12px"),
                        rx.table.column_header_cell("",             padding="10px 12px"),
                    ),
                    background="#10121f",
                ),
                rx.table.body(rx.foreach(EscaladeState.entries, entry_row)),
                width="100%",
            ),
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="14px",
            overflow="hidden",
            width="100%",
        ),
        rx.hstack(
            rx.icon_button(
                rx.icon("chevron-left", size=14),
                on_click=EscaladeState.go_page(EscaladeState.page - 1),
                disabled=EscaladeState.page <= 1,
                background="#1e2235",
                color=TEXT,
                border=f"1px solid {BORDER}",
                border_radius="8px",
                size="2",
            ),
            rx.text(
                "Page " + EscaladeState.page.to_string() + " / " + EscaladeState.total_pages.to_string(),
                color=MUTED,
                font_size="0.82rem",
            ),
            rx.icon_button(
                rx.icon("chevron-right", size=14),
                on_click=EscaladeState.go_page(EscaladeState.page + 1),
                disabled=EscaladeState.page >= EscaladeState.total_pages,
                background="#1e2235",
                color=TEXT,
                border=f"1px solid {BORDER}",
                border_radius="8px",
                size="2",
            ),
            spacing="3",
            align="center",
        ),
        entry_modal(),
        spacing="4",
        width="100%",
        on_mount=EscaladeState.load_data,
    )


def escalade_page() -> rx.Component:
    return page_layout(escalade_content(), "Matrice d'escalade N1")
