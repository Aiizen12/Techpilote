import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
from techpilot.state.models import TicketItem, MatrixSuggestion
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
    # Liaison matrice
    matrix_search: str = ""
    matrix_results: list[MatrixSuggestion] = []
    matrix_selected: MatrixSuggestion = MatrixSuggestion()
    # Champs d'escalade stockés en vars simples (fiables entre handlers async)
    esc_perimetre: str = ""
    esc_typologie: str = ""
    esc_interlocuteur: str = ""
    esc_n2: str = ""
    esc_wp_n2: str = ""
    # Détail ticket
    show_detail: bool = False
    detail_ticket: TicketItem = TicketItem()
    detail_edit_mode: bool = False
    detail_form: dict = {
        "titre": "", "ticket_pere": "", "description": "",
        "impact": "normale", "perimetre": "", "technicien_id": "",
        "technicien_nom": "", "etat": "en_cours", "notes": "",
    }

    def open_detail(self, tid: str):
        ticket = next((t for t in self.tickets if t.id == tid), None)
        if ticket:
            self.detail_ticket = ticket
            self.detail_edit_mode = False
            self.show_detail = True

    def close_detail(self):
        self.show_detail = False
        self.detail_edit_mode = False

    def start_edit(self):
        t = self.detail_ticket
        self.detail_form = {
            "titre":          t.titre,
            "ticket_pere":    t.ticket_pere,
            "description":    t.description,
            "impact":         t.impact if t.impact else "normale",
            "perimetre":      t.perimetre,
            "technicien_id":  t.technicien_id,
            "technicien_nom": t.technicien_nom,
            "etat":           t.etat if t.etat else "en_cours",
            "notes":          t.notes,
        }
        self.detail_edit_mode = True

    def cancel_edit(self):
        self.detail_edit_mode = False
        self.detail_form = {
            "titre": "", "ticket_pere": "", "description": "",
            "impact": "normale", "perimetre": "", "technicien_id": "",
            "technicien_nom": "", "etat": "en_cours", "notes": "",
        }

    def set_detail_field(self, field: str, val: str):
        self.detail_form = {**self.detail_form, field: val}

    def set_detail_impact(self, val: str):
        self.detail_form = {**self.detail_form, "impact": val}

    def set_detail_etat(self, val: str):
        self.detail_form = {**self.detail_form, "etat": val}

    def set_detail_tech(self, tid: str):
        tid = "" if tid == "_none" else tid
        nom = ""
        for t in self.technicians:
            if t.get("id") == tid:
                nom = t.get("nom") or ""
        self.detail_form = {**self.detail_form, "technicien_id": tid, "technicien_nom": nom}

    def save_detail(self):
        tid = self.detail_ticket.id
        db  = load_db()
        idx = next((i for i, x in enumerate(db.get("tickets") or []) if str(x.get("id")) == tid), -1)
        if idx == -1:
            return
        t = db["tickets"][idx]
        t["titre"]          = self.detail_form.get("titre", t.get("titre", ""))
        t["ticket_pere"]    = self.detail_form.get("ticket_pere", "")
        t["description"]    = self.detail_form.get("description", "")
        t["impact"]         = self.detail_form.get("impact", t.get("impact", "normale"))
        t["perimetre"]      = self.detail_form.get("perimetre", "")
        t["technicien_id"]  = self.detail_form.get("technicien_id", "")
        t["technicien_nom"] = self.detail_form.get("technicien_nom", "")
        t["etat"]           = self.detail_form.get("etat", t.get("etat", "en_cours"))
        t["notes"]          = self.detail_form.get("notes", "")
        t["date_modification"] = datetime.utcnow().isoformat()
        if t["etat"] == "resolu" and not t.get("date_resolution"):
            t["date_resolution"] = datetime.utcnow().isoformat()
        save_db(db)
        log_activity("", "UPDATE", "ticket", f"Modifié: {t.get('titre', tid[:8])}")
        self.detail_edit_mode = False
        self.load()
        # Refresh le détail avec les nouvelles données
        updated = next((tk for tk in self.tickets if tk.id == tid), None)
        if updated:
            self.detail_ticket = updated
        return rx.toast.success("Incident mis à jour.")

    async def go_to_escalade(self, search_query: str):
        """Navigue vers la matrice d'escalade avec la recherche pré-remplie."""
        from techpilot.state.escalade import EscaladeState
        esc = await self.get_state(EscaladeState)
        esc.search = search_query
        esc.mode   = "recherche"
        yield rx.redirect("/escalade")

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
                escalade_interlocuteur=x.get("escalade_interlocuteur") or "",
                escalade_n2=x.get("escalade_n2") or "",
                escalade_wp_n2=x.get("escalade_wp_n2") or "",
                escalade_perimetre=x.get("escalade_perimetre") or "",
                escalade_typologie=x.get("escalade_typologie") or "",
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
            "escalade_perimetre": "", "escalade_typologie": "",
            "escalade_interlocuteur": "", "escalade_n2": "", "escalade_wp_n2": "",
        }
        self.matrix_search = ""
        self.matrix_results = []
        self.matrix_selected = MatrixSuggestion()
        self.esc_perimetre = ""
        self.esc_typologie = ""
        self.esc_interlocuteur = ""
        self.esc_n2 = ""
        self.esc_wp_n2 = ""
        self.show_form = True

    def close_form(self):
        self.show_form = False

    def set_field(self, field: str, val: str):
        self.form = {**self.form, field: val}

    def set_impact(self, val: str):
        self.form = {**self.form, "impact": val}

    def set_etat(self, val: str):
        self.form = {**self.form, "etat": val}

    # ── Liaison matrice ────────────────────────────────────────────────────────

    def search_matrix(self, val: str):
        self.matrix_search = val
        if not val or len(val) < 2:
            self.matrix_results = []
            return
        q = val.lower()
        db = load_db()
        results = []
        for r in (db.get("escalation_matrix") or []):
            perim = (r.get("perimetre") or "").lower()
            typo  = (r.get("typologie") or "").lower()
            interl = (r.get("interlocuteur") or "").lower()
            if q in perim or q in typo or q in interl:
                results.append(MatrixSuggestion(
                    key=f"{r.get('perimetre','')}|{r.get('typologie','')}",
                    perimetre=r.get("perimetre") or "",
                    typologie=r.get("typologie") or "",
                    interlocuteur=r.get("interlocuteur") or "",
                    traitement_n2n3=r.get("traitement_n2n3") or "",
                    wp_n2=r.get("wp_n2") or "",
                ))
                if len(results) >= 8:
                    break
        self.matrix_results = results

    def select_matrix(self, key: str):
        # Conservé pour compatibilité (non utilisé par l'UI)
        for r in self.matrix_results:
            if r.key == key:
                self.matrix_selected = r
                self.form = {**self.form, "perimetre": r.perimetre}
                break
        self.matrix_search = ""
        self.matrix_results = []

    def select_matrix_at(self, idx: int):
        """Sélectionne matrix_results[idx] — un seul int, le plus fiable dans rx.foreach."""
        if idx < 0 or idx >= len(self.matrix_results):
            return
        r = self.matrix_results[idx]
        perim  = r.perimetre
        typo   = r.typologie
        interl = r.interlocuteur
        n2     = r.traitement_n2n3
        wp_n2  = r.wp_n2
        self.matrix_selected = MatrixSuggestion(
            key=f"{perim}|{typo}",
            perimetre=perim,
            typologie=typo,
            interlocuteur=interl,
            traitement_n2n3=n2,
            wp_n2=wp_n2,
        )
        # Stocke tout dans le form dict (source de vérité unique pour create())
        self.form = {
            **self.form,
            "perimetre":             perim,
            "escalade_perimetre":    perim,
            "escalade_typologie":    typo,
            "escalade_interlocuteur": interl,
            "escalade_n2":           n2,
            "escalade_wp_n2":        wp_n2,
        }
        # Copie aussi dans les vars simples (pour compatibilité)
        self.esc_perimetre     = perim
        self.esc_typologie     = typo
        self.esc_interlocuteur = interl
        self.esc_n2            = n2
        self.esc_wp_n2         = wp_n2
        self.matrix_search = ""
        self.matrix_results = []

    def clear_matrix(self):
        self.matrix_selected   = MatrixSuggestion()
        self.esc_perimetre     = ""
        self.esc_typologie     = ""
        self.esc_interlocuteur = ""
        self.esc_n2            = ""
        self.esc_wp_n2         = ""
        self.form = {
            **self.form,
            "escalade_perimetre": "",
            "escalade_typologie": "",
            "escalade_interlocuteur": "",
            "escalade_n2": "",
            "escalade_wp_n2": "",
        }
        self.matrix_search = ""
        self.matrix_results = []

    def set_tech(self, tid: str):
        tid = "" if tid == "_none" else tid
        nom = ""
        for t in self.technicians:
            if t.get("id") == tid:
                nom = t.get("nom") or ""
        self.form = {**self.form, "technicien_id": tid, "technicien_nom": nom}

    def create(self):
        if not self.form.get("titre"):
            return
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
            "escalade_perimetre":     self.form.get("escalade_perimetre", self.esc_perimetre),
            "escalade_typologie":     self.form.get("escalade_typologie", self.esc_typologie),
            "escalade_interlocuteur": self.form.get("escalade_interlocuteur", self.esc_interlocuteur),
            "escalade_n2":            self.form.get("escalade_n2", self.esc_n2),
            "escalade_wp_n2":         self.form.get("escalade_wp_n2", self.esc_wp_n2),
        })
        save_db(db)
        log_activity("", "CREATE", "ticket", f"Incident: {titre}")
        self.show_form = False
        self.load()
        return rx.toast.success(f"Incident « {titre} » déclaré.")

    def resolve(self, tid: str):
        db = load_db()
        toast = None
        for t in db.get("tickets") or []:
            if t.get("id") == tid:
                t["etat"] = "resolu"
                t["date_resolution"]   = datetime.utcnow().isoformat()
                t["date_modification"] = datetime.utcnow().isoformat()
                log_activity("", "UPDATE", "ticket", f"Résolu: {t.get('titre', tid[:8])}")
                toast = rx.toast.success("Incident marqué comme résolu.")
        save_db(db)
        self.load()
        return toast

    def delete(self, tid: str):
        db = load_db()
        ticket = next((t for t in (db.get("tickets") or []) if t.get("id") == tid), None)
        db["tickets"] = [t for t in (db.get("tickets") or []) if t.get("id") != tid]
        save_db(db)
        self.load()
        if ticket:
            log_activity("", "DELETE", "ticket", f"Supprimé: {ticket.get('titre', tid[:8])}")
            return rx.toast.warning(f"Incident « {ticket.get('titre', '')} » supprimé.")

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


