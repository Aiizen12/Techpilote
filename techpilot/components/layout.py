import reflex as rx
from techpilot.state.auth import AuthState

BG = "#0d0f1a"
SIDEBAR_BG = "#10121f"
BORDER = "#1e2235"
PRIMARY = "#6366f1"
TEXT = "#e2e8f0"
MUTED = "#64748b"
HOVER_BG = "rgba(99,102,241,0.12)"
ACTIVE_BG = "rgba(99,102,241,0.2)"


def nav_item(label: str, icon: str, href: str, active_path: str) -> rx.Component:
    is_active = rx.State.router.page.path == href
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=18, color=rx.cond(is_active, PRIMARY, MUTED)),
            rx.text(
                label,
                font_size="0.875rem",
                font_weight=rx.cond(is_active, "600", "400"),
                color=rx.cond(is_active, TEXT, MUTED),
            ),
            spacing="3",
            align="center",
            padding="9px 12px",
            border_radius="10px",
            background=rx.cond(is_active, ACTIVE_BG, "transparent"),
            _hover={"background": HOVER_BG, "cursor": "pointer"},
            transition="all 0.15s",
            width="100%",
        ),
        href=href,
        text_decoration="none",
        width="100%",
    )


def sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Logo
            rx.hstack(
                rx.box(
                    rx.text("⚡", font_size="1.2rem"),
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    border_radius="10px",
                    padding="6px 10px",
                ),
                rx.text(
                    "TechPilot",
                    font_size="1.1rem",
                    font_weight="700",
                    color=TEXT,
                ),
                spacing="3",
                align="center",
                padding="1.2rem 1rem 1rem",
            ),
            rx.divider(border_color=BORDER, margin_y="0.5rem"),
            # Navigation
            rx.vstack(
                rx.text("NAVIGATION", font_size="0.65rem", font_weight="700", color=MUTED, padding_left="12px", padding_top="4px"),
                nav_item("Dashboard",   "layout-dashboard", "/dashboard",   "/dashboard"),
                nav_item("Planning",    "calendar-days",    "/planning",    "/planning"),
                nav_item("Escalade N1", "git-branch",       "/escalade",    "/escalade"),
                nav_item("Tickets",     "ticket",           "/tickets",     "/tickets"),
                nav_item("Documents",   "folder",           "/documents",   "/documents"),
                spacing="1",
                width="100%",
            ),
            rx.divider(border_color=BORDER, margin_y="0.5rem"),
            rx.vstack(
                rx.text("ÉQUIPE", font_size="0.65rem", font_weight="700", color=MUTED, padding_left="12px", padding_top="4px"),
                nav_item("Techniciens", "users",        "/techniciens", "/techniciens"),
                nav_item("Actualités",  "newspaper",    "/actualites",  "/actualites"),
                nav_item("Quêtes",      "trophy",       "/quetes",      "/quetes"),
                nav_item("Feedbacks",   "message-circle","feedbacks",   "/feedbacks"),
                spacing="1",
                width="100%",
            ),
            rx.cond(
                AuthState.is_manager,
                rx.vstack(
                    rx.divider(border_color=BORDER, margin_y="0.5rem"),
                    rx.text("ADMIN", font_size="0.65rem", font_weight="700", color=MUTED, padding_left="12px", padding_top="4px"),
                    nav_item("Permissions", "shield",   "/permissions", "/permissions"),
                    nav_item("Audit",       "file-text","/audit",       "/audit"),
                    spacing="1",
                    width="100%",
                ),
            ),
            # Spacer
            rx.spacer(),
            # User info + logout
            rx.divider(border_color=BORDER),
            rx.hstack(
                rx.box(
                    rx.text(
                        AuthState.user_nom[:2].upper(),
                        color="white",
                        font_weight="700",
                        font_size="0.8rem",
                    ),
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    border_radius="50%",
                    width="32px",
                    height="32px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.vstack(
                    rx.text(AuthState.user_nom, color=TEXT, font_size="0.8rem", font_weight="600"),
                    rx.text(AuthState.user_role, color=MUTED, font_size="0.7rem", text_transform="capitalize"),
                    spacing="0",
                    align="start",
                ),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("log-out", size=16),
                    on_click=AuthState.logout,
                    background="transparent",
                    color=MUTED,
                    cursor="pointer",
                    _hover={"color": "#f87171", "background": "rgba(239,68,68,0.1)"},
                    border_radius="8px",
                    size="2",
                ),
                spacing="2",
                align="center",
                padding="0.8rem 0.8rem",
                width="100%",
            ),
            height="100%",
            spacing="0",
            width="100%",
        ),
        width="220px",
        min_height="100vh",
        background=SIDEBAR_BG,
        border_right=f"1px solid {BORDER}",
        position="fixed",
        left="0",
        top="0",
        z_index="100",
        display="flex",
        flex_direction="column",
    )


def page_layout(content: rx.Component, title: str = "") -> rx.Component:
    return rx.box(
        sidebar(),
        rx.box(
            # Header
            rx.box(
                rx.hstack(
                    rx.heading(title, size="5", color=TEXT, font_weight="700") if title else rx.box(),
                    rx.spacer(),
                    rx.box(
                        rx.icon("bell", size=18, color=MUTED),
                        background="transparent",
                        cursor="pointer",
                        padding="6px",
                        border_radius="8px",
                        _hover={"background": HOVER_BG, "color": TEXT},
                    ),
                    spacing="3",
                    align="center",
                    padding="1rem 1.5rem",
                ),
                background=SIDEBAR_BG,
                border_bottom=f"1px solid {BORDER}",
                position="sticky",
                top="0",
                z_index="50",
            ),
            # Contenu
            rx.box(
                content,
                padding="1.5rem",
                min_height="calc(100vh - 57px)",
            ),
            margin_left="220px",
            background=BG,
            min_height="100vh",
        ),
        on_mount=AuthState.check_auth,
    )
