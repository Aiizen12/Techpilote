import reflex as rx
from techpilot.components.layout import page_layout

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
PRIMARY = "#6366f1"
BORDER  = "#1c2138"
CARD    = "#111524"

TOOLS = [
    {"id": "diagnostic", "label": "Aide au diagnostic N1", "icon": "stethoscope", "color": "#06b6d4", "src": "/diagnostic.html"},
    {"id": "reseau",     "label": "N1 Réseau",             "icon": "wifi",        "color": "#818cf8", "src": "/reseau.html"},
]


class OutilsState(rx.State):
    active_tool: str = "diagnostic"

    def set_tool(self, tool_id: str):
        self.active_tool = tool_id


def _tool_tab(tool: dict) -> rx.Component:
    is_active = OutilsState.active_tool == tool["id"]
    return rx.button(
        rx.icon(tool["icon"], size=13),
        tool["label"],
        on_click=OutilsState.set_tool(tool["id"]),
        display="inline-flex",
        align_items="center",
        gap="6px",
        padding="5px 14px",
        border_radius="8px",
        font_size="0.8rem",
        font_weight="500",
        cursor="pointer",
        border=rx.cond(is_active, "1px solid rgba(99,102,241,0.5)", f"1px solid {BORDER}"),
        background=rx.cond(is_active, "rgba(99,102,241,0.15)", "transparent"),
        color=rx.cond(is_active, PRIMARY, MUTED),
        _hover={"border_color": "rgba(99,102,241,0.4)", "color": TEXT},
    )


def _iframe_for(tool: dict) -> rx.Component:
    return rx.el.iframe(
        src=tool["src"],
        width="100%",
        display=rx.cond(OutilsState.active_tool == tool["id"], "block", "none"),
        style={
            "height": "calc(100vh - 130px)",
            "border": f"1px solid {BORDER}",
            "border_radius": "12px",
            "background": "#0d0f1a",
        },
    )


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
                # Onglets
                rx.hstack(
                    *[_tool_tab(t) for t in TOOLS],
                    spacing="2",
                ),
                width="100%", align="center",
            ),

            # Iframes (toutes montées, visibilité gérée par CSS display)
            *[_iframe_for(t) for t in TOOLS],

            spacing="3", width="100%",
        ),
        title="Outils",
    )
