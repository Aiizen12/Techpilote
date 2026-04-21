import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.state.auth import AuthState
from techpilot.state.dashboard import DashboardState
from techpilot.state.models import PlanningRow, AstreinteEntry, TechPresence, TicketTrend, QuickLink, ActualiteItem, TechStatItem, ChangelogEntry

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
CARD_BG = "#111524"
BORDER  = "#1c2138"
PRIMARY = "#6366f1"
BG      = "#080b14"


# ── Helpers actualités ────────────────────────────────────────────────────────

def _actu_color(t) -> rx.Var:
    return rx.cond(t == "success", "#22c55e",
           rx.cond(t == "warning", "#f59e0b",
           rx.cond(t == "alerte",  "#ef4444", PRIMARY)))

def _actu_bg(t) -> rx.Var:
    return rx.cond(t == "success", "rgba(34,197,94,0.12)",
           rx.cond(t == "warning", "rgba(245,158,11,0.12)",
           rx.cond(t == "alerte",  "rgba(239,68,68,0.12)", "rgba(99,102,241,0.12)")))

def _actu_icon(t) -> rx.Var:
    return rx.cond(t == "success", "check-circle-2",
           rx.cond(t == "warning", "triangle-alert",
           rx.cond(t == "alerte",  "bell-ring", "info")))

def _actu_label(t) -> rx.Var:
    return rx.cond(t == "success", "Succès",
           rx.cond(t == "warning", "Avertissement",
           rx.cond(t == "alerte",  "Alerte", "Info")))


def actu_mini_card(a: ActualiteItem) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.icon(_actu_icon(a["type"]), size=15, color=_actu_color(a["type"])),
            width="32px", height="32px",
            background=_actu_bg(a["type"]),
            border_radius="8px",
            display="flex", align_items="center", justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.hstack(
                rx.cond(
                    a["epingle"],
                    rx.icon("pin", size=11, color="#fbbf24"),
                ),
                rx.text(a["titre"], color=TEXT, font_size="0.82rem", font_weight="600",
                        flex="1", overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
                rx.text(
                    rx.cond(a["date_creation"] != "", a["date_creation"][:10], ""),
                    color=MUTED, font_size="0.7rem", flex_shrink="0",
                ),
                spacing="2", align="center", width="100%",
            ),
            rx.cond(
                a["contenu"] != "",
                rx.text(a["contenu"], color=MUTED, font_size="0.75rem",
                        overflow="hidden", display="-webkit-box",
                        style={"-webkit-line-clamp": "2", "-webkit-box-orient": "vertical"}),
            ),
            spacing="1", align="start", flex="1", min_width="0",
        ),
        spacing="3", align="start",
        padding="0.65rem 0.9rem",
        border_bottom=f"1px solid {BORDER}",
        width="100%",
        _hover={"background": "rgba(255,255,255,0.02)"},
    )


# ── Config panel ───────────────────────────────────────────────────────────────

def _widget_toggle(label: str, icon_name: str, is_on, on_toggle) -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.icon(icon_name, size=15, color=rx.cond(is_on, PRIMARY, MUTED)),
            rx.text(label, color=rx.cond(is_on, TEXT, MUTED), font_size="0.85rem", font_weight="500"),
            spacing="2", align="center",
        ),
        rx.spacer(),
        rx.switch(checked=is_on, on_change=lambda _: on_toggle, color_scheme="indigo"),
        width="100%", align="center",
        padding="0.6rem 0.5rem",
        border_radius="8px",
        cursor="pointer",
        on_click=on_toggle,
        _hover={"background": "rgba(255,255,255,0.04)"},
    )


