import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.state.planning import PlanningState
from techpilot.state.models import PlanningEntry, AstreinteEntry

TEXT = "#e2e8f0"
MUTED = "#64748b"
CARD_BG = "#151728"
BORDER = "#1e2235"
PRIMARY = "#6366f1"

COLOR_CDS = "#1a3a2a"
COLOR_CDS_BORDER = "#22c55e"
COLOR_TT = "#0c2a38"
COLOR_TT_BORDER = "#06b6d4"
COLOR_ASTREINTE = "#3a1a1a"
COLOR_ASTREINTE_BORDER = "#ef4444"
COLOR_ABSENT = "#3a2e00"
COLOR_ABSENT_BORDER = "#eab308"
COLOR_REPOS = "#1a1a2a"
COLOR_REPOS_BORDER = "#334155"


def tech_row(item: PlanningEntry) -> rx.Component:
    tech_name = item["tech_name"]
    horaire = item["horaire"]
    tt = item["telework_days"]
    bendoc = item["bendoc_pause"]

    bg = rx.cond(
        horaire.lower().contains("astreinte"), COLOR_ASTREINTE,
        rx.cond(
            horaire.lower().contains("absent") | horaire.lower().contains("congé"),
            COLOR_ABSENT,
            rx.cond(tt != "", COLOR_TT, rx.cond(horaire != "", COLOR_CDS, COLOR_REPOS))
        )
    )
    border_c = rx.cond(
        horaire.lower().contains("astreinte"), COLOR_ASTREINTE_BORDER,
        rx.cond(
            horaire.lower().contains("absent") | horaire.lower().contains("congé"),
            COLOR_ABSENT_BORDER,
            rx.cond(tt != "", COLOR_TT_BORDER, rx.cond(horaire != "", COLOR_CDS_BORDER, COLOR_REPOS_BORDER))
        )
    )

    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.box(
                    rx.text(tech_name[:2].upper(), color="white", font_size="0.7rem", font_weight="700"),
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    border_radius="50%",
                    width="28px",
                    height="28px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    flex_shrink="0",
                ),
                rx.text(tech_name, color=TEXT, font_size="0.875rem", font_weight="500"),
                spacing="2",
                align="center",
            ),
            padding="10px 14px",
            white_space="nowrap",
        ),
        rx.table.cell(
            rx.box(
                rx.vstack(
                    rx.text(horaire, font_size="0.8rem", font_weight="600", color=TEXT),
                    rx.cond(
                        tt != "",
                        rx.badge("TT " + tt, color_scheme="cyan", variant="soft", radius="full", font_size="0.65rem"),
                    ),
                    rx.cond(
                        bendoc != "",
                        rx.text(bendoc, font_size="0.65rem", color=MUTED),
                    ),
                    spacing="1",
                    align="start",
                ),
                background=bg,
                border="1px solid " + border_c,
                border_radius="8px",
                padding="8px 12px",
                min_height="60px",
                width="100%",
            ),
            padding="6px 8px",
        ),
    )


def astreinte_card(a: AstreinteEntry) -> rx.Component:
    return rx.box(
        rx.text(a["period"], color=TEXT, font_size="0.8rem", font_weight="600"),
        rx.hstack(
            rx.icon("sunrise", size=14, color="#f59e0b"),
            rx.text(a["slot_matin"], color=MUTED, font_size="0.75rem"),
            spacing="1",
        ),
        rx.hstack(
            rx.icon("sunset", size=14, color="#8b5cf6"),
            rx.text(a["slot_soir"], color=MUTED, font_size="0.75rem"),
            spacing="1",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="10px",
        padding="0.8rem 1rem",
        min_width="160px",
    )


def _legend_badge(label: str, color: str) -> rx.Component:
    return rx.hstack(
        rx.box(width="10px", height="10px", background=color, border_radius="2px", flex_shrink="0"),
        rx.text(label, color=MUTED, font_size="0.75rem"),
        spacing="2",
        align="center",
    )


def planning_content() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.hstack(
                rx.icon_button(
                    rx.icon("chevron-left", size=16),
                    on_click=PlanningState.prev_week,
                    background="#1e2235",
                    color=TEXT,
                    border=f"1px solid {BORDER}",
                    border_radius="8px",
                    size="2",
                    _hover={"background": "#2a2d4a"},
                ),
                rx.select(
                    PlanningState.semaines,
                    value=PlanningState.selected_week,
                    on_change=PlanningState.select_week,
                    background="#1e2235",
                    color=TEXT,
                    border=f"1px solid {BORDER}",
                    border_radius="8px",
                    min_width="200px",
                ),
                rx.icon_button(
                    rx.icon("chevron-right", size=16),
                    on_click=PlanningState.next_week,
                    background="#1e2235",
                    color=TEXT,
                    border=f"1px solid {BORDER}",
                    border_radius="8px",
                    size="2",
                    _hover={"background": "#2a2d4a"},
                ),
                rx.spacer(),
                rx.hstack(
                    _legend_badge("Présentiel", COLOR_CDS_BORDER),
                    _legend_badge("Télétravail", COLOR_TT_BORDER),
                    _legend_badge("Astreinte", COLOR_ASTREINTE_BORDER),
                    _legend_badge("Absence", COLOR_ABSENT_BORDER),
                    spacing="3",
                ),
                spacing="3",
                align="center",
            ),
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="12px",
            padding="0.8rem 1rem",
            width="100%",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell(
                            "Technicien",
                            color=MUTED,
                            font_size="0.75rem",
                            font_weight="600",
                            padding="10px 14px",
                            white_space="nowrap",
                        ),
                        rx.table.column_header_cell(
                            PlanningState.selected_week,
                            color=TEXT,
                            font_size="0.85rem",
                            font_weight="600",
                            padding="10px 14px",
                        ),
                    ),
                    background="#10121f",
                ),
                rx.table.body(
                    rx.foreach(PlanningState.entries_by_tech, tech_row),
                ),
                width="100%",
            ),
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="14px",
            overflow="hidden",
            width="100%",
        ),
        rx.box(
            rx.text("Astreintes", color=TEXT, font_weight="600", font_size="0.9rem", margin_bottom="0.8rem"),
            rx.hstack(
                rx.foreach(PlanningState.astreintes, astreinte_card),
                spacing="3",
                wrap="wrap",
            ),
        ),
        spacing="4",
        width="100%",
        on_mount=PlanningState.load_data,
    )


def planning_page() -> rx.Component:
    return page_layout(planning_content(), "Planning")
