import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
from techpilot.state.models import TicketItem
import uuid
from datetime import datetime

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
CARD_BG = "#111524"
BORDER  = "#1c2138"
PRIMARY = "#6366f1"
RED     = "#ef4444"
GREEN   = "#22c55e"

IMPACTS = ["critique", "haute", "normale", "basse"]

SEVERITY_LABEL = {"critique": "Critique", "haute": "Haute", "normale": "Modéré", "basse": "Faible"}
SEVERITY_COLOR = {"critique": "#ef4444", "haute": "#f59e0b", "normale": "#6366f1", "basse": "#94a3b8"}


class TicketsState(rx.State):
    tickets: list[TicketItem] = []
    tab: str = "tous"           # "tous" | "en_cours" | "resolu"
    count_en_cours: int = 0
    count_resolus: int = 0
    show_form: bool = False
    form: dict = {"titre": "", "description": "", "impact": "normale", "numero": ""}

    def load(self):
        db = load_db()
        raw = sorted(db.get("tickets") or [], key=lambda x: x.get("date_creation") or "", reverse=True)
        self.count_en_cours = sum(1 for x in raw if x.get("etat") == "en_cours")
        self.count_resolus  = sum(1 for x in raw if x.get("etat") == "resolu")
        if self.tab == "en_cours":
            filtered = [x for x in raw if x.get("etat") == "en_cours"]
        elif self.tab == "resolu":
            filtered = [x for x in raw if x.get("etat") == "resolu"]
        else:
            filtered = raw
        self.tickets = [
            TicketItem(
                id=str(x.get("id") or ""),
                titre=x.get("titre") or "",
                description=x.get("description") or "",
                impact=x.get("impact") or "",
                etat=x.get("etat") or "",
                date_creation=x.get("date_creation") or "",
            )
            for x in filtered
        ]

    def set_tab(self, val: str):
        self.tab = val
        self.load()

    def open_form(self):
        self.form = {"titre": "", "description": "", "impact": "normale", "numero": ""}
        self.show_form = True

    def close_form(self):
        self.show_form = False

    def set_field(self, field: str, val: str):
        self.form = {**self.form, field: val}

    def create(self):
        if not self.form.get("titre"):
            return
        db = load_db()
        if "tickets" not in db:
            db["tickets"] = []
        db["tickets"].append({
            "id": str(uuid.uuid4()),
            "titre":       self.form.get("titre", ""),
            "description": self.form.get("description", ""),
            "impact":      self.form.get("impact", "normale"),
            "numero":      self.form.get("numero", ""),
            "etat": "en_cours",
            "date_creation":    datetime.utcnow().isoformat(),
            "date_modification": datetime.utcnow().isoformat(),
            "date_resolution":  None,
        })
        save_db(db)
        self.show_form = False
        self.load()

    def resolve(self, tid: str):
        db = load_db()
        for t in db.get("tickets") or []:
            if t.get("id") == tid:
                t["etat"] = "resolu"
                t["date_resolution"]  = datetime.utcnow().isoformat()
                t["date_modification"] = datetime.utcnow().isoformat()
        save_db(db)
        self.load()

    def delete(self, tid: str):
        db = load_db()
        db["tickets"] = [t for t in (db.get("tickets") or []) if t.get("id") != tid]
        save_db(db)
        self.load()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _severity_badge(impact) -> rx.Component:
    return rx.match(
        impact,
        ("critique", rx.badge("Critique", color_scheme="red",    variant="soft", radius="full", font_size="0.72rem")),
        ("haute",    rx.badge("Haute",     color_scheme="amber",  variant="soft", radius="full", font_size="0.72rem")),
        ("normale",  rx.badge("Modéré",    color_scheme="violet", variant="soft", radius="full", font_size="0.72rem")),
        ("basse",    rx.badge("Faible",    color_scheme="gray",   variant="soft", radius="full", font_size="0.72rem")),
        rx.badge(impact, color_scheme="gray", variant="soft", radius="full", font_size="0.72rem"),
    )


