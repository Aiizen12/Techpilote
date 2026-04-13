import reflex as rx
from techpilot.state.auth import AuthState
from techpilot.state.escalade import EscaladeState
from techpilot.state.notifications import NotificationState

# ── Design tokens ─────────────────────────────────────────────────────────────
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
    mobile_open: bool = False

    def toggle(self):
        self.collapsed = not self.collapsed

    def toggle_mobile(self):
        self.mobile_open = not self.mobile_open

    def close_mobile(self):
        self.mobile_open = False

    def search_key(self, key: str):
        if key == "Enter":
            return rx.redirect("/escalade")


# ── Notification item ─────────────────────────────────────────────────────────

def notif_item(item: dict) -> rx.Component:
    is_ticket = item["type"] == "ticket"
    color  = rx.cond(is_ticket, "#ef4444", PRIMARY)
    bg     = rx.cond(is_ticket, "rgba(239,68,68,0.12)", "rgba(99,102,241,0.12)")
    icon   = rx.cond(is_ticket, "shield-alert", "pin")
    return rx.hstack(
        rx.box(
            rx.icon(icon, size=14, color=color),
            background=bg,
            border_radius="8px",
            width="32px",
            height="32px",
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(item["title"], color=TEXT, font_size="0.8rem", font_weight="600",
                    white_space="nowrap", overflow="hidden", text_overflow="ellipsis"),
            rx.text(item["sub"], color=MUTED, font_size="0.7rem"),
            spacing="0",
            align="start",
            flex="1",
            min_width="0",
        ),
        spacing="3",
        align="center",
        padding="0.65rem 1rem",
        border_bottom=f"1px solid {BORDER}",
        cursor="pointer",
        _hover={"background": "rgba(255,255,255,0.03)"},
        width="100%",
        on_click=NotificationState.navigate(item["href"]),
    )


# ── Notification panel ────────────────────────────────────────────────────────

def notification_panel() -> rx.Component:
    return rx.box(
        # Header
        rx.hstack(
            rx.hstack(
                rx.icon("bell", size=14, color=PRIMARY),
                rx.text("Notifications", color=TEXT, font_size="0.875rem", font_weight="700"),
                spacing="2", align="center",
            ),
            rx.spacer(),
            rx.cond(
                NotificationState.count > 0,
                rx.badge(
                    NotificationState.count,
                    color_scheme="red", variant="soft", radius="full", font_size="0.68rem",
                ),
            ),
            spacing="2", align="center",
            padding="0.75rem 1rem",
            border_bottom=f"1px solid {BORDER}",
        ),
        # Corps
        rx.cond(
            NotificationState.count == 0,
            rx.box(
                rx.vstack(
                    rx.icon("bell-off", size=36, color=MUTED),
                    rx.text("Aucune notification", color=MUTED, font_size="0.82rem"),
                    spacing="3", align="center",
                ),
                padding="2.5rem",
                display="flex",
                justify_content="center",
            ),
            rx.box(
                rx.foreach(NotificationState.items, notif_item),
                max_height="360px",
                overflow_y="auto",
                width="100%",
            ),
        ),
        position="absolute",
        top="calc(100% + 8px)",
        right="0",
        width="340px",
        background=SIDEBAR_BG,
        border=f"1px solid {BORDER}",
        border_radius="14px",
        box_shadow="0 8px 40px rgba(0,0,0,0.55)",
        z_index="300",
        overflow="hidden",
    )


# ── Nav item ──────────────────────────────────────────────────────────────────

