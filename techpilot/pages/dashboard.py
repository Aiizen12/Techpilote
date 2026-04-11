import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.state.auth import AuthState
from techpilot.state.dashboard import DashboardState
from techpilot.state.models import PlanningRow, AstreinteEntry, TechPresence, TicketTrend, QuickLink

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
CARD_BG = "#111524"
BORDER  = "#1c2138"
PRIMARY = "#6366f1"
BG      = "#080b14"


# ── KPI card avec gradient coloré ─────────────────────────────────────────────

def kpi_card(label: str, value, icon_name: str, gradient: str) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(label, color="rgba(255,255,255,0.75)", font_size="0.75rem", font_weight="500"),
                rx.text(value, color="white", font_size="2.2rem", font_weight="800", line_height="1"),
                spacing="2",
                align="start",
            ),
            rx.spacer(),
            rx.box(
                rx.icon(icon_name, size=26, color="rgba(255,255,255,0.9)"),
                background="rgba(255,255,255,0.18)",
                border_radius="12px",
                padding="10px",
            ),
            align="center",
        ),
        background=gradient,
        border_radius="16px",
        padding="1.3rem 1.4rem",
        flex="1",
        min_width="150px",
        box_shadow="0 4px 24px rgba(0,0,0,0.25)",
    )


# ── Présence card ──────────────────────────────────────────────────────────────

def presence_card(p: TechPresence) -> rx.Component:
    status_color = rx.cond(
        p["status"] == "present", "#22c55e",
        rx.cond(p["status"] == "tt",     "#06b6d4",
        rx.cond(p["status"] == "absent", "#ef4444", "#475569"))
    )
    status_label = rx.cond(
        p["status"] == "present", "Présent",
        rx.cond(p["status"] == "tt",     "TT",
        rx.cond(p["status"] == "absent", "Absent", "Repos"))
    )
    status_scheme = rx.cond(
        p["status"] == "present", "green",
        rx.cond(p["status"] == "tt",     "cyan",
        rx.cond(p["status"] == "absent", "red", "gray"))
    )
    return rx.vstack(
        rx.box(
            rx.text(p["initials"], color="white", font_weight="700", font_size="0.85rem"),
            background=p["color"],
            border_radius="50%",
            width="44px",
            height="44px",
            display="flex",
            align_items="center",
            justify_content="center",
            outline="2px solid " + status_color,
            outline_offset="2px",
        ),
        rx.text(p["nom"], color=TEXT, font_size="0.72rem", text_align="center", font_weight="500"),
        rx.badge(status_label, color_scheme=status_scheme, variant="soft", radius="full", font_size="0.58rem"),
        spacing="1",
        align="center",
    )


# ── Astreinte card ─────────────────────────────────────────────────────────────

def astreinte_card(a: AstreinteEntry) -> rx.Component:
    return rx.hstack(
        rx.box(
            width="8px", height="8px",
            background="#f59e0b",
            border_radius="50%",
            flex_shrink="0",
            margin_top="5px",
        ),
        rx.vstack(
            rx.text(a["period"], color=TEXT, font_size="0.8rem", font_weight="700"),
            rx.hstack(
                rx.text("Matin", color=MUTED, font_size="0.72rem", min_width="36px"),
                rx.text(a["slot_matin"], color=TEXT, font_size="0.72rem", font_weight="500"),
                spacing="2",
            ),
            rx.hstack(
                rx.text("Soir", color=MUTED, font_size="0.72rem", min_width="36px"),
                rx.text(a["slot_soir"], color=TEXT, font_size="0.72rem", font_weight="500"),
                spacing="2",
            ),
            spacing="1",
            align="start",
        ),
        spacing="3",
        align="start",
        padding="0.7rem 0.9rem",
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="10px",
        width="100%",
    )


# ── Planning row ───────────────────────────────────────────────────────────────

