import reflex as rx
from techpilot.components.layout import page_layout

BORDER = "#1c2138"


def outils_page() -> rx.Component:
    return page_layout(
        rx.box(
            rx.el.iframe(
                src="/tools.html",
                width="100%",
                height="100%",
                style={
                    "border": "none",
                    "display": "block",
                    "min_height": "calc(100vh - 53px)",
                },
            ),
            width="calc(100% + 3rem)",
            height="calc(100vh - 53px)",
            margin_left="-1.5rem",
            margin_top="-1.5rem",
            overflow="hidden",
        ),
        title="Outils",
    )
