import hashlib
import secrets
import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
from techpilot.state.auth import AuthState, _verify, _hash
from techpilot.db.activity import log_activity

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
CARD_BG = "#111524"
BORDER  = "#1c2138"
PRIMARY = "#6366f1"

COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#06b6d4", "#8b5cf6", "#ec4899"]


class ProfilState(rx.State):
    nom: str = ""
    matricule: str = ""
    email: str = ""
    color: str = "#6366f1"
    role: str = ""

    current_password: str = ""
    new_password: str = ""
    confirm_password: str = ""

    def load(self):
        auth = self.get_state_sync(AuthState) if hasattr(self, "get_state_sync") else None
        db = load_db()

        # Récupérer depuis l'état Auth (via token déjà chargé)
        # On relit le user_id depuis le token en session
        # AuthState est déjà chargé dans check_auth, on lit depuis la DB
        from techpilot.state.auth import _decode_token
        # On accède aux vars parentes via substates
        pass

    async def load_profile(self):
        auth = await self.get_state(AuthState)
        self.role = auth.user_role
        self.nom  = auth.user_nom

        if auth.user_role == "manager":
            self.matricule = "—"
            self.email     = "—"
            self.color     = PRIMARY
            return

        db = load_db()
        tech = next((t for t in db["technicians"] if str(t.get("id")) == str(auth.user_id)), None)
        if tech:
            self.nom       = tech.get("nom", "")
            self.matricule = str(tech.get("matricule", ""))
            self.email     = tech.get("email", "")
            self.color     = tech.get("color", PRIMARY)

    def set_field(self, field: str, val: str):
        setattr(self, field, val)

    def set_color(self, c: str):
        self.color = c

    async def save_info(self):
        auth = await self.get_state(AuthState)
        if auth.user_role == "manager":
            yield rx.toast.info("Le profil manager ne peut pas être modifié ici.")
            return
        db = load_db()
        idx = next((i for i, t in enumerate(db["technicians"]) if str(t.get("id")) == str(auth.user_id)), -1)
        if idx == -1:
            yield rx.toast.error("Technicien introuvable.")
            return
        db["technicians"][idx]["email"] = self.email
        db["technicians"][idx]["color"] = self.color
        save_db(db)
        log_activity(self.nom, "UPDATE", "profil", "Mise à jour email/couleur")
        yield rx.toast.success("Profil mis à jour.")

    async def change_password(self):
        if not self.current_password or not self.new_password or not self.confirm_password:
            yield rx.toast.error("Tous les champs mot de passe sont requis.")
            return
        if self.new_password != self.confirm_password:
            yield rx.toast.error("Les mots de passe ne correspondent pas.")
            return
        if len(self.new_password) < 6:
            yield rx.toast.error("Le mot de passe doit faire au moins 6 caractères.")
            return

        auth = await self.get_state(AuthState)
        db   = load_db()

        if auth.user_role == "manager":
            mgr = db.get("manager_auth") or {}
            if mgr.get("password_hash"):
                if not _verify(self.current_password, mgr["password_hash"], mgr["salt"]):
                    yield rx.toast.error("Mot de passe actuel incorrect.")
                    return
            salt = secrets.token_hex(16)
            db["manager_auth"] = {"password_hash": _hash(self.new_password, salt), "salt": salt}
        else:
            tech = next((t for t in db["technicians"] if str(t.get("id")) == str(auth.user_id)), None)
            if not tech:
                yield rx.toast.error("Technicien introuvable.")
                return
            if tech.get("password_hash"):
                if not _verify(self.current_password, tech["password_hash"], tech.get("password_salt", "")):
                    yield rx.toast.error("Mot de passe actuel incorrect.")
                    return
            idx = next(i for i, t in enumerate(db["technicians"]) if str(t.get("id")) == str(auth.user_id))
            salt = secrets.token_hex(16)
            db["technicians"][idx]["password_hash"] = _hash(self.new_password, salt)
            db["technicians"][idx]["password_salt"] = salt

        save_db(db)
        self.current_password = ""
        self.new_password     = ""
        self.confirm_password = ""
        log_activity(self.nom, "UPDATE", "profil", "Changement de mot de passe")
        yield rx.toast.success("Mot de passe modifié avec succès.")


# ── Composants ────────────────────────────────────────────────────────────────

def _section(title: str, icon: str, *children) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(
                rx.icon(icon, size=16, color=PRIMARY),
                background="rgba(99,102,241,0.1)",
                border_radius="8px",
                padding="7px",
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.text(title, color=TEXT, font_size="0.95rem", font_weight="700"),
            spacing="2",
            align="center",
            margin_bottom="1rem",
        ),
        *children,
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="14px",
        padding="1.5rem",
        width="100%",
    )


