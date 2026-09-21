import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.state.backlog import BacklogState
from techpilot.state.auth import AuthState

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
CARD_BG = "#111524"
BORDER  = "#1c2138"
PRIMARY = "#6366f1"
GREEN   = "#22c55e"
AMBER   = "#f59e0b"
RED     = "#ef4444"


def _kpi(icon: str, label: str, value, color: str) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.icon(icon, size=16, color=color),
            background=f"rgba(255,255,255,0.05)", border_radius="9px",
            width="34px", height="34px",
            display="flex", align_items="center", justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(value, color=TEXT, font_weight="800", font_size="1.15rem"),
            rx.text(label, color=MUTED, font_size="0.72rem"),
            spacing="0", align="start",
        ),
        spacing="3", align="center",
        background=CARD_BG, border=f"1px solid {BORDER}",
        border_radius="12px", padding="0.85rem 1.1rem",
    )


def _renfort_banner(r: dict) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(r["tech_initials"], color="white", font_weight="700", font_size="0.72rem"),
            background=r["tech_color"], border_radius="50%",
            width="26px", height="26px",
            display="flex", align_items="center", justify_content="center",
            flex_shrink="0",
        ),
        rx.text(r["tech_nom"], color=TEXT, font_weight="600", font_size="0.82rem"),
        rx.text("a soldé", color=MUTED, font_size="0.78rem"),
        rx.text(r["source"], color=MUTED, font_size="0.78rem", font_style="italic"),
        rx.icon("arrow-right", size=13, color=PRIMARY),
        rx.text("renforce", color=MUTED, font_size="0.78rem"),
        rx.text(r["target"], color=PRIMARY, font_weight="700", font_size="0.82rem"),
        spacing="2", align="center",
        background="rgba(99,102,241,0.08)", border=f"1px solid {PRIMARY}33",
        border_radius="10px", padding="0.5rem 0.9rem", width="fit-content",
    )


def category_card(c: dict) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(c["nom"], color=TEXT, font_weight="700", font_size="0.9rem", line_height="1.25"),
                rx.spacer(),
                rx.cond(
                    c["is_max"],
                    rx.badge("Volumineuse", color_scheme="orange", variant="soft", font_size="0.62rem"),
                ),
                align="start", width="100%",
            ),
            rx.hstack(
                rx.cond(
                    c["has_titulaire"],
                    rx.hstack(
                        rx.box(
                            rx.text(c["titulaire_initials"], color="white",
                                    font_weight="700", font_size="0.72rem"),
                            background=c["titulaire_color"], border_radius="50%",
                            width="28px", height="28px",
                            display="flex", align_items="center", justify_content="center",
                            flex_shrink="0",
                        ),
                        rx.text(c["titulaire_nom"], color=MUTED, font_size="0.78rem"),
                        spacing="2", align="center",
                    ),
                    rx.text("Aucun titulaire", color=MUTED, font_size="0.78rem", font_style="italic"),
                ),
                rx.spacer(),
                rx.cond(
                    AuthState.is_manager & ~BacklogState.demo_mode,
                    rx.icon_button(
                        rx.icon("pencil", size=12),
                        on_click=BacklogState.open_assign(c["nom"]),
                        background="transparent", color=MUTED,
                        border=f"1px solid {BORDER}", border_radius="6px",
                        size="1", cursor="pointer",
                        _hover={"color": PRIMARY, "border_color": PRIMARY},
                    ),
                ),
                align="center", width="100%",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text(c["ouverts"].to_string(), color=TEXT, font_weight="800", font_size="1.4rem"),
                    rx.text("ouverts", color=MUTED, font_size="0.68rem"),
                    spacing="0", align="start",
                ),
                rx.vstack(
                    rx.text(c["traites"].to_string(), color=MUTED, font_weight="700", font_size="1.1rem"),
                    rx.text("traités", color=MUTED, font_size="0.68rem"),
                    spacing="0", align="start",
                ),
                spacing="5", align="end", width="100%",
            ),
            rx.cond(
                c["is_soldee"],
                rx.hstack(
                    rx.icon("circle-check", size=12, color=GREEN),
                    rx.text("Catégorie soldée", color=GREEN, font_size="0.72rem", font_weight="600"),
                    spacing="1", align="center",
                ),
            ),
            rx.cond(
                c["has_renforts"],
                rx.hstack(
                    rx.icon("users", size=12, color=PRIMARY),
                    rx.text("Renfort : ", c["renforts_label"], color=PRIMARY, font_size="0.72rem", font_weight="600"),
                    spacing="1", align="center",
                ),
            ),
            spacing="3", align="start", width="100%",
        ),
        background=CARD_BG,
        border=rx.cond(c["is_max"], f"1px solid {AMBER}66", f"1px solid {BORDER}"),
        border_radius="14px", padding="1.1rem",
        transition="border-color 0.2s",
    )


