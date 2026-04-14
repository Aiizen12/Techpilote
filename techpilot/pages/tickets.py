import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
from techpilot.state.models import TicketItem
from techpilot.state.auth import AuthState
from techpilot.db.activity import log_activity
import uuid
import base64
from datetime import datetime

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
CARD_BG = "#111524"
BORDER  = "#1c2138"
PRIMARY = "#6366f1"
RED     = "#ef4444"
GREEN   = "#22c55e"

IMPACTS = ["basse", "normale", "haute", "critique"]

IMPACT_CONFIG = {
    "basse":    {"label": "Faible",    "color": "#6ee7b7", "bg": "rgba(34,197,94,0.15)",   "border_on": "rgba(34,197,94,0.5)"},
    "normale":  {"label": "Modéré",    "color": "#93c5fd", "bg": "rgba(59,130,246,0.15)",  "border_on": "rgba(59,130,246,0.5)"},
    "haute":    {"label": "Haute",     "color": "#fcd34d", "bg": "rgba(245,158,11,0.15)",  "border_on": "rgba(245,158,11,0.5)"},
    "critique": {"label": "Critique",  "color": "#f87171", "bg": "rgba(239,68,68,0.15)",   "border_on": "rgba(239,68,68,0.5)"},
}


class TicketsState(rx.State):
    tickets: list[TicketItem] = []
    tab: str = "tous"
    count_en_cours: int = 0
    count_resolus: int = 0
    show_form: bool = False
    technicians: list[dict] = []
    form: dict = {
        "titre": "", "ticket_pere": "", "description": "",
        "impact": "normale", "perimetre": "", "technicien_id": "",
        "technicien_nom": "", "etat": "en_cours", "notes": "",
    }

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
                ticket_pere=x.get("ticket_pere") or "",
                description=x.get("description") or "",
                impact=x.get("impact") or "",
                perimetre=x.get("perimetre") or "",
                technicien_id=str(x.get("technicien_id") or ""),
                technicien_nom=x.get("technicien_nom") or "",
                etat=x.get("etat") or "",
                notes=x.get("notes") or "",
                date_creation=x.get("date_creation") or "",
            )
            for x in filtered
        ]
        # Load techs for selector
        self.technicians = [
            {"id": str(t.get("id") or ""), "nom": t.get("nom") or ""}
            for t in (db.get("technicians") or [])
        ]

    def set_tab(self, val: str):
        self.tab = val
        self.load()

    def open_form(self):
        self.form = {
            "titre": "", "ticket_pere": "", "description": "",
            "impact": "normale", "perimetre": "", "technicien_id": "",
            "technicien_nom": "", "etat": "en_cours", "notes": "",
        }
        self.show_form = True

    def close_form(self):
        self.show_form = False

    def set_field(self, field: str, val: str):
        self.form = {**self.form, field: val}

    def set_impact(self, val: str):
        self.form = {**self.form, "impact": val}

    def set_etat(self, val: str):
        self.form = {**self.form, "etat": val}

    def set_tech(self, tid: str):
        tid = "" if tid == "_none" else tid
        nom = ""
        for t in self.technicians:
            if t.get("id") == tid:
                nom = t.get("nom") or ""
        self.form = {**self.form, "technicien_id": tid, "technicien_nom": nom}

    async def create(self):
        if not self.form.get("titre"):
            return
        auth = await self.get_state(AuthState)
        db = load_db()
        if "tickets" not in db:
            db["tickets"] = []
        titre = self.form.get("titre", "")
        db["tickets"].append({
            "id": str(uuid.uuid4()),
            "titre":          titre,
            "ticket_pere":    self.form.get("ticket_pere", ""),
            "description":    self.form.get("description", ""),
            "impact":         self.form.get("impact", "normale"),
            "perimetre":      self.form.get("perimetre", ""),
            "technicien_id":  self.form.get("technicien_id", ""),
            "technicien_nom": self.form.get("technicien_nom", ""),
            "etat":           self.form.get("etat", "en_cours"),
            "notes":          self.form.get("notes", ""),
            "date_creation":      datetime.utcnow().isoformat(),
            "date_modification":  datetime.utcnow().isoformat(),
            "date_resolution":    None,
        })
        save_db(db)
        log_activity(auth.user_nom, "CREATE", "ticket", f"Incident: {titre}")
        self.show_form = False
        self.load()
        yield rx.toast.success(f"Incident « {titre} » déclaré.")

    async def resolve(self, tid: str):
        auth = await self.get_state(AuthState)
        db = load_db()
        for t in db.get("tickets") or []:
            if t.get("id") == tid:
                t["etat"] = "resolu"
                t["date_resolution"]   = datetime.utcnow().isoformat()
                t["date_modification"] = datetime.utcnow().isoformat()
                log_activity(auth.user_nom, "UPDATE", "ticket", f"Résolu: {t.get('titre', tid[:8])}")
                yield rx.toast.success("Incident marqué comme résolu.")
        save_db(db)
        self.load()

    async def delete(self, tid: str):
        auth = await self.get_state(AuthState)
        db = load_db()
        ticket = next((t for t in (db.get("tickets") or []) if t.get("id") == tid), None)
        db["tickets"] = [t for t in (db.get("tickets") or []) if t.get("id") != tid]
        save_db(db)
        if ticket:
            log_activity(auth.user_nom, "DELETE", "ticket", f"Supprimé: {ticket.get('titre', tid[:8])}")
            yield rx.toast.warning(f"Incident « {ticket.get('titre', '')} » supprimé.")
        self.load()

    def export_csv(self):
        def esc(v: str) -> str:
            return '"' + str(v or "").replace('"', '""') + '"'

        db = load_db()
        tickets = db.get("tickets") or []
        rows = ["ID,Titre,Ticket père,Impact,Périmètre,Technicien,État,Notes,Date création"]
        for t in tickets:
            rows.append(",".join([
                esc(str(t.get("id", ""))[:8]),
                esc(t.get("titre", "")),
                esc(t.get("ticket_pere", "")),
                esc(t.get("impact", "")),
                esc(t.get("perimetre", "")),
                esc(t.get("technicien_nom", "")),
                esc(t.get("etat", "")),
                esc(t.get("notes", "")),
                esc(str(t.get("date_creation", ""))[:10]),
            ]))
        csv = "\n".join(rows)
        b64 = base64.b64encode(csv.encode("utf-8")).decode()
        yield rx.call_script(f"""
var csv = atob('{b64}');
var blob = new Blob([csv], {{type:'text/csv;charset=utf-8;'}});
var url = URL.createObjectURL(blob);
var a = document.createElement('a');
a.href = url;
a.download = 'incidents_' + new Date().toISOString().slice(0,10) + '.csv';
document.body.appendChild(a); a.click();
document.body.removeChild(a); URL.revokeObjectURL(url);
""")


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