def _detail_impact_btn(val: str, label: str, color: str, bg: str) -> rx.Component:
    is_active = TicketsState.detail_form["impact"] == val
    return rx.box(
        rx.text(label, font_size="0.78rem", font_weight="600",
                color=rx.cond(is_active, color, MUTED)),
        padding="0.5rem 0.375rem",
        border_radius="10px",
        border=rx.cond(is_active, f"2px solid {color}88", f"2px solid {BORDER}"),
        background=rx.cond(is_active, bg, "rgba(255,255,255,0.02)"),
        cursor="pointer",
        text_align="center",
        transition="all 0.15s",
        on_click=TicketsState.set_detail_impact(val),
        flex="1",
    )


def _detail_etat_btn(val: str, label: str, icon_name: str, color: str, bg: str) -> rx.Component:
    is_active = TicketsState.detail_form["etat"] == val
    return rx.box(
        rx.hstack(
            rx.icon(icon_name, size=15, color=rx.cond(is_active, "white", MUTED)),
            rx.text(label, font_size="0.85rem", font_weight="600",
                    color=rx.cond(is_active, "white", MUTED)),
            spacing="2", align="center", justify="center",
        ),
        padding="0.7rem",
        border_radius="12px",
        border=rx.cond(is_active, "none", f"1.5px dashed {BORDER}"),
        background=rx.cond(is_active, bg, "rgba(255,255,255,0.03)"),
        cursor="pointer",
        text_align="center",
        transition="all 0.2s",
        on_click=TicketsState.set_detail_etat(val),
        flex="1",
    )


