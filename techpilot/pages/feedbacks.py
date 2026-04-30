import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
from techpilot.state.auth import AuthState
from techpilot.state.models import FeedbackItem
import uuid
from datetime import datetime

TEXT = "#f1f5f9"; MUTED = "#94a3b8"; CARD_BG = "#111524"; BORDER = "#1c2138"; PRIMARY = "#6366f1"
TYPES = ["bug", "suggestion", "amélioration"]
STATUTS = ["ouvert", "en_cours", "résolu", "fermé"]


class FeedbacksState(rx.State):
    feedbacks: list[FeedbackItem] = []
    filter_statut: str = ""
    show_form: bool = False
    form: dict = {"titre": "", "description": "", "type": "bug", "priorite": "normale"}

    def load(self):
        db = load_db()
        items = sorted(db.get("feedbacks") or [], key=lambda f: f.get("date_creation") or "", reverse=True)
        filtered = [f for f in items if not self.filter_statut or f.get("statut") == self.filter_statut]
        self.feedbacks = [
            FeedbackItem(
                id=str(item.get("id") or ""),
                titre=item.get("titre") or "",
                description=item.get("description") or "",
                type=item.get("type") or "",
                statut=item.get("statut") or "",
                priorite=item.get("priorite") or "",
                auteur_nom=item.get("auteur_nom") or "",
                date_creation=item.get("date_creation") or "",
                votes_count=len(item.get("votes") or []),
            )
            for item in filtered
        ]

    def set_filter(self, v: str):
        self.filter_statut = v
        self.load()

    def clear_filter(self):
        self.filter_statut = ""
        self.load()

    def open_form(self):
        self.form = {"titre": "", "description": "", "type": "bug", "priorite": "normale"}
        self.show_form = True

    def close_form(self):
        self.show_form = False

    def set_field(self, f: str, v: str):
        self.form = {**self.form, f: v}

    async def create(self):
        if not self.form.get("titre"):
            return
        auth = await self.get_state(AuthState)
        db = load_db()
        if "feedbacks" not in db:
            db["feedbacks"] = []
        db["feedbacks"].append({
            "id": str(uuid.uuid4()),
            **self.form,
            "statut": "ouvert",
            "auteur_id": auth.user_id,
            "auteur_nom": auth.user_nom,
            "votes": [],
            "date_creation": datetime.utcnow().isoformat(),
        })
        save_db(db)
        self.show_form = False
        self.load()

    async def vote(self, fid: str):
        auth = await self.get_state(AuthState)
        uid = auth.user_id
        db = load_db()
        for f in db.get("feedbacks") or []:
            if f.get("id") == fid:
                votes = f.get("votes") or []
                if uid in votes:
                    votes.remove(uid)
                else:
                    votes.append(uid)
                f["votes"] = votes
        save_db(db)
        self.load()

    def update_statut(self, fid: str, statut: str):
        db = load_db()
        for f in db.get("feedbacks") or []:
            if f.get("id") == fid:
                f["statut"] = statut
        save_db(db)
        self.load()

    def delete(self, fid: str):
        db = load_db()
        db["feedbacks"] = [f for f in (db.get("feedbacks") or []) if f.get("id") != fid]
        save_db(db)
        self.load()


def _statut_color(statut) -> rx.Var:
    return rx.cond(
        statut == "ouvert", "red",
        rx.cond(statut == "en_cours", "amber",
        rx.cond(statut == "résolu", "green", "gray"))
    )


