import reflex as rx
from techpilot.components.layout import page_layout

BORDER = "#1c2138"


def bdc_procedures_page() -> rx.Component:
    return page_layout(
        rx.el.iframe(
            src="/bdc_dashboard.html",
            width="100%",
            style={
                "height": "calc(100vh - 130px)",
                "border": f"1px solid {BORDER}",
                "border_radius": "12px",
                "background": "#0d0f1a",
            },
        ),
        title="Suivi procédures",
    )
