import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
from techpilot.state.models import TechnicienItem
import uuid

TEXT = "#f1f5f9"; MUTED = "#94a3b8"; CARD_BG = "#111524"; BORDER = "#1c2138"; PRIMARY = "#6366f1"

COLORS = ["#6366f1","#22c55e","#f59e0b","#ef4444","#06b6d4","#8b5cf6","#ec4899"]


class TechniciensState(rx.State):
    technicians: list[TechnicienItem] = []
    show_form: bool = False
    edit_id: str = ""
    form: dict = {"nom": "", "matricule": "", "email": "", "color": "#6366f1"}

    def load(self):
        self.technicians = [
            TechnicienItem(
                id=str(t.get("id") or ""),
                nom=t.get("nom") or "",
                matricule=str(t.get("matricule") or ""),
                email=t.get("email") or "",
                color=t.get("color") or "",
                active=bool(t.get("active", True)),
            )
            for t in load_db()["technicians"]
        ]

    def open_create(self):
        self.edit_id = ""
        self.form = {"nom": "", "matricule": "", "email": "", "color": PRIMARY}
        self.show_form = True

    def open_edit(self, tech_id: str):
        db = load_db()
        tech = next((t for t in db["technicians"] if str(t.get("id")) == tech_id), None)
        if tech:
            self.edit_id = tech_id
            self.form = {
                "nom": tech.get("nom", ""),
                "matricule": tech.get("matricule", ""),
                "email": tech.get("email", ""),
                "color": tech.get("color", PRIMARY),
            }
            self.show_form = True

    def close(self):
        self.show_form = False

    def set_field(self, f: str, v: str):
        self.form = {**self.form, f: v}

    def save(self):
        db = load_db()
        if self.edit_id:
            idx = next((i for i, t in enumerate(db["technicians"]) if str(t.get("id")) == self.edit_id), -1)
            if idx != -1:
                db["technicians"][idx] = {**db["technicians"][idx], **self.form}
        else:
            db["technicians"].append({"id": str(uuid.uuid4()), **self.form, "active": True, "permissions": {}})
        save_db(db)
        self.show_form = False
        self.load()

    def toggle_active(self, tid: str):
        db = load_db()
        for t in db["technicians"]:
            if str(t.get("id")) == tid:
                t["active"] = not t.get("active", True)
        save_db(db)
        self.load()


def tech_card(tech: TechnicienItem) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.text(tech["nom"][:2].upper(), color="white", font_weight="700"),
                    background=rx.cond(tech["color"], tech["color"], PRIMARY),
                    border_radius="50%", width="42px", height="42px",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.spacer(),
                rx.cond(
                    tech["active"],
                    rx.badge("Actif", color_scheme="green", variant="soft", radius="full"),
                    rx.badge("Inactif", color_scheme="gray", variant="soft", radius="full"),
                ),
            ),
            rx.text(tech["nom"], color=TEXT, font_weight="600", font_size="1rem"),
            rx.text("#" + tech["matricule"], color=MUTED, font_size="0.8rem"),
            rx.text(tech["email"], color=MUTED, font_size="0.78rem"),
            rx.hstack(
                rx.button(
                    "Modifier",
                    on_click=TechniciensState.open_edit(tech["id"]),
                    background="rgba(99,102,241,0.1)", color=PRIMARY,
                    border=f"1px solid rgba(99,102,241,0.3)", border_radius="6px",
                    padding="5px 12px", font_size="0.78rem", cursor="pointer",
                ),
                rx.button(
                    rx.cond(tech["active"], "Désactiver", "Activer"),
                    on_click=TechniciensState.toggle_active(tech["id"]),
                    background="transparent", color=MUTED,
                    border=f"1px solid {BORDER}", border_radius="6px",
                    padding="5px 12px", font_size="0.78rem", cursor="pointer",
                ),
                spacing="2",
            ),
            spacing="2", align="start", width="100%",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="14px",
        padding="1.2rem",
        _hover={"border_color": rx.cond(tech["color"], tech["color"], PRIMARY)},
        transition="border-color 0.2s",
    )


def techniciens_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(TechniciensState.technicians.length().to_string() + " techniciens", color=MUTED, font_size="0.85rem"),
            rx.spacer(),
            rx.button(rx.icon("plus", size=16), "Ajouter", on_click=TechniciensState.open_create, background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)", color="white", border_radius="8px", padding="8px 16px", font_size="0.85rem", cursor="pointer", spacing="2"),
            width="100%", align="center",
        ),
        rx.grid(rx.foreach(TechniciensState.technicians, tech_card), columns="3", spacing="4", width="100%"),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(rx.text(rx.cond(TechniciensState.edit_id != "", "Modifier le technicien", "Nouveau technicien"), color=TEXT, font_weight="700")),
                rx.vstack(
                    rx.input(placeholder="Nom *", value=TechniciensState.form["nom"], on_change=lambda v: TechniciensState.set_field("nom", v), background="#1c2138", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px", width="100%"),
                    rx.input(placeholder="Matricule", value=TechniciensState.form["matricule"], on_change=lambda v: TechniciensState.set_field("matricule", v), background="#1c2138", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px", width="100%"),
                    rx.input(placeholder="Email", value=TechniciensState.form["email"], on_change=lambda v: TechniciensState.set_field("email", v), background="#1c2138", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px", width="100%"),
                    rx.hstack(
                        rx.button("Annuler", on_click=TechniciensState.close, background="transparent", color=MUTED, border=f"1px solid {BORDER}", border_radius="8px", cursor="pointer"),
                        rx.button("Enregistrer", on_click=TechniciensState.save, background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)", color="white", border_radius="8px", cursor="pointer"),
                        spacing="3", justify="end", width="100%",
                    ),
                    spacing="3", width="100%",
                ),
                background="#111524", border=f"1px solid {BORDER}", border_radius="16px", padding="1.5rem", max_width="400px",
            ),
            open=TechniciensState.show_form,
        ),
        spacing="4", width="100%", on_mount=TechniciensState.load,
    )


def techniciens_page() -> rx.Component:
    return page_layout(techniciens_content(), "Techniciens")