def planning_row_v2(row: PlanningRow) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.box(
                    rx.text(row["technician_name"][:2].upper(), color="white", font_size="0.65rem", font_weight="700"),
                    background=PRIMARY,
                    border_radius="50%",
                    width="26px", height="26px",
                    display="flex", align_items="center", justify_content="center",
                    flex_shrink="0",
                ),
                rx.text(row["technician_name"], color=TEXT, font_size="0.82rem", font_weight="500"),
                spacing="2", align="center",
            ),
            padding="9px 12px", white_space="nowrap",
        ),
        rx.table.cell(rx.text(row["horaire"], color=MUTED, font_size="0.78rem"), padding="9px 12px"),
        rx.table.cell(
            rx.cond(
                row["telework_days"] != "",
                rx.badge(row["telework_days"], color_scheme="cyan", variant="soft", radius="full", font_size="0.65rem"),
                rx.text("—", color=MUTED, font_size="0.78rem"),
            ),
            padding="9px 12px",
        ),
        rx.table.cell(
            rx.cond(
                row["bendoc_pause"] != "",
                rx.text(row["bendoc_pause"], color=MUTED, font_size="0.72rem"),
                rx.text("—", color=MUTED, font_size="0.78rem"),
            ),
            padding="9px 12px",
        ),
        _hover={"background": "rgba(255,255,255,0.02)"},
    )


# ── Quick link row ─────────────────────────────────────────────────────────────

def quick_link_row(lk: QuickLink) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.icon("link-2", size=14, color="#a5b4fc"),
            width="28px", height="28px",
            background="rgba(99,102,241,0.12)",
            border_radius="7px",
            display="flex", align_items="center", justify_content="center",
            flex_shrink="0",
        ),
        rx.link(
            lk["nom"],
            href=lk["url"],
            target="_blank",
            color="#a5b4fc",
            font_size="0.82rem",
            font_weight="500",
            flex="1",
            _hover={"text_decoration": "underline"},
        ),
        rx.icon_button(
            rx.icon("x", size=12),
            on_click=DashboardState.delete_link(lk["id"]),
            background="transparent",
            color=MUTED,
            size="1",
            cursor="pointer",
            _hover={"color": "#ef4444"},
        ),
        spacing="2",
        align="center",
        padding="0.5rem 0.75rem",
        border_bottom=f"1px solid {BORDER}",
        _hover={"background": "rgba(255,255,255,0.02)"},
    )


# ── Dashboard content ──────────────────────────────────────────────────────────