def _impact_color(impact) -> rx.Var:
    return rx.cond(impact == "critique", "#f87171",
           rx.cond(impact == "haute",    "#fcd34d",
           rx.cond(impact == "normale",  "#93c5fd", "#6ee7b7")))


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


def _impact_btn(val: str, label: str, color: str, bg: str) -> rx.Component:
    is_active = TicketsState.form["impact"] == val
    return rx.box(
        rx.vstack(
            rx.text(label, font_size="0.78rem", font_weight="600",
                    color=rx.cond(is_active, color, MUTED)),
            spacing="1",
            align="center",
        ),
        padding="0.5rem 0.375rem",
        border_radius="10px",
        border=rx.cond(is_active, f"2px solid {color}88", f"2px solid {BORDER}"),
        background=rx.cond(is_active, bg, "rgba(255,255,255,0.02)"),
        cursor="pointer",
        text_align="center",
        transition="all 0.15s",
        on_click=TicketsState.set_impact(val),
        flex="1",
    )


def _etat_btn(val: str, label: str, icon_name: str, color: str, bg: str) -> rx.Component:
    is_active = TicketsState.form["etat"] == val
    return rx.box(
        rx.hstack(
            rx.icon(icon_name, size=15, color=rx.cond(is_active, "white", MUTED)),
            rx.text(label, font_size="0.85rem", font_weight="600",
                    color=rx.cond(is_active, "white", MUTED)),
            spacing="2",
            align="center",
            justify="center",
        ),
        padding="0.7rem",
        border_radius="12px",
        border=rx.cond(is_active, "none", f"1.5px dashed {BORDER}"),
        background=rx.cond(is_active, bg, "rgba(255,255,255,0.03)"),
        cursor="pointer",
        text_align="center",
        transition="all 0.2s",
        on_click=TicketsState.set_etat(val),
        flex="1",
    )


