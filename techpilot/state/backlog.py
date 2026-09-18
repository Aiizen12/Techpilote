import reflex as rx

from techpilot.db.database import load_db, save_db
from techpilot.state.auth import AuthState
from techpilot.db.activity import log_activity

BACKLOG_CATEGORIES = [
    "Poste de travail & périphériques",
    "Téléphonie fixe & mobile",
    "Outils collaboratifs",
    "Applications métier",
    "Réseau & Internet",
    "Sécurité & accès",
]


class BacklogState(rx.State):
    technicians: list[dict] = []
    categories: list[dict] = []
    renfort_techs: list[dict] = []

    show_assign_form: bool = False
    assign_categorie: str = ""
    assign_tech_id: str = ""

    def load(self):
        db = load_db()
        techs = [t for t in (db.get("technicians") or []) if t.get("active", True)]
        self.technicians = [
            {
                "id": str(t.get("id") or ""),
                "nom": t.get("nom") or "",
                "color": t.get("color") or "#6366f1",
                "initials": (t.get("nom") or "")[:2].upper(),
            }
            for t in techs
        ]
        tech_by_id = {t["id"]: t for t in self.technicians}
        tickets = db.get("tickets") or []
        titulaires = db.get("backlog_titulaires") or {}

        open_by_tech: dict = {}
        resolved_by_tech: dict = {}
        for tk in tickets:
            tid = str(tk.get("technicien_id") or "")
            if not tid:
                continue
            if tk.get("etat") == "en_cours":
                open_by_tech[tid] = open_by_tech.get(tid, 0) + 1
            elif tk.get("etat") == "resolu":
                resolved_by_tech[tid] = resolved_by_tech.get(tid, 0) + 1

        rows = []
        for cat in BACKLOG_CATEGORIES:
            tid = str(titulaires.get(cat) or "")
            t = tech_by_id.get(tid, {})
            has_titulaire = bool(tid) and tid in tech_by_id
            rows.append({
                "nom": cat,
                "titulaire_id": tid if has_titulaire else "",
                "titulaire_nom": t.get("nom") or "" if has_titulaire else "",
                "titulaire_color": t.get("color") or "#6366f1" if has_titulaire else "#3a4058",
                "titulaire_initials": t.get("initials") or "" if has_titulaire else "",
                "has_titulaire": has_titulaire,
                "ouverts": open_by_tech.get(tid, 0) if has_titulaire else 0,
                "traites": resolved_by_tech.get(tid, 0) if has_titulaire else 0,
            })

        max_ouverts = max((r["ouverts"] for r in rows), default=0)
        max_cat = ""
        for r in rows:
            r["is_max"] = max_ouverts > 0 and r["ouverts"] == max_ouverts
            r["is_soldee"] = r["has_titulaire"] and r["ouverts"] == 0
            if r["is_max"] and not max_cat:
                max_cat = r["nom"]

        renfort_map: dict = {}
        renfort_techs = []
        if max_cat:
            for r in rows:
                if r["is_soldee"] and r["nom"] != max_cat:
                    renfort_techs.append({
                        "tech_nom": r["titulaire_nom"],
                        "tech_color": r["titulaire_color"],
                        "tech_initials": r["titulaire_initials"],
                        "source": r["nom"],
                        "target": max_cat,
                    })
                    renfort_map.setdefault(max_cat, []).append(r["titulaire_nom"])

        for r in rows:
            noms = renfort_map.get(r["nom"], [])
            r["renforts_label"] = ", ".join(noms)
            r["has_renforts"] = len(noms) > 0

        self.categories = rows
        self.renfort_techs = renfort_techs

    @rx.var
    def total_ouverts(self) -> int:
        return sum(r["ouverts"] for r in self.categories)

    @rx.var
    def total_traites(self) -> int:
        return sum(r["traites"] for r in self.categories)

    @rx.var
    def max_categorie_nom(self) -> str:
        for r in self.categories:
            if r["is_max"] and r["ouverts"] > 0:
                return r["nom"]
        return ""

    # ── Assignation titulaire ────────────────────────────────────────────────

    def open_assign(self, categorie: str):
        self.assign_categorie = categorie
        current = next((r for r in self.categories if r["nom"] == categorie), {})
        self.assign_tech_id = current.get("titulaire_id") or "_none"
        self.show_assign_form = True

    def close_assign(self):
        self.show_assign_form = False

    def set_assign_tech(self, tid: str):
        self.assign_tech_id = tid

    async def save_assign(self):
        auth = await self.get_state(AuthState)
        if not auth.is_manager:
            yield rx.toast.error("Droits insuffisants.")
            return
        db = load_db()
        titulaires = db.get("backlog_titulaires") or {}
        if self.assign_tech_id and self.assign_tech_id != "_none":
            titulaires[self.assign_categorie] = self.assign_tech_id
        else:
            titulaires.pop(self.assign_categorie, None)
        db["backlog_titulaires"] = titulaires
        save_db(db)
        tech_nom = next((t["nom"] for t in self.technicians if t["id"] == self.assign_tech_id), "")
        log_activity(auth.user_nom, "UPDATE", "backlog",
                     f"Titulaire '{self.assign_categorie}' -> {tech_nom or 'aucun'}")
        self.show_assign_form = False
        yield rx.toast.success("Titulaire mis à jour.")
        self.load()
