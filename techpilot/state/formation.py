import uuid
from datetime import datetime

import reflex as rx

from techpilot.db.database import load_db, save_db
from techpilot.state.models import FormationModule, OnboardingStep, OnboardingTechProgress
from techpilot.state.auth import AuthState
from techpilot.db.activity import log_activity

FORMATION_CATEGORIES = ["Réseau", "Active Directory", "Freshservice", "Téléphonie", "Sécurité", "Processus N1", "Autre"]
ONBOARDING_CATS = ["Accès", "Outils", "Processus", "Formation", "Autre"]


class FormationState(rx.State):
    tab: str = "modules"

    # ── Modules ───────────────────────────────────────────────────────────────
    modules: list[FormationModule] = []
    modules_view: list[FormationModule] = []
    my_reads: list[str] = []
    cat_filter: str = ""
    mod_search: str = ""

    show_mod_form: bool = False
    edit_mod_id: str = ""
    mod_form: dict = {
        "titre": "", "categorie": "Réseau",
        "description": "", "contenu": "", "difficulte": "Débutant",
    }

    show_mod_detail: bool = False
    detail_mod_id: str = ""
    detail_mod_titre: str = ""
    detail_mod_categorie: str = ""
    detail_mod_difficulte: str = ""
    detail_mod_contenu: str = ""
    detail_mod_auteur: str = ""
    detail_mod_date: str = ""
    detail_mod_read_count: int = 0

    # ── Onboarding ────────────────────────────────────────────────────────────
    onboarding_steps: list[OnboardingStep] = []
    onboarding_progress: list[OnboardingTechProgress] = []

    show_step_form: bool = False
    edit_step_id: str = ""
    step_form: dict = {"titre": "", "description": "", "categorie": "Accès", "ordre": "0"}

    show_checklist: bool = False
    checklist_tech_id: str = ""
    checklist_tech_nom: str = ""
    checklist_tech_color: str = ""
    checklist_steps_done: list[str] = []

    # ── Chargement ────────────────────────────────────────────────────────────
    async def load(self):
        auth = await self.get_state(AuthState)
        db = load_db()
        user_nom = auth.user_nom or ""

        raw_mods = db.get("formation_modules") or []
        self.my_reads = [
            str(m.get("id")) for m in raw_mods
            if user_nom in (m.get("lu_par") or [])
        ]
        self.modules = [
            FormationModule(
                id=str(m.get("id") or ""),
                titre=m.get("titre") or "",
                categorie=m.get("categorie") or "",
                description=m.get("description") or "",
                contenu=m.get("contenu") or "",
                difficulte=m.get("difficulte") or "Débutant",
                auteur_nom=m.get("auteur_nom") or "",
                date_creation=m.get("date_creation") or "",
                lu_count=len(m.get("lu_par") or []),
            )
            for m in raw_mods
        ]
        self._apply_mod_filters()

        self.onboarding_steps = [
            OnboardingStep(
                id=str(s.get("id") or ""),
                titre=s.get("titre") or "",
                description=s.get("description") or "",
                categorie=s.get("categorie") or "Général",
                ordre=int(s.get("ordre") or 0),
            )
            for s in sorted(db.get("onboarding_steps") or [], key=lambda x: x.get("ordre", 0))
        ]

        techs = [t for t in (db.get("technicians") or []) if t.get("active")]
        progress_map = {str(p.get("tech_id")): p for p in (db.get("onboarding_progress") or [])}
        self.onboarding_progress = [
            OnboardingTechProgress(
                tech_id=str(t.get("id") or ""),
                tech_nom=t.get("nom") or "",
                color=t.get("color") or "#6366f1",
                steps_done=list(progress_map.get(str(t.get("id")), {}).get("steps_done") or []),
                date_debut=str(progress_map.get(str(t.get("id")), {}).get("date_debut") or ""),
                assigned=str(t.get("id")) in progress_map,
            )
            for t in techs
        ]

    def set_tab(self, t: str):
        self.tab = t

    # ── Filtres modules ───────────────────────────────────────────────────────
    def _apply_mod_filters(self):
        result = self.modules
        if self.cat_filter:
            result = [m for m in result if m.categorie == self.cat_filter]
        if self.mod_search:
            q = self.mod_search.lower()
            result = [m for m in result if q in m.titre.lower() or q in m.description.lower()]
        self.modules_view = result

    def set_cat_filter(self, cat: str):
        self.cat_filter = cat if self.cat_filter != cat else ""
        self._apply_mod_filters()

    def set_mod_search(self, v: str):
        self.mod_search = v
        self._apply_mod_filters()

    # ── CRUD modules ──────────────────────────────────────────────────────────
    def open_mod_create(self):
        self.edit_mod_id = ""
        self.mod_form = {"titre": "", "categorie": "Réseau", "description": "", "contenu": "", "difficulte": "Débutant"}
        self.show_mod_form = True

    def open_mod_edit(self, mod_id: str):
        db = load_db()
        m = next((m for m in db.get("formation_modules") or [] if str(m.get("id")) == mod_id), None)
        if m:
            self.edit_mod_id = mod_id
            self.mod_form = {
                "titre": m.get("titre") or "",
                "categorie": m.get("categorie") or "Réseau",
                "description": m.get("description") or "",
                "contenu": m.get("contenu") or "",
                "difficulte": m.get("difficulte") or "Débutant",
            }
            self.show_mod_form = True

    def close_mod_form(self):
        self.show_mod_form = False

    def set_mod_field(self, f: str, v: str):
        self.mod_form = {**self.mod_form, f: v}

    async def save_module(self):
        auth = await self.get_state(AuthState)
        if auth.user_role != "manager":
            yield rx.toast.error("Droits insuffisants.")
            return
        db = load_db()
        db.setdefault("formation_modules", [])
        if self.edit_mod_id:
            for m in db["formation_modules"]:
                if str(m.get("id")) == self.edit_mod_id:
                    m.update({k: v for k, v in self.mod_form.items()})
            log_activity(auth.user_nom, "UPDATE", "formation", f"Module modifié: {self.mod_form.get('titre')}")
        else:
            db["formation_modules"].append({
                "id": str(uuid.uuid4()),
                **self.mod_form,
                "lu_par": [],
                "auteur_nom": auth.user_nom,
                "date_creation": datetime.utcnow().strftime("%Y-%m-%d"),
            })
            log_activity(auth.user_nom, "CREATE", "formation", f"Module créé: {self.mod_form.get('titre')}")
        save_db(db)
        self.show_mod_form = False
        yield rx.toast.success("Module enregistré.")
        await self.load()

    async def delete_module(self, mod_id: str):
        auth = await self.get_state(AuthState)
        if auth.user_role != "manager":
            yield rx.toast.error("Droits insuffisants.")
            return
        db = load_db()
        db["formation_modules"] = [m for m in db.get("formation_modules") or [] if str(m.get("id")) != mod_id]
        save_db(db)
        yield rx.toast.info("Module supprimé.")
        await self.load()

    # ── Statut lecture ────────────────────────────────────────────────────────
    async def toggle_read(self, mod_id: str):
        auth = await self.get_state(AuthState)
        user_nom = auth.user_nom or ""
        db = load_db()
        for m in db.get("formation_modules") or []:
            if str(m.get("id")) == mod_id:
                lu_par = list(m.get("lu_par") or [])
                if user_nom in lu_par:
                    lu_par.remove(user_nom)
                else:
                    lu_par.append(user_nom)
                m["lu_par"] = lu_par
                break
        save_db(db)
        await self.load()
        # Re-sync detail read count
        if self.show_mod_detail and self.detail_mod_id == mod_id:
            db2 = load_db()
            m2 = next((m for m in db2.get("formation_modules") or [] if str(m.get("id")) == mod_id), None)
            if m2:
                self.detail_mod_read_count = len(m2.get("lu_par") or [])

    # ── Détail module ─────────────────────────────────────────────────────────
    def open_mod_detail(self, mod_id: str):
        db = load_db()
        m = next((m for m in db.get("formation_modules") or [] if str(m.get("id")) == mod_id), None)
        if m:
            self.detail_mod_id = mod_id
            self.detail_mod_titre = m.get("titre") or ""
            self.detail_mod_categorie = m.get("categorie") or ""
            self.detail_mod_difficulte = m.get("difficulte") or ""
            self.detail_mod_contenu = m.get("contenu") or ""
            self.detail_mod_auteur = m.get("auteur_nom") or ""
            self.detail_mod_date = m.get("date_creation") or ""
            self.detail_mod_read_count = len(m.get("lu_par") or [])
            self.show_mod_detail = True

    def close_mod_detail(self):
        self.show_mod_detail = False

    # ── CRUD étapes onboarding ────────────────────────────────────────────────
    def open_step_create(self):
        self.edit_step_id = ""
        next_ordre = max((s.ordre for s in self.onboarding_steps), default=-1) + 1
        self.step_form = {"titre": "", "description": "", "categorie": "Accès", "ordre": str(next_ordre)}
        self.show_step_form = True

    def open_step_edit(self, step_id: str):
        db = load_db()
        s = next((s for s in db.get("onboarding_steps") or [] if str(s.get("id")) == step_id), None)
        if s:
            self.edit_step_id = step_id
            self.step_form = {
                "titre": s.get("titre") or "",
                "description": s.get("description") or "",
                "categorie": s.get("categorie") or "Accès",
                "ordre": str(s.get("ordre") or 0),
            }
            self.show_step_form = True

    def close_step_form(self):
        self.show_step_form = False

    def set_step_field(self, f: str, v: str):
        self.step_form = {**self.step_form, f: v}

    async def save_step(self):
        auth = await self.get_state(AuthState)
        if auth.user_role != "manager":
            yield rx.toast.error("Droits insuffisants.")
            return
        db = load_db()
        db.setdefault("onboarding_steps", [])
        try:
            ordre = int(self.step_form.get("ordre") or 0)
        except Exception:
            ordre = 0
        if self.edit_step_id:
            for s in db["onboarding_steps"]:
                if str(s.get("id")) == self.edit_step_id:
                    s.update({
                        "titre": self.step_form.get("titre"),
                        "description": self.step_form.get("description"),
                        "categorie": self.step_form.get("categorie"),
                        "ordre": ordre,
                    })
        else:
            db["onboarding_steps"].append({
                "id": str(uuid.uuid4()),
                "titre": self.step_form.get("titre") or "",
                "description": self.step_form.get("description") or "",
                "categorie": self.step_form.get("categorie") or "Accès",
                "ordre": ordre,
            })
        save_db(db)
        self.show_step_form = False
        yield rx.toast.success("Étape enregistrée.")
        await self.load()

    async def delete_step(self, step_id: str):
        auth = await self.get_state(AuthState)
        if auth.user_role != "manager":
            yield rx.toast.error("Droits insuffisants.")
            return
        db = load_db()
        db["onboarding_steps"] = [s for s in db.get("onboarding_steps") or [] if str(s.get("id")) != step_id]
        save_db(db)
        yield rx.toast.info("Étape supprimée.")
        await self.load()

    # ── Parcours onboarding ───────────────────────────────────────────────────
    async def assign_onboarding(self, tech_id: str):
        auth = await self.get_state(AuthState)
        if auth.user_role != "manager":
            yield rx.toast.error("Droits insuffisants.")
            return
        db = load_db()
        db.setdefault("onboarding_progress", [])
        existing = next((p for p in db["onboarding_progress"] if str(p.get("tech_id")) == tech_id), None)
        if not existing:
            tech = next((t for t in db.get("technicians") or [] if str(t.get("id")) == tech_id), {})
            db["onboarding_progress"].append({
                "tech_id": tech_id,
                "tech_nom": tech.get("nom") or "",
                "steps_done": [],
                "date_debut": datetime.utcnow().strftime("%Y-%m-%d"),
            })
            save_db(db)
            log_activity(auth.user_nom, "CREATE", "onboarding", f"Parcours assigné à {tech.get('nom')}")
            yield rx.toast.success("Parcours assigné.")
        await self.load()

    async def unassign_onboarding(self, tech_id: str):
        auth = await self.get_state(AuthState)
        if auth.user_role != "manager":
            yield rx.toast.error("Droits insuffisants.")
            return
        db = load_db()
        tech_nom = next((p.get("tech_nom") for p in db.get("onboarding_progress") or [] if str(p.get("tech_id")) == tech_id), "")
        db["onboarding_progress"] = [p for p in db.get("onboarding_progress") or [] if str(p.get("tech_id")) != tech_id]
        save_db(db)
        log_activity(auth.user_nom, "DELETE", "onboarding", f"Parcours retiré à {tech_nom}")
        yield rx.toast.info("Parcours retiré.")
        await self.load()

    def open_checklist(self, tech_id: str):
        for p in self.onboarding_progress:
            if p.tech_id == tech_id:
                self.checklist_tech_id = tech_id
                self.checklist_tech_nom = p.tech_nom
                self.checklist_tech_color = p.color
                self.checklist_steps_done = list(p.steps_done)
                self.show_checklist = True
                break

    def close_checklist(self):
        self.show_checklist = False

    async def toggle_step_done(self, step_id: str):
        db = load_db()
        for p in db.get("onboarding_progress") or []:
            if str(p.get("tech_id")) == self.checklist_tech_id:
                done = list(p.get("steps_done") or [])
                if step_id in done:
                    done.remove(step_id)
                else:
                    done.append(step_id)
                p["steps_done"] = done
                self.checklist_steps_done = done
                break
        save_db(db)
        await self.load()
        for p in self.onboarding_progress:
            if p.tech_id == self.checklist_tech_id:
                self.checklist_steps_done = list(p.steps_done)
                break
