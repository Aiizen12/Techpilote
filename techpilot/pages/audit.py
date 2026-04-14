import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db
from techpilot.state.models import LogEntry

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
CARD_BG = "#111524"
BORDER  = "#1c2138"
PRIMARY = "#6366f1"

ACTION_COLORS = {
    "CREATE":     "green",
    "UPDATE":     "amber",
    "DELETE":     "red",
    "LOGIN":      "blue",
    "LOGIN_FAIL": "red",
    "LOGOUT":     "gray",
}

ACTION_LABELS = {
    "CREATE":     "Créé",
    "UPDATE":     "Modifié",
    "DELETE":     "Supprimé",
    "LOGIN":      "Connexion",
    "LOGIN_FAIL": "Échec login",
    "LOGOUT":     "Déconnexion",
}


class AuditState(rx.State):
    logs: list[LogEntry] = []
    filter_action: str = ""
    filter_user: str = ""
    search: str = ""

    # Stats
    total_logs: int = 0
    count_login: int = 0
    count_errors: int = 0
    count_changes: int = 0

    def load(self):
        raw = list(reversed(load_db().get("audit_log") or []))
        self.total_logs   = len(raw)
        self.count_login  = sum(1 for x in raw if x.get("action") == "LOGIN")
        self.count_errors = sum(1 for x in raw if x.get("action") == "LOGIN_FAIL")
        self.count_changes = sum(1 for x in raw if x.get("action") in ("CREATE", "UPDATE", "DELETE"))
        self._apply_filters(raw)

    def _apply_filters(self, raw: list):
        results = raw
        if self.filter_action:
            results = [x for x in results if x.get("action") == self.filter_action]
        if self.filter_user:
            results = [x for x in results if self.filter_user.lower() in (x.get("user_nom") or "").lower()]
        if self.search:
            q = self.search.lower()
            results = [
                x for x in results
                if q in (x.get("detail") or "").lower()
                or q in (x.get("entity") or "").lower()
                or q in (x.get("user_nom") or "").lower()
            ]
        self.logs = [
            LogEntry(
                timestamp=item.get("timestamp") or "",
                user_nom=item.get("user_nom") or "",
                action=item.get("action") or "",
                entity=item.get("entity") or "",
                detail=item.get("detail") or "",
            )
            for item in results[:200]
        ]

    def set_filter_action(self, val: str):
        self.filter_action = val
        self.load()

    def set_filter_user(self, val: str):
        self.filter_user = val
        raw = list(reversed(load_db().get("audit_log") or []))
        self._apply_filters(raw)

    def set_search(self, val: str):
        self.search = val
        raw = list(reversed(load_db().get("audit_log") or []))
        self._apply_filters(raw)

    def clear_filters(self):
        self.filter_action = ""
        self.filter_user = ""
        self.search = ""
        self.load()


def _action_color(action) -> rx.Var:
    return rx.match(
        action,
        ("CREATE",     "green"),
        ("UPDATE",     "amber"),
        ("DELETE",     "red"),
        ("LOGIN",      "blue"),
        ("LOGIN_FAIL", "red"),
        ("LOGOUT",     "gray"),
        "gray",
    )


def _action_label(action) -> rx.Var:
    return rx.match(
        action,
        ("CREATE",     "Créé"),
        ("UPDATE",     "Modifié"),
        ("DELETE",     "Supprimé"),
        ("LOGIN",      "Connexion"),
        ("LOGIN_FAIL", "Échec login"),
        ("LOGOUT",     "Déconnexion"),
        action,
    )


def _entity_icon(entity) -> rx.Var:
    return rx.match(
        entity,
        ("technicien", "users"),
        ("ticket",     "shield-alert"),
        ("auth",       "lock"),
        "file-text",
    )