def _detail_tech_pill(t: dict) -> rx.Component:
    is_active = TicketsState.detail_form["technicien_id"] == t["id"]
    return rx.button(
        t["nom"],
        on_click=TicketsState.set_detail_tech(t["id"]),
        style={
            "background": rx.cond(is_active, "rgba(99,102,241,0.2)", "transparent"),
            "color":      rx.cond(is_active, PRIMARY, MUTED),
            "border":     rx.cond(is_active, "1px solid rgba(99,102,241,0.4)", f"1px solid {BORDER}"),
            "border_radius": "20px", "padding": "3px 10px",
            "font_size": "0.75rem", "cursor": "pointer",
            "white_space": "nowrap", "font_weight": "500",
        },
    )


def matrix_result_item(s: MatrixSuggestion, idx) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(s["perimetre"], color=MUTED, font_size="0.68rem"),
            rx.text(s["typologie"], color=TEXT, font_size="0.82rem", font_weight="500"),
            spacing="0",
            align="start",
            flex="1",
            min_width="0",
        ),
        rx.text("→ " + s["interlocuteur"], color=PRIMARY, font_size="0.72rem",
                flex_shrink="0", max_width="140px", overflow="hidden",
                text_overflow="ellipsis", white_space="nowrap"),
        spacing="3",
        align="center",
        padding="0.6rem 0.85rem",
        border_bottom=f"1px solid {BORDER}",
        cursor="pointer",
        width="100%",
        on_click=TicketsState.select_matrix_at(idx),
        _hover={"background": "rgba(99,102,241,0.08)"},
    )


