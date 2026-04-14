import reflex as rx
from techpilot.components.layout import page_layout

TEXT    = "#f1f5f9"
PRIMARY = "#6366f1"
BORDER  = "#1c2138"


def outils_page() -> rx.Component:
    return page_layout(
        rx.vstack(
            rx.hstack(
                rx.icon("wrench", size=20, color=PRIMARY),
                rx.heading("Outils", color=TEXT, size="5"),
                spacing="2", align="center",
                width="100%",
            ),
            rx.el.iframe(
                src="/tools.html",
                width="100%",
                style={
                    "height": "calc(100vh - 110px)",
                    "border": f"1px solid {BORDER}",
                    "border_radius": "12px",
                    "background": "#0d0f1a",
                },
            ),
            spacing="3", width="100%",
        ),
        title="Outils",
    )