def _kpi(label: str, value, color: str, icon: str) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(
                rx.icon(icon, size=18, color=color),
                background=f"rgba({_hex_to_rgb(color)}, 0.12)",
                border_radius="10px",
                padding="8px",
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.vstack(
                rx.text(label, color=MUTED, font_size="0.65rem", font_weight="700", letter_spacing="0.1em"),
                rx.text(value, color=color, font_size="1.8rem", font_weight="800", line_height="1"),
                spacing="1",
                align="start",
            ),
            spacing="3",
            align="center",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_left=f"3px solid {color}",
        border_radius="12px",
        padding="1rem 1.25rem",
        flex="1",
    )


def _hex_to_rgb(hex_color: str) -> str:
    """Convertit #rrggbb → 'r, g, b' pour rgba()."""
    mapping = {
        "#6366f1": "99, 102, 241",
        "#22c55e": "34, 197, 94",
        "#ef4444": "239, 68, 68",
        "#f59e0b": "245, 158, 11",
    }
    return mapping.get(hex_color, "99, 102, 241")


def _filter_btn(label: str, val: str, current) -> rx.Component:
    is_active = current == val
    return rx.box(
        rx.text(label, font_size="0.78rem", font_weight=rx.cond(is_active, "600", "400"),
                color=rx.cond(is_active, TEXT, MUTED)),
        padding="5px 12px",
        border_radius="6px",
        background=rx.cond(is_active, "rgba(99,102,241,0.2)", "transparent"),
        border=rx.cond(is_active, f"1px solid rgba(99,102,241,0.5)", f"1px solid {BORDER}"),
        cursor="pointer",
        on_click=AuditState.set_filter_action(val),
        transition="all 0.15s",
    )


