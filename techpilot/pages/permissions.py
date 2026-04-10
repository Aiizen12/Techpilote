import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
from techpilot.state.auth import AuthState, DEFAULT_PERMS

TEXT = "#e2e8f0"; MUTED = "#64748b"; CARD_BG = "#151728"; BORDER = "#1e2235"; PRIMARY = "#6366f1"

PERM_LABELS = {
    "planning_edit": "Modifier le planning",
    "matrix_edit": "Modifier la matrice",
    "technicians_edit": "Gérer les techniciens",
    "tickets_manage": "Gérer les tickets",
    "import_excel": "Importer Excel",
    "permissions_manage": "Gérer les permissions",
}


class PermissionsState(rx.State):
    rows: list[dict] = []

    def load(self):
        db = load_db()
        self.rows = [
            {
                "id": t.get("id"),
                "nom": t.get("nom") or t.get("name") or "?",
                "permissions": {**DEFAULT_PERMS, **(t.get("permissions") or {})},
            }
            for t in db["technicians"]
        ]

    def toggle_perm(self, tech_id: str, perm_key: str):
        db = load_db()
        idx = next((i for i, t in enumerate(db["technicians"]) if str(t.get("id")) == str(tech_id)), -1)
        if idx == -1:
            return
        current = {**DEFAULT_PERMS, **(db["technicians"][idx].get("permissions") or {})}
        current[perm_key] = not current[perm_key]
        db["technicians"][idx]["permissions"] = current
        save_db(db)
        self.load()


def perm_row(row: dict) -> rx.Component:
    perms = row.get("permissions") or {}
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.box(
                    rx.text((row.get("nom") or "?")[:2].upper(), color="white", font_size="0.7rem", font_weight="700"),
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    border_radius="50%", width="28px", height="28px",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.text(row.get("nom", ""), color=TEXT, font_size="0.875rem"),
                spacing="2", align="center",
            ),
            padding="10px 14px", white_space="nowrap",
        ),
        *[
            rx.table.cell(
                rx.switch(
                    checked=perms.get(key, False),
                    on_change=lambda v, t=str(row.get("id", "")), k=key: PermissionsState.toggle_perm(t, k),
                    color_scheme="indigo",
                ),
                padding="10px 14px", text_align="center",
            )
            for key in DEFAULT_PERMS.keys()
        ],
    )


def permissions_content() -> rx.Component:
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Technicien", color=MUTED, font_size="0.75rem", padding="10px 14px"),
                    *[
                        rx.table.column_header_cell(label, color=MUTED, font_size="0.72rem", padding="10px 14px", text_align="center")
                        for label in PERM_LABELS.values()
                    ],
                ),
                background="#10121f",
            ),
            rx.table.body(rx.foreach(PermissionsState.rows, perm_row)),
            width="100%",
        ),
        background=CARD_BG, border=f"1px solid {BORDER}", border_radius="14px", overflow="auto",
        on_mount=PermissionsState.load,
    )


def permissions_page() -> rx.Component:
    return page_layout(permissions_content(), "Permissions")
