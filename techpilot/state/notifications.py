import reflex as rx
from techpilot.db.database import load_db


class NotificationState(rx.State):
    count: int = 0
    items: list[dict] = []
    show_panel: bool = False

    def load(self):
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

        # Actualités épinglées → info violettes
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

        self.items = items[:15]
        self.count = len(items)

    def toggle_panel(self):
        self.show_panel = not self.show_panel

    def close_panel(self):
        self.show_panel = False

    def navigate(self, href: str):
        self.show_panel = False
        return rx.redirect(href)