def nav_item(label: str, icon_name: str, href: str, mobile: bool = False) -> rx.Component:
    is_active = rx.State.router.page.path == href

    icon_el = rx.icon(icon_name, size=17, color=rx.cond(is_active, PRIMARY, MUTED))

    collapsed_item = rx.box(
        icon_el,
        width="40px", height="38px",
        border_radius="10px",
        background=rx.cond(is_active, ACTIVE_BG, "transparent"),
        display="flex", align_items="center", justify_content="center",
        margin_x="auto",
        _hover={"background": HOVER_BG, "cursor": "pointer"},
        transition="background 0.15s",
    )

    expanded_item = rx.hstack(
        rx.box(icon_el, width="24px", flex_shrink="0",
               display="flex", align_items="center", justify_content="center"),
        rx.text(label, font_size="0.875rem",
                font_weight=rx.cond(is_active, "600", "400"),
                color=rx.cond(is_active, TEXT, MUTED)),
        spacing="3", align="center",
        padding="9px 12px",
        border_radius="10px",
        background=rx.cond(is_active, ACTIVE_BG, "transparent"),
        border_left=rx.cond(is_active, f"2px solid {PRIMARY}", "2px solid transparent"),
        _hover={"background": HOVER_BG, "cursor": "pointer"},
        transition="all 0.15s",
        width="100%",
    )

    inner = rx.cond(LayoutState.collapsed, collapsed_item, expanded_item) if not mobile else expanded_item

    return rx.link(
        inner,
        href=href,
        text_decoration="none",
        width="100%",
        display="block",
        on_click=LayoutState.close_mobile if mobile else None,
    )


# ── Section label ─────────────────────────────────────────────────────────────

def section_label(text: str, mobile: bool = False) -> rx.Component:
    if mobile:
        return rx.text(text, font_size="0.6rem", font_weight="700", color=MUTED,
                       padding_left="14px", padding_top="8px", letter_spacing="0.1em")
    return rx.cond(
        ~LayoutState.collapsed,
        rx.text(text, font_size="0.6rem", font_weight="700", color=MUTED,
                padding_left="14px", padding_top="8px", letter_spacing="0.1em"),
    )


# ── Nav group ─────────────────────────────────────────────────────────────────

def nav_group(*items, mobile: bool = False) -> rx.Component:
    px = "0.75rem" if mobile else rx.cond(LayoutState.collapsed, "0.6rem", "0.75rem")
    return rx.box(
        rx.vstack(*items, spacing="1", width="100%"),
        padding_x=px,
        padding_y="0.4rem",
        width="100%",
    )


# ── Sidebar content (réutilisé desktop + mobile) ──────────────────────────────

