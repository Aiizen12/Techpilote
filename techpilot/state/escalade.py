import reflex as rx
from techpilot.db.database import load_db


class EscaladeState(rx.State):
    entries: list[dict] = []
    perimetres: list[str] = []
    selected_perimetres: list[str] = []
    search: str = ""
    page: int = 1
    total: int = 0
    limit: int = 25
    selected_entry: dict = {}
    show_modal: bool = False

    def load_data(self):
        db = load_db()
        self.perimetres = sorted(set(
            r.get("perimetre", "") for r in db["escalation_matrix"] if r.get("perimetre")
        ))
        self._filter(db)

    def _filter(self, db: dict | None = None):
        if db is None:
            db = load_db()
        results = db["escalation_matrix"]

        if self.search:
            q = self.search.lower()
            results = [
                r for r in results
                if q in (r.get("perimetre") or "").lower()
                or q in (r.get("typologie") or "").lower()
                or q in (r.get("categorie_fresh") or "").lower()
                or q in (r.get("traitement_n1") or "").lower()
                or q in (r.get("interlocuteur") or "").lower()
                or q in (r.get("traitement_n2n3") or "").lower()
            ]

        if self.selected_perimetres:
            results = [r for r in results if r.get("perimetre") in self.selected_perimetres]

        self.total = len(results)
        offset = (self.page - 1) * self.limit
        self.entries = results[offset: offset + self.limit]

    def set_search(self, val: str):
        self.search = val
        self.page = 1
        self._filter()

    def toggle_perimetre(self, p: str):
        if p in self.selected_perimetres:
            self.selected_perimetres = [x for x in self.selected_perimetres if x != p]
        else:
            self.selected_perimetres = [*self.selected_perimetres, p]
        self.page = 1
        self._filter()

    def clear_filters(self):
        self.search = ""
        self.selected_perimetres = []
        self.page = 1
        self._filter()

    def go_page(self, p: int):
        self.page = p
        self._filter()

    def open_entry(self, entry: dict):
        self.selected_entry = entry
        self.show_modal = True

    def close_modal(self):
        self.show_modal = False

    @rx.var
    def total_pages(self) -> int:
        return max(1, (self.total + self.limit - 1) // self.limit)