def feedback_card(f: FeedbackItem) -> rx.Component:
    return rx.box(
        # En-tête : badges + date
        rx.hstack(
            rx.badge(f["type"], color_scheme="indigo", variant="soft", radius="full"),
            rx.badge(f["statut"], color_scheme=_statut_color(f["statut"]), variant="soft", radius="full"),
            rx.badge(f["priorite"], color_scheme="gray", variant="soft", radius="full"),
            rx.spacer(),
            rx.text(f["date_creation"][:10], color=MUTED, font_size="0.72rem"),
            spacing="2", align="center", width="100%", flex_wrap="wrap",
        ),
        # Titre
        rx.text(
            f["titre"], color=TEXT, font_weight="600", font_size="0.9rem",
            margin_top="0.5rem",
        ),
        # Description
        rx.text(
            f["description"], color=MUTED, font_size="0.82rem",
            overflow="hidden",
            display="-webkit-box",
            style={"-webkit-line-clamp": "3", "-webkit-box-orient": "vertical"},
        ),
        # Pied : auteur + actions
        rx.hstack(
            rx.text("Par " + f["auteur_nom"], color=MUTED, font_size="0.72rem"),
            rx.spacer(),
            rx.button(
                rx.icon("thumbs-up", size=13), f["votes_count"].to_string(),
                on_click=FeedbacksState.vote(f["id"]),
                background="rgba(99,102,241,0.1)", color=PRIMARY,
                border=f"1px solid rgba(99,102,241,0.25)", border_radius="7px",
                padding="5px 10px", font_size="0.75rem", cursor="pointer",
            ),
            rx.cond(
                AuthState.is_manager,
                rx.select(
                    STATUTS, value=f["statut"],
                    on_change=lambda v: FeedbacksState.update_statut(f["id"], v),
                    background="#1c2138", style={"color": TEXT, "font_size": "0.75rem"},
                    border=f"1px solid {BORDER}", border_radius="6px", width="110px",
                ),
            ),
            rx.cond(
                AuthState.is_manager,
                rx.icon_button(
                    rx.icon("trash-2", size=13),
                    on_click=FeedbacksState.delete(f["id"]),
                    background="transparent", color=MUTED,
                    size="1", cursor="pointer", border_radius="6px",
                    _hover={"color": "#ef4444"},
                ),
            ),
            spacing="2", align="center", width="100%", margin_top="0.75rem", flex_wrap="wrap",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="12px",
        padding="1rem 1.2rem",
        width="100%",
        _hover={"border_color": "rgba(99,102,241,0.35)"},
        transition="border-color 0.15s",
    )


def feedbacks_content() -> rx.Component:
    return rx.vstack(
        # Barre de filtres + bouton
        rx.hstack(
            rx.select(
                STATUTS, placeholder="Tous les statuts",
                value=FeedbacksState.filter_statut,
                on_change=FeedbacksState.set_filter,
                background="#1c2138", style={"color": TEXT},
                border=f"1px solid {BORDER}", border_radius="8px",
            ),
            rx.cond(
                FeedbacksState.filter_statut != "",
                rx.icon_button(
                    rx.icon("x", size=14), on_click=FeedbacksState.clear_filter,
                    background="transparent", color=MUTED,
                    border=f"1px solid {BORDER}", border_radius="8px",
                    size="2", cursor="pointer", _hover={"color": TEXT},
                ),
            ),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=15), "Nouveau feedback",
                on_click=FeedbacksState.open_form,
                background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                color="white", border_radius="8px",
                padding="8px 16px", font_size="0.85rem", cursor="pointer",
            ),
            width="100%", align="center", flex_wrap="wrap", gap="2",
        ),
        # Grille 2 colonnes responsive
        rx.box(
            rx.foreach(FeedbacksState.feedbacks, feedback_card),
            display="grid",
            grid_template_columns="repeat(auto-fill, minmax(420px, 1fr))",
            gap="0.875rem",
            width="100%",
        ),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(rx.text("Nouveau feedback", color=TEXT, font_weight="700")),
                rx.vstack(
                    rx.input(placeholder="Titre *", value=FeedbacksState.form["titre"], on_change=lambda v: FeedbacksState.set_field("titre", v), background="#1c2138", style={"color": TEXT}, border=f"1px solid {BORDER}", border_radius="8px", width="100%"),
                    rx.text_area(placeholder="Description", value=FeedbacksState.form["description"], on_change=lambda v: FeedbacksState.set_field("description", v), background="#1c2138", style={"color": TEXT}, border=f"1px solid {BORDER}", border_radius="8px", width="100%"),
                    rx.hstack(
                        rx.select(TYPES, value=FeedbacksState.form["type"], on_change=lambda v: FeedbacksState.set_field("type", v), background="#1c2138", style={"color": TEXT}, border=f"1px solid {BORDER}", border_radius="8px"),
                        rx.select(["basse", "normale", "haute", "critique"], value=FeedbacksState.form["priorite"], on_change=lambda v: FeedbacksState.set_field("priorite", v), background="#1c2138", style={"color": TEXT}, border=f"1px solid {BORDER}", border_radius="8px"),
                        spacing="3", width="100%",
                    ),
                    rx.hstack(
                        rx.button("Annuler", on_click=FeedbacksState.close_form, background="transparent", color=MUTED, border=f"1px solid {BORDER}", border_radius="8px", cursor="pointer"),
                        rx.button("Envoyer", on_click=FeedbacksState.create, background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)", color="white", border_radius="8px", cursor="pointer"),
                        spacing="3", justify="end", width="100%",
                    ),
                    spacing="3", width="100%",
                ),
                background="#111524", border=f"1px solid {BORDER}", border_radius="16px", padding="1.5rem", max_width="480px",
            ),
            open=FeedbacksState.show_form,
        ),
        spacing="4", width="100%", on_mount=FeedbacksState.load,
    )


def feedbacks_page() -> rx.Component:
    return page_layout(feedbacks_content(), "Feedbacks")
