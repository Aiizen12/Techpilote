import uuid
from datetime import datetime, timedelta

import reflex as rx

from techpilot.db.database import load_db, save_db
from techpilot.state.models import (
    AstreinteEntry, PlanningRow,
    TechPresence, QuickLink,
)

DEFAULT_TECH_COLORS = [
    "#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#06b6d4", "#8b5cf6", "#ec4899",
]
DAY_MAP = {0: "LU", 1: "MA", 2: "ME", 3: "JE", 4: "VE", 5: "SA", 6: "DI"}
MONTH_FR = ["janvier","février","mars","avril","mai","juin",
            "juillet","août","septembre","octobre","novembre","décembre"]
DAY_FR   = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]


class DashboardState(rx.State):
    # KPIs
    technicians_actifs: int = 0
    tickets_ouverts: int = 0
    entrees_matrice: int = 0
    semaines_planning: int = 0

    # Sections
    astreintes: list[AstreinteEntry] = []
    planning_semaine: list[PlanningRow] = []
    presence_today: list[TechPresence] = []
    ticket_trends: list[dict] = []

    # Notes & liens
    quick_notes: str = ""
    quick_links: list[QuickLink] = []
    show_link_form: bool = False
    link_form_nom: str = ""
    link_form_url: str = ""

    # Meta
    today_label: str = ""

    # ── Chargement principal ──────────────────────────────────────────────────

    def load_data(self):
        db = load_db()
        now = datetime.utcnow()
        today_idx = now.weekday()
        today_day = DAY_MAP.get(today_idx, "LU")
        self.today_label = f"{DAY_FR[today_idx]} {now.day} {MONTH_FR[now.month - 1]} {now.year}"

        tickets = db.get("tickets") or []
        techs   = db.get("technicians") or []

        # KPIs
        self.technicians_actifs = sum(1 for t in techs if t.get("active"))
        self.tickets_ouverts    = sum(1 for t in tickets if t.get("etat") == "en_cours")
        self.entrees_matrice    = len(db.get("escalation_matrix") or [])
        semaines = sorted(set(p.get("week") for p in db.get("planning") or [] if p.get("week")))
        self.semaines_planning  = len(semaines)

        # Astreintes
        self.astreintes = [
            AstreinteEntry(
                period=a.get("period") or "",
                slot_matin=a.get("slot_matin") or "",
                slot_soir=a.get("slot_soir") or "",
            )
            for a in (db.get("astreintes") or [])
        ]

        # Planning — semaine sauvegardée ou la plus récente
        saved_week = db.get("planning_selected_week", "")
        if saved_week and saved_week in semaines:
            latest = saved_week
        else:
            latest = semaines[-1] if semaines else None
        active_names = {t.get("nom", "") for t in techs if t.get("active", True)}
        seen: set = set()
        plan_rows = []
        if latest:
            for p in db.get("planning") or []:
                if p.get("week") != latest:
                    continue
                name = p.get("technician_name") or p.get("technicien_nom") or ""
                if not name or name in seen or name not in active_names:
                    continue
                seen.add(name)
                plan_rows.append(PlanningRow(
                    technician_name=name,
                    horaire=p.get("horaire") or "",
                    telework_days=p.get("telework_days") or "",
                    bendoc_pause=p.get("bendoc_pause") or "",
                ))
        self.planning_semaine = plan_rows

        # Présence aujourd'hui (dérivée du planning)
        tech_color_map = {t.get("nom", ""): t.get("color", "") for t in techs}
        presence = []
        planned_names: set = set()

        for i, row in enumerate(plan_rows):
            nom    = row.technician_name
            h      = row.horaire.lower()
            tt_days = row.telework_days
            color  = tech_color_map.get(nom, "") or DEFAULT_TECH_COLORS[i % len(DEFAULT_TECH_COLORS)]
            planned_names.add(nom)

            if any(k in h for k in ("absent", "congé", "conge", " cp", "abs")):
                status = "absent"
            elif today_day in tt_days:
                status = "tt"
            elif h:
                status = "present"
            else:
                status = "repos"

            presence.append(TechPresence(nom=nom, initials=nom[:2].upper(), color=color, status=status))

        # Techs actifs non planifiés → "repos"
        for i, t in enumerate(techs):
            if not t.get("active"):
                continue
            nom = t.get("nom", "")
            if nom in planned_names:
                continue
            color = t.get("color", "") or DEFAULT_TECH_COLORS[i % len(DEFAULT_TECH_COLORS)]
            presence.append(TechPresence(nom=nom, initials=nom[:2].upper(), color=color, status="repos"))

        self.presence_today = presence

        # Tendance tickets — 8 dernières semaines
        trends = []
        for w in range(7, -1, -1):
            ref  = now - timedelta(weeks=w)
            wnum = ref.isocalendar()[1]
            yr   = ref.year
            label = f"S{wnum:02d}"

            def _week(ts: str) -> tuple:
                try:
                    d = datetime.fromisoformat(ts[:19])
                    return d.isocalendar()[1], d.year
                except Exception:
                    return -1, -1

            crees   = sum(1 for t in tickets if t.get("date_creation") and _week(t["date_creation"]) == (wnum, yr))
            resolus = sum(1 for t in tickets if t.get("date_resolution") and _week(t["date_resolution"]) == (wnum, yr))
            trends.append({"week": label, "crees": crees, "resolus": resolus})
        self.ticket_trends = trends

        # Notes rapides & liens rapides
        self.quick_notes = (db.get("quick_notes") or {}).get("__global__", "")
        self.quick_links = [
            QuickLink(id=str(lk.get("id") or ""), nom=lk.get("nom") or "", url=lk.get("url") or "")
            for lk in (db.get("quick_links") or [])
        ]

    # ── Notes rapides ─────────────────────────────────────────────────────────

    def set_quick_notes(self, val: str):
        self.quick_notes = val

    def save_notes(self):
        db = load_db()
        if "quick_notes" not in db:
            db["quick_notes"] = {}
        db["quick_notes"]["__global__"] = self.quick_notes
        save_db(db)

    # ── Liens rapides ─────────────────────────────────────────────────────────

    def open_link_form(self):
        self.link_form_nom = ""
        self.link_form_url = ""
        self.show_link_form = True

    def close_link_form(self):
        self.show_link_form = False

    def set_link_nom(self, v: str):
        self.link_form_nom = v

    def set_link_url(self, v: str):
        self.link_form_url = v

    def add_link(self):
        if not self.link_form_nom or not self.link_form_url:
            return
        db = load_db()
        if "quick_links" not in db:
            db["quick_links"] = []
        db["quick_links"].append({
            "id": str(uuid.uuid4()),
            "nom": self.link_form_nom,
            "url": self.link_form_url,
        })
        save_db(db)
        self.show_link_form = False
        self.load_data()

    def delete_link(self, lid: str):
        db = load_db()
        db["quick_links"] = [lk for lk in (db.get("quick_links") or []) if str(lk.get("id")) != lid]
        save_db(db)
        self.load_data()
