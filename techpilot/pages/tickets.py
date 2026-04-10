import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
import uuid
from datetime import datetime

TEXT = "#e2e8f0"; MUTED = "#64748b"; CARD_BG = "#151728"; BORDER = "#1e2235"; PRIMARY = "#6366f1"

ETATS = ["en_cours", "resolu", "ferme"]
IMPACTS = ["critique", "haute", "normale", "basse"]


class TicketsState(rx.State):
    tickets: list[dict] = []
    filter_etat: str = ""
    show_form: bool = False
    form: dict = {"titre": "", "description": "", "impact": "normale", "perimetre": "", "notes": ""}

    def load(self):
        db = load_db()
        t = sorted(db.get("tickets") or [], key=lambda x: x.get("date_creation") or "", reverse=True)
        self.tickets = [x for x in t if not self.filter_etat or x.get("etat") == self.filter_etat]

    def set_filter(self, val: str):
        self.filter_etat = val
        self.load()

    def open_form(self):
        self.form = {"titre": "", "description": "", "impact": "normale", "perimetre": "", "notes": ""}
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
            **self.form,
            "etat": "en_cours",
            "date_creation": datetime.utcnow().isoformat(),
            "date_modification": datetime.utcnow().isoformat(),
            "date_resolution": None,
        })
        save_db(db)
        self.show_form = False
        self.load()

    def resolve(self, tid: str):
        db = load_db()
        for t in db.get("tickets") or []:
            if t.get("id") == tid:
                t["etat"] = "resolu"
                t["date_resolution"] = datetime.utcnow().isoformat()
                t["date_modification"] = datetime.utcnow().isoformat()
        save_db(db)
        self.load()

    def delete(self, tid: str):
        db = load_db()
        db["tickets"] = [t for t in (db.get("tickets") or []) if t.get("id") != tid]
        save_db(db)
        self.load()


def _etat_badge(etat) -> rx.Component:
    return rx.match(
        etat,
        ("en_cours", rx.badge("en cours", color_scheme="amber", variant="soft", radius="full")),
        ("resolu",   rx.badge("résolu",   color_scheme="green", variant="soft", radius="full")),
        ("ferme",    rx.badge("fermé",    color_scheme="gray",  variant="soft", radius="full")),
        rx.badge(etat, color_scheme="gray", variant="soft", radius="full"),
    )


def ticket_row(t: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(t["titre"], color=TEXT, font_size="0.85rem"), padding="10px 12px"),
        rx.table.cell(
            rx.badge(
                t["impact"],
                color_scheme=rx.cond((t["impact"] == "critique") | (t["impact"] == "haute"), "amber", "gray"),
                variant="soft", radius="full",
            ),
            padding="10px 12px",
        ),
        rx.table.cell(_etat_badge(t["etat"]), padding="10px 12px"),
        rx.table.cell(rx.text(t["date_creation"][:10], color=MUTED, font_size="0.8rem"), padding="10px 12px"),
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    t["etat"] == "en_cours",
                    rx.icon_button(rx.icon("check", size=14), on_click=TicketsState.resolve(t["id"]), background="rgba(34,197,94,0.1)", color="#22c55e", border_radius="6px", size="1", cursor="pointer"),
                ),
                rx.icon_button(rx.icon("trash-2", size=14), on_click=TicketsState.delete(t["id"]), background="rgba(239,68,68,0.1)", color="#ef4444", border_radius="6px", size="1", cursor="pointer"),
                spacing="2",
            ),
            padding="10px 12px",
        ),
        _hover={"background": "rgba(255,255,255,0.02)"},
    )


def tickets_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.select(["", *ETATS], placeholder="Tous les états", value=TicketsState.filter_etat, on_change=TicketsState.set_filter, background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px"),
            rx.spacer(),
            rx.button(rx.icon("plus", size=16), "Nouveau ticket", on_click=TicketsState.open_form, background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)", color="white", border_radius="8px", padding="8px 16px", font_size="0.85rem", cursor="pointer", spacing="2"),
            width="100%", align="center",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(rx.table.row(
                    rx.table.column_header_cell("Titre",    color=MUTED, font_size="0.75rem", padding="10px 12px"),
                    rx.table.column_header_cell("Impact",   color=MUTED, font_size="0.75rem", padding="10px 12px"),
                    rx.table.column_header_cell("État",     color=MUTED, font_size="0.75rem", padding="10px 12px"),
                    rx.table.column_header_cell("Date",     color=MUTED, font_size="0.75rem", padding="10px 12px"),
                    rx.table.column_header_cell("",         padding="10px 12px"),
                ), background="#10121f"),
                rx.table.body(rx.foreach(TicketsState.tickets, ticket_row)),
                width="100%",
            ),
            background=CARD_BG, border=f"1px solid {BORDER}", border_radius="14px", overflow="hidden", width="100%",
        ),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(rx.text("Nouveau ticket", color=TEXT, font_weight="700")),
                rx.vstack(
                    rx.input(placeholder="Titre *", value=TicketsState.form["titre"], on_change=lambda v: TicketsState.set_field("titre", v), background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px", width="100%"),
                    rx.text_area(placeholder="Description", value=TicketsState.form["description"], on_change=lambda v: TicketsState.set_field("description", v), background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px", width="100%"),
                    rx.select(IMPACTS, value=TicketsState.form["impact"], on_change=lambda v: TicketsState.set_field("impact", v), background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px"),
                    rx.hstack(
                        rx.button("Annuler", on_click=TicketsState.close_form, background="transparent", color=MUTED, border=f"1px solid {BORDER}", border_radius="8px", cursor="pointer"),
                        rx.button("Créer", on_click=TicketsState.create, background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)", color="white", border_radius="8px", cursor="pointer"),
                        spacing="3", justify="end", width="100%",
                    ),
                    spacing="3", width="100%",
                ),
                background="#151728", border=f"1px solid {BORDER}", border_radius="16px", padding="1.5rem", max_width="480px",
            ),
            open=TicketsState.show_form,
        ),
        spacing="4", width="100%", on_mount=TicketsState.load,
    )


def tickets_page() -> rx.Component:
    return page_layout(tickets_content(), "Tickets")
