import reflex as rx
from techpilot.components.layout import page_layout

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
PRIMARY = "#6366f1"
BORDER  = "#1c2138"


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
                rx.hstack(
                    rx.box(
                        rx.icon("stethoscope", size=13, color="#06b6d4"),
                        background="rgba(6,182,212,0.1)",
                        border="1px solid rgba(6,182,212,0.2)",
                        border_radius="6px",
                        padding="3px 7px",
                        display="inline-flex",
                    ),
                    rx.text(
                        "Aide au diagnostic N1",
                        color=MUTED, font_size="0.8rem",
                    ),
                    spacing="2", align="center",
                ),
                width="100%", align="center",
            ),

            # Iframe plein écran
            rx.el.iframe(
                src="/diagnostic.html",
                width="100%",
                style={
                    "height": "calc(100vh - 130px)",
                    "border": f"1px solid {BORDER}",
                    "border_radius": "12px",
                    "background": "#1d1515",
                },
            ),

            spacing="4", width="100%",
        ),
        title="Outils",
    )