def _step(n: str, text: str) -> rx.Component:
    return rx.vstack(
        rx.text(n, color=MUTED, font_size="0.68rem", font_weight="700"),
        rx.text(text, color=MUTED, font_size="0.76rem", line_height="1.4"),
        spacing="1", align="center", text_align="center",
        flex="1", min_width="0",
    )


def rule_explainer() -> rx.Component:
    return rx.hstack(
        _step("1", "Le technicien solde entièrement sa catégorie assignée"),
        rx.icon("arrow-right", size=14, color=MUTED, flex_shrink="0"),
        _step("2", "La catégorie retombe à zéro : signal de fin"),
        rx.icon("arrow-right", size=14, color=MUTED, flex_shrink="0"),
        _step("3", "Il rejoint la catégorie la plus volumineuse du moment"),
        rx.icon("arrow-right", size=14, color=MUTED, flex_shrink="0"),
        _step("4", "Il traite en renfort, aux côtés du titulaire"),
        spacing="3", align="center", width="100%",
        background=CARD_BG, border=f"1px solid {BORDER}",
        border_radius="14px", padding="1rem 1.25rem",
    )


def assign_form_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.text("Assigner un titulaire", color=TEXT, font_weight="700", font_size="1rem"),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=15),
                        on_click=BacklogState.close_assign,
                        background="rgba(255,255,255,0.06)", color=MUTED,
                        border_radius="7px", size="2", cursor="pointer",
                    ),
                    width="100%", align="center",
                ),
                rx.text(BacklogState.assign_categorie, color=PRIMARY, font_size="0.88rem", font_weight="600"),
                rx.select.root(
                    rx.select.trigger(placeholder="Choisir un technicien…", width="100%"),
                    rx.select.content(
                        rx.select.item("Aucun titulaire", value="_none"),
                        rx.foreach(
                            BacklogState.technicians,
                            lambda t: rx.select.item(t["nom"], value=t["id"]),
                        ),
                    ),
                    value=BacklogState.assign_tech_id,
                    on_change=BacklogState.set_assign_tech,
                    width="100%",
                ),
                rx.hstack(
                    rx.button("Annuler", on_click=BacklogState.close_assign,
                              background="transparent", color=MUTED,
                              border=f"1px solid {BORDER}", border_radius="8px", cursor="pointer"),
                    rx.button("Enregistrer", on_click=BacklogState.save_assign,
                              background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                              color="white", border_radius="8px", cursor="pointer", font_weight="600"),
                    spacing="3", justify="end", width="100%",
                ),
                spacing="4", width="100%",
            ),
            background="#111524", border=f"1px solid {BORDER}",
            border_radius="16px", padding="1.5rem", max_width="420px", width="95vw",
        ),
        open=BacklogState.show_assign_form,
    )


