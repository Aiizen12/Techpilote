import reflex as rx
from techpilot.components.layout import page_layout

TEXT    = "#f1f5f9"
PRIMARY = "#6366f1"
BORDER  = "#1c2138"


def outils_page() -> rx.Component:
    return page_layout(
        rx.box(
            rx.el.iframe(
                src="/tools.html",
                width="100%",
                style={
                    "height": "calc(100vh - 56px)",
                    "border": "none",
                    "display": "block",
                },
            ),
            width="100%",
            padding="0",
        ),
        title="Outils",
    )