def incident_row(t: TicketItem) -> rx.Component:
    border_color = rx.cond(t["etat"] == "en_cours", RED, GREEN)
    num_display  = rx.cond(t["id"] != "", t["id"][:6].upper(), "------")
    date_display = rx.cond(t["date_creation"] != "", t["date_creation"][:10], "")

    return rx.box(
        rx.hstack(
            # Contenu cliquable (flex=1, frère des boutons)
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
                    flex_shrink="0",
                ),
                rx.text(t["titre"], color=TEXT, font_size="0.875rem", font_weight="500",
                        flex="1", min_width="0", overflow="hidden",
                        text_overflow="ellipsis", white_space="nowrap"),
                _severity_badge(t["impact"]),
                rx.cond(
                    t["technicien_nom"] != "",
                    rx.text(t["technicien_nom"], color=MUTED, font_size="0.78rem",
                            white_space="nowrap", flex_shrink="0"),
                    rx.text("Non assigné", color=MUTED, font_size="0.78rem",
                            white_space="nowrap", flex_shrink="0"),
                ),
                rx.cond(
                    t["escalade_interlocuteur"] != "",
                    rx.badge(
                        rx.hstack(
                            rx.icon("git-branch", size=10),
                            rx.text("→ " + t["escalade_interlocuteur"],
                                    font_size="0.68rem", max_width="100px",
                                    overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
                            spacing="1", align="center",
                        ),
                        color_scheme="indigo", variant="soft", radius="full",
                        flex_shrink="0",
                    ),
                ),
                rx.text(date_display, color=MUTED, font_size="0.78rem",
                        white_space="nowrap", flex_shrink="0"),
                spacing="3",
                align="center",
                flex="1",
                min_width="0",
                cursor="pointer",
                on_click=TicketsState.open_detail(t["id"]),
            ),
            # Boutons action (frère, pas enfant de la zone cliquable)
            rx.cond(
                AuthState.can_manage_tickets,
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
                    flex_shrink="0",
                ),
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
        _hover={"background": "rgba(255,255,255,0.035)"},
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


def ticket_detail_dialog() -> rx.Component:
    t = TicketsState.detail_ticket
    border_color = rx.cond(t["etat"] == "en_cours", RED, GREEN)

    def _field(label: str, value) -> rx.Component:
        return rx.vstack(
            rx.text(label, color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.06em"),
            rx.text(value, color=TEXT, font_size="0.875rem"),
            spacing="0", align="start",
        )

    # ── Vue lecture ───────────────────────────────────────────────────────────
    read_view = rx.vstack(
        # Header
        rx.hstack(
            rx.box(
                rx.cond(
                    t["etat"] == "en_cours",
                    rx.icon("clock", size=18, color=RED),
                    rx.icon("circle-check", size=18, color=GREEN),
                ),
                background=rx.cond(t["etat"] == "en_cours",
                                   "rgba(239,68,68,0.12)", "rgba(34,197,94,0.12)"),
                border_radius="8px", padding="8px",
                display="flex", align_items="center", justify_content="center",
            ),
            rx.vstack(
                rx.text(t["titre"], color=TEXT, font_size="1rem", font_weight="700"),
                rx.hstack(
                    rx.box(
                        rx.text(t["id"][:6].upper(), color=MUTED,
                                font_size="0.68rem", font_family="monospace"),
                        background="rgba(255,255,255,0.05)",
                        border=f"1px solid {BORDER}",
                        border_radius="4px", padding="2px 6px",
                    ),
                    rx.cond(
                        t["etat"] == "en_cours",
                        rx.badge("En cours", color_scheme="red", variant="soft", radius="full"),
                        rx.badge("Résolu", color_scheme="green", variant="soft", radius="full"),
                    ),
                    _severity_badge(t["impact"]),
                    spacing="2", align="center",
                ),
                spacing="1", align="start",
            ),
            rx.spacer(),
            # Bouton Modifier (si droits)
            rx.cond(
                AuthState.can_manage_tickets,
                rx.icon_button(
                    rx.icon("pencil", size=14),
                    on_click=TicketsState.start_edit,
                    background="rgba(99,102,241,0.1)",
                    color=PRIMARY,
                    border=f"1px solid rgba(99,102,241,0.3)",
                    size="2", cursor="pointer",
                    border_radius="8px",
                    title="Modifier",
                    _hover={"background": "rgba(99,102,241,0.2)"},
                ),
            ),
            rx.icon_button(
                rx.icon("x", size=16),
                on_click=TicketsState.close_detail,
                background="transparent", color=MUTED,
                size="2", cursor="pointer",
                _hover={"background": "rgba(255,255,255,0.08)"},
            ),
            spacing="2", align="center", width="100%",
        ),

        rx.divider(border_color=BORDER),

        # Description
        rx.cond(
            t["description"] != "",
            rx.vstack(
                rx.text("DESCRIPTION", color=MUTED, font_size="0.68rem",
                        font_weight="700", letter_spacing="0.06em"),
                rx.text(t["description"], color=TEXT, font_size="0.875rem",
                        white_space="pre-wrap"),
                spacing="1", align="start", width="100%",
            ),
        ),

        rx.hstack(
            rx.cond(t["perimetre"] != "", _field("PÉRIMÈTRE", t["perimetre"])),
            rx.cond(
                t["technicien_nom"] != "",
                _field("TECHNICIEN", t["technicien_nom"]),
                _field("TECHNICIEN", "Non assigné"),
            ),
            rx.cond(t["ticket_pere"] != "", _field("TICKET PÈRE", t["ticket_pere"])),
            spacing="6", align="start", wrap="wrap",
        ),

        rx.cond(
            t["notes"] != "",
            rx.vstack(
                rx.text("NOTES / ACTIONS MENÉES", color=MUTED, font_size="0.68rem",
                        font_weight="700", letter_spacing="0.06em"),
                rx.box(
                    rx.text(t["notes"], color=TEXT, font_size="0.875rem",
                            white_space="pre-wrap"),
                    background="rgba(255,255,255,0.03)",
                    border=f"1px solid {BORDER}",
                    border_radius="8px", padding="0.75rem",
                    width="100%",
                ),
                spacing="1", align="start", width="100%",
            ),
        ),

        # ── Escalade — cliquable vers la matrice ──────────────────────────────
        rx.cond(
            t["escalade_interlocuteur"] != "",
            rx.vstack(
                rx.hstack(
                    rx.icon("git-branch", size=13, color=PRIMARY),
                    rx.text("ESCALADE", color=MUTED, font_size="0.68rem",
                            font_weight="700", letter_spacing="0.06em"),
                    rx.text("· cliquer pour voir dans la matrice", color=MUTED,
                            font_size="0.62rem", font_style="italic"),
                    spacing="1", align="center",
                ),
                rx.hstack(
                    rx.vstack(
                        rx.vstack(
                            rx.text("Interlocuteur", color=MUTED, font_size="0.65rem",
                                    font_weight="700", letter_spacing="0.05em"),
                            rx.text(t["escalade_interlocuteur"], color=TEXT,
                                    font_size="0.85rem", font_weight="600"),
                            spacing="0", align="start",
                        ),
                        rx.cond(
                            t["escalade_n2"] != "",
                            rx.vstack(
                                rx.text("Traitement N2/N3", color=MUTED, font_size="0.65rem",
                                        font_weight="700", letter_spacing="0.05em"),
                                rx.text(t["escalade_n2"], color=TEXT, font_size="0.85rem"),
                                spacing="0", align="start",
                            ),
                        ),
                        rx.cond(
                            t["escalade_wp_n2"] != "",
                            rx.vstack(
                                rx.text("WP N2", color=MUTED, font_size="0.65rem",
                                        font_weight="700", letter_spacing="0.05em"),
                                rx.text(t["escalade_wp_n2"], color=TEXT, font_size="0.85rem"),
                                spacing="0", align="start",
                            ),
                        ),
                        spacing="3", align="start", flex="1",
                    ),
                    rx.icon("arrow-right", size=16, color=PRIMARY, flex_shrink="0"),
                    spacing="3", align="center", width="100%",
                    padding="0.75rem",
                    background="rgba(99,102,241,0.07)",
                    border=f"1px solid rgba(99,102,241,0.2)",
                    border_radius="8px",
                    cursor="pointer",
                    on_click=TicketsState.go_to_escalade(
                        t["escalade_perimetre"] + " " + t["escalade_interlocuteur"]
                    ),
                    _hover={"background": "rgba(99,102,241,0.14)", "border_color": "rgba(99,102,241,0.4)"},
                    transition="all 0.15s",
                ),
                spacing="2", align="start", width="100%",
            ),
        ),

        rx.text(
            rx.cond(t["date_creation"] != "", "Créé le " + t["date_creation"][:10], ""),
            color=MUTED, font_size="0.72rem",
        ),

        spacing="4", width="100%",
    )

    # ── Vue édition ───────────────────────────────────────────────────────────
    edit_view = rx.vstack(
        # Header édition
        rx.hstack(
            rx.box(
                rx.icon("pencil", size=16, color="white"),
                background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                border_radius="8px", padding="8px",
                display="flex", align_items="center", justify_content="center",
            ),
            rx.vstack(
                rx.text("Modifier l'incident", color=TEXT, font_size="1rem", font_weight="700"),
                rx.text(t["id"][:6].upper(), color=MUTED, font_size="0.68rem", font_family="monospace"),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.icon_button(
                rx.icon("x", size=16),
                on_click=TicketsState.cancel_edit,
                background="transparent", color=MUTED,
                size="2", cursor="pointer",
                _hover={"background": "rgba(255,255,255,0.08)"},
            ),
            spacing="3", align="center", width="100%",
        ),

        rx.divider(border_color=BORDER),

        # Ticket père + Titre
        rx.hstack(
            rx.vstack(
                rx.text("TICKET PÈRE", color=MUTED, font_size="0.68rem", font_weight="700",
                        letter_spacing="0.07em"),
                rx.input(
                    placeholder="INC-12345",
                    value=TicketsState.detail_form["ticket_pere"],
                    on_change=lambda v: TicketsState.set_detail_field("ticket_pere", v),
                    background="#1c2138", color=TEXT,
                    border=f"1px solid {BORDER}", border_radius="8px",
                    font_family="monospace", font_size="0.82rem",
                ),
                spacing="1", align="start", width="150px",
            ),
            rx.vstack(
                rx.text("TITRE *", color=MUTED, font_size="0.68rem", font_weight="700",
                        letter_spacing="0.07em"),
                rx.input(
                    placeholder="Titre de l'incident",
                    value=TicketsState.detail_form["titre"],
                    on_change=lambda v: TicketsState.set_detail_field("titre", v),
                    background="#1c2138", color=TEXT,
                    border=f"1px solid {BORDER}", border_radius="8px", width="100%",
                ),
                spacing="1", align="start", flex="1",
            ),
            spacing="3", align="end", width="100%",
        ),

        # Description
        rx.vstack(
            rx.text("DESCRIPTION", color=MUTED, font_size="0.68rem", font_weight="700",
                    letter_spacing="0.07em"),
            rx.text_area(
                placeholder="Symptômes, utilisateurs impactés, périmètre…",
                value=TicketsState.detail_form["description"],
                on_change=lambda v: TicketsState.set_detail_field("description", v),
                background="#1c2138", color=TEXT,
                border=f"1px solid {BORDER}", border_radius="8px", width="100%", rows="3",
            ),
            spacing="1", align="start", width="100%",
        ),

        # Impact
        rx.vstack(
            rx.text("IMPACT", color=MUTED, font_size="0.68rem", font_weight="700",
                    letter_spacing="0.07em"),
            rx.hstack(
                _detail_impact_btn("basse",    "Faible",   "#6ee7b7", "rgba(34,197,94,0.15)"),
                _detail_impact_btn("normale",  "Modéré",   "#93c5fd", "rgba(59,130,246,0.15)"),
                _detail_impact_btn("haute",    "Haute",    "#fcd34d", "rgba(245,158,11,0.15)"),
                _detail_impact_btn("critique", "Critique", "#f87171", "rgba(239,68,68,0.15)"),
                spacing="2", width="100%",
            ),
            spacing="1", align="start", width="100%",
        ),

        # Périmètre
        rx.vstack(
            rx.text("PÉRIMÈTRE", color=MUTED, font_size="0.68rem", font_weight="700",
                    letter_spacing="0.07em"),
            rx.input(
                placeholder="Réseau, Impression…",
                value=TicketsState.detail_form["perimetre"],
                on_change=lambda v: TicketsState.set_detail_field("perimetre", v),
                background="#1c2138", color=TEXT,
                border=f"1px solid {BORDER}", border_radius="8px", width="100%",
            ),
            spacing="1", align="start", width="100%",
        ),

        # Technicien
        rx.vstack(
            rx.text("TECHNICIEN RÉFÉRENT", color=MUTED, font_size="0.68rem", font_weight="700",
                    letter_spacing="0.07em"),
            rx.flex(
                rx.button(
                    "Non assigné",
                    on_click=TicketsState.set_detail_tech("_none"),
                    style={
                        "background": rx.cond(
                            TicketsState.detail_form["technicien_id"] == "",
                            "rgba(99,102,241,0.2)", "transparent"
                        ),
                        "color": rx.cond(
                            TicketsState.detail_form["technicien_id"] == "",
                            PRIMARY, MUTED
                        ),
                        "border": rx.cond(
                            TicketsState.detail_form["technicien_id"] == "",
                            "1px solid rgba(99,102,241,0.4)", f"1px solid {BORDER}"
                        ),
                        "border_radius": "20px", "padding": "3px 10px",
                        "font_size": "0.75rem", "cursor": "pointer",
                        "white_space": "nowrap", "font_weight": "500",
                    },
                ),
                rx.foreach(TicketsState.technicians, _detail_tech_pill),
                flex_wrap="wrap", gap="6px",
            ),
            spacing="1", align="start", width="100%",
        ),

        # État
        rx.vstack(
            rx.text("ÉTAT", color=MUTED, font_size="0.68rem", font_weight="700",
                    letter_spacing="0.07em"),
            rx.hstack(
                _detail_etat_btn("en_cours", "En cours", "clock",
                                 RED, f"linear-gradient(135deg, {RED}, #b91c1c)"),
                _detail_etat_btn("resolu",   "Résolu",   "circle-check",
                                 GREEN, "linear-gradient(135deg, #059669, #10b981)"),
                spacing="3", width="100%",
            ),
            spacing="1", align="start", width="100%",
        ),

        # Notes
        rx.vstack(
            rx.text("NOTES / ACTIONS MENÉES", color=MUTED, font_size="0.68rem", font_weight="700",
                    letter_spacing="0.07em"),
            rx.text_area(
                placeholder="Actions effectuées, contournements mis en place…",
                value=TicketsState.detail_form["notes"],
                on_change=lambda v: TicketsState.set_detail_field("notes", v),
                background="#1c2138", color=TEXT,
                border=f"1px solid {BORDER}", border_radius="8px", width="100%", rows="2",
            ),
            spacing="1", align="start", width="100%",
        ),

        # Boutons
        rx.hstack(
            rx.button(
                "Annuler",
                on_click=TicketsState.cancel_edit,
                background="transparent", color=MUTED,
                border=f"1px solid {BORDER}", border_radius="8px", cursor="pointer",
            ),
            rx.button(
                rx.icon("check", size=15),
                "Enregistrer",
                on_click=TicketsState.save_detail,
                background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                color="white", border_radius="8px", cursor="pointer",
                font_weight="700", spacing="2",
            ),
            spacing="3", justify="end", width="100%",
        ),

        spacing="4", width="100%",
    )

    return rx.dialog.root(
        rx.dialog.content(
            rx.cond(TicketsState.detail_edit_mode, edit_view, read_view),
            background="#111524",
            border=f"1px solid {BORDER}",
            border_top=f"3px solid " + border_color,
            border_radius="16px",
            padding="1.5rem",
            max_width="560px",
            overflow_y="auto",
            max_height="90vh",
        ),
        open=TicketsState.show_detail,
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
            rx.cond(
                AuthState.can_manage_tickets,
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
                    width="100%",
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

                    # Lien matrice
                    rx.vstack(
                        rx.hstack(
                            rx.icon("git-branch", size=13, color=PRIMARY),
                            rx.text("LIEN MATRICE D'ESCALADE", color=MUTED, font_size="0.68rem",
                                    font_weight="700", letter_spacing="0.07em"),
                            rx.text("(optionnel)", color=MUTED, font_size="0.65rem"),
                            spacing="2", align="center",
                        ),
                        rx.cond(
                            TicketsState.matrix_selected.key != "",
                            # Entrée sélectionnée
                            rx.hstack(
                                rx.box(
                                    rx.vstack(
                                        rx.hstack(
                                            rx.icon("git-branch", size=12, color=PRIMARY),
                                            rx.text(
                                                TicketsState.matrix_selected.perimetre + " · " +
                                                TicketsState.matrix_selected.typologie,
                                                color=TEXT, font_size="0.8rem", font_weight="600",
                                            ),
                                            spacing="2", align="center",
                                        ),
                                        rx.hstack(
                                            rx.text("→", color=MUTED, font_size="0.75rem"),
                                            rx.text(TicketsState.matrix_selected.interlocuteur,
                                                    color=PRIMARY, font_size="0.78rem", font_weight="600"),
                                            spacing="1", align="center",
                                        ),
                                        rx.cond(
                                            TicketsState.matrix_selected.traitement_n2n3 != "",
                                            rx.text(TicketsState.matrix_selected.traitement_n2n3,
                                                    color=MUTED, font_size="0.72rem",
                                                    overflow="hidden", display="-webkit-box",
                                                    style={"-webkit-line-clamp": "2", "-webkit-box-orient": "vertical"}),
                                        ),
                                        spacing="1", align="start",
                                    ),
                                    background="rgba(99,102,241,0.08)",
                                    border="1px solid rgba(99,102,241,0.25)",
                                    border_radius="10px",
                                    padding="0.7rem 0.9rem",
                                    flex="1",
                                ),
                                rx.icon_button(
                                    rx.icon("x", size=13),
                                    on_click=TicketsState.clear_matrix,
                                    background="transparent",
                                    color=MUTED,
                                    border_radius="7px",
                                    size="1",
                                    cursor="pointer",
                                    _hover={"color": RED},
                                    title="Retirer le lien",
                                ),
                                spacing="2", align="start", width="100%",
                            ),
                            # Barre de recherche + dropdown absolu
                            rx.box(
                                rx.input(
                                    placeholder="Rechercher par périmètre, typologie, interlocuteur…",
                                    value=TicketsState.matrix_search,
                                    on_change=TicketsState.search_matrix,
                                    background="#1c2138",
                                    color=TEXT,
                                    border=f"1px solid {BORDER}",
                                    border_radius="8px",
                                    width="100%",
                                    font_size="0.82rem",
                                    _focus={"border_color": PRIMARY, "outline": "none"},
                                    _placeholder={"color": "#475569"},
                                ),
                                rx.cond(
                                    TicketsState.matrix_results.length() > 0,
                                    rx.box(
                                        rx.foreach(TicketsState.matrix_results, lambda s, i: matrix_result_item(s, i)),
                                        position="absolute",
                                        top="100%",
                                        left="0",
                                        right="0",
                                        z_index="200",
                                        background="#0d1021",
                                        border=f"1px solid {BORDER}",
                                        border_radius="8px",
                                        max_height="220px",
                                        overflow_y="auto",
                                        width="100%",
                                        margin_top="4px",
                                        box_shadow="0 8px 24px rgba(0,0,0,0.5)",
                                    ),
                                ),
                                position="relative",
                                width="100%",
                            ),
                        ),
                        spacing="2",
                        align="start",
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
                    padding="1.25rem 1.5rem 1.5rem 1.5rem",
                ),

                background="#111524",
                border=f"1px solid {BORDER}",
                border_radius="16px",
                padding="0",
                max_width="560px",
                overflow_y="auto",
                max_height="92vh",
            ),
            open=TicketsState.show_form,
        ),

        # Dialog détail ticket
        ticket_detail_dialog(),

        spacing="4",
        width="100%",
        on_mount=TicketsState.load,
    )


def tickets_page() -> rx.Component:
    return page_layout(tickets_content(), "")
