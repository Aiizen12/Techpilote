import reflex as rx
from techpilot.components.layout import page_layout

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
PRIMARY = "#6366f1"
BORDER  = "#1c2138"


class OutilsState(rx.State):
    active_tool: str = "diagnostic"

    def set_diagnostic(self):
        self.active_tool = "diagnostic"

    def set_reseau(self):
        self.active_tool = "reseau"


def _tab_btn(label: str, icon: str, tool_id: str, handler) -> rx.Component:
    is_active = OutilsState.active_tool == tool_id
    return rx.button(
        rx.icon(icon, size=13),
        label,
        on_click=handler,
        style={
            "display": "inline-flex",
            "align_items": "center",
            "gap": "6px",
            "padding": "5px 14px",
            "border_radius": "8px",
            "font_size": "0.8rem",
            "font_weight": "500",
            "cursor": "pointer",
            "border": rx.cond(is_active, "1px solid rgba(99,102,241,0.5)", f"1px solid {BORDER}"),
            "background": rx.cond(is_active, "rgba(99,102,241,0.15)", "transparent"),
            "color": rx.cond(is_active, PRIMARY, MUTED),
        },
    )


def outils_page() -> rx.Component:
    return page_layout(
        rx.vstack(
            # En-tête avec onglets
            rx.hstack(
                rx.hstack(
                    rx.icon("wrench", size=20, color=PRIMARY),
                    rx.heading("Outils", color=TEXT, size="5"),
                    spacing="2", align="center",
                ),
                rx.spacer(),
                rx.hstack(
                    _tab_btn("Aide au diagnostic N1", "stethoscope", "diagnostic", OutilsState.set_diagnostic),
                    _tab_btn("N1 Réseau", "wifi", "reseau", OutilsState.set_reseau),
                    spacing="2",
                ),
                width="100%", align="center",
            ),

            # Iframe diagnostic
            rx.cond(
                OutilsState.active_tool == "diagnostic",
                rx.el.iframe(
                    src="/diagnostic.html",
                    width="100%",
                    style={
                        "height": "calc(100vh - 130px)",
                        "border": f"1px solid {BORDER}",
                        "border_radius": "12px",
                        "background": "#0d0f1a",
                    },
                ),
                rx.el.iframe(
                    src="/reseau.html",
                    width="100%",
                    style={
                        "height": "calc(100vh - 130px)",
                        "border": f"1px solid {BORDER}",
                        "border_radius": "12px",
                        "background": "#0d0f1a",
                    },
                ),
            ),

            spacing="3", width="100%",
        ),
        title="Outils",
    )
