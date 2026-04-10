import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.state.auth import AuthState
from techpilot.state.dashboard import DashboardState

TEXT = "#e2e8f0"
MUTED = "#64748b"
CARD_BG = "#151728"
BORDER = "#1e2235"
PRIMARY = "#6366f1"


def kpi_card(label: str, value, icon: str, color: str) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(label, color=MUTED, font_size="0.78rem", font_weight="600"),
                rx.text(value, color=TEXT, font_size="2rem", font_weight="800"),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            rx.box(
                rx.icon(icon, size=24, color=color),
                background=f"rgba({_hex_to_rgb(color)},0.12)",
                border_radius="12px",
                padding="12px",
            ),
            align="center",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="14px",
        padding="1.2rem",
        flex="1",
        min_width="160px",
    )


def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b}"


def planning_row(entry: dict) -> rx.Component:
    name = entry.get("technician_name") or entry.get("technicien_nom") or "?"
    horaire = entry.get("horaire") or "—"
    tt = entry.get("telework_days") or ""
    return rx.tr(
        rx.td(rx.text(name, color=TEXT, font_size="0.875rem"), padding="10px 14px"),
        rx.td(rx.text(horaire, color=MUTED, font_size="0.875rem"), padding="10px 14px"),
        rx.td(
            rx.cond(
                tt != "",
                rx.badge(tt, color_scheme="cyan", variant="soft", radius="full"),
                rx.text("—", color=MUTED, font_size="0.875rem"),
            ),
            padding="10px 14px",
        ),
    )


def astreinte_row(a: dict) -> rx.Component:
    return rx.tr(
        rx.td(rx.text(a.get("period", ""), color=TEXT, font_size="0.875rem"), padding="10px 14px"),
        rx.td(
            rx.badge(a.get("slot_matin", ""), color_scheme="amber", variant="soft"),
            padding="10px 14px",
        ),
        rx.td(
            rx.badge(a.get("slot_soir", ""), color_scheme="indigo", variant="soft"),
            padding="10px 14px",
        ),
    )


def dashboard_content() -> rx.Component:
    return rx.vstack(
        # KPI row
        rx.hstack(
            kpi_card("Techniciens actifs",  DashboardState.technicians_actifs, "users",       "#22c55e"),
            kpi_card("Tickets ouverts",     DashboardState.tickets_ouverts,    "ticket",       "#f59e0b"),
            kpi_card("Entrées matrice",     DashboardState.entrees_matrice,    "git-branch",   PRIMARY),
            kpi_card("Semaines planning",   DashboardState.semaines_planning,  "calendar-days","#06b6d4"),
            spacing="4",
            width="100%",
            wrap="wrap",
        ),
        # Ligne du bas : planning + astreintes
        rx.hstack(
            # Planning semaine courante
            rx.box(
                rx.text("Planning — semaine en cours", color=TEXT, font_weight="600", font_size="0.9rem", margin_bottom="0.8rem"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Technicien", color=MUTED, font_size="0.75rem"),
                            rx.table.column_header_cell("Horaires",   color=MUTED, font_size="0.75rem"),
                            rx.table.column_header_cell("Télétravail",color=MUTED, font_size="0.75rem"),
                        ),
                        background=f"{CARD_BG}",
                    ),
                    rx.table.body(
                        rx.foreach(DashboardState.planning_semaine, planning_row),
                    ),
                    width="100%",
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="14px",
                padding="1.2rem",
                flex="1",
            ),
            # Astreintes
            rx.box(
                rx.text("Astreintes à venir", color=TEXT, font_weight="600", font_size="0.9rem", margin_bottom="0.8rem"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Période",  color=MUTED, font_size="0.75rem"),
                            rx.table.column_header_cell("06h-08h",  color=MUTED, font_size="0.75rem"),
                            rx.table.column_header_cell("18h-20h",  color=MUTED, font_size="0.75rem"),
                        ),
                        background=CARD_BG,
                    ),
                    rx.table.body(
                        rx.foreach(DashboardState.astreintes, astreinte_row),
                    ),
                    width="100%",
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="14px",
                padding="1.2rem",
                width="340px",
            ),
            spacing="4",
            width="100%",
            align="start",
        ),
        spacing="5",
        width="100%",
        on_mount=DashboardState.load_data,
    )


def dashboard_page() -> rx.Component:
    return page_layout(dashboard_content(), f"Bonjour {AuthState.user_nom} 👋")
