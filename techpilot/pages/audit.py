import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db

TEXT = "#e2e8f0"; MUTED = "#64748b"; CARD_BG = "#151728"; BORDER = "#1e2235"

ACTION_COLORS = {"CREATE": "green", "UPDATE": "amber", "DELETE": "red"}


class AuditState(rx.State):
    logs: list[dict] = []

    def load(self):
        self.logs = list(reversed(load_db().get("audit_log") or []))


def log_row(log: dict) -> rx.Component:
    action = log.get("action", "")
    return rx.table.row(
        rx.table.cell(rx.text((log.get("timestamp") or "")[:16].replace("T", " "), color=MUTED, font_size="0.78rem"), padding="8px 12px"),
        rx.table.cell(rx.text(log.get("user_nom", ""), color=TEXT, font_size="0.82rem"), padding="8px 12px"),
        rx.table.cell(rx.badge(action, color_scheme=ACTION_COLORS.get(action, "gray"), variant="soft", radius="full"), padding="8px 12px"),
        rx.table.cell(rx.text(log.get("entity", ""), color=MUTED, font_size="0.78rem"), padding="8px 12px"),
        rx.table.cell(rx.text(log.get("detail", ""), color=TEXT, font_size="0.82rem"), padding="8px 12px"),
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