def config_panel() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.box(
                rx.hstack(
                    rx.box(
                        rx.icon("sliders-horizontal", size=16, color="white"),
                        background="rgba(255,255,255,0.2)",
                        border_radius="9px",
                        padding="7px",
                        display="flex", align_items="center", justify_content="center",
                    ),
                    rx.vstack(
                        rx.text("Personnaliser le dashboard", color="white", font_size="0.95rem", font_weight="700"),
                        rx.text("Affiche ou masque les sections", color="rgba(255,255,255,0.65)", font_size="0.72rem"),
                        spacing="0", align="start",
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=15),
                        on_click=DashboardState.toggle_config_panel,
                        background="rgba(255,255,255,0.15)",
                        color="white",
                        border_radius="7px",
                        size="2",
                        cursor="pointer",
                        _hover={"background": "rgba(255,255,255,0.25)"},
                    ),
                    spacing="3", align="center",
                ),
                background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                border_radius="12px 12px 0 0",
                padding="1.1rem 1.25rem",
                margin="-24px -24px 0 -24px",
            ),
            rx.vstack(
                _widget_toggle("KPIs",                   "bar-chart-2",    DashboardState.w_kpis,       DashboardState.toggle_w_kpis),
                _widget_toggle("Présence & Astreintes",  "users",          DashboardState.w_presence,   DashboardState.toggle_w_presence),
                _widget_toggle("Tendance tickets",       "trending-up",    DashboardState.w_trends,     DashboardState.toggle_w_trends),
                _widget_toggle("Planning semaine",       "calendar-days",  DashboardState.w_planning,   DashboardState.toggle_w_planning),
                _widget_toggle("Notes & Liens rapides",  "notebook-pen",   DashboardState.w_notes_links, DashboardState.toggle_w_notes_links),
                _widget_toggle("Actualités",             "newspaper",      DashboardState.w_actualites, DashboardState.toggle_w_actualites),
                _widget_toggle("Stats techniciens",      "bar-chart-2",    DashboardState.w_tech_stats, DashboardState.toggle_w_tech_stats),
                _widget_toggle("Mises à jour",           "sparkles",       DashboardState.w_changelog,  DashboardState.toggle_w_changelog),
                spacing="1",
                width="100%",
                padding_top="1rem",
            ),
            background="#111524", border=f"1px solid {BORDER}",
            border_radius="16px", padding="24px", max_width="380px",
            overflow="hidden",
        ),
        open=DashboardState.show_config_panel,
    )


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


# ── Stats techniciens ─────────────────────────────────────────────────────────

