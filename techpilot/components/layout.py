import reflex as rx
from techpilot.state.auth import AuthState

# ── V2 Design tokens ──────────────────────────────────────────────────────────
BG          = "#080b14"
SIDEBAR_BG  = "#0d1021"
BORDER      = "#1c2138"
PRIMARY     = "#6366f1"
TEXT        = "#f1f5f9"
MUTED       = "#94a3b8"
HOVER_BG    = "rgba(99,102,241,0.1)"
ACTIVE_BG   = "rgba(99,102,241,0.18)"

SIDEBAR_FULL      = "240px"
SIDEBAR_COLLAPSED = "64px"


class LayoutState(rx.State):
    collapsed: bool = False

    def toggle(self):
        self.collapsed = not self.collapsed


# ── Nav item ──────────────────────────────────────────────────────────────────

def nav_item(label: str, icon_name: str, href: str) -> rx.Component:
    is_active = rx.State.router.page.path == href

    icon_el = rx.icon(
        icon_name,
        size=17,
        color=rx.cond(is_active, PRIMARY, MUTED),
    )

    # Collapsed: icon centré
    collapsed_item = rx.box(
        icon_el,
        width="40px",
        height="38px",
        border_radius="10px",
        background=rx.cond(is_active, ACTIVE_BG, "transparent"),
        display="flex",
        align_items="center",
        justify_content="center",
        margin_x="auto",
        _hover={"background": HOVER_BG, "cursor": "pointer"},
        transition="background 0.15s",
    )

    # Expanded: icon + label
    expanded_item = rx.hstack(
        rx.box(
            icon_el,
            width="24px",
            flex_shrink="0",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
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
        border_left=rx.cond(is_active, f"2px solid {PRIMARY}", "2px solid transparent"),
        _hover={"background": HOVER_BG, "cursor": "pointer"},
        transition="all 0.15s",
        width="100%",
    )

    return rx.link(
        rx.cond(LayoutState.collapsed, collapsed_item, expanded_item),
        href=href,
        text_decoration="none",
        width="100%",
        display="block",
    )


# ── Section label ─────────────────────────────────────────────────────────────

def section_label(text: str) -> rx.Component:
    return rx.cond(
        ~LayoutState.collapsed,
        rx.text(
            text,
            font_size="0.6rem",
            font_weight="700",
            color=MUTED,
            padding_left="14px",
            padding_top="8px",
            letter_spacing="0.1em",
        ),
    )


# ── Nav group ─────────────────────────────────────────────────────────────────

def nav_group(*items) -> rx.Component:
    return rx.box(
        rx.vstack(*items, spacing="1", width="100%"),
        padding_x=rx.cond(LayoutState.collapsed, "0.6rem", "0.75rem"),
        padding_y="0.4rem",
        width="100%",
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────

def sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(

            # ── Logo + toggle ────────────────────────────────────────────────
            rx.hstack(
                rx.cond(
                    ~LayoutState.collapsed,
                    rx.hstack(
                        rx.box(
                            rx.text("⚡", font_size="1.1rem"),
                            background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                            border_radius="9px",
                            padding="5px 8px",
                        ),
                        rx.text(
                            "TechPilot",
                            font_size="1rem",
                            font_weight="700",
                            color=TEXT,
                            letter_spacing="-0.01em",
                        ),
                        spacing="2",
                        align="center",
                    ),
                ),
                rx.spacer(),
                rx.icon_button(
                    rx.icon(
                        rx.cond(LayoutState.collapsed, "panel-left-open", "panel-left-close"),
                        size=16,
                    ),
                    on_click=LayoutState.toggle,
                    background="transparent",
                    color=MUTED,
                    cursor="pointer",
                    border_radius="8px",
                    size="2",
                    _hover={"background": HOVER_BG, "color": TEXT},
                ),
                width="100%",
                align="center",
                padding=rx.cond(
                    LayoutState.collapsed,
                    "1rem 0.8rem",
                    "1rem 0.75rem 1rem 1rem",
                ),
                flex_shrink="0",
            ),

            rx.divider(border_color=BORDER),

            # ── Navigation ───────────────────────────────────────────────────
            nav_group(
                section_label("NAVIGATION"),
                nav_item("Dashboard",   "layout-dashboard", "/dashboard"),
                nav_item("Planning",    "calendar-days",    "/planning"),
                nav_item("Escalade N1", "git-branch",       "/escalade"),
                nav_item("Tickets",     "ticket",           "/tickets"),
                nav_item("Documents",   "folder",           "/documents"),
            ),

            rx.divider(border_color=BORDER, margin_y="0"),

            # ── Équipe ───────────────────────────────────────────────────────
            nav_group(
                section_label("ÉQUIPE"),
                nav_item("Techniciens", "users",          "/techniciens"),
                nav_item("Actualités",  "newspaper",      "/actualites"),
                nav_item("Quêtes",      "trophy",         "/quetes"),
                nav_item("Feedbacks",   "message-circle", "/feedbacks"),
            ),

            # ── Admin (manager only) ─────────────────────────────────────────
            rx.cond(
                AuthState.is_manager,
                rx.vstack(
                    rx.divider(border_color=BORDER, margin_y="0"),
                    nav_group(
                        section_label("ADMIN"),
                        nav_item("Permissions",  "shield",    "/permissions"),
                        nav_item("Audit",        "file-text", "/audit"),
                        nav_item("Import Excel", "file-up",   "/import-excel"),
                    ),
                    spacing="0",
                    width="100%",
                ),
            ),

            rx.spacer(),

            rx.divider(border_color=BORDER),

            # ── User section ─────────────────────────────────────────────────
            rx.box(
                rx.cond(
                    ~LayoutState.collapsed,
                    rx.hstack(
                        rx.box(
                            rx.text(
                                AuthState.user_nom[:2].upper(),
                                color="white",
                                font_weight="700",
                                font_size="0.72rem",
                            ),
                            background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                            border_radius="50%",
                            width="30px",
                            height="30px",
                            display="flex",
                            align_items="center",
                            justify_content="center",
                            flex_shrink="0",
                        ),
                        rx.vstack(
                            rx.text(AuthState.user_nom, color=TEXT, font_size="0.8rem", font_weight="600"),
                            rx.text(AuthState.user_role, color=MUTED, font_size="0.68rem", text_transform="capitalize"),
                            spacing="0",
                            align="start",
                            flex="1",
                            overflow="hidden",
                            min_width="0",
                        ),
                        rx.icon_button(
                            rx.icon("log-out", size=15),
                            on_click=AuthState.logout,
                            background="transparent",
                            color=MUTED,
                            cursor="pointer",
                            _hover={"color": "#f87171", "background": "rgba(239,68,68,0.1)"},
                            border_radius="7px",
                            size="2",
                        ),
                        spacing="2",
                        align="center",
                        width="100%",
                        overflow="hidden",
                    ),
                    # Collapsed : juste l'icône logout centré
                    rx.box(
                        rx.icon_button(
                            rx.icon("log-out", size=15),
                            on_click=AuthState.logout,
                            background="transparent",
                            color=MUTED,
                            cursor="pointer",
                            _hover={"color": "#f87171", "background": "rgba(239,68,68,0.1)"},
                            border_radius="7px",
                            size="2",
                        ),
                        display="flex",
                        justify_content="center",
                        width="100%",
                    ),
                ),
                padding="0.75rem",
                width="100%",
            ),

            height="100%",
            spacing="0",
            width="100%",
            overflow="hidden",
        ),

        width=rx.cond(LayoutState.collapsed, SIDEBAR_COLLAPSED, SIDEBAR_FULL),
        min_height="100vh",
        background=SIDEBAR_BG,
        border_right=f"1px solid {BORDER}",
        position="fixed",
        left="0",
        top="0",
        z_index="100",
        display="flex",
        flex_direction="column",
        transition="width 0.22s cubic-bezier(0.4,0,0.2,1)",
        overflow="hidden",
        flex_shrink="0",
    )


# ── Page layout ───────────────────────────────────────────────────────────────

def page_layout(content: rx.Component, title: str = "") -> rx.Component:
    return rx.box(
        sidebar(),
        rx.box(
            # Header
            rx.box(
                rx.hstack(
                    rx.heading(title, size="5", color=TEXT, font_weight="700"),
                    rx.spacer(),
                    rx.box(
                        rx.icon("bell", size=17, color=MUTED),
                        background="transparent",
                        cursor="pointer",
                        padding="7px",
                        border_radius="8px",
                        _hover={"background": HOVER_BG},
                        transition="background 0.15s",
                    ),
                    spacing="3",
                    align="center",
                    padding="0.85rem 1.5rem",
                ),
                background=SIDEBAR_BG,
                border_bottom=f"1px solid {BORDER}",
                position="sticky",
                top="0",
                z_index="50",
            ),
            # Content
            rx.box(
                content,
                padding="1.5rem",
                min_height="calc(100vh - 57px)",
            ),
            margin_left=rx.cond(LayoutState.collapsed, SIDEBAR_COLLAPSED, SIDEBAR_FULL),
            background=BG,
            min_height="100vh",
            transition="margin-left 0.22s cubic-bezier(0.4,0,0.2,1)",
        ),
        on_mount=AuthState.check_auth,
    )
