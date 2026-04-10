import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
from techpilot.state.auth import AuthState
import uuid
from datetime import datetime

TEXT = "#e2e8f0"; MUTED = "#64748b"; CARD_BG = "#151728"; BORDER = "#1e2235"; PRIMARY = "#6366f1"
TYPES = ["bug", "suggestion", "amélioration"]
STATUTS = ["ouvert", "en_cours", "résolu", "fermé"]
STATUT_COLORS = {"ouvert": "red", "en_cours": "amber", "résolu": "green", "fermé": "gray"}


class FeedbacksState(rx.State):
    feedbacks: list[dict] = []
    filter_statut: str = ""
    show_form: bool = False
    form: dict = {}

    def load(self):
        db = load_db()
        items = sorted(db.get("feedbacks") or [], key=lambda f: f.get("date_creation") or "", reverse=True)
        self.feedbacks = [f for f in items if not self.filter_statut or f.get("statut") == self.filter_statut]

    def set_filter(self, v: str):
        self.filter_statut = v
        self.load()

    def open_form(self):
        self.form = {"titre": "", "description": "", "type": "bug", "priorite": "normale"}
        self.show_form = True

    def close_form(self):
        self.show_form = False

    def set_field(self, f: str, v: str):
        self.form = {**self.form, f: v}

    def create(self):
        if not self.form.get("titre"):
            return
        db = load_db()
        if "feedbacks" not in db:
            db["feedbacks"] = []
        db["feedbacks"].append({
            "id": str(uuid.uuid4()),
            **self.form,
            "statut": "ouvert",
            "auteur_id": AuthState.user_id,
            "auteur_nom": AuthState.user_nom,
            "votes": [],
            "date_creation": datetime.utcnow().isoformat(),
        })
        save_db(db)
        self.show_form = False
        self.load()

    def vote(self, fid: str):
        db = load_db()
        uid = AuthState.user_id
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


def feedback_card(f: dict) -> rx.Component:
    statut = f.get("statut", "ouvert")
    color_scheme = STATUT_COLORS.get(statut, "gray")
    nb_votes = len(f.get("votes") or [])
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.badge(f.get("type", ""), color_scheme="indigo", variant="soft", radius="full"),
                    rx.badge(statut, color_scheme=color_scheme, variant="soft", radius="full"),
                    rx.badge(f.get("priorite", ""), color_scheme="gray", variant="soft", radius="full"),
                    rx.spacer(),
                    rx.text((f.get("date_creation") or "")[:10], color=MUTED, font_size="0.75rem"),
                    spacing="2", align="center", width="100%",
                ),
                rx.text(f.get("titre", ""), color=TEXT, font_weight="600", font_size="0.9rem"),
                rx.text(f.get("description", ""), color=MUTED, font_size="0.82rem"),
                rx.text(f"Par {f.get('auteur_nom', '')}", color=MUTED, font_size="0.72rem"),
                spacing="2", align="start", width="100%",
            ),
            rx.vstack(
                rx.button(
                    rx.icon("thumbs-up", size=14), str(nb_votes),
                    on_click=FeedbacksState.vote(f.get("id", "")),
                    background="rgba(99,102,241,0.1)", color=PRIMARY,
                    border=f"1px solid rgba(99,102,241,0.3)", border_radius="8px",
                    padding="6px 10px", font_size="0.78rem", cursor="pointer", spacing="1",
                ),
                rx.cond(
                    AuthState.is_manager,
                    rx.select(
                        STATUTS, value=statut,
                        on_change=lambda v: FeedbacksState.update_statut(f.get("id", ""), v),
                        background="#1e2035", color=TEXT, border=f"1px solid {BORDER}",
                        border_radius="6px", font_size="0.75rem", width="110px",
                    ),
                ),
                spacing="2", align="center",
            ),
            spacing="3", align="start", width="100%",
        ),
        background=CARD_BG, border=f"1px solid {BORDER}", border_radius="12px", padding="1rem 1.2rem",
    )


def feedbacks_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.select(["", *STATUTS], placeholder="Tous les statuts", value=FeedbacksState.filter_statut, on_change=FeedbacksState.set_filter, background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px"),
            rx.spacer(),
            rx.button(rx.icon("plus", size=16), "Nouveau feedback", on_click=FeedbacksState.open_form, background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)", color="white", border_radius="8px", padding="8px 16px", font_size="0.85rem", cursor="pointer", spacing="2"),
            width="100%", align="center",
        ),
        rx.vstack(rx.foreach(FeedbacksState.feedbacks, feedback_card), spacing="3", width="100%"),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(rx.text("Nouveau feedback", color=TEXT, font_weight="700")),
                rx.vstack(
                    rx.input(placeholder="Titre *", value=FeedbacksState.form.get("titre", ""), on_change=lambda v: FeedbacksState.set_field("titre", v), background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px", width="100%"),
                    rx.text_area(placeholder="Description", value=FeedbacksState.form.get("description", ""), on_change=lambda v: FeedbacksState.set_field("description", v), background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px", width="100%"),
                    rx.hstack(
                        rx.select(TYPES, value=FeedbacksState.form.get("type", "bug"), on_change=lambda v: FeedbacksState.set_field("type", v), background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px"),
                        rx.select(["basse", "normale", "haute", "critique"], value=FeedbacksState.form.get("priorite", "normale"), on_change=lambda v: FeedbacksState.set_field("priorite", v), background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px"),
                        spacing="3", width="100%",
                    ),
                    rx.hstack(
                        rx.button("Annuler", on_click=FeedbacksState.close_form, background="transparent", color=MUTED, border=f"1px solid {BORDER}", border_radius="8px", cursor="pointer"),
                        rx.button("Envoyer", on_click=FeedbacksState.create, background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)", color="white", border_radius="8px", cursor="pointer"),
                        spacing="3", justify="end", width="100%",
                    ),
                    spacing="3", width="100%",
                ),
                background="#151728", border=f"1px solid {BORDER}", border_radius="16px", padding="1.5rem", max_width="480px",
            ),
            open=FeedbacksState.show_form,
        ),
        spacing="4", width="100%", on_mount=FeedbacksState.load,
    )


def feedbacks_page() -> rx.Component:
    return page_layout(feedbacks_content(), "Feedbacks")
