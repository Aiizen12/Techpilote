import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
from techpilot.state.auth import AuthState, DEFAULT_PERMS
from techpilot.state.models import PermRow
from techpilot.db.activity import log_activity

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
CARD_BG = "#111524"
BORDER  = "#1c2138"
PRIMARY = "#6366f1"

PERM_META = {
    "planning_edit":      {"label": "Planning",       "desc": "Modifier le planning et les astreintes",  "icon": "calendar-days", "color": "#06b6d4"},
    "matrix_edit":        {"label": "Matrice",         "desc": "Consulter et modifier la matrice d'escalade", "icon": "git-branch",   "color": "#8b5cf6"},
    "technicians_edit":   {"label": "Techniciens",     "desc": "Créer, modifier, activer les techniciens", "icon": "users",         "color": "#22c55e"},
    "tickets_manage":     {"label": "Tickets",         "desc": "Créer et gérer les incidents",            "icon": "shield-alert",  "color": "#ef4444"},
    "import_excel":       {"label": "Import Excel",    "desc": "Importer des fichiers Excel",             "icon": "file-up",       "color": "#f59e0b"},
    "permissions_manage": {"label": "Permissions",     "desc": "Gérer les droits des techniciens",        "icon": "shield",        "color": "#6366f1"},
    "escalade_proc_edit": {"label": "Procédures N1",   "desc": "Ajouter / modifier les procédures N1 sur les fiches escalade", "icon": "pencil", "color": "#22c55e"},
    "doc_edit":           {"label": "Suivi de doc",    "desc": "Modifier la feuille Amélioration Desk", "icon": "notebook-pen", "color": "#f97316"},
}


class PermissionsState(rx.State):
    rows: list[PermRow] = []

    def load(self):
        db = load_db()
        self.rows = [
            PermRow(
                id=str(t.get("id") or ""),
                nom=t.get("nom") or "?",
                **{k: ({**DEFAULT_PERMS, **(t.get("permissions") or {})}).get(k, False) for k in DEFAULT_PERMS.keys()},
            )
            for t in db["technicians"]
        ]

    async def toggle_perm(self, tech_id: str, perm_key: str):
        db  = load_db()
        idx = next((i for i, t in enumerate(db["technicians"]) if str(t.get("id")) == tech_id), -1)
        if idx == -1:
            return
        current = {**DEFAULT_PERMS, **(db["technicians"][idx].get("permissions") or {})}
        current[perm_key] = not current[perm_key]
        db["technicians"][idx]["permissions"] = current
        save_db(db)

        nom   = db["technicians"][idx].get("nom", tech_id)
        label = PERM_META.get(perm_key, {}).get("label", perm_key)
        state = "accordé" if current[perm_key] else "retiré"
        auth  = await self.get_state(AuthState)
        log_activity(auth.user_nom, "UPDATE", "permissions", f"{nom} — {label} {state}")

        yield rx.toast.success(f"{label} {state} pour {nom}.")
        self.load()

    async def grant_all(self, tech_id: str):
        db  = load_db()
        idx = next((i for i, t in enumerate(db["technicians"]) if str(t.get("id")) == tech_id), -1)
        if idx == -1:
            return
        db["technicians"][idx]["permissions"] = {k: True for k in DEFAULT_PERMS}
        save_db(db)
        nom  = db["technicians"][idx].get("nom", tech_id)
        auth = await self.get_state(AuthState)
        log_activity(auth.user_nom, "UPDATE", "permissions", f"{nom} — tous les droits accordés")
        yield rx.toast.success(f"Tous les droits accordés à {nom}.")
        self.load()

    async def revoke_all(self, tech_id: str):
        db  = load_db()
        idx = next((i for i, t in enumerate(db["technicians"]) if str(t.get("id")) == tech_id), -1)
        if idx == -1:
            return
        db["technicians"][idx]["permissions"] = {k: False for k in DEFAULT_PERMS}
        save_db(db)
        nom  = db["technicians"][idx].get("nom", tech_id)
        auth = await self.get_state(AuthState)
        log_activity(auth.user_nom, "UPDATE", "permissions", f"{nom} — tous les droits retirés")
        yield rx.toast.warning(f"Tous les droits retirés pour {nom}.")
        self.load()


# ── Composants ────────────────────────────────────────────────────────────────

