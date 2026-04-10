import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db
from techpilot.state.models import LogEntry

TEXT = "#e2e8f0"; MUTED = "#64748b"; CARD_BG = "#151728"; BORDER = "#1e2235"


class AuditState(rx.State):
    logs: list[LogEntry] = []

    def load(self):
        raw = list(reversed(load_db().get("audit_log") or []))
        self.logs = [
            LogEntry(
                timestamp=item.get("timestamp") or "",
                user_nom=item.get("user_nom") or "",
                action=item.get("action") or "",
                entity=item.get("entity") or "",
                detail=item.get("detail") or "",
            )
            for item in raw
        ]


def _action_color(action) -> rx.Var:
    return rx.cond(
        action == "CREATE", "green",
        rx.cond(action == "UPDATE", "amber",
        rx.cond(action == "DELETE", "red", "gray"))
    )


def log_row(log: LogEntry) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(log["timestamp"][:16], color=MUTED, font_size="0.78rem"), padding="8px 12px"),
        rx.table.cell(rx.text(log["user_nom"], color=TEXT, font_size="0.82rem"), padding="8px 12px"),
        rx.table.cell(rx.badge(log["action"], color_scheme=_action_color(log["action"]), variant="soft", radius="full"), padding="8px 12px"),
        rx.table.cell(rx.text(log["entity"], color=MUTED, font_size="0.78rem"), padding="8px 12px"),
        rx.table.cell(rx.text(log["detail"], color=TEXT, font_size="0.82rem"), padding="8px 12px"),
        _hover={"background": "rgba(255,255,255,0.02)"},
    )


def audit_content() -> rx.Component:
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Horodatage", color=MUTED, font_size="0.75rem", padding="10px 12px"),
                    rx.table.column_header_cell("Utilisateur", color=MUTED, font_size="0.75rem", padding="10px 12px"),
                    rx.table.column_header_cell("Action", color=MUTED, font_size="0.75rem", padding="10px 12px"),
                    rx.table.column_header_cell("Entité", color=MUTED, font_size="0.75rem", padding="10px 12px"),
                    rx.table.column_header_cell("Détail", color=MUTED, font_size="0.75rem", padding="10px 12px"),
                ),
                background="#10121f",
            ),
            rx.table.body(rx.foreach(AuditState.logs, log_row)),
            width="100%",
        ),
        background=CARD_BG, border=f"1px solid {BORDER}", border_radius="14px", overflow="auto",
        on_mount=AuditState.load,
    )


def audit_page() -> rx.Component:
    return page_layout(audit_content(), "Journal d'audit")