def _tab_btn(label: str, val: str, active_val) -> rx.Component:
    is_active = active_val == val
    return rx.box(
        rx.text(label, font_size="0.85rem", font_weight=rx.cond(is_active, "600", "400"),
                color=rx.cond(is_active, TEXT, MUTED)),
        padding="6px 16px",
        border_radius="8px",
        background=rx.cond(is_active, RED, "transparent"),
        cursor="pointer",
        transition="all 0.15s",
        on_click=TicketsState.set_tab(val),
        _hover={"background": rx.cond(is_active, RED, "rgba(255,255,255,0.05)")},
    )


def incident_row(t: TicketItem) -> rx.Component:
    border_color = rx.cond(t["etat"] == "en_cours", RED, GREEN)
    num_display  = rx.cond(t["id"] != "", t["id"][:6].upper(), "------")
    date_display = rx.cond(t["date_creation"] != "", t["date_creation"][:10], "")

    return rx.box(
        rx.hstack(
            # Icône état
            rx.cond(
                t["etat"] == "en_cours",
                rx.icon("clock", size=16, color=RED),
                rx.icon("circle-check", size=16, color=GREEN),
            ),
            # Numéro
            rx.box(
                rx.text(num_display, color=MUTED, font_size="0.72rem", font_family="monospace"),
                background="rgba(255,255,255,0.05)",
                border=f"1px solid {BORDER}",
                border_radius="4px",
                padding="2px 6px",
            ),
            # Titre
            rx.text(t["titre"], color=TEXT, font_size="0.875rem", font_weight="500", flex="1"),
            # Sévérité
            _severity_badge(t["impact"]),
            # Assigné
            rx.text("Non assigné", color=MUTED, font_size="0.78rem"),
            # Date
            rx.text(date_display, color=MUTED, font_size="0.78rem"),
            # Actions
            rx.hstack(
                rx.cond(
                    t["etat"] == "en_cours",
                    rx.icon_button(
                        rx.icon("pencil", size=13),
                        on_click=TicketsState.resolve(t["id"]),
                        background="transparent",
                        color=MUTED,
                        size="1",
                        cursor="pointer",
                        _hover={"color": TEXT},
                    ),
                ),
                rx.icon_button(
                    rx.icon("trash-2", size=13),
                    on_click=TicketsState.delete(t["id"]),
                    background="transparent",
                    color=MUTED,
                    size="1",
                    cursor="pointer",
                    _hover={"color": RED},
                ),
                spacing="1",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_left=f"3px solid " + border_color,
        border_radius="10px",
        padding="0.85rem 1.1rem",
        width="100%",
        transition="background 0.15s",
        _hover={"background": "rgba(255,255,255,0.02)"},
    )


def tickets_content() -> rx.Component:
    return rx.vstack(

        # ── Header ────────────────────────────────────────────────────────────
        rx.hstack(
            rx.hstack(
                rx.box(
                    rx.icon("shield-alert", size=20, color="white"),
                    background=f"linear-gradient(135deg, {RED}, #b91c1c)",
                    border_radius="10px",
                    padding="8px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.vstack(
                    rx.text("Incidents Généraux", color=TEXT, font_size="1.15rem", font_weight="700"),
                    rx.text("Suivi des incidents majeurs impactant le support N1",
                            color=MUTED, font_size="0.8rem"),
                    spacing="0",
                    align="start",
                ),
                spacing="3",
                align="center",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=16),
                "Déclarer un incident",
                on_click=TicketsState.open_form,
                background=f"linear-gradient(135deg, {RED}, #b91c1c)",
                color="white",
                border_radius="8px",
                padding="8px 18px",
                font_size="0.85rem",
                font_weight="600",
                cursor="pointer",
                spacing="2",
                _hover={"opacity": "0.9"},
            ),
            width="100%",
            align="center",
        ),

        # ── KPI cards ─────────────────────────────────────────────────────────
        rx.hstack(
            # EN COURS
            rx.box(
                rx.hstack(
                    rx.box(
                        rx.icon("clock", size=22, color=RED),
                        background="rgba(239,68,68,0.12)",
                        border_radius="10px",
                        padding="10px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                    rx.vstack(
                        rx.text("EN COURS", color=MUTED, font_size="0.65rem", font_weight="700", letter_spacing="0.1em"),
                        rx.text(TicketsState.count_en_cours, color=RED, font_size="2rem", font_weight="800", line_height="1"),
                        rx.text("incident actif", color=MUTED, font_size="0.72rem"),
                        spacing="1",
                        align="start",
                    ),
                    spacing="4",
                    align="center",
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_left=f"3px solid {RED}",
                border_radius="12px",
                padding="1.2rem 1.5rem",
                flex="1",
            ),
            # RÉSOLUS
            rx.box(
                rx.hstack(
                    rx.box(
                        rx.icon("circle-check", size=22, color=GREEN),
                        background="rgba(34,197,94,0.12)",
                        border_radius="10px",
                        padding="10px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                    rx.vstack(
                        rx.text("RÉSOLUS", color=MUTED, font_size="0.65rem", font_weight="700", letter_spacing="0.1em"),
                        rx.text(TicketsState.count_resolus, color=GREEN, font_size="2rem", font_weight="800", line_height="1"),
                        rx.text("incidents clôturés", color=MUTED, font_size="0.72rem"),
                        spacing="1",
                        align="start",
                    ),
                    spacing="4",
                    align="center",
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_left=f"3px solid {GREEN}",
                border_radius="12px",
                padding="1.2rem 1.5rem",
                flex="1",
            ),
            spacing="4",
            width="100%",
        ),

        # ── Onglets ───────────────────────────────────────────────────────────
        rx.hstack(
            _tab_btn("Tous",      "tous",     TicketsState.tab),
            _tab_btn("En cours",  "en_cours", TicketsState.tab),
            _tab_btn("Résolus",   "resolu",   TicketsState.tab),
            spacing="1",
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="10px",
            padding="4px",
        ),

        # ── Liste incidents ───────────────────────────────────────────────────
        rx.vstack(
            rx.foreach(TicketsState.tickets, incident_row),
            spacing="2",
            width="100%",
        ),

        # ── Dialog création ───────────────────────────────────────────────────
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(rx.text("Déclarer un incident", color=TEXT, font_weight="700")),
                rx.vstack(
                    rx.input(
                        placeholder="Titre *",
                        value=TicketsState.form["titre"],
                        on_change=lambda v: TicketsState.set_field("titre", v),
                        background="#1c2138", color=TEXT, border=f"1px solid {BORDER}",
                        border_radius="8px", width="100%",
                    ),
                    rx.input(
                        placeholder="Numéro Freshservice (optionnel)",
                        value=TicketsState.form["numero"],
                        on_change=lambda v: TicketsState.set_field("numero", v),
                        background="#1c2138", color=TEXT, border=f"1px solid {BORDER}",
                        border_radius="8px", width="100%",
                    ),
                    rx.text_area(
                        placeholder="Description",
                        value=TicketsState.form["description"],
                        on_change=lambda v: TicketsState.set_field("description", v),
                        background="#1c2138", color=TEXT, border=f"1px solid {BORDER}",
                        border_radius="8px", width="100%",
                    ),
                    rx.select(
                        IMPACTS,
                        value=TicketsState.form["impact"],
                        on_change=lambda v: TicketsState.set_field("impact", v),
                        background="#1c2138", color=TEXT, border=f"1px solid {BORDER}",
                        border_radius="8px",
                    ),
                    rx.hstack(
                        rx.button("Annuler", on_click=TicketsState.close_form,
                                  background="transparent", color=MUTED,
                                  border=f"1px solid {BORDER}", border_radius="8px", cursor="pointer"),
                        rx.button("Créer", on_click=TicketsState.create,
                                  background=f"linear-gradient(135deg, {RED}, #b91c1c)",
                                  color="white", border_radius="8px", cursor="pointer"),
                        spacing="3", justify="end", width="100%",
                    ),
                    spacing="3", width="100%",
                ),
                background="#111524", border=f"1px solid {BORDER}",
                border_radius="16px", padding="1.5rem", max_width="480px",
            ),
            open=TicketsState.show_form,
        ),

        spacing="4",
        width="100%",
        on_mount=TicketsState.load,
    )


def tickets_page() -> rx.Component:
    return page_layout(tickets_content(), "")
