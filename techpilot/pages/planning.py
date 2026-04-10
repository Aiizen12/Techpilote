import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.state.planning import PlanningState

TEXT = "#e2e8f0"
MUTED = "#64748b"
CARD_BG = "#151728"
BORDER = "#1e2235"
PRIMARY = "#6366f1"

# Codes couleur planning (style TibTime)
COLOR_CDS = "#1a3a2a"       # vert foncé — présentiel
COLOR_CDS_BORDER = "#22c55e"
COLOR_TT = "#0c2a38"        # cyan foncé — télétravail
COLOR_TT_BORDER = "#06b6d4"
COLOR_ASTREINTE = "#3a1a1a" # rouge foncé — astreinte
COLOR_ASTREINTE_BORDER = "#ef4444"
COLOR_ABSENT = "#3a2e00"    # jaune foncé — absence
COLOR_ABSENT_BORDER = "#eab308"
COLOR_REPOS = "#1a1a2a"     # gris — repos
COLOR_REPOS_BORDER = "#334155"


def _get_cell_style(entry: dict | None) -> tuple[str, str, str]:
    """Retourne (bg, border_color, text_color) selon le type d'entrée."""
    if not entry:
        return COLOR_REPOS, COLOR_REPOS_BORDER, MUTED

    horaire = (entry.get("horaire") or "").lower()
    tt = (entry.get("telework_days") or "").lower()

    if "astreinte" in horaire:
        return COLOR_ASTREINTE, COLOR_ASTREINTE_BORDER, "#fca5a5"
    if "absent" in horaire or "congé" in horaire or "absence" in horaire:
        return COLOR_ABSENT, COLOR_ABSENT_BORDER, "#fde68a"
    if tt and horaire:
        return COLOR_TT, COLOR_TT_BORDER, "#67e8f9"
    if horaire:
        return COLOR_CDS, COLOR_CDS_BORDER, "#86efac"
    return COLOR_REPOS, COLOR_REPOS_BORDER, MUTED


def planning_cell(tech_name: str) -> rx.Component:
    entry = PlanningState.entries.find(
        lambda e: (e.get("technician_name") or e.get("technicien_nom") or "") == tech_name
    )

    # On utilise rx.foreach pour trouver l'entrée du tech
    def render_entry(e: dict) -> rx.Component:
        horaire = e.get("horaire") or ""
        tt = e.get("telework_days") or ""
        bendoc = e.get("bendoc_pause") or ""
        is_astreinte = rx.cond(horaire.lower().contains("astreinte"), True, False)
        is_absent = rx.cond(
            horaire.lower().contains("absent") | horaire.lower().contains("congé"),
            True, False
        )

        return rx.box(
            rx.vstack(
                rx.text(horaire, font_size="0.75rem", font_weight="600", color=TEXT),
                rx.cond(tt != "", rx.badge("TT: " + tt, color_scheme="cyan",   variant="soft", radius="full", font_size="0.65rem")),
                rx.cond(bendoc != "", rx.text(bendoc, font_size="0.65rem", color=MUTED)),
                spacing="1",
                align="start",
            ),
            padding="8px 10px",
            min_height="60px",
        )

    return rx.box(
        rx.cond(
            PlanningState.entries.length() > 0,
            rx.foreach(
                rx.filter(
                    PlanningState.entries,
                    lambda e: (e.get("technician_name") or e.get("technicien_nom") or "") == tech_name
                ),
                render_entry,
            ),
            rx.text("—", color=MUTED, font_size="0.75rem", padding="8px 10px"),
        ),
        background=CARD_BG,
        border_radius="8px",
        border=f"1px solid {BORDER}",
        min_height="60px",
        width="100%",
    )