def demo_bar() -> rx.Component:
    return rx.hstack(
        rx.cond(
            BacklogState.demo_mode,
            rx.hstack(
                rx.icon("flask-conical", size=13, color="#a78bfa"),
                rx.text("Mode démonstration — tickets factices réels (visibles dans Tickets/Dashboard)",
                        color="#a78bfa", font_size="0.72rem", font_weight="600"),
                spacing="2", align="center",
                background="rgba(139,92,246,0.1)", border="1px solid rgba(139,92,246,0.3)",
                border_radius="7px", padding="4px 10px", width="fit-content",
            ),
        ),
        rx.spacer(),
        rx.cond(
            AuthState.is_manager,
            rx.hstack(
                rx.button(
                    rx.icon("dice-5", size=13), "Nouvelle journée (démo)",
                    on_click=BacklogState.demo_new_day,
                    background="rgba(139,92,246,0.1)", color="#a78bfa",
                    border="1px solid rgba(139,92,246,0.3)", border_radius="7px",
                    font_size="0.78rem", padding="6px 12px", cursor="pointer", spacing="2",
                    _hover={"background": "rgba(139,92,246,0.2)"},
                ),
                rx.cond(
                    BacklogState.demo_mode,
                    rx.fragment(
                        rx.button(
                            rx.icon("fast-forward", size=13), "Faire avancer",
                            on_click=BacklogState.demo_advance,
                            background="rgba(99,102,241,0.1)", color=PRIMARY,
                            border=f"1px solid rgba(99,102,241,0.3)", border_radius="7px",
                            font_size="0.78rem", padding="6px 12px", cursor="pointer", spacing="2",
                            _hover={"background": "rgba(99,102,241,0.2)"},
                        ),
                        rx.button(
                            rx.icon("trash-2", size=13), "Supprimer les tickets de démo",
                            on_click=BacklogState.demo_cleanup,
                            background="transparent", color=MUTED,
                            border=f"1px solid {BORDER}", border_radius="7px",
                            font_size="0.78rem", padding="6px 12px", cursor="pointer", spacing="2",
                            _hover={"color": RED, "border_color": RED},
                        ),
                    ),
                ),
                spacing="2", align="center",
            ),
        ),
        spacing="3", align="center", width="100%",
    )


def backlog_content() -> rx.Component:
    return rx.vstack(
        rx.vstack(
            rx.text(
                "Chaque technicien traite intégralement sa catégorie tout en restant joignable. "
                "Une fois sa catégorie soldée, il vient en renfort sur la catégorie la plus volumineuse.",
                color=MUTED, font_size="0.85rem", line_height="1.5", max_width="720px",
            ),
            spacing="1", align="start", width="100%",
        ),

        demo_bar(),

        rx.cond(
            BacklogState.demo_is_cleared,
            rx.hstack(
                rx.icon("party-popper", size=14, color=GREEN),
                rx.text("Backlog entièrement soldé — belle démonstration !", color=GREEN,
                        font_size="0.8rem", font_weight="600"),
                spacing="2", align="center",
                background="rgba(34,197,94,0.08)", border=f"1px solid {GREEN}33",
                border_radius="8px", padding="0.5rem 0.9rem", width="fit-content",
            ),
        ),

        rx.hstack(
            _kpi("inbox", "Tickets ouverts", BacklogState.total_ouverts.to_string(), PRIMARY),
            _kpi("check-check", "Tickets traités", BacklogState.total_traites.to_string(), GREEN),
            _kpi("flame", "Catégorie la plus chargée",
                 rx.cond(BacklogState.max_categorie_nom != "", BacklogState.max_categorie_nom, "—"), AMBER),
            spacing="3", width="100%", wrap="wrap",
        ),

        rx.cond(
            BacklogState.renfort_techs.length() > 0,
            rx.vstack(
                rx.text("Renforts actifs", color=TEXT, font_weight="600", font_size="0.85rem"),
                rx.vstack(
                    rx.foreach(BacklogState.renfort_techs, _renfort_banner),
                    spacing="2", width="100%",
                ),
                spacing="2", width="100%",
            ),
        ),

        rx.grid(
            rx.foreach(BacklogState.categories, category_card),
            columns="3", spacing="4", width="100%",
        ),

        rule_explainer(),

        assign_form_dialog(),

        spacing="5", width="100%",
        on_mount=BacklogState.load,
    )


def backlog_page() -> rx.Component:
    return page_layout(backlog_content(), "Répartition backlog")
