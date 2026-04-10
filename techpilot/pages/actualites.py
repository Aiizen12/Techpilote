import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
from techpilot.state.auth import AuthState
import uuid
from datetime import datetime

TEXT = "#e2e8f0"; MUTED = "#64748b"; CARD_BG = "#151728"; BORDER = "#1e2235"; PRIMARY = "#6366f1"
TYPES = ["info", "success", "warning", "alerte"]
TYPE_COLORS = {"info": "indigo", "success": "green", "warning": "amber", "alerte": "red"}


class ActualitesState(rx.State):
    actualites: list[dict] = []
    show_form: bool = False
    form: dict = {}

    def load(self):
        db = load_db()
        items = db.get("actualites") or []
        items.sort(key=lambda a: (not a.get("epingle", False), -(datetime.fromisoformat(a["date_creation"]).timestamp() if a.get("date_creation") else 0)))
        self.actualites = items

    def open_form(self):
        self.form = {"titre": "", "contenu": "", "type": "info", "epingle": False}
        self.show_form = True

    def close_form(self):
        self.show_form = False

    def set_field(self, f: str, v):
        self.form = {**self.form, f: v}

    def create(self):
        if not self.form.get("titre"):
            return
        db = load_db()
        if "actualites" not in db:
            db["actualites"] = []
        db["actualites"].append({
            "id": str(uuid.uuid4()),
            **self.form,
            "auteur_id": AuthState.user_id,
            "auteur_nom": AuthState.user_nom,
            "date_creation": datetime.utcnow().isoformat(),
        })
        save_db(db)
        self.show_form = False
        self.load()

    def toggle_epingle(self, aid: str):
        db = load_db()
        for a in db.get("actualites") or []:
            if a.get("id") == aid:
                a["epingle"] = not a.get("epingle", False)
        save_db(db)
        self.load()

    def delete(self, aid: str):
        db = load_db()
        db["actualites"] = [a for a in (db.get("actualites") or []) if a.get("id") != aid]
        save_db(db)
        self.load()


_BORDER_COLORS = {"indigo": PRIMARY, "green": "#22c55e", "amber": "#f59e0b", "red": "#ef4444"}


def actu_card(a: dict) -> rx.Component:
    color_scheme = TYPE_COLORS.get(a.get("type", "info"), "indigo")
    border_color = _BORDER_COLORS.get(color_scheme, PRIMARY)
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.badge(a.get("type", "info"), color_scheme=color_scheme, variant="soft", radius="full"),
                    rx.cond(a.get("epingle", False), rx.badge("📌 Épinglé", color_scheme="amber", variant="soft", radius="full")),
                    rx.spacer(),
                    rx.text((a.get("date_creation") or "")[:10], color=MUTED, font_size="0.75rem"),
                    spacing="2", align="center", width="100%",
                ),
                rx.text(a.get("titre", ""), color=TEXT, font_weight="600", font_size="0.95rem"),
                rx.text(a.get("contenu", ""), color=MUTED, font_size="0.85rem"),
                rx.text(f"Par {a.get('auteur_nom', '')}", color=MUTED, font_size="0.75rem"),
                spacing="2", align="start", width="100%",
            ),
            rx.vstack(
                rx.cond(
                    AuthState.is_manager,
                    rx.icon_button(
                        rx.icon("pin", size=14),
                        on_click=ActualitesState.toggle_epingle(a.get("id", "")),
                        background="rgba(251,191,36,0.1)", color="#fbbf24",
                        border_radius="6px", size="1", cursor="pointer",
                    ),
                ),
                rx.icon_button(
                    rx.icon("trash-2", size=14),
                    on_click=ActualitesState.delete(a.get("id", "")),
                    background="rgba(239,68,68,0.1)", color="#ef4444",
                    border_radius="6px", size="1", cursor="pointer",
                ),
                spacing="2",
            ),
            spacing="3", align="start", width="100%",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_left=f"3px solid {border_color}",
        border_radius="12px",
        padding="1rem 1.2rem",
    )


def actualites_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=16), "Nouvelle actualité",
                on_click=ActualitesState.open_form,
                background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                color="white", border_radius="8px", padding="8px 16px",
                font_size="0.85rem", cursor="pointer", spacing="2",
            ),
            width="100%", align="center",
        ),
        rx.vstack(rx.foreach(ActualitesState.actualites, actu_card), spacing="3", width="100%"),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(rx.text("Nouvelle actualité", color=TEXT, font_weight="700")),
                rx.vstack(
                    rx.input(placeholder="Titre *", value=ActualitesState.form.get("titre", ""), on_change=lambda v: ActualitesState.set_field("titre", v), background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px", width="100%"),
                    rx.text_area(placeholder="Contenu", value=ActualitesState.form.get("contenu", ""), on_change=lambda v: ActualitesState.set_field("contenu", v), background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px", width="100%"),
                    rx.select(TYPES, value=ActualitesState.form.get("type", "info"), on_change=lambda v: ActualitesState.set_field("type", v), background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px"),
                    rx.hstack(
                        rx.button("Annuler", on_click=ActualitesState.close_form, background="transparent", color=MUTED, border=f"1px solid {BORDER}", border_radius="8px", cursor="pointer"),
                        rx.button("Publier", on_click=ActualitesState.create, background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)", color="white", border_radius="8px", cursor="pointer"),
                        spacing="3", justify="end", width="100%",
                    ),
                    spacing="3", width="100%",
                ),
                background="#151728", border=f"1px solid {BORDER}", border_radius="16px", padding="1.5rem", max_width="480px",
            ),
            open=ActualitesState.show_form,
        ),
        spacing="4", width="100%", on_mount=ActualitesState.load,
    )


def actualites_page() -> rx.Component:
    return page_layout(actualites_content(), "Actualités")