def tech_row(tech_name: str) -> rx.Component:
    # Trouve l'entrée pour ce technicien dans la semaine sélectionnée
    matching = rx.foreach(
        PlanningState.entries,
        lambda e: rx.cond(
            (e.get("technician_name") or e.get("technicien_nom") or "") == tech_name,
            entry_cell(e),
            rx.box(),
        )
    )

    return rx.tr(
        rx.td(
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
        rx.td(
            entry_cell_for_tech(tech_name),
            padding="6px 8px",
        ),
    )


def entry_cell_for_tech(tech_name: str) -> rx.Component:
    """Affiche la cellule planning pour un technicien donné."""
    # On filtre les entries pour ce tech
    tech_entries = rx.Var.create(
        [e for e in PlanningState.entries if (e.get("technician_name") or e.get("technicien_nom") or "") == tech_name]
    )

    def render(e: dict) -> rx.Component:
        horaire = e.get("horaire") or ""
        tt = e.get("telework_days") or ""
        bendoc = e.get("bendoc_pause") or ""

        # Détermine la couleur
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

        return rx.box(
            rx.vstack(
                rx.text(horaire, font_size="0.8rem", font_weight="600", color=TEXT),
                rx.cond(tt != "", rx.badge("TT " + tt, color_scheme="cyan", variant="soft", radius="full", font_size="0.65rem")),
                rx.cond(bendoc != "", rx.text(bendoc, font_size="0.65rem", color=MUTED, max_width="200px")),
                spacing="1",
                align="start",
            ),
            background=bg,
            border=f"1px solid " + border_c,
            border_radius="8px",
            padding="8px 12px",
            min_height="60px",
            width="100%",
        )

    return rx.cond(
        PlanningState.entries.length() > 0,
        rx.foreach(
            rx.list.filter(
                PlanningState.entries,
                lambda e: (e["technician_name"] if "technician_name" in e else e.get("technicien_nom", "")) == tech_name
            ),
            render,
        ),
        rx.box(
            rx.text("—", color=MUTED, font_size="0.75rem"),
            background=COLOR_REPOS,
            border=f"1px solid {COLOR_REPOS_BORDER}",
            border_radius="8px",
            padding="8px 12px",
            min_height="60px",
        ),
    )


def planning_content() -> rx.Component:
    return rx.vstack(
        # Contrôles semaine
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
                # Légende
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
            background="#151728",
            border=f"1px solid {BORDER}",
            border_radius="12px",
            padding="0.8rem 1rem",
            width="100%",
        ),
        # Tableau planning
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
                    rx.foreach(PlanningState.tech_names, tech_row),
                ),
                width="100%",
            ),
            background="#151728",
            border=f"1px solid {BORDER}",
            border_radius="14px",
            overflow="hidden",
            width="100%",
        ),
        # Astreintes
        rx.box(
            rx.text("Astreintes", color=TEXT, font_weight="600", font_size="0.9rem", margin_bottom="0.8rem"),
            rx.hstack(
                rx.foreach(
                    PlanningState.astreintes,
                    lambda a: rx.box(
                        rx.text(a.get("period", ""), color=TEXT, font_size="0.8rem", font_weight="600"),
                        rx.hstack(
                            rx.icon("sunrise", size=14, color="#f59e0b"),
                            rx.text(a.get("slot_matin", ""), color=MUTED, font_size="0.75rem"),
                            spacing="1",
                        ),
                        rx.hstack(
                            rx.icon("sunset", size=14, color="#8b5cf6"),
                            rx.text(a.get("slot_soir", ""), color=MUTED, font_size="0.75rem"),
                            spacing="1",
                        ),
                        background="#151728",
                        border=f"1px solid {BORDER}",
                        border_radius="10px",
                        padding="0.8rem 1rem",
                        min_width="160px",
                    )
                ),
                spacing="3",
                wrap="wrap",
            ),
        ),
        spacing="4",
        width="100%",
        on_mount=PlanningState.load_data,
    )


def _legend_badge(label: str, color: str) -> rx.Component:
    return rx.hstack(
        rx.box(width="10px", height="10px", background=color, border_radius="2px", flex_shrink="0"),
        rx.text(label, color=MUTED, font_size="0.75rem"),
        spacing="2",
        align="center",
    )


def planning_page() -> rx.Component:
    return page_layout(planning_content(), "Planning")
