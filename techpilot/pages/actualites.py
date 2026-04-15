import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
from techpilot.state.auth import AuthState
from techpilot.state.models import ActualiteItem
import uuid
from datetime import datetime

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
CARD_BG = "#111524"
BORDER  = "#1c2138"
PRIMARY = "#6366f1"

TYPES = ["info", "success", "warning", "alerte"]

# Par type : (couleur_texte, couleur_bg_icon, couleur_border, icône, label)
TYPE_CONFIG = {
    "info":    ("#6366f1", "rgba(99,102,241,0.12)",  "#6366f1", "info",           "Info"),
    "success": ("#22c55e", "rgba(34,197,94,0.12)",   "#22c55e", "check-circle-2", "Succès"),
    "warning": ("#f59e0b", "rgba(245,158,11,0.12)",  "#f59e0b", "triangle-alert", "Avertissement"),
    "alerte":  ("#ef4444", "rgba(239,68,68,0.12)",   "#ef4444", "siren",          "Alerte"),
}


class ActualitesState(rx.State):
    actualites: list[ActualiteItem] = []
    show_form: bool = False
    form: dict = {"titre": "", "contenu": "", "type": "info", "epingle": False}

    def load(self):
        db = load_db()
        items = db.get("actualites") or []
        items.sort(key=lambda a: (
            not a.get("epingle", False),
            -(datetime.fromisoformat(a["date_creation"]).timestamp()
              if a.get("date_creation") else 0)
        ))
        self.actualites = [
            ActualiteItem(
                id=str(a.get("id") or ""),
                titre=a.get("titre") or "",
                contenu=a.get("contenu") or "",
                type=a.get("type") or "",
                epingle=bool(a.get("epingle", False)),
                auteur_nom=a.get("auteur_nom") or "",
                date_creation=a.get("date_creation") or "",
            )
            for a in items
        ]

    def open_form(self):
        self.form = {"titre": "", "contenu": "", "type": "info", "epingle": False}
        self.show_form = True

    def close_form(self):
        self.show_form = False

    def set_field(self, f: str, v):
        self.form = {**self.form, f: v}

    def toggle_form_epingle(self):
        self.form = {**self.form, "epingle": not self.form.get("epingle", False)}

    async def create(self):
        if not self.form.get("titre"):
            return
        auth = await self.get_state(AuthState)
        db = load_db()
        if "actualites" not in db:
            db["actualites"] = []
        db["actualites"].append({
            "id": str(uuid.uuid4()),
            **self.form,
            "auteur_id":  auth.user_id,
            "auteur_nom": auth.user_nom,
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


# ── Helpers ────────────────────────────────────────────────────────────────────

def _type_color(t) -> rx.Var:
    return rx.cond(t == "success", "#22c55e",
           rx.cond(t == "warning", "#f59e0b",
           rx.cond(t == "alerte",  "#ef4444", PRIMARY)))

def _type_bg(t) -> rx.Var:
    return rx.cond(t == "success", "rgba(34,197,94,0.12)",
           rx.cond(t == "warning", "rgba(245,158,11,0.12)",
           rx.cond(t == "alerte",  "rgba(239,68,68,0.12)", "rgba(99,102,241,0.12)")))

def _type_icon(t) -> rx.Var:
    return rx.cond(t == "success", "check-circle-2",
           rx.cond(t == "warning", "triangle-alert",
           rx.cond(t == "alerte",  "bell-ring", "info")))

def _type_label(t) -> rx.Var:
    return rx.cond(t == "success", "Succès",
           rx.cond(t == "warning", "Avertissement",
           rx.cond(t == "alerte",  "Alerte", "Info")))

def _initials(nom) -> rx.Var:
    return nom[:2].upper()


# ── Carte actualité ────────────────────────────────────────────────────────────

def actu_card(a: ActualiteItem) -> rx.Component:
    return rx.box(

        # Bandeau épinglé
        rx.cond(
            a["epingle"],
            rx.box(
                rx.hstack(
                    rx.icon("pin", size=12, color="#fbbf24"),
                    rx.text("Épinglé", color="#fbbf24", font_size="0.7rem", font_weight="600"),
                    spacing="1", align="center",
                ),
                background="rgba(251,191,36,0.08)",
                border_bottom=f"1px solid rgba(251,191,36,0.2)",
                padding="5px 1.2rem",
            ),
        ),

        # Corps
        rx.hstack(

            # Icône type
            rx.box(
                rx.icon(_type_icon(a["type"]), size=20, color=_type_color(a["type"])),
                background=_type_bg(a["type"]),
                border_radius="10px",
                width="42px",
                height="42px",
                display="flex",
                align_items="center",
                justify_content="center",
                flex_shrink="0",
            ),

            # Contenu central
            rx.vstack(
                # Label type + date
                rx.hstack(
                    rx.text(
                        _type_label(a["type"]),
                        color=_type_color(a["type"]),
                        font_size="0.7rem",
                        font_weight="700",
                        letter_spacing="0.06em",
                        text_transform="uppercase",
                    ),
                    rx.box(width="1px", height="12px", background=BORDER),
                    rx.text(a["date_creation"][:10], color=MUTED, font_size="0.75rem"),
                    spacing="2",
                    align="center",
                ),
                # Titre
                rx.text(a["titre"], color=TEXT, font_size="1rem", font_weight="700", line_height="1.3"),
                # Contenu (si présent)
                rx.cond(
                    a["contenu"] != "",
                    rx.text(a["contenu"], color=MUTED, font_size="0.85rem", line_height="1.6"),
                ),
                # Footer auteur
                rx.hstack(
                    rx.box(
                        rx.text(_initials(a["auteur_nom"]), color="white", font_size="0.6rem", font_weight="700"),
                        background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                        border_radius="50%",
                        width="20px",
                        height="20px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        flex_shrink="0",
                    ),
                    rx.text("Par " + a["auteur_nom"], color=MUTED, font_size="0.75rem"),
                    spacing="2",
                    align="center",
                ),
                spacing="2",
                align="start",
                flex="1",
            ),

            # Actions
            rx.vstack(
                rx.cond(
                    AuthState.is_manager,
                    rx.icon_button(
                        rx.icon("pin", size=14),
                        on_click=ActualitesState.toggle_epingle(a["id"]),
                        background=rx.cond(a["epingle"], "rgba(251,191,36,0.15)", "transparent"),
                        color=rx.cond(a["epingle"], "#fbbf24", MUTED),
                        border_radius="7px",
                        size="2",
                        cursor="pointer",
                        _hover={"color": "#fbbf24", "background": "rgba(251,191,36,0.1)"},
                    ),
                ),
                rx.icon_button(
                    rx.icon("trash-2", size=14),
                    on_click=ActualitesState.delete(a["id"]),
                    background="transparent",
                    color=MUTED,
                    border_radius="7px",
                    size="2",
                    cursor="pointer",
                    _hover={"color": "#ef4444", "background": "rgba(239,68,68,0.1)"},
                ),
                spacing="1",
                align="end",
            ),

            spacing="4",
            align="start",
            padding="1.1rem 1.3rem",
            width="100%",
        ),

        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_left="3px solid " + _type_color(a["type"]),
        border_radius="14px",
        overflow="hidden",
        width="100%",
        transition="box-shadow 0.15s",
        _hover={"box_shadow": "0 4px 24px rgba(0,0,0,0.25)"},
    )


# ── Page ──────────────────────────────────────────────────────────────────────

def actualites_content() -> rx.Component:
    return rx.vstack(

        # Header
        rx.hstack(
            rx.hstack(
                rx.box(
                    rx.icon("newspaper", size=20, color="white"),
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    border_radius="10px",
                    padding="8px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.vstack(
                    rx.text("Actualités", color=TEXT, font_size="1.15rem", font_weight="700"),
                    rx.text("Informations et annonces de l'équipe",
                            color=MUTED, font_size="0.8rem"),
                    spacing="0",
                    align="start",
                ),
                spacing="3",
                align="center",
            ),
            rx.spacer(),
            rx.cond(
                AuthState.is_manager,
                rx.button(
                    rx.icon("plus", size=16),
                    "Nouvelle actualité",
                    on_click=ActualitesState.open_form,
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    color="white",
                    border_radius="8px",
                    padding="8px 18px",
                    font_size="0.85rem",
                    font_weight="600",
                    cursor="pointer",
                    spacing="2",
                    _hover={"opacity": "0.9"},
                ),
            ),
            width="100%",
            align="center",
        ),

        # Feed
        rx.vstack(
            rx.foreach(ActualitesState.actualites, actu_card),
            spacing="3",
            width="100%",
        ),

        # Dialog
        rx.dialog.root(
            rx.dialog.content(

                # Header gradient
                rx.box(
                    rx.hstack(
                        rx.box(
                            rx.icon("newspaper", size=18, color="white"),
                            background="rgba(255,255,255,0.2)",
                            border_radius="10px",
                            padding="8px",
                            display="flex",
                            align_items="center",
                            justify_content="center",
                        ),
                        rx.vstack(
                            rx.text("Nouvelle actualité", color="white", font_size="1rem", font_weight="700"),
                            rx.text("Publier une information à l'équipe",
                                    color="rgba(255,255,255,0.7)", font_size="0.72rem"),
                            spacing="0",
                            align="start",
                        ),
                        spacing="3",
                        align="center",
                    ),
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    border_radius="12px 12px 0 0",
                    padding="1.25rem 1.5rem",
                    margin="-24px -24px 0 -24px",
                ),

                rx.vstack(
                    # Type (4 boutons)
                    rx.vstack(
                        rx.text("TYPE", color=MUTED, font_size="0.68rem", font_weight="700",
                                letter_spacing="0.07em"),
                        rx.hstack(
                            *[
                                rx.box(
                                    rx.text(label, font_size="0.78rem", font_weight="600",
                                            color=rx.cond(
                                                ActualitesState.form["type"] == val,
                                                _type_color(val), MUTED
                                            )),
                                    padding="0.5rem 0.6rem",
                                    border_radius="10px",
                                    border=rx.cond(
                                        ActualitesState.form["type"] == val,
                                        "2px solid " + _type_color(val),
                                        f"2px solid {BORDER}",
                                    ),
                                    background=rx.cond(
                                        ActualitesState.form["type"] == val,
                                        _type_bg(val),
                                        "rgba(255,255,255,0.02)",
                                    ),
                                    cursor="pointer",
                                    text_align="center",
                                    flex="1",
                                    transition="all 0.15s",
                                    on_click=ActualitesState.set_field("type", val),
                                )
                                for val, label in [
                                    ("info", "Info"),
                                    ("success", "Succès"),
                                    ("warning", "Avertissement"),
                                    ("alerte", "Alerte"),
                                ]
                            ],
                            spacing="2",
                            width="100%",
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),

                    # Titre
                    rx.vstack(
                        rx.hstack(
                            rx.text("TITRE", color=MUTED, font_size="0.68rem", font_weight="700",
                                    letter_spacing="0.07em"),
                            rx.text("*", color="#ef4444", font_size="0.75rem"),
                            spacing="1",
                        ),
                        rx.input(
                            placeholder="Titre de l'actualité...",
                            value=ActualitesState.form["titre"],
                            on_change=lambda v: ActualitesState.set_field("titre", v),
                            background="#1c2138", color=TEXT,
                            border=f"1px solid {BORDER}", border_radius="8px", width="100%",
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),

                    # Contenu
                    rx.vstack(
                        rx.text("CONTENU", color=MUTED, font_size="0.68rem", font_weight="700",
                                letter_spacing="0.07em"),
                        rx.text_area(
                            placeholder="Décris l'actualité en détail...",
                            value=ActualitesState.form["contenu"],
                            on_change=lambda v: ActualitesState.set_field("contenu", v),
                            background="#1c2138", color=TEXT,
                            border=f"1px solid {BORDER}", border_radius="8px", width="100%",
                            rows="4",
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),

                    # Épingler
                    rx.box(
                        rx.hstack(
                            rx.checkbox(
                                checked=ActualitesState.form["epingle"],
                                on_change=ActualitesState.toggle_form_epingle,
                                color_scheme="amber",
                            ),
                            rx.hstack(
                                rx.icon("pin", size=14, color="#fbbf24"),
                                rx.text("Épingler cette actualité", color=TEXT, font_size="0.875rem"),
                                spacing="2",
                                align="center",
                            ),
                            spacing="3",
                            align="center",
                            cursor="pointer",
                        ),
                        background="rgba(251,191,36,0.06)",
                        border=f"1px solid rgba(251,191,36,0.2)",
                        border_radius="10px",
                        padding="0.75rem 1rem",
                        cursor="pointer",
                        width="100%",
                        on_click=ActualitesState.toggle_form_epingle,
                    ),

                    # Boutons
                    rx.hstack(
                        rx.button(
                            "Annuler",
                            on_click=ActualitesState.close_form,
                            background="transparent", color=MUTED,
                            border=f"1px solid {BORDER}", border_radius="8px", cursor="pointer",
                        ),
                        rx.button(
                            rx.icon("send", size=15),
                            "Publier",
                            on_click=ActualitesState.create,
                            background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                            color="white", border_radius="8px", cursor="pointer",
                            font_weight="700",
                            spacing="2",
                        ),
                        spacing="3", justify="end", width="100%",
                    ),

                    spacing="4",
                    width="100%",
                    padding_top="1.25rem",
                ),

                background="#111524", border=f"1px solid {BORDER}",
                border_radius="16px", padding="24px", max_width="520px",
                overflow="hidden",
            ),
            open=ActualitesState.show_form,
        ),

        spacing="4",
        width="100%",
        max_width="760px",
        on_mount=ActualitesState.load,
    )


def actualites_page() -> rx.Component:
    return page_layout(actualites_content(), "")