def sidebar_content(mobile: bool = False) -> rx.Component:
    return rx.vstack(

        # Logo + toggle
        rx.hstack(
            rx.cond(
                ~LayoutState.collapsed if not mobile else rx.Var.create(True),
                rx.hstack(
                    rx.box(
                        rx.text("⚡", font_size="1.1rem"),
                        background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                        border_radius="9px",
                        padding="5px 8px",
                    ),
                    rx.text("TechPilot", font_size="1rem", font_weight="700",
                            color=TEXT, letter_spacing="-0.01em"),
                    spacing="2", align="center",
                ),
            ),
            rx.spacer(),
            rx.icon_button(
                rx.icon("x" if mobile else rx.cond(LayoutState.collapsed, "panel-left-open", "panel-left-close"), size=16),
                on_click=LayoutState.close_mobile if mobile else LayoutState.toggle,
                background="transparent", color=MUTED, cursor="pointer",
                border_radius="8px", size="2",
                _hover={"background": HOVER_BG, "color": TEXT},
            ),
            width="100%", align="center",
            padding="1rem 0.75rem 1rem 1rem",
            flex_shrink="0",
        ),

        rx.divider(border_color=BORDER),

        # Navigation
        nav_group(
            section_label("NAVIGATION", mobile=mobile),
            nav_item("Dashboard",   "layout-dashboard", "/dashboard",  mobile=mobile),
            nav_item("Planning",    "calendar-days",    "/planning",   mobile=mobile),
            nav_item("Escalade N1", "git-branch",       "/escalade",   mobile=mobile),
            nav_item("Tickets",     "ticket",           "/tickets",    mobile=mobile),
            nav_item("Documents",   "folder",           "/documents",  mobile=mobile),
            mobile=mobile,
        ),
        rx.divider(border_color=BORDER, margin_y="0"),

        # Équipe
        nav_group(
            section_label("ÉQUIPE", mobile=mobile),
            nav_item("Techniciens", "users",          "/techniciens", mobile=mobile),
            nav_item("Actualités",  "newspaper",      "/actualites",  mobile=mobile),
            nav_item("Quêtes",      "trophy",         "/quetes",      mobile=mobile),
            nav_item("Feedbacks",   "message-circle", "/feedbacks",   mobile=mobile),
            mobile=mobile,
        ),

        # Admin
        rx.cond(
            AuthState.is_manager,
            rx.vstack(
                rx.divider(border_color=BORDER, margin_y="0"),
                nav_group(
                    section_label("ADMIN", mobile=mobile),
                    nav_item("Permissions",  "shield",    "/permissions",  mobile=mobile),
                    nav_item("Audit",        "file-text", "/audit",        mobile=mobile),
                    nav_item("Import Excel", "file-up",   "/import-excel", mobile=mobile),
                    mobile=mobile,
                ),
                spacing="0", width="100%",
            ),
        ),

        rx.spacer(),
        rx.divider(border_color=BORDER),

        # User section
        rx.box(
            rx.hstack(
                rx.box(
                    rx.text(AuthState.user_nom[:2].upper(), color="white",
                            font_weight="700", font_size="0.72rem"),
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    border_radius="50%", width="30px", height="30px",
                    display="flex", align_items="center", justify_content="center",
                    flex_shrink="0",
                ),
                rx.vstack(
                    rx.text(AuthState.user_nom, color=TEXT, font_size="0.8rem", font_weight="600"),
                    rx.text(AuthState.user_role, color=MUTED, font_size="0.68rem", text_transform="capitalize"),
                    spacing="0", align="start", flex="1",
                    overflow="hidden", min_width="0",
                ),
                rx.icon_button(
                    rx.icon("log-out", size=15),
                    on_click=AuthState.logout,
                    background="transparent", color=MUTED, cursor="pointer",
                    _hover={"color": "#f87171", "background": "rgba(239,68,68,0.1)"},
                    border_radius="7px", size="2",
                ),
                spacing="2", align="center", width="100%", overflow="hidden",
            ),
            padding="0.75rem",
            width="100%",
        ),

        height="100%",
        spacing="0",
        width="100%",
        overflow="hidden",
    )


# ── Sidebar desktop ───────────────────────────────────────────────────────────

def sidebar() -> rx.Component:
    return rx.box(
        sidebar_content(mobile=False),
        id="tp-sidebar",
        width=rx.cond(LayoutState.collapsed, SIDEBAR_COLLAPSED, SIDEBAR_FULL),
        min_height="100vh",
        background=SIDEBAR_BG,
        border_right=f"1px solid {BORDER}",
        position="fixed",
        left="0", top="0",
        z_index="100",
        display="flex",
        flex_direction="column",
        transition="width 0.22s cubic-bezier(0.4,0,0.2,1)",
        overflow="hidden",
        flex_shrink="0",
    )


# ── Sidebar mobile (overlay) ──────────────────────────────────────────────────

def mobile_sidebar() -> rx.Component:
    return rx.cond(
        LayoutState.mobile_open,
        rx.box(
            # Overlay sombre
            rx.box(
                position="fixed", inset="0",
                background="rgba(0,0,0,0.6)",
                z_index="150",
                on_click=LayoutState.close_mobile,
            ),
            # Panneau
            rx.box(
                sidebar_content(mobile=True),
                position="fixed",
                left="0", top="0",
                width="260px",
                height="100vh",
                background=SIDEBAR_BG,
                border_right=f"1px solid {BORDER}",
                z_index="200",
                display="flex",
                flex_direction="column",
                overflow="hidden",
            ),
        ),
    )


# ── Page layout ───────────────────────────────────────────────────────────────