def _tech_stat_bar(value: int, total: int, color: str) -> rx.Component:
    pct = rx.cond(total > 0, (value * 100 // total).to_string() + "%", "0%")
    return rx.box(
        rx.box(background=color, width=pct, height="100%", border_radius="4px",
               transition="width 0.3s ease"),
        background="rgba(255,255,255,0.06)", border_radius="4px",
        height="6px", width="100%", overflow="hidden",
    )


def tech_stat_card(s: TechStatItem) -> rx.Component:
    esc_pct = rx.cond(s["total"] > 0, (s["escalades"] * 100 // s["total"]).to_string() + "%", "0%")
    return rx.box(
        rx.hstack(
            rx.box(
                rx.text(s["nom"][:2].upper(), color="white", font_size="0.72rem", font_weight="700"),
                background=s["color"], border_radius="50%",
                width="34px", height="34px", flex_shrink="0",
                display="flex", align_items="center", justify_content="center",
            ),
            rx.vstack(
                rx.hstack(
                    rx.text(s["nom"], color=TEXT, font_size="0.82rem", font_weight="600"),
                    rx.spacer(),
                    rx.text(s["total"].to_string() + " ticket(s)", color=MUTED, font_size="0.72rem"),
                    width="100%", align="center",
                ),
                _tech_stat_bar(s["resolus"], s["total"], "#22c55e"),
                rx.hstack(
                    rx.hstack(
                        rx.box(width="8px", height="8px", background="#ef4444",
                               border_radius="50%", flex_shrink="0"),
                        rx.text(s["en_cours"].to_string() + " en cours", color=MUTED, font_size="0.7rem"),
                        spacing="1", align="center",
                    ),
                    rx.hstack(
                        rx.box(width="8px", height="8px", background="#22c55e",
                               border_radius="50%", flex_shrink="0"),
                        rx.text(s["resolus"].to_string() + " résolus", color=MUTED, font_size="0.7rem"),
                        spacing="1", align="center",
                    ),
                    rx.spacer(),
                    rx.cond(
                        s["escalades"] > 0,
                        rx.text("↑ " + esc_pct + " escaladés", color="#f59e0b", font_size="0.7rem"),
                    ),
                    spacing="3", width="100%", align="center",
                ),
                spacing="1", flex="1", min_width="0",
            ),
            spacing="3", align="center", width="100%",
        ),
        background=CARD_BG, border=f"1px solid {BORDER}",
        border_radius="12px", padding="0.875rem 1rem",
    )


# ── Changelog widget ──────────────────────────────────────────────────────────

def _cl_type_color(t) -> rx.Var:
    return rx.cond(t == "feature",     "#6366f1",
           rx.cond(t == "fix",         "#ef4444",
           rx.cond(t == "amélioration","#22c55e", "#f59e0b")))

def _cl_type_bg(t) -> rx.Var:
    return rx.cond(t == "feature",     "rgba(99,102,241,0.12)",
           rx.cond(t == "fix",         "rgba(239,68,68,0.12)",
           rx.cond(t == "amélioration","rgba(34,197,94,0.12)", "rgba(245,158,11,0.12)")))

def _cl_type_label(t) -> rx.Var:
    return rx.cond(t == "feature",     "Nouveauté",
           rx.cond(t == "fix",         "Correction",
           rx.cond(t == "amélioration","Amélioration", t)))

def _cl_type_icon(t) -> rx.Var:
    return rx.cond(t == "feature",     "sparkles",
           rx.cond(t == "fix",         "wrench",
           rx.cond(t == "amélioration","trending-up", "info")))

def changelog_item(c: ChangelogEntry) -> rx.Component:
    return rx.box(
        rx.hstack(
            # Badge type + version
            rx.hstack(
                rx.box(
                    rx.icon(_cl_type_icon(c["type"]), size=13, color=_cl_type_color(c["type"])),
                    background=_cl_type_bg(c["type"]),
                    border_radius="7px",
                    width="28px", height="28px",
                    display="flex", align_items="center", justify_content="center",
                    flex_shrink="0",
                ),
                rx.box(
                    rx.text(_cl_type_label(c["type"]),
                            color=_cl_type_color(c["type"]),
                            font_size="0.62rem", font_weight="700"),
                    background=_cl_type_bg(c["type"]),
                    border=rx.cond(
                        c["type"] == "feature",  "1px solid rgba(99,102,241,0.3)",
                        rx.cond(c["type"] == "fix", "1px solid rgba(239,68,68,0.3)",
                        "1px solid rgba(34,197,94,0.3)")
                    ),
                    border_radius="6px",
                    padding="1px 7px",
                    white_space="nowrap",
                ),
                rx.badge(
                    "v" + c["version"],
                    color_scheme="indigo", variant="soft",
                    radius="full", font_size="0.65rem",
                ),
                spacing="2", align="center",
            ),
            rx.spacer(),
            rx.text(c["date"], color=MUTED, font_size="0.7rem", flex_shrink="0"),
            rx.icon_button(
                rx.icon("trash-2", size=12),
                on_click=DashboardState.delete_changelog_entry(c["id"]),
                background="transparent", color=MUTED, size="1",
                cursor="pointer",
                _hover={"color": "#ef4444"},
            ),
            spacing="2", align="center", width="100%",
        ),
        rx.text(c["titre"], color=TEXT, font_size="0.85rem", font_weight="600",
                margin_top="0.5rem", margin_bottom="0.4rem"),
        rx.vstack(
            rx.foreach(
                c["items"],
                lambda item: rx.hstack(
                    rx.box(width="5px", height="5px", background=MUTED,
                           border_radius="50%", flex_shrink="0", margin_top="5px"),
                    rx.text(item, color=MUTED, font_size="0.78rem"),
                    spacing="2", align="start",
                )
            ),
            spacing="1", align="start",
        ),
        padding="0.9rem 1rem",
        border_bottom=f"1px solid {BORDER}",
        _hover={"background": "rgba(255,255,255,0.015)"},
        width="100%",
    )


def changelog_form() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.box(
                rx.hstack(
                    rx.box(
                        rx.icon("sparkles", size=15, color="white"),
                        background="rgba(255,255,255,0.2)",
                        border_radius="9px", padding="7px",
                        display="flex", align_items="center", justify_content="center",
                    ),
                    rx.text("Nouvelle entrée changelog", color="white",
                            font_size="0.95rem", font_weight="700"),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=15),
                        on_click=DashboardState.close_changelog_form,
                        background="rgba(255,255,255,0.15)", color="white",
                        border_radius="7px", size="2", cursor="pointer",
                        _hover={"background": "rgba(255,255,255,0.25)"},
                    ),
                    spacing="3", align="center",
                ),
                background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                border_radius="12px 12px 0 0",
                padding="1.1rem 1.25rem",
                margin="-24px -24px 0 -24px",
            ),
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text("Version *", color=MUTED, font_size="0.75rem"),
                        rx.input(
                            placeholder="ex: 2.4.0",
                            value=DashboardState.cl_form_version,
                            on_change=DashboardState.set_cl_version,
                            background="#0d1021", color=TEXT,
                            border=f"1px solid {BORDER}", border_radius="8px",
                        ),
                        spacing="1", flex="1",
                    ),
                    rx.vstack(
                        rx.text("Type *", color=MUTED, font_size="0.75rem"),
                        rx.select.root(
                            rx.select.trigger(
                                background="#0d1021", color=TEXT,
                                border=f"1px solid {BORDER}", border_radius="8px",
                                width="100%",
                            ),
                            rx.select.content(
                                rx.select.item("Nouveauté",    value="feature"),
                                rx.select.item("Amélioration", value="amélioration"),
                                rx.select.item("Correction",   value="fix"),
                                background="#111524", border=f"1px solid {BORDER}",
                            ),
                            value=DashboardState.cl_form_type,
                            on_change=DashboardState.set_cl_type,
                        ),
                        spacing="1", flex="1",
                    ),
                    spacing="3", width="100%",
                ),
                rx.vstack(
                    rx.text("Titre *", color=MUTED, font_size="0.75rem"),
                    rx.input(
                        placeholder="Ex: Recherche globale Ctrl+K",
                        value=DashboardState.cl_form_titre,
                        on_change=DashboardState.set_cl_titre,
                        background="#0d1021", color=TEXT,
                        border=f"1px solid {BORDER}", border_radius="8px", width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                rx.vstack(
                    rx.text("Détails (une ligne par item)", color=MUTED, font_size="0.75rem"),
                    rx.text_area(
                        placeholder="Recherche dans tickets, matrice, documents et gabarits\nAccès via Ctrl+K depuis n'importe quelle page\nCopie gabarit en un clic",
                        value=DashboardState.cl_form_items,
                        on_change=DashboardState.set_cl_items,
                        background="#0d1021", color=TEXT,
                        border=f"1px solid {BORDER}", border_radius="8px",
                        min_height="110px", width="100%", font_size="0.82rem",
                        _placeholder={"color": "#475569"},
                    ),
                    spacing="1", width="100%",
                ),
                rx.hstack(
                    rx.button(
                        "Annuler", on_click=DashboardState.close_changelog_form,
                        background="transparent", color=MUTED,
                        border=f"1px solid {BORDER}", border_radius="8px", cursor="pointer",
                    ),
                    rx.button(
                        rx.icon("plus", size=14), "Ajouter",
                        on_click=DashboardState.add_changelog_entry,
                        background=f"linear-gradient(135deg,{PRIMARY},#8b5cf6)",
                        color="white", border_radius="8px", cursor="pointer", spacing="2",
                    ),
                    spacing="3", justify="end", width="100%",
                ),
                spacing="4", width="100%", padding_top="1.25rem",
            ),
            background="#111524", border=f"1px solid {BORDER}",
            border_radius="16px", padding="24px", max_width="480px",
            overflow="hidden",
        ),
        open=DashboardState.show_changelog_form,
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
            rx.icon_button(
                rx.icon("settings-2", size=15),
                on_click=DashboardState.toggle_config_panel,
                background="rgba(255,255,255,0.06)",
                color=MUTED,
                border_radius="8px",
                size="2",
                cursor="pointer",
                title="Personnaliser le dashboard",
                _hover={"background": "rgba(99,102,241,0.18)", "color": PRIMARY},
            ),
            width="100%", align="center",
            padding="0.3rem 0",
            spacing="3",
        ),

        config_panel(),

        # ── KPI row ─────────────────────────────────────────────────────────
        rx.cond(
            DashboardState.w_kpis,
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
        ),

        # ── Actualités ───────────────────────────────────────────────────────
        rx.cond(
            DashboardState.w_actualites,
            rx.box(
                rx.hstack(
                    rx.icon("newspaper", size=15, color=PRIMARY),
                    rx.text("Actualités", color=TEXT, font_size="0.85rem", font_weight="600"),
                    rx.spacer(),
                    rx.link(
                        rx.hstack(
                            rx.text("Voir tout", color=MUTED, font_size="0.75rem"),
                            rx.icon("arrow-right", size=13, color=MUTED),
                            spacing="1", align="center",
                        ),
                        href="/actualites",
                        _hover={"color": PRIMARY},
                    ),
                    spacing="2", align="center", margin_bottom="0.5rem",
                ),
                rx.cond(
                    DashboardState.actualites_widget.length() == 0,
                    rx.box(
                        rx.text("Aucune actualité pour le moment", color=MUTED, font_size="0.82rem", text_align="center"),
                        padding="1.5rem 0",
                    ),
                    rx.box(
                        rx.foreach(DashboardState.actualites_widget, actu_mini_card),
                        background="#0d1021",
                        border=f"1px solid {BORDER}",
                        border_radius="10px",
                        overflow="hidden",
                    ),
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="14px",
                padding="1.1rem 1.2rem",
                width="100%",
            ),
        ),

        # ── Présence + Astreintes ────────────────────────────────────────────
        rx.cond(
            DashboardState.w_presence,
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
        ),

        # ── Graphique ticket trends ──────────────────────────────────────────
        rx.cond(
            DashboardState.w_trends,
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
        ),

        # ── Planning de la semaine ────────────────────────────────────────────
        rx.cond(
            DashboardState.w_planning,
            rx.box(
                rx.hstack(
                    rx.icon("calendar-days", size=15, color="#06b6d4"),
                    rx.text("Planning de la semaine", color=TEXT, font_size="0.85rem", font_weight="600"),
                    rx.spacer(),
                    rx.button(
                        "Tous",
                        on_click=DashboardState.planning_show_all,
                        background="transparent", color=MUTED,
                        border=f"1px solid {BORDER}", border_radius="6px",
                        font_size="0.72rem", padding="2px 10px", cursor="pointer",
                        _hover={"border_color": "#06b6d4", "color": "#06b6d4"},
                    ),
                    spacing="2", align="center", margin_bottom="0.75rem",
                    width="100%",
                ),
                rx.hstack(
                    rx.foreach(
                        DashboardState.planning_all_names,
                        lambda name: rx.button(
                            name,
                            on_click=DashboardState.toggle_planning_tech(name),
                            background=rx.cond(
                                DashboardState.planning_filter_techs.contains(name),
                                "rgba(6,182,212,0.15)", "transparent",
                            ),
                            color=rx.cond(
                                DashboardState.planning_filter_techs.contains(name),
                                "#06b6d4", MUTED,
                            ),
                            border=rx.cond(
                                DashboardState.planning_filter_techs.contains(name),
                                "1px solid rgba(6,182,212,0.4)", f"1px solid {BORDER}",
                            ),
                            border_radius="20px", font_size="0.72rem",
                            padding="2px 12px", cursor="pointer",
                            _hover={"border_color": "#06b6d4", "color": "#06b6d4"},
                        ),
                    ),
                    wrap="wrap", spacing="2", margin_bottom="0.75rem",
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
                    rx.table.body(rx.foreach(DashboardState.planning_semaine_view, planning_row_v2)),
                    width="100%",
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="14px",
                padding="1rem 1.2rem 0",
                overflow="hidden",
                width="100%",
            ),
        ),

        # ── Notes rapides + Liens rapides ────────────────────────────────────
        rx.cond(
            DashboardState.w_notes_links,
            rx.hstack(
                rx.box(
                    rx.hstack(
                        rx.icon("notebook-pen", size=15, color="#f59e0b"),
                        rx.text("Notes rapides", color=TEXT, font_size="0.85rem", font_weight="600"),
                        rx.spacer(),
                        rx.text("Auto-sauvegardé", color=MUTED, font_size="0.7rem"),
                        rx.icon_button(
                            rx.icon("picture-in-picture-2", size=13),
                            on_click=rx.call_script(
                                "window.open('/notes-window', 'TechPilotNotes', "
                                "'width=440,height=520,resizable=yes,scrollbars=no')"
                            ),
                            background="rgba(245,158,11,0.12)",
                            color="#f59e0b",
                            border_radius="7px",
                            size="1",
                            cursor="pointer",
                            title="Ouvrir en fenêtre séparée",
                            _hover={"background": "rgba(245,158,11,0.25)"},
                        ),
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
        ),

        # ── Stats techniciens ────────────────────────────────────────────────
        rx.cond(
            DashboardState.w_tech_stats,
            rx.box(
                rx.hstack(
                    rx.icon("bar-chart-2", size=15, color=PRIMARY),
                    rx.text("Stats techniciens", color=TEXT, font_size="0.85rem", font_weight="600"),
                    spacing="2", align="center", margin_bottom="0.8rem",
                ),
                rx.cond(
                    DashboardState.tech_stats.length() == 0,
                    rx.box(
                        rx.text("Aucune donnée disponible", color=MUTED, font_size="0.82rem", text_align="center"),
                        padding="1.5rem 0",
                    ),
                    rx.grid(
                        rx.foreach(DashboardState.tech_stats, tech_stat_card),
                        columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                        spacing="3",
                        width="100%",
                    ),
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="14px",
                padding="1.1rem 1.2rem",
                width="100%",
            ),
        ),

        # ── Mises à jour (Changelog) ─────────────────────────────────────────
        rx.cond(
            DashboardState.w_changelog,
            rx.box(
                rx.hstack(
                    rx.icon("sparkles", size=15, color=PRIMARY),
                    rx.text("Mises à jour", color=TEXT, font_size="0.85rem", font_weight="600"),
                    rx.spacer(),
                    rx.button(
                        rx.icon("plus", size=13), "Nouvelle entrée",
                        on_click=DashboardState.open_changelog_form,
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
                    spacing="2", align="center", margin_bottom="0.6rem",
                ),
                rx.cond(
                    DashboardState.changelog.length() == 0,
                    rx.box(
                        rx.text("Aucune mise à jour enregistrée", color=MUTED,
                                font_size="0.82rem", text_align="center"),
                        padding="1.5rem 0",
                    ),
                    rx.box(
                        rx.foreach(DashboardState.changelog, changelog_item),
                        background="#0d1021",
                        border=f"1px solid {BORDER}",
                        border_radius="10px",
                        overflow="hidden",
                        max_height="420px",
                        overflow_y="auto",
                    ),
                ),
                changelog_form(),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="14px",
                padding="1.1rem 1.2rem",
                width="100%",
            ),
        ),

        spacing="4",
        width="100%",
        on_mount=DashboardState.load_data,
    )


def dashboard_page() -> rx.Component:
    return page_layout(dashboard_content(), "Bonjour " + AuthState.user_nom + " 👋")
