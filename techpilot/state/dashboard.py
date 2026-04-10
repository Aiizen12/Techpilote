import reflex as rx
from techpilot.db.database import load_db


class DashboardState(rx.State):
    technicians_actifs: int = 0
    tickets_ouverts: int = 0
    entrees_matrice: int = 0
    semaines_planning: int = 0
    tickets_par_tech: list[dict] = []
    astreintes: list[dict] = []
    planning_semaine: list[dict] = []

    def load_data(self):
        db = load_db()
        incidents = db.get("tickets") or []
        self.technicians_actifs = sum(1 for t in db["technicians"] if t.get("active"))
        self.tickets_ouverts = sum(1 for t in incidents if t.get("etat") == "en_cours")
        self.entrees_matrice = len(db["escalation_matrix"])

        semaines = sorted(set(p.get("week") for p in db["planning"] if p.get("week")))
        self.semaines_planning = len(semaines)

        # Tickets par tech
        by_tech: dict = {}
        for t in incidents:
            nom = t.get("technicien_nom")
            if nom:
                by_tech[nom] = by_tech.get(nom, 0) + 1
        tech_names = ["Bastian", "Adrien", "Mirgaël", "Cédric", "Thaïs", "Alistair"]
        self.tickets_par_tech = [{"nom": n, "count": by_tech.get(n, 0)} for n in tech_names]

        # Astreintes
        self.astreintes = db.get("astreintes") or []

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
                result.append(p)
        self.planning_semaine = result