def incident_row(t: TicketItem) -> rx.Component:
    border_color = rx.cond(t["etat"] == "en_cours", RED, GREEN)
    num_display  = rx.cond(t["id"] != "", t["id"][:6].upper(), "------")
    date_display = rx.cond(t["date_creation"] != "", t["date_creation"][:10], "")

    return rx.box(
        rx.hstack(
            rx.cond(
                t["etat"] == "en_cours",
                rx.icon("clock", size=16, color=RED),
                rx.icon("circle-check", size=16, color=GREEN),
            ),
            rx.box(
                rx.text(num_display, color=MUTED, font_size="0.72rem", font_family="monospace"),
                background="rgba(255,255,255,0.05)",
                border=f"1px solid {BORDER}",
                border_radius="4px",
                padding="2px 6px",
            ),
            rx.text(t["titre"], color=TEXT, font_size="0.875rem", font_weight="500", flex="1"),
            _severity_badge(t["impact"]),
            rx.cond(
                t["technicien_nom"] != "",
                rx.text(t["technicien_nom"], color=MUTED, font_size="0.78rem"),
                rx.text("Non assigné", color=MUTED, font_size="0.78rem"),
            ),
            rx.text(date_display, color=MUTED, font_size="0.78rem"),
            rx.hstack(
                rx.cond(
                    t["etat"] == "en_cours",
                    rx.icon_button(
                        rx.icon("circle-check", size=13),
                        on_click=TicketsState.resolve(t["id"]),
                        background="transparent",
                        color=MUTED,
                        size="1",
                        cursor="pointer",
                        _hover={"color": GREEN},
                        title="Marquer comme résolu",
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


def _tech_pill(t: dict) -> rx.Component:
    is_active = TicketsState.form["technicien_id"] == t["id"]
    return rx.button(
        t["nom"],
        on_click=TicketsState.set_tech(t["id"]),
        style={
            "background": rx.cond(is_active, "rgba(99,102,241,0.2)", "transparent"),
            "color": rx.cond(is_active, PRIMARY, MUTED),
            "border": rx.cond(is_active, "1px solid rgba(99,102,241,0.4)", f"1px solid {BORDER}"),
            "border_radius": "20px", "padding": "3px 10px",
            "font_size": "0.75rem", "cursor": "pointer",
            "white_space": "nowrap", "font_weight": "500",
        },
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
                rx.icon("download", size=15),
                "Exporter CSV",
                on_click=TicketsState.export_csv,
                background="rgba(239,68,68,0.1)",
                color=RED,
                border=f"1px solid rgba(239,68,68,0.3)",
                border_radius="8px",
                padding="8px 16px",
                font_size="0.82rem",
                font_weight="600",
                cursor="pointer",
                spacing="2",
                _hover={"background": "rgba(239,68,68,0.2)"},
            ),
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
            _tab_btn("Tous",     "tous",     TicketsState.tab),
            _tab_btn("En cours", "en_cours", TicketsState.tab),
            _tab_btn("Résolus",  "resolu",   TicketsState.tab),
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

                # Header gradient
                rx.box(
                    rx.hstack(
                        rx.box(
                            rx.icon("shield-alert", size=18, color="white"),
                            background="rgba(255,255,255,0.2)",
                            border_radius="10px",
                            padding="8px",
                            display="flex",
                            align_items="center",
                            justify_content="center",
                        ),
                        rx.vstack(
                            rx.text("Déclarer un incident", color="white", font_size="1rem", font_weight="700"),
                            rx.text("Renseigner les informations de l'incident",
                                    color="rgba(255,255,255,0.7)", font_size="0.72rem"),
                            spacing="0",
                            align="start",
                        ),
                        spacing="3",
                        align="center",
                    ),
                    background=f"linear-gradient(135deg, {RED}, #b91c1c)",
                    border_radius="12px 12px 0 0",
                    padding="1.25rem 1.5rem",
                    margin="-24px -24px 0 -24px",
                ),

                rx.vstack(
                    # Ticket père + Titre
                    rx.hstack(
                        rx.vstack(
                            rx.text("TICKET PÈRE", color=MUTED, font_size="0.68rem", font_weight="700",
                                    letter_spacing="0.07em"),
                            rx.input(
                                placeholder="INC-12345",
                                value=TicketsState.form["ticket_pere"],
                                on_change=lambda v: TicketsState.set_field("ticket_pere", v),
                                background="#1c2138", color=TEXT,
                                border=f"1px solid {BORDER}", border_radius="8px",
                                font_family="monospace", font_size="0.82rem",
                            ),
                            spacing="1",
                            align="start",
                            width="160px",
                        ),
                        rx.vstack(
                            rx.hstack(
                                rx.text("TITRE", color=MUTED, font_size="0.68rem", font_weight="700",
                                        letter_spacing="0.07em"),
                                rx.text("*", color=RED, font_size="0.75rem"),
                                spacing="1",
                            ),
                            rx.input(
                                placeholder="Titre court et descriptif",
                                value=TicketsState.form["titre"],
                                on_change=lambda v: TicketsState.set_field("titre", v),
                                background="#1c2138", color=TEXT,
                                border=f"1px solid {BORDER}", border_radius="8px", width="100%",
                            ),
                            spacing="1",
                            align="start",
                            flex="1",
                        ),
                        spacing="3",
                        align="end",
                        width="100%",
                    ),

                    # Description
                    rx.vstack(
                        rx.text("DESCRIPTION DE L'INCIDENT", color=MUTED, font_size="0.68rem",
                                font_weight="700", letter_spacing="0.07em"),
                        rx.text_area(
                            placeholder="Décrivez l'incident : symptômes observés, utilisateurs impactés, périmètre...",
                            value=TicketsState.form["description"],
                            on_change=lambda v: TicketsState.set_field("description", v),
                            background="#1c2138", color=TEXT,
                            border=f"1px solid {BORDER}", border_radius="8px", width="100%",
                            rows="3",
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),

                    # Impact (4 boutons)
                    rx.vstack(
                        rx.text("IMPACT", color=MUTED, font_size="0.68rem", font_weight="700",
                                letter_spacing="0.07em"),
                        rx.hstack(
                            _impact_btn("basse",    "Faible",   "#6ee7b7", "rgba(34,197,94,0.15)"),
                            _impact_btn("normale",  "Modéré",   "#93c5fd", "rgba(59,130,246,0.15)"),
                            _impact_btn("haute",    "Haute",    "#fcd34d", "rgba(245,158,11,0.15)"),
                            _impact_btn("critique", "Critique", "#f87171", "rgba(239,68,68,0.15)"),
                            spacing="2",
                            width="100%",
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),

                    # Périmètre + Technicien
                    rx.hstack(
                        rx.vstack(
                            rx.text("PÉRIMÈTRE", color=MUTED, font_size="0.68rem", font_weight="700",
                                    letter_spacing="0.07em"),
                            rx.input(
                                placeholder="Réseau, Impression...",
                                value=TicketsState.form["perimetre"],
                                on_change=lambda v: TicketsState.set_field("perimetre", v),
                                background="#1c2138", color=TEXT,
                                border=f"1px solid {BORDER}", border_radius="8px", width="100%",
                            ),
                            spacing="1",
                            align="start",
                            flex="1",
                        ),
                        rx.vstack(
                            rx.text("TECHNICIEN RÉFÉRENT", color=MUTED, font_size="0.68rem",
                                    font_weight="700", letter_spacing="0.07em"),
                            rx.flex(
                                rx.button(
                                    "Non assigné",
                                    on_click=TicketsState.set_tech("_none"),
                                    style={
                                        "background": rx.cond(
                                            TicketsState.form["technicien_id"] == "",
                                            "rgba(99,102,241,0.2)", "transparent"
                                        ),
                                        "color": rx.cond(
                                            TicketsState.form["technicien_id"] == "",
                                            PRIMARY, MUTED
                                        ),
                                        "border": rx.cond(
                                            TicketsState.form["technicien_id"] == "",
                                            "1px solid rgba(99,102,241,0.4)", f"1px solid {BORDER}"
                                        ),
                                        "border_radius": "20px", "padding": "3px 10px",
                                        "font_size": "0.75rem", "cursor": "pointer",
                                        "white_space": "nowrap", "font_weight": "500",
                                    },
                                ),
                                rx.foreach(TicketsState.technicians, _tech_pill),
                                flex_wrap="wrap", gap="6px",
                            ),
                            spacing="1",
                            align="start",
                            flex="1",
                        ),
                        spacing="3",
                        width="100%",
                    ),

                    # État
                    rx.vstack(
                        rx.text("ÉTAT DE L'INCIDENT", color=MUTED, font_size="0.68rem",
                                font_weight="700", letter_spacing="0.07em"),
                        rx.hstack(
                            _etat_btn("en_cours", "En cours", "clock",
                                      RED, f"linear-gradient(135deg, {RED}, #b91c1c)"),
                            _etat_btn("resolu",   "Résolu",   "circle-check",
                                      GREEN, "linear-gradient(135deg, #059669, #10b981)"),
                            spacing="3",
                            width="100%",
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),

                    # Notes
                    rx.vstack(
                        rx.text("NOTES / ACTIONS MENÉES", color=MUTED, font_size="0.68rem",
                                font_weight="700", letter_spacing="0.07em"),
                        rx.text_area(
                            placeholder="Actions effectuées, contournements mis en place...",
                            value=TicketsState.form["notes"],
                            on_change=lambda v: TicketsState.set_field("notes", v),
                            background="#1c2138", color=TEXT,
                            border=f"1px solid {BORDER}", border_radius="8px", width="100%",
                            rows="2",
                        ),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),

                    # Boutons
                    rx.hstack(
                        rx.button("Annuler", on_click=TicketsState.close_form,
                                  background="transparent", color=MUTED,
                                  border=f"1px solid {BORDER}", border_radius="8px", cursor="pointer"),
                        rx.button(
                            rx.icon("check", size=15),
                            "Créer l'incident",
                            on_click=TicketsState.create,
                            background=f"linear-gradient(135deg, {RED}, #b91c1c)",
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

                background="#111524",
                border=f"1px solid {BORDER}",
                border_radius="16px",
                padding="24px",
                max_width="560px",
                overflow="hidden",
            ),
            open=TicketsState.show_form,
        ),

        spacing="4",
        width="100%",
        on_mount=TicketsState.load,
    )


def tickets_page() -> rx.Component:
    return page_layout(tickets_content(), "")