def log_row(log: LogEntry) -> rx.Component:
    ts_short = rx.cond(log["timestamp"] != "", log["timestamp"][:16].replace("T", " "), "—")
    return rx.table.row(
        rx.table.cell(
            rx.text(ts_short, color=MUTED, font_size="0.75rem", font_family="monospace"),
            padding="8px 12px",
        ),
        rx.table.cell(
            rx.hstack(
                rx.box(
                    rx.icon(_entity_icon(log["entity"]), size=12, color=MUTED),
                    width="22px", height="22px",
                    background="rgba(255,255,255,0.05)",
                    border_radius="5px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.text(log["user_nom"], color=TEXT, font_size="0.82rem"),
                spacing="2",
                align="center",
            ),
            padding="8px 12px",
        ),
        rx.table.cell(
            rx.badge(
                _action_label(log["action"]),
                color_scheme=_action_color(log["action"]),
                variant="soft",
                radius="full",
                font_size="0.7rem",
            ),
            padding="8px 12px",
        ),
        rx.table.cell(
            rx.text(log["entity"], color=MUTED, font_size="0.75rem", text_transform="capitalize"),
            padding="8px 12px",
        ),
        rx.table.cell(
            rx.text(log["detail"], color=TEXT, font_size="0.8rem"),
            padding="8px 12px",
        ),
        _hover={"background": "rgba(255,255,255,0.02)"},
    )


def audit_content() -> rx.Component:
    return rx.vstack(

        # ── Header ────────────────────────────────────────────────────────────
        rx.hstack(
            rx.hstack(
                rx.box(
                    rx.icon("file-text", size=20, color="white"),
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    border_radius="10px",
                    padding="8px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.vstack(
                    rx.text("Journal d'activité", color=TEXT, font_size="1.1rem", font_weight="700"),
                    rx.text("Historique de toutes les actions effectuées", color=MUTED, font_size="0.78rem"),
                    spacing="0",
                    align="start",
                ),
                spacing="3",
                align="center",
            ),
            rx.spacer(),
            rx.text(
                AuditState.total_logs.to_string() + " entrées",
                color=MUTED,
                font_size="0.82rem",
            ),
            width="100%",
            align="center",
        ),

        # ── KPI ───────────────────────────────────────────────────────────────
        rx.hstack(
            _kpi("CONNEXIONS",   AuditState.count_login,   "#6366f1", "log-in"),
            _kpi("MODIFICATIONS", AuditState.count_changes, "#f59e0b", "pencil"),
            _kpi("ÉCHECS LOGIN", AuditState.count_errors,  "#ef4444", "shield-x"),
            spacing="4",
            width="100%",
        ),

        # ── Filtres ───────────────────────────────────────────────────────────
        rx.box(
            rx.hstack(
                # Filtre action
                rx.hstack(
                    _filter_btn("Tous",        "",            AuditState.filter_action),
                    _filter_btn("Connexion",   "LOGIN",       AuditState.filter_action),
                    _filter_btn("Créé",        "CREATE",      AuditState.filter_action),
                    _filter_btn("Modifié",     "UPDATE",      AuditState.filter_action),
                    _filter_btn("Supprimé",    "DELETE",      AuditState.filter_action),
                    _filter_btn("Échec login", "LOGIN_FAIL",  AuditState.filter_action),
                    spacing="2",
                    flex_wrap="wrap",
                ),
                rx.spacer(),
                # Recherche
                rx.box(
                    rx.icon("search", size=13, color=MUTED,
                            position="absolute", left="9px",
                            top="50%", transform="translateY(-50%)"),
                    rx.input(
                        placeholder="Rechercher…",
                        value=AuditState.search,
                        on_change=AuditState.set_search,
                        background="#1c2138",
                        color=TEXT,
                        border=f"1px solid {BORDER}",
                        border_radius="8px",
                        padding_left="30px",
                        font_size="0.8rem",
                        width="200px",
                        _focus={"border_color": PRIMARY, "outline": "none"},
                        _placeholder={"color": MUTED},
                    ),
                    position="relative",
                ),
                # Filtre utilisateur
                rx.input(
                    placeholder="Utilisateur…",
                    value=AuditState.filter_user,
                    on_change=AuditState.set_filter_user,
                    background="#1c2138",
                    color=TEXT,
                    border=f"1px solid {BORDER}",
                    border_radius="8px",
                    font_size="0.8rem",
                    width="150px",
                    _focus={"border_color": PRIMARY, "outline": "none"},
                    _placeholder={"color": MUTED},
                ),
                rx.cond(
                    (AuditState.filter_action != "") | (AuditState.filter_user != "") | (AuditState.search != ""),
                    rx.button(
                        rx.icon("x", size=13),
                        "Effacer",
                        on_click=AuditState.clear_filters,
                        background="transparent",
                        color=MUTED,
                        border=f"1px solid {BORDER}",
                        border_radius="6px",
                        font_size="0.78rem",
                        cursor="pointer",
                        spacing="1",
                    ),
                ),
                spacing="3",
                align="center",
                width="100%",
                flex_wrap="wrap",
            ),
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="12px",
            padding="0.9rem 1.2rem",
            width="100%",
        ),

        # ── Tableau ───────────────────────────────────────────────────────────
        rx.cond(
            AuditState.logs.length() == 0,
            rx.box(
                rx.vstack(
                    rx.icon("file-search", size=40, color=MUTED),
                    rx.text("Aucune entrée", color=MUTED, font_size="0.9rem"),
                    rx.text("Les actions apparaîtront ici dès qu'elles seront effectuées.",
                            color=MUTED, font_size="0.78rem"),
                    spacing="3",
                    align="center",
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="14px",
                padding="4rem",
                display="flex",
                justify_content="center",
                width="100%",
            ),
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Horodatage",  color=MUTED, font_size="0.72rem", padding="10px 12px"),
                            rx.table.column_header_cell("Utilisateur", color=MUTED, font_size="0.72rem", padding="10px 12px"),
                            rx.table.column_header_cell("Action",      color=MUTED, font_size="0.72rem", padding="10px 12px"),
                            rx.table.column_header_cell("Entité",      color=MUTED, font_size="0.72rem", padding="10px 12px"),
                            rx.table.column_header_cell("Détail",      color=MUTED, font_size="0.72rem", padding="10px 12px"),
                        ),
                        background="#0d1021",
                    ),
                    rx.table.body(rx.foreach(AuditState.logs, log_row)),
                    width="100%",
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="14px",
                overflow="auto",
                width="100%",
            ),
        ),

        spacing="4",
        width="100%",
        on_mount=AuditState.load,
    )


def audit_page() -> rx.Component:
    return page_layout(audit_content(), "Activité")