def _field(label: str, *children) -> rx.Component:
    return rx.vstack(
        rx.text(label, color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.07em"),
        *children,
        spacing="1",
        align="start",
        width="100%",
    )


def _pw_input(placeholder: str, field: str) -> rx.Component:
    return rx.input(
        placeholder=placeholder,
        value=getattr(ProfilState, field),
        on_change=lambda v: ProfilState.set_field(field, v),
        type="password",
        background="#1c2138",
        color=TEXT,
        border=f"1px solid {BORDER}",
        border_radius="8px",
        width="100%",
        _focus={"border_color": PRIMARY, "outline": "none"},
        _placeholder={"color": "#475569"},
    )


def profil_content() -> rx.Component:
    return rx.vstack(

        # ── Header ────────────────────────────────────────────────────────────
        rx.hstack(
            rx.box(
                rx.text(
                    ProfilState.nom[:2].upper(),
                    color="white", font_weight="800", font_size="1.4rem",
                ),
                background=rx.cond(
                    ProfilState.color != "",
                    ProfilState.color,
                    f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                ),
                border_radius="50%",
                width="64px", height="64px",
                display="flex",
                align_items="center",
                justify_content="center",
                flex_shrink="0",
            ),
            rx.vstack(
                rx.text(ProfilState.nom, color=TEXT, font_size="1.3rem", font_weight="700"),
                rx.hstack(
                    rx.badge(
                        rx.cond(ProfilState.role == "manager", "Responsable", "Technicien"),
                        color_scheme=rx.cond(ProfilState.role == "manager", "indigo", "green"),
                        variant="soft", radius="full",
                    ),
                    rx.cond(
                        ProfilState.matricule != "—",
                        rx.text("·  #" + ProfilState.matricule, color=MUTED, font_size="0.82rem"),
                    ),
                    spacing="2", align="center",
                ),
                spacing="1",
                align="start",
            ),
            spacing="4",
            align="center",
            width="100%",
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="14px",
            padding="1.5rem",
        ),

        rx.hstack(

            # ── Infos ─────────────────────────────────────────────────────────
            _section(
                "Informations",
                "user",
                rx.vstack(
                    _field(
                        "NOM",
                        rx.box(
                            rx.text(ProfilState.nom, color=MUTED, font_size="0.875rem"),
                            background="rgba(255,255,255,0.03)",
                            border=f"1px solid {BORDER}",
                            border_radius="8px",
                            padding="8px 12px",
                            width="100%",
                        ),
                    ),
                    _field(
                        "MATRICULE",
                        rx.box(
                            rx.text(ProfilState.matricule, color=MUTED, font_size="0.875rem"),
                            background="rgba(255,255,255,0.03)",
                            border=f"1px solid {BORDER}",
                            border_radius="8px",
                            padding="8px 12px",
                            width="100%",
                        ),
                    ),
                    _field(
                        "EMAIL",
                        rx.input(
                            placeholder="votre@email.com",
                            value=ProfilState.email,
                            on_change=lambda v: ProfilState.set_field("email", v),
                            background="#1c2138", color=TEXT,
                            border=f"1px solid {BORDER}", border_radius="8px",
                            width="100%",
                            _focus={"border_color": PRIMARY, "outline": "none"},
                            _placeholder={"color": "#475569"},
                        ),
                    ),
                    _field(
                        "COULEUR D'AVATAR",
                        rx.hstack(
                            *[
                                rx.box(
                                    rx.cond(
                                        ProfilState.color == c,
                                        rx.icon("check", size=12, color="white"),
                                    ),
                                    width="28px", height="28px",
                                    background=c,
                                    border_radius="50%",
                                    cursor="pointer",
                                    display="flex",
                                    align_items="center",
                                    justify_content="center",
                                    border=rx.cond(
                                        ProfilState.color == c,
                                        "3px solid white",
                                        "3px solid transparent",
                                    ),
                                    on_click=ProfilState.set_color(c),
                                    transition="transform 0.15s",
                                    _hover={"transform": "scale(1.15)"},
                                )
                                for c in COLORS
                            ],
                            spacing="2",
                        ),
                    ),
                    rx.button(
                        rx.icon("save", size=15),
                        "Enregistrer",
                        on_click=ProfilState.save_info,
                        background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                        color="white",
                        border_radius="8px",
                        padding="9px 20px",
                        font_size="0.85rem",
                        font_weight="600",
                        cursor="pointer",
                        spacing="2",
                        width="100%",
                        margin_top="0.5rem",
                    ),
                    spacing="4",
                    width="100%",
                ),
            ),

            # ── Mot de passe ──────────────────────────────────────────────────
            _section(
                "Changer le mot de passe",
                "lock",
                rx.vstack(
                    _field("MOT DE PASSE ACTUEL",    _pw_input("••••••••", "current_password")),
                    _field("NOUVEAU MOT DE PASSE",   _pw_input("Min. 6 caractères", "new_password")),
                    _field("CONFIRMER",               _pw_input("Répéter le nouveau mot de passe", "confirm_password")),
                    rx.box(
                        rx.hstack(
                            rx.icon("info", size=12, color=MUTED),
                            rx.text(
                                "Le nouveau mot de passe doit faire au moins 6 caractères.",
                                color=MUTED, font_size="0.72rem",
                            ),
                            spacing="1", align="center",
                        ),
                    ),
                    rx.button(
                        rx.icon("key-round", size=15),
                        "Modifier le mot de passe",
                        on_click=ProfilState.change_password,
                        background="rgba(99,102,241,0.12)",
                        color=PRIMARY,
                        border=f"1px solid rgba(99,102,241,0.35)",
                        border_radius="8px",
                        padding="9px 20px",
                        font_size="0.85rem",
                        font_weight="600",
                        cursor="pointer",
                        spacing="2",
                        width="100%",
                        margin_top="0.5rem",
                        _hover={"background": "rgba(99,102,241,0.22)"},
                    ),
                    spacing="4",
                    width="100%",
                ),
            ),

            spacing="5",
            width="100%",
            wrap="wrap",
            align="start",
        ),

        spacing="5",
        width="100%",
        on_mount=ProfilState.load_profile,
    )


def profil_page() -> rx.Component:
    return page_layout(profil_content(), "Mon profil")