def _perm_header() -> rx.Component:
    """Ligne d'en-tête avec icônes et descriptions."""
    return rx.hstack(
        # Colonne technicien
        rx.box(width="160px", flex_shrink="0"),
        # Colonnes permissions
        *[
            rx.vstack(
                rx.box(
                    rx.icon(meta["icon"], size=14, color=meta["color"]),
                    background=f"rgba(99,102,241,0.08)",
                    border_radius="7px",
                    padding="6px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.text(meta["label"], color=MUTED, font_size="0.7rem", font_weight="600", text_align="center"),
                spacing="1",
                align="center",
                width="90px",
                flex_shrink="0",
            )
            for meta in PERM_META.values()
        ],
        # Colonne actions
        rx.box(width="120px", flex_shrink="0"),
        spacing="0",
        align="center",
        padding="0.75rem 1rem",
        background="#0d1021",
        border_bottom=f"1px solid {BORDER}",
        width="100%",
        overflow_x="auto",
    )


def _perm_switch(row: PermRow, key: str, color: str) -> rx.Component:
    return rx.box(
        rx.switch(
            checked=row[key],
            on_change=PermissionsState.toggle_perm(row["id"], key),
            color_scheme="indigo",
        ),
        width="90px",
        flex_shrink="0",
        display="flex",
        align_items="center",
        justify_content="center",
    )


def perm_row(row: PermRow) -> rx.Component:
    return rx.hstack(
        # Avatar + nom
        rx.hstack(
            rx.box(
                rx.text(row["nom"][:2].upper(), color="white", font_size="0.72rem", font_weight="700"),
                background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                border_radius="50%",
                width="32px", height="32px",
                display="flex", align_items="center", justify_content="center",
                flex_shrink="0",
            ),
            rx.text(row["nom"], color=TEXT, font_size="0.875rem", font_weight="500", white_space="nowrap"),
            spacing="2",
            align="center",
            width="160px",
            flex_shrink="0",
        ),
        # Switches
        *[
            _perm_switch(row, key, meta["color"])
            for key, meta in PERM_META.items()
        ],
        # Actions rapides
        rx.hstack(
            rx.button(
                "Tout",
                on_click=PermissionsState.grant_all(row["id"]),
                background="rgba(34,197,94,0.1)",
                color="#22c55e",
                border=f"1px solid rgba(34,197,94,0.25)",
                border_radius="6px",
                font_size="0.7rem",
                font_weight="600",
                padding="4px 8px",
                cursor="pointer",
                _hover={"background": "rgba(34,197,94,0.2)"},
            ),
            rx.button(
                "Aucun",
                on_click=PermissionsState.revoke_all(row["id"]),
                background="rgba(239,68,68,0.08)",
                color="#ef4444",
                border=f"1px solid rgba(239,68,68,0.2)",
                border_radius="6px",
                font_size="0.7rem",
                font_weight="600",
                padding="4px 8px",
                cursor="pointer",
                _hover={"background": "rgba(239,68,68,0.18)"},
            ),
            spacing="2",
        ),
        spacing="0",
        align="center",
        padding="0.85rem 1rem",
        border_bottom=f"1px solid {BORDER}",
        width="100%",
        overflow_x="auto",
        _hover={"background": "rgba(255,255,255,0.015)"},
        transition="background 0.15s",
    )


def permissions_content() -> rx.Component:
    return rx.vstack(

        # ── Header ────────────────────────────────────────────────────────────
        rx.hstack(
            rx.hstack(
                rx.box(
                    rx.icon("shield", size=20, color="white"),
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    border_radius="10px",
                    padding="8px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.vstack(
                    rx.text("Gestion des permissions", color=TEXT, font_size="1.1rem", font_weight="700"),
                    rx.text("Définissez les droits d'accès de chaque technicien", color=MUTED, font_size="0.78rem"),
                    spacing="0", align="start",
                ),
                spacing="3", align="center",
            ),
            width="100%",
            align="center",
        ),

        # ── Légende ───────────────────────────────────────────────────────────
        rx.hstack(
            *[
                rx.hstack(
                    rx.box(
                        rx.icon(meta["icon"], size=12, color=meta["color"]),
                        background=f"rgba(99,102,241,0.07)",
                        border_radius="5px",
                        padding="4px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                    rx.vstack(
                        rx.text(meta["label"], color=TEXT, font_size="0.75rem", font_weight="600"),
                        rx.text(meta["desc"], color=MUTED, font_size="0.68rem"),
                        spacing="0", align="start",
                    ),
                    spacing="2", align="center",
                    background=CARD_BG,
                    border=f"1px solid {BORDER}",
                    border_left=f"3px solid {meta['color']}",
                    border_radius="8px",
                    padding="0.5rem 0.75rem",
                    flex="1",
                    min_width="140px",
                )
                for meta in PERM_META.values()
            ],
            spacing="2",
            width="100%",
            wrap="wrap",
        ),

        # ── Tableau ───────────────────────────────────────────────────────────
        rx.box(
            _perm_header(),
            rx.vstack(
                rx.foreach(PermissionsState.rows, perm_row),
                spacing="0",
                width="100%",
            ),
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="14px",
            overflow="auto",
            width="100%",
        ),

        spacing="5",
        width="100%",
        on_mount=PermissionsState.load,
    )


def permissions_page() -> rx.Component:
    return page_layout(permissions_content(), "Permissions")
