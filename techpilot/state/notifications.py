import reflex as rx
from techpilot.db.database import load_db
from techpilot.state.auth import AuthState


class NotificationState(rx.State):
    count: int = 0
    items: list[dict] = []
    show_panel: bool = False

    async def load(self):
        auth = await self.get_state(AuthState)
        db = load_db()
        items = []

        # Tickets en cours → alertes rouges
        for t in (db.get("tickets") or []):
            if t.get("etat") == "en_cours":
                impact = t.get("impact") or ""
                date = (t.get("date_creation") or "")[:10]
                items.append({
                    "type":  "ticket",
                    "title": t.get("titre") or "Incident sans titre",
                    "sub":   f"Impact {impact} · {date}",
                    "href":  "/tickets",
                })

        # Actualités épinglées → violettes
        for a in (db.get("actualites") or []):
            if a.get("epingle"):
                auteur = a.get("auteur_nom") or ""
                date   = (a.get("date_creation") or "")[:10]
                items.append({
                    "type":  "actu",
                    "title": a.get("titre") or "Actualité",
                    "sub":   f"Par {auteur} · {date}",
                    "href":  "/actualites",
                })

        # Feedbacks ouverts → oranges
        for f in (db.get("feedbacks") or []):
            if f.get("statut") == "ouvert":
                prio = f.get("priorite") or ""
                date = (f.get("date_creation") or "")[:10]
                items.append({
                    "type":  "feedback",
                    "title": f.get("titre") or "Feedback",
                    "sub":   f"Priorité {prio} · {date}",
                    "href":  "/feedbacks",
                })

        # Quêtes à valider → jaunes (manager seulement)
        if auth.user_role == "manager":
            pending = db.get("pending_validations") or []
            for p in pending:
                items.append({
                    "type":  "quete",
                    "title": p.get("quete_titre") or "Quête à valider",
                    "sub":   f"{p.get('user_nom', '')} · {p.get('xp', 0)} XP",
                    "href":  "/quetes",
                })

        self.items = items[:20]
        self.count = len(items)

    def toggle_panel(self):
        if not self.show_panel:
            return [NotificationState.load, NotificationState._open_panel]
        self.show_panel = False

    def _open_panel(self):
        self.show_panel = True

    def close_panel(self):
        self.show_panel = False

    def navigate(self, href: str):
        self.show_panel = False
        return rx.redirect(href)
