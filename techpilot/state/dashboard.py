import reflex as rx
from techpilot.db.database import load_db
from techpilot.state.models import AstreinteEntry, PlanningRow


class DashboardState(rx.State):
    technicians_actifs: int = 0
    tickets_ouverts: int = 0
    entrees_matrice: int = 0
    semaines_planning: int = 0
    astreintes: list[AstreinteEntry] = []
    planning_semaine: list[PlanningRow] = []

    def load_data(self):
        db = load_db()
        incidents = db.get("tickets") or []
        self.technicians_actifs = sum(1 for t in db["technicians"] if t.get("active"))
        self.tickets_ouverts = sum(1 for t in incidents if t.get("etat") == "en_cours")
        self.entrees_matrice = len(db["escalation_matrix"])

        semaines = sorted(set(p.get("week") for p in db["planning"] if p.get("week")))
        self.semaines_planning = len(semaines)

        # Astreintes
        self.astreintes = [
            AstreinteEntry(
                period=a.get("period") or "",
                slot_matin=a.get("slot_matin") or "",
                slot_soir=a.get("slot_soir") or "",
            )
            for a in (db.get("astreintes") or [])
        ]

        # Planning semaine courante
        latest = semaines[-1] if semaines else None
        seen: set = set()
        result = []
        if latest:
            for p in db["planning"]:
                if p.get("week") != latest:
                    continue
                name = p.get("technician_name") or p.get("technicien_nom")
                if not name or name in seen:
                    continue
                seen.add(name)
                result.append(PlanningRow(
                    technician_name=name,
                    horaire=p.get("horaire") or "",
                    telework_days=p.get("telework_days") or "",
                ))
        self.planning_semaine = result
