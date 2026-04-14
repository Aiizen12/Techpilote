import reflex as rx
from techpilot.db.database import load_db, save_db
from techpilot.state.models import PlanningEntry, AstreinteEntry


def _normalize_week(w: str) -> str:
    return (w or "").split("\n")[0].split("\r")[0].strip()


class PlanningState(rx.State):
    semaines: list[str] = []
    selected_week: str = ""
    entries: list[dict] = []
    astreintes: list[AstreinteEntry] = []
    tech_names: list[str] = []
    entries_by_tech: list[PlanningEntry] = []

    def load_data(self):
        db = load_db()
        # Uniquement les techniciens actifs
        self.tech_names = [
            t.get("nom", "") for t in db.get("technicians", [])
            if t.get("active", True) and t.get("nom")
        ]
        semaines = list(dict.fromkeys(
            _normalize_week(p.get("week", ""))
            for p in db["planning"] if p.get("week")
        ))
        self.semaines = semaines
        saved = db.get("planning_selected_week", "")
        if saved and saved in semaines:
            self.selected_week = saved
        else:
            self.selected_week = semaines[-1] if semaines else ""
        self.astreintes = [
            AstreinteEntry(
                period=a.get("period") or "",
                slot_matin=a.get("slot_matin") or "",
                slot_soir=a.get("slot_soir") or "",
            )
            for a in (db.get("astreintes") or [])
        ]
        self._load_entries(db)

    def _load_entries(self, db: dict):
        if not self.selected_week:
            self.entries = []
            self.entries_by_tech = []
            return
        self.entries = [
            p for p in db["planning"]
            if _normalize_week(p.get("week", "")) == self.selected_week
        ]
        self._update_entries_by_tech()

    def _update_entries_by_tech(self):
        result = []
        for tech_name in self.tech_names:
            entry = next(
                (e for e in self.entries
                 if (e.get("technician_name") or e.get("technicien_nom") or "") == tech_name),
                {}
            )
            result.append(PlanningEntry(
                tech_name=tech_name,
                horaire=entry.get("horaire") or "",
                telework_days=entry.get("telework_days") or "",
                bendoc_pause=entry.get("bendoc_pause") or "",
            ))
        self.entries_by_tech = result

    def select_week(self, week: str):
        self.selected_week = week
        db = load_db()
        db["planning_selected_week"] = week
        save_db(db)
        self._load_entries(db)

    def prev_week(self):
        if self.selected_week in self.semaines:
            idx = self.semaines.index(self.selected_week)
            if idx > 0:
                self.select_week(self.semaines[idx - 1])

    def next_week(self):
        if self.selected_week in self.semaines:
            idx = self.semaines.index(self.selected_week)
            if idx < len(self.semaines) - 1:
                self.select_week(self.semaines[idx + 1])
