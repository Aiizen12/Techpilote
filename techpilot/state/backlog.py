import random
import uuid
from datetime import datetime

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

DEMO_IMPACTS = ["basse", "normale", "normale", "haute", "critique"]
DEMO_TITLES = [
    "Ne démarre plus", "Lenteur anormale", "Erreur de connexion", "Écran bleu",
    "Périphérique non reconnu", "Mise à jour bloquée", "Accès refusé",
    "Synchronisation en échec", "Message d'erreur récurrent", "Panne intermittente",
]


class BacklogState(rx.State):
    technicians: list[dict] = []
    categories: list[dict] = []
    renfort_techs: list[dict] = []
    demo_mode: bool = False

    show_assign_form: bool = False
    assign_categorie: str = ""
    assign_tech_id: str = ""

    # ── Calcul partagé ────────────────────────────────────────────────────────

    @staticmethod
    def _derive(rows: list[dict]) -> tuple[list[dict], list[dict]]:
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

        return rows, renfort_techs

    # ── Chargement (données réelles, tickets de démo inclus) ─────────────────

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

        has_demo_tickets = any(tk.get("is_demo") for tk in tickets)
        self.demo_mode = has_demo_tickets

        open_by_tech: dict = {}
        resolved_by_tech: dict = {}
        for tk in tickets:
            # Pendant une démo, la vue backlog ne compte que les tickets factices
            # (les vrais tickets restent visibles dans Tickets/Dashboard sans être mélangés ici).
            if has_demo_tickets and not tk.get("is_demo"):
                continue
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

        self.categories, self.renfort_techs = self._derive(rows)

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

    @rx.var
    def demo_is_cleared(self) -> bool:
        return self.demo_mode and bool(self.categories) and all(r["ouverts"] == 0 for r in self.categories)

    # ── Mode démonstration (vrais tickets, marqués is_demo) ──────────────────

    async def demo_new_day(self):
        auth = await self.get_state(AuthState)
        if not auth.is_manager:
            yield rx.toast.error("Droits insuffisants.")
            return
        if not self.technicians:
            yield rx.toast.error("Aucun technicien actif.")
            return

        db = load_db()
        tickets = [tk for tk in (db.get("tickets") or []) if not tk.get("is_demo")]

        pool = list(self.technicians)
        random.shuffle(pool)
        titulaires = {}
        now_iso = datetime.utcnow().isoformat()
        for i, cat in enumerate(BACKLOG_CATEGORIES):
            t = pool[i % len(pool)]
            titulaires[cat] = t["id"]
            for _ in range(random.randint(8, 25)):
                tickets.append({
                    "id": str(uuid.uuid4()),
                    "titre": f"🎭 DÉMO — {random.choice(DEMO_TITLES)}",
                    "ticket_pere": "",
                    "description": f"Ticket de démonstration ({cat}).",
                    "impact": random.choice(DEMO_IMPACTS),
                    "perimetre": cat,
                    "technicien_id": t["id"],
                    "technicien_nom": t["nom"],
                    "etat": "en_cours",
                    "notes": "",
                    "date_creation": now_iso,
                    "date_modification": now_iso,
                    "date_resolution": None,
                    "escalade_perimetre": "", "escalade_typologie": "",
                    "escalade_interlocuteur": "", "escalade_n2": "", "escalade_wp_n2": "",
                    "is_demo": True,
                })

        db["tickets"] = tickets
        db["backlog_titulaires"] = titulaires
        save_db(db)
        log_activity(auth.user_nom, "CREATE", "backlog", "Démo backlog générée (tickets factices)")
        yield rx.toast.success("Nouvelle journée de démo générée.")
        self.load()

    async def demo_advance(self):
        auth = await self.get_state(AuthState)
        if not auth.is_manager:
            yield rx.toast.error("Droits insuffisants.")
            return
        if not self.demo_mode:
            return

        renfort_count: dict = {}
        for r in self.renfort_techs:
            renfort_count[r["target"]] = renfort_count.get(r["target"], 0) + 1
        cat_by_tech = {r["titulaire_id"]: r["nom"] for r in self.categories if r["has_titulaire"]}

        db = load_db()
        tickets = db.get("tickets") or []
        now_iso = datetime.utcnow().isoformat()

        open_demo_by_tech: dict = {}
        for tk in tickets:
            if tk.get("is_demo") and tk.get("etat") == "en_cours":
                open_demo_by_tech.setdefault(str(tk.get("technicien_id") or ""), []).append(tk)

        for tid, tks in open_demo_by_tech.items():
            cat = cat_by_tech.get(tid, "")
            boost = 1 + renfort_count.get(cat, 0)
            n_resolve = min(len(tks), random.randint(3, 8) * boost)
            for tk in random.sample(tks, n_resolve):
                tk["etat"] = "resolu"
                tk["date_resolution"] = now_iso
                tk["date_modification"] = now_iso

        save_db(db)
        self.load()

    async def demo_cleanup(self):
        auth = await self.get_state(AuthState)
        if not auth.is_manager:
            yield rx.toast.error("Droits insuffisants.")
            return
        db = load_db()
        db["tickets"] = [tk for tk in (db.get("tickets") or []) if not tk.get("is_demo")]
        db.pop("backlog_titulaires", None)
        save_db(db)
        log_activity(auth.user_nom, "DELETE", "backlog", "Tickets de démo supprimés")
        yield rx.toast.info("Tickets de démo supprimés.")
        self.load()

    # ── Assignation titulaire (données réelles) ──────────────────────────────

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
