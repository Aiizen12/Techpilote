import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
from techpilot.state.models import TechnicienItem
from techpilot.state.auth import AuthState
from techpilot.db.activity import log_activity
import uuid
import secrets
import hashlib

TEXT = "#f1f5f9"; MUTED = "#94a3b8"; CARD_BG = "#111524"; BORDER = "#1c2138"; PRIMARY = "#6366f1"

COLORS = ["#6366f1","#22c55e","#f59e0b","#ef4444","#06b6d4","#8b5cf6","#ec4899"]


class TechniciensState(rx.State):
    technicians: list[TechnicienItem] = []
    show_form: bool = False
    edit_id: str = ""
    form: dict = {"nom": "", "matricule": "", "email": "", "color": "#6366f1", "new_password": ""}

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
        self.form = {"nom": "", "matricule": "", "email": "", "color": PRIMARY, "new_password": ""}
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
                "new_password": "",
            }
            self.show_form = True

    def close(self):
        self.show_form = False

    def set_field(self, f: str, v: str):
        self.form = {**self.form, f: v}

    async def save(self):
        auth = await self.get_state(AuthState)
        if auth.user_role != "manager" and not auth.permissions.get("technicians_edit", False):
            yield rx.toast.error("Vous n'avez pas le droit de modifier les techniciens.")
            return
        db = load_db()
        new_password = self.form.get("new_password", "").strip()
        fields = {k: v for k, v in self.form.items() if k != "new_password"}

        if self.edit_id:
            idx = next((i for i, t in enumerate(db["technicians"]) if str(t.get("id")) == self.edit_id), -1)
            if idx != -1:
                db["technicians"][idx] = {**db["technicians"][idx], **fields}
                if new_password:
                    salt = secrets.token_hex(16)
                    h = hashlib.pbkdf2_hmac("sha512", new_password.encode(), salt.encode(), 100000, dklen=64).hex()
                    db["technicians"][idx]["password_hash"] = h
                    db["technicians"][idx]["password_salt"] = salt
                log_activity(auth.user_nom, "UPDATE", "technicien", f"Modifié: {fields.get('nom', self.edit_id)}")
        else:
            new_tech = {"id": str(uuid.uuid4()), **fields, "active": True, "permissions": {}}
            if new_password:
                salt = secrets.token_hex(16)
                h = hashlib.pbkdf2_hmac("sha512", new_password.encode(), salt.encode(), 100000, dklen=64).hex()
                new_tech["password_hash"] = h
                new_tech["password_salt"] = salt
            db["technicians"].append(new_tech)
            log_activity(auth.user_nom, "CREATE", "technicien", f"Créé: {fields.get('nom', '')}")

        save_db(db)
        self.show_form = False
        self.load()
        action = "modifié" if self.edit_id else "créé"
        yield rx.toast.success(f"Technicien {action} avec succès.")

    async def delete(self, tid: str):
        auth = await self.get_state(AuthState)
        if auth.user_role != "manager" and not auth.permissions.get("technicians_edit", False):
            yield rx.toast.error("Vous n'avez pas le droit de supprimer un technicien.")
            return
        db = load_db()
        tech = next((t for t in db["technicians"] if str(t.get("id")) == tid), None)
        if tech:
            db["technicians"] = [t for t in db["technicians"] if str(t.get("id")) != tid]
            save_db(db)
            log_activity(auth.user_nom, "DELETE", "technicien", f"Supprimé: {tech.get('nom', tid)}")
            self.load()
            yield rx.toast.success(f"{tech.get('nom', '')} supprimé.")

    async def toggle_active(self, tid: str):
        auth = await self.get_state(AuthState)
        if auth.user_role != "manager" and not auth.permissions.get("technicians_edit", False):
            yield rx.toast.error("Vous n'avez pas le droit de modifier les techniciens.")
            return
        db = load_db()
        for t in db["technicians"]:
            if str(t.get("id")) == tid:
                t["active"] = not t.get("active", True)
                new_status = "activé" if t["active"] else "désactivé"
                log_activity(auth.user_nom, "UPDATE", "technicien", f"{t.get('nom', tid)} {new_status}")
                yield rx.toast.info(f"{t.get('nom', '')} {new_status}.")
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
            rx.cond(
                AuthState.is_manager | AuthState.can_edit_technicians,
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
                    rx.button(
                        rx.icon("trash-2", size=13),
                        on_click=TechniciensState.delete(tech["id"]),
                        background="transparent", color="#ef4444",
                        border="1px solid rgba(239,68,68,0.3)", border_radius="6px",
                        padding="5px 10px", font_size="0.78rem", cursor="pointer",
                        _hover={"background": "rgba(239,68,68,0.1)"},
                    ),
                    spacing="2",
                ),
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
            rx.cond(
                AuthState.is_manager | AuthState.can_edit_technicians,
                rx.button(rx.icon("plus", size=16), "Ajouter", on_click=TechniciensState.open_create, background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)", color="white", border_radius="8px", padding="8px 16px", font_size="0.85rem", cursor="pointer", spacing="2"),
            ),
            width="100%", align="center",
        ),
        rx.grid(rx.foreach(TechniciensState.technicians, tech_card), columns="3", spacing="4", width="100%"),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(rx.text(rx.cond(TechniciensState.edit_id != "", "Modifier le technicien", "Nouveau technicien"), color=TEXT, font_weight="700")),
                rx.vstack(
                    rx.input(placeholder="Nom *", value=TechniciensState.form["nom"], on_change=lambda v: TechniciensState.set_field("nom", v), background="#1c2138", style={"color": TEXT}, border=f"1px solid {BORDER}", border_radius="8px", width="100%"),
                    rx.input(placeholder="Matricule", value=TechniciensState.form["matricule"], on_change=lambda v: TechniciensState.set_field("matricule", v), background="#1c2138", style={"color": TEXT}, border=f"1px solid {BORDER}", border_radius="8px", width="100%"),
                    rx.input(placeholder="Email", value=TechniciensState.form["email"], on_change=lambda v: TechniciensState.set_field("email", v), background="#1c2138", style={"color": TEXT}, border=f"1px solid {BORDER}", border_radius="8px", width="100%"),
                    # Séparateur mot de passe
                    rx.box(
                        rx.hstack(
                            rx.divider(border_color=BORDER, flex="1"),
                            rx.text("Mot de passe", color=MUTED, font_size="0.72rem",
                                    font_weight="600", letter_spacing="0.05em", white_space="nowrap"),
                            rx.divider(border_color=BORDER, flex="1"),
                            spacing="2", align="center", width="100%",
                        ),
                    ),
                    rx.input(
                        placeholder=rx.cond(
                            TechniciensState.edit_id != "",
                            "Nouveau mot de passe (laisser vide = inchangé)",
                            "Mot de passe",
                        ),
                        value=TechniciensState.form["new_password"],
                        on_change=lambda v: TechniciensState.set_field("new_password", v),
                        type="password",
                        background="#1c2138", color=TEXT,
                        border=f"1px solid {BORDER}", border_radius="8px", width="100%",
                    ),
                    rx.cond(
                        TechniciensState.edit_id != "",
                        rx.hstack(
                            rx.icon("info", size=12, color=MUTED),
                            rx.text("Laisser vide pour conserver le mot de passe actuel",
                                    color=MUTED, font_size="0.72rem"),
                            spacing="1", align="center",
                        ),
                    ),
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
