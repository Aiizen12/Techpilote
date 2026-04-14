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


def outils_page() -> rx.Component:
    return page_layout(
        rx.vstack(
            # En-tête
            rx.hstack(
                rx.hstack(
                    rx.icon("wrench", size=20, color=PRIMARY),
                    rx.heading("Outils", color=TEXT, size="5"),
                    spacing="2", align="center",
                ),
                rx.spacer(),
                # Onglet Diagnostic
                rx.button(
                    rx.icon("stethoscope", size=13),
                    "Aide au diagnostic N1",
                    on_click=OutilsState.set_diagnostic,
                    color=rx.cond(OutilsState.active_tool == "diagnostic", PRIMARY, MUTED),
                    border=rx.cond(
                        OutilsState.active_tool == "diagnostic",
                        "1px solid rgba(99,102,241,0.5)",
                        f"1px solid {BORDER}",
                    ),
                    background=rx.cond(
                        OutilsState.active_tool == "diagnostic",
                        "rgba(99,102,241,0.15)",
                        "transparent",
                    ),
                    border_radius="8px",
                    padding="5px 14px",
                    font_size="0.8rem",
                    font_weight="500",
                    cursor="pointer",
                    display="inline-flex",
                    align_items="center",
                    gap="6px",
                ),
                # Onglet Réseau
                rx.button(
                    rx.icon("wifi", size=13),
                    "N1 Réseau",
                    on_click=OutilsState.set_reseau,
                    color=rx.cond(OutilsState.active_tool == "reseau", PRIMARY, MUTED),
                    border=rx.cond(
                        OutilsState.active_tool == "reseau",
                        "1px solid rgba(99,102,241,0.5)",
                        f"1px solid {BORDER}",
                    ),
                    background=rx.cond(
                        OutilsState.active_tool == "reseau",
                        "rgba(99,102,241,0.15)",
                        "transparent",
                    ),
                    border_radius="8px",
                    padding="5px 14px",
                    font_size="0.8rem",
                    font_weight="500",
                    cursor="pointer",
                    display="inline-flex",
                    align_items="center",
                    gap="6px",
                ),
                width="100%", align="center", spacing="2",
            ),

            # Iframe
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