def dashboard_content() -> rx.Component:
    return rx.vstack(

        # ── Status bar ──────────────────────────────────────────────────────
        rx.hstack(
            rx.hstack(
                rx.box(width="8px", height="8px", background="#22c55e", border_radius="50%", flex_shrink="0"),
                rx.text("SYSTÈME OPÉRATIONNEL", color="#22c55e", font_size="0.72rem", font_weight="700", letter_spacing="0.08em"),
                spacing="2", align="center",
            ),
            rx.spacer(),
            rx.text(DashboardState.today_label, color=MUTED, font_size="0.8rem"),
            width="100%", align="center",
            padding="0.3rem 0",
        ),

        # ── KPI row ─────────────────────────────────────────────────────────
        rx.hstack(
            kpi_card("Techniciens actifs", DashboardState.technicians_actifs, "users",
                     "linear-gradient(135deg,#6366f1,#8b5cf6)"),
            kpi_card("Tickets ouverts",    DashboardState.tickets_ouverts,    "ticket",
                     "linear-gradient(135deg,#ef4444,#f97316)"),
            kpi_card("Entrées matrice",    DashboardState.entrees_matrice,    "git-branch",
                     "linear-gradient(135deg,#06b6d4,#0284c7)"),
            kpi_card("Semaines planning",  DashboardState.semaines_planning,  "calendar-days",
                     "linear-gradient(135deg,#22c55e,#16a34a)"),
            spacing="4", width="100%", wrap="wrap",
        ),

        # ── Présence + Astreintes ────────────────────────────────────────────
        rx.hstack(
            rx.box(
                rx.hstack(
                    rx.icon("users", size=15, color=PRIMARY),
                    rx.text("Présence aujourd'hui", color=TEXT, font_size="0.85rem", font_weight="600"),
                    spacing="2", align="center", margin_bottom="1rem",
                ),
                rx.flex(
                    rx.foreach(DashboardState.presence_today, presence_card),
                    wrap="wrap",
                    gap="1rem",
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="14px",
                padding="1.1rem 1.2rem",
                flex="1",
            ),
            rx.box(
                rx.hstack(
                    rx.icon("alarm-clock", size=15, color="#f59e0b"),
                    rx.text("Astreintes à venir", color=TEXT, font_size="0.85rem", font_weight="600"),
                    spacing="2", align="center", margin_bottom="0.8rem",
                ),
                rx.vstack(
                    rx.foreach(DashboardState.astreintes, astreinte_card),
                    spacing="2", width="100%",
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="14px",
                padding="1.1rem 1.2rem",
                width="300px",
                flex_shrink="0",
                max_height="340px",
                overflow_y="auto",
            ),
            spacing="4", width="100%", align="start",
        ),

        # ── Graphique ticket trends ──────────────────────────────────────────
        rx.box(
            rx.hstack(
                rx.icon("trending-up", size=15, color=PRIMARY),
                rx.text("Tendance tickets — 8 dernières semaines", color=TEXT, font_size="0.85rem", font_weight="600"),
                rx.spacer(),
                rx.hstack(
                    rx.box(width="10px", height="2px", background="#6366f1", border_radius="2px"),
                    rx.text("Créés",   color=MUTED, font_size="0.72rem"),
                    rx.box(width="10px", height="2px", background="#22c55e", border_radius="2px", margin_left="8px"),
                    rx.text("Résolus", color=MUTED, font_size="0.72rem"),
                    spacing="2", align="center",
                ),
                spacing="2", align="center", margin_bottom="0.8rem",
            ),
            rx.recharts.line_chart(
                rx.recharts.line(
                    data_key="crees",
                    stroke="#6366f1",
                    stroke_width=2,
                    dot={"fill": "#6366f1", "r": 3},
                    type_="monotone",
                    name="Créés",
                ),
                rx.recharts.line(
                    data_key="resolus",
                    stroke="#22c55e",
                    stroke_width=2,
                    dot={"fill": "#22c55e", "r": 3},
                    type_="monotone",
                    name="Résolus",
                ),
                rx.recharts.x_axis(data_key="week", tick={"fill": MUTED, "fontSize": 11}),
                rx.recharts.y_axis(tick={"fill": MUTED, "fontSize": 11}, width=30),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="rgba(255,255,255,0.04)"),
                rx.recharts.tooltip(
                    content_style={"background": "#111524", "border": f"1px solid {BORDER}", "borderRadius": "8px"},
                    label_style={"color": TEXT},
                ),
                data=DashboardState.ticket_trends,
                width="100%",
                height=180,
                margin={"top": 5, "right": 10, "left": -10, "bottom": 0},
            ),
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="14px",
            padding="1.1rem 1.2rem",
            width="100%",
        ),

        # ── Planning de la semaine ────────────────────────────────────────────
        rx.box(
            rx.hstack(
                rx.icon("calendar-days", size=15, color="#06b6d4"),
                rx.text("Planning de la semaine", color=TEXT, font_size="0.85rem", font_weight="600"),
                spacing="2", align="center", margin_bottom="0.8rem",
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Technicien", color=MUTED, font_size="0.7rem", padding="8px 12px"),
                        rx.table.column_header_cell("Horaires",   color=MUTED, font_size="0.7rem", padding="8px 12px"),
                        rx.table.column_header_cell("Jours TT",   color=MUTED, font_size="0.7rem", padding="8px 12px"),
                        rx.table.column_header_cell("Bendoc",     color=MUTED, font_size="0.7rem", padding="8px 12px"),
                    ),
                    background="#0d1021",
                ),
                rx.table.body(rx.foreach(DashboardState.planning_semaine, planning_row_v2)),
                width="100%",
            ),
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="14px",
            overflow="hidden",
            width="100%",
        ),

        # ── Notes rapides + Liens rapides ────────────────────────────────────
        rx.hstack(
            rx.box(
                rx.hstack(
                    rx.icon("notebook-pen", size=15, color="#f59e0b"),
                    rx.text("Notes rapides", color=TEXT, font_size="0.85rem", font_weight="600"),
                    rx.spacer(),
                    rx.text("Auto-sauvegardé", color=MUTED, font_size="0.7rem"),
                    spacing="2", align="center", margin_bottom="0.8rem",
                ),
                rx.text_area(
                    placeholder="Tes notes, rappels, astuces du jour…",
                    value=DashboardState.quick_notes,
                    on_change=DashboardState.set_quick_notes,
                    on_blur=DashboardState.save_notes,
                    background="#0d1021",
                    color=TEXT,
                    border=f"1px solid {BORDER}",
                    border_radius="10px",
                    padding="0.75rem",
                    font_size="0.82rem",
                    min_height="120px",
                    width="100%",
                    resize="vertical",
                    _placeholder={"color": "#475569"},
                    _focus={"border_color": PRIMARY, "outline": "none"},
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="14px",
                padding="1.1rem 1.2rem",
                flex="1",
            ),
            rx.box(
                rx.hstack(
                    rx.icon("link-2", size=15, color="#a5b4fc"),
                    rx.text("Liens rapides", color=TEXT, font_size="0.85rem", font_weight="600"),
                    rx.spacer(),
                    rx.button(
                        rx.icon("plus", size=13), "Ajouter",
                        on_click=DashboardState.open_link_form,
                        background="rgba(99,102,241,0.12)",
                        color="#a5b4fc",
                        border="1px solid rgba(99,102,241,0.3)",
                        border_radius="7px",
                        font_size="0.72rem",
                        padding="4px 10px",
                        cursor="pointer",
                        spacing="1",
                        _hover={"background": "rgba(99,102,241,0.22)"},
                    ),
                    spacing="2", align="center", margin_bottom="0.8rem",
                ),
                rx.cond(
                    DashboardState.quick_links.length() == 0,
                    rx.box(
                        rx.text("Aucun lien enregistré", color=MUTED, font_size="0.8rem", text_align="center"),
                        padding="1.5rem 0",
                    ),
                    rx.box(
                        rx.foreach(DashboardState.quick_links, quick_link_row),
                        background="#0d1021",
                        border=f"1px solid {BORDER}",
                        border_radius="10px",
                        overflow="hidden",
                    ),
                ),
                rx.dialog.root(
                    rx.dialog.content(
                        rx.dialog.title(rx.text("Ajouter un lien", color=TEXT, font_weight="700")),
                        rx.vstack(
                            rx.input(
                                placeholder="Nom *",
                                value=DashboardState.link_form_nom,
                                on_change=DashboardState.set_link_nom,
                                background="#0d1021", color=TEXT,
                                border=f"1px solid {BORDER}", border_radius="8px", width="100%",
                            ),
                            rx.input(
                                placeholder="URL *",
                                value=DashboardState.link_form_url,
                                on_change=DashboardState.set_link_url,
                                background="#0d1021", color=TEXT,
                                border=f"1px solid {BORDER}", border_radius="8px", width="100%",
                            ),
                            rx.hstack(
                                rx.button("Annuler", on_click=DashboardState.close_link_form,
                                          background="transparent", color=MUTED,
                                          border=f"1px solid {BORDER}", border_radius="8px", cursor="pointer"),
                                rx.button("Ajouter", on_click=DashboardState.add_link,
                                          background=f"linear-gradient(135deg,{PRIMARY},#8b5cf6)",
                                          color="white", border_radius="8px", cursor="pointer"),
                                spacing="3", justify="end", width="100%",
                            ),
                            spacing="3", width="100%",
                        ),
                        background="#111524", border=f"1px solid {BORDER}",
                        border_radius="16px", padding="1.5rem", max_width="400px",
                    ),
                    open=DashboardState.show_link_form,
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="14px",
                padding="1.1rem 1.2rem",
                flex="1",
            ),
            spacing="4", width="100%", align="start",
        ),

        spacing="4",
        width="100%",
        on_mount=DashboardState.load_data,
    )


def dashboard_page() -> rx.Component:
    return page_layout(dashboard_content(), "Bonjour " + AuthState.user_nom + " 👋")