def page_layout(content: rx.Component, title: str = "") -> rx.Component:
    return rx.box(

        # CSS responsive
        rx.script("""
(function() {
  var s = document.createElement('style');
  s.textContent = `
    @media (max-width: 1024px) {
      #tp-sidebar { display: none !important; }
      #tp-main   { margin-left: 0 !important; }
      #tp-ham    { display: flex !important; }
      #tp-search { display: none !important; }
    }
    #tp-ham { display: none; }
  `;
  document.head.appendChild(s);
})();
"""),

        # Sidebar desktop
        sidebar(),

        # Sidebar mobile overlay
        mobile_sidebar(),

        # Contenu principal
        rx.box(
            # Header sticky
            rx.box(
                rx.hstack(
                    # Hamburger (mobile uniquement, affiché via CSS)
                    rx.icon_button(
                        rx.icon("menu", size=18),
                        id="tp-ham",
                        on_click=LayoutState.toggle_mobile,
                        background="transparent",
                        color=MUTED,
                        cursor="pointer",
                        border_radius="8px",
                        size="2",
                        _hover={"background": HOVER_BG, "color": TEXT},
                    ),
                    rx.heading(title, size="5", color=TEXT, font_weight="700"),
                    rx.spacer(),
                    # Barre de recherche (masquée sur mobile via CSS)
                    rx.box(
                        rx.icon("search", size=14, color=MUTED,
                                position="absolute", left="10px",
                                top="50%", transform="translateY(-50%)"),
                        rx.input(
                            placeholder="Recherche dans la matrice…",
                            on_change=EscaladeState.set_search,
                            on_key_down=LayoutState.search_key,
                            background="rgba(255,255,255,0.05)",
                            border=f"1px solid {BORDER}",
                            color=TEXT,
                            border_radius="8px",
                            padding_left="32px",
                            padding_right="10px",
                            padding_y="7px",
                            font_size="0.82rem",
                            width="240px",
                            _focus={"border_color": PRIMARY, "outline": "none",
                                    "background": "rgba(99,102,241,0.07)"},
                            _placeholder={"color": MUTED},
                        ),
                        id="tp-search",
                        position="relative",
                    ),
                    # Cloche notifications
                    rx.box(
                        rx.box(
                            rx.icon("bell", size=17,
                                    color=rx.cond(NotificationState.count > 0, PRIMARY, MUTED)),
                            rx.cond(
                                NotificationState.count > 0,
                                rx.box(
                                    rx.text(
                                        rx.cond(
                                            NotificationState.count > 9,
                                            "9+",
                                            NotificationState.count.to_string(),
                                        ),
                                        color="white", font_size="0.55rem", font_weight="800",
                                        line_height="1",
                                    ),
                                    position="absolute",
                                    top="-3px", right="-3px",
                                    background="#ef4444",
                                    border_radius="50%",
                                    width="16px", height="16px",
                                    display="flex",
                                    align_items="center",
                                    justify_content="center",
                                    border=f"2px solid {SIDEBAR_BG}",
                                ),
                            ),
                            position="relative",
                            background=rx.cond(NotificationState.show_panel, HOVER_BG, "transparent"),
                            cursor="pointer",
                            padding="7px",
                            border_radius="8px",
                            _hover={"background": HOVER_BG},
                            on_click=NotificationState.toggle_panel,
                            transition="background 0.15s",
                        ),
                        rx.cond(NotificationState.show_panel, notification_panel()),
                        position="relative",
                    ),
                    spacing="3",
                    align="center",
                    padding="0.75rem 1.5rem",
                ),
                background=SIDEBAR_BG,
                border_bottom=f"1px solid {BORDER}",
                position="sticky",
                top="0",
                z_index="50",
            ),
            # Contenu page
            rx.box(content, padding="1.5rem", min_height="calc(100vh - 53px)"),

            id="tp-main",
            margin_left=rx.cond(LayoutState.collapsed, SIDEBAR_COLLAPSED, SIDEBAR_FULL),
            background=BG,
            min_height="100vh",
            transition="margin-left 0.22s cubic-bezier(0.4,0,0.2,1)",
        ),

        on_mount=[AuthState.check_auth, NotificationState.load],
    )
