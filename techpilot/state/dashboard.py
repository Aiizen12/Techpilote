import uuid
from datetime import datetime, timedelta

import reflex as rx

from techpilot.db.database import load_db, save_db
from techpilot.state.models import (
    AstreinteEntry, PlanningRow,
    TechPresence, QuickLink, ActualiteItem, TechStatItem, ChangelogEntry,
)
from techpilot.state.auth import AuthState

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

    # Actualités widget
    actualites_widget: list[ActualiteItem] = []

    # Stats techniciens
    tech_stats: list[TechStatItem] = []
    w_tech_stats: bool = True

    # Changelog
    changelog: list[ChangelogEntry] = []
    w_changelog: bool = True
    show_changelog_form: bool = False
    cl_form_version: str = ""
    cl_form_titre: str = ""
    cl_form_items: str = ""
    cl_form_type: str = "feature"

    # Widget visibility
    w_kpis: bool = True
    w_presence: bool = True
    w_trends: bool = True
    w_planning: bool = True
    w_notes_links: bool = True
    w_actualites: bool = True
    show_config_panel: bool = False

    # Planning filter
    planning_filter_techs: list[str] = []
    planning_all_names: list[str] = []
    planning_semaine_view: list[PlanningRow] = []
    planning_filter_initialized: bool = False

    # Meta
    today_label: str = ""

    # ── Chargement principal ──────────────────────────────────────────────────

    async def load_data(self):
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
        all_names = [r.technician_name for r in plan_rows]
        self.planning_all_names = all_names

        # Initialise le filtre au premier chargement : uniquement le tech connecté
        if not self.planning_filter_initialized:
            auth = await self.get_state(AuthState)
            user_nom = auth.user_nom or ""
            self.planning_filter_techs = [user_nom] if user_nom in all_names else all_names
            self.planning_filter_initialized = True

        self._apply_planning_filter()

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

        # ── Stats par technicien ─────────────────────────────────────────
        stats_map: dict[str, dict] = {}
        for t in techs:
            if not t.get("active"):
                continue
            nom = t.get("nom") or ""
            color = t.get("color") or ""
            stats_map[nom] = {"nom": nom, "color": color,
                              "total": 0, "en_cours": 0, "resolus": 0, "escalades": 0}
        for tk in tickets:
            nom = tk.get("technicien_nom") or ""
            if nom not in stats_map:
                stats_map[nom] = {"nom": nom, "color": "#6366f1",
                                  "total": 0, "en_cours": 0, "resolus": 0, "escalades": 0}
            stats_map[nom]["total"] += 1
            if tk.get("etat") == "en_cours":
                stats_map[nom]["en_cours"] += 1
            else:
                stats_map[nom]["resolus"] += 1
            if tk.get("escalade_interlocuteur") or tk.get("escalade_n2"):
                stats_map[nom]["escalades"] += 1
        self.tech_stats = [
            TechStatItem(
                nom=v["nom"], color=v["color"],
                total=v["total"], en_cours=v["en_cours"],
                resolus=v["resolus"], escalades=v["escalades"],
            )
            for v in sorted(stats_map.values(), key=lambda x: -x["total"])
            if v["nom"]
        ]

        # Widget config
        cfg = db.get("dashboard_config") or {}
        self.w_kpis       = cfg.get("kpis", True)
        self.w_presence   = cfg.get("presence", True)
        self.w_trends     = cfg.get("trends", True)
        self.w_planning   = cfg.get("planning", True)
        self.w_notes_links = cfg.get("notes_links", True)
        self.w_actualites = cfg.get("actualites", True)
        self.w_tech_stats = cfg.get("tech_stats", True)
        self.w_changelog  = cfg.get("changelog", True)

        # Changelog — du plus récent au plus ancien
        cl_items = db.get("changelog") or []
        self.changelog = [
            ChangelogEntry(
                id=str(c.get("id") or ""),
                version=c.get("version") or "",
                date=c.get("date") or "",
                titre=c.get("titre") or "",
                items=c.get("items") or [],
                type=c.get("type") or "feature",
            )
            for c in sorted(cl_items, key=lambda x: x.get("date", ""), reverse=True)
        ]

        # Actualités widget (5 dernières, épinglées en premier)
        actu_items = db.get("actualites") or []
        actu_sorted = sorted(actu_items, key=lambda a: (
            not a.get("epingle", False),
            -(datetime.fromisoformat(a["date_creation"]).timestamp()
              if a.get("date_creation") else 0)
        ))
        self.actualites_widget = [
            ActualiteItem(
                id=str(a.get("id") or ""),
                titre=a.get("titre") or "",
                contenu=a.get("contenu") or "",
                type=a.get("type") or "",
                epingle=bool(a.get("epingle", False)),
                auteur_nom=a.get("auteur_nom") or "",
                date_creation=a.get("date_creation") or "",
            )
            for a in actu_sorted[:5]
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

    # ── Config dashboard ──────────────────────────────────────────────────────

    def toggle_config_panel(self):
        self.show_config_panel = not self.show_config_panel

    def _save_config(self):
        db = load_db()
        db["dashboard_config"] = {
            "kpis":        self.w_kpis,
            "presence":    self.w_presence,
            "trends":      self.w_trends,
            "planning":    self.w_planning,
            "notes_links": self.w_notes_links,
            "actualites":  self.w_actualites,
            "tech_stats":  self.w_tech_stats,
            "changelog":   self.w_changelog,
        }
        save_db(db)

    def toggle_w_kpis(self):
        self.w_kpis = not self.w_kpis
        self._save_config()

    def toggle_w_presence(self):
        self.w_presence = not self.w_presence
        self._save_config()

    def toggle_w_trends(self):
        self.w_trends = not self.w_trends
        self._save_config()

    def toggle_w_planning(self):
        self.w_planning = not self.w_planning
        self._save_config()

    def toggle_w_notes_links(self):
        self.w_notes_links = not self.w_notes_links
        self._save_config()

    def toggle_w_actualites(self):
        self.w_actualites = not self.w_actualites
        self._save_config()

    def toggle_w_tech_stats(self):
        self.w_tech_stats = not self.w_tech_stats
        self._save_config()

    def toggle_w_changelog(self):
        self.w_changelog = not self.w_changelog
        self._save_config()

    def _apply_planning_filter(self):
        if not self.planning_filter_techs:
            self.planning_semaine_view = self.planning_semaine
        else:
            self.planning_semaine_view = [
                r for r in self.planning_semaine
                if r.technician_name in self.planning_filter_techs
            ]

    def toggle_planning_tech(self, name: str):
        if name in self.planning_filter_techs:
            remaining = [n for n in self.planning_filter_techs if n != name]
            self.planning_filter_techs = remaining if remaining else self.planning_filter_techs
        else:
            self.planning_filter_techs = [*self.planning_filter_techs, name]
        self._apply_planning_filter()

    def planning_show_all(self):
        self.planning_filter_techs = list(self.planning_all_names)
        self._apply_planning_filter()

    # ── Changelog ─────────────────────────────────────────────────────────────

    def open_changelog_form(self):
        self.cl_form_version = ""
        self.cl_form_titre   = ""
        self.cl_form_items   = ""
        self.cl_form_type    = "feature"
        self.show_changelog_form = True

    def close_changelog_form(self):
        self.show_changelog_form = False

    def set_cl_version(self, v: str): self.cl_form_version = v
    def set_cl_titre(self, v: str):   self.cl_form_titre   = v
    def set_cl_items(self, v: str):   self.cl_form_items   = v
    def set_cl_type(self, v: str):    self.cl_form_type    = v

    def add_changelog_entry(self):
        if not self.cl_form_version.strip() or not self.cl_form_titre.strip():
            return
        items = [l.strip() for l in self.cl_form_items.splitlines() if l.strip()]
        db = load_db()
        if "changelog" not in db:
            db["changelog"] = []
        db["changelog"].append({
            "id":      str(uuid.uuid4()),
            "version": self.cl_form_version.strip(),
            "date":    datetime.utcnow().strftime("%Y-%m-%d"),
            "titre":   self.cl_form_titre.strip(),
            "items":   items,
            "type":    self.cl_form_type,
        })
        save_db(db)
        self.show_changelog_form = False
        self.load_data()

    def delete_changelog_entry(self, eid: str):
        db = load_db()
        db["changelog"] = [c for c in (db.get("changelog") or []) if str(c.get("id")) != eid]
        save_db(db)
        self.load_data()
