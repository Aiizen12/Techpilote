import math
import uuid
from datetime import datetime

import reflex as rx

from techpilot.db.database import load_db, save_db
from techpilot.state.models import FormationModule, OnboardingStep, OnboardingTechProgress
from techpilot.state.auth import AuthState
from techpilot.db.activity import log_activity

FORMATION_CATEGORIES = ["Réseau", "Active Directory", "Freshservice", "Téléphonie", "Sécurité", "Processus N1", "Autre"]
ONBOARDING_CATS = ["Accès", "Outils", "Processus", "Formation", "Autre"]

# Layout du cercle de compétences (vue individuelle)
RADIAL_SIZE   = 520   # px, conteneur carré
RADIAL_RADIUS = 190   # px, rayon des nœuds satellites
NODE_SIZE     = 84    # px, diamètre du nœud (ring + icône)
LABEL_WIDTH   = 104   # px, largeur de la carte nœud (ring + libellé), pour centrer le texte


def _ring_style(pct: int, color: str) -> str:
    return f"conic-gradient({color} {pct}%, rgba(255,255,255,0.08) {pct}% 100%)"


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

    # ── Compétences (lié au Skill Map) ──────────────────────────────────────────
    comp_view: str = "equipe"   # "equipe" | "individuel"
    comp_themes: list[dict] = []
    comp_formations: list[dict] = []
    comp_progress: list[dict] = []   # toutes les entrées skill_progress, tous techs
    comp_techs: list[dict] = []      # techs actifs [{id, nom, color}]

    comp_selected_tech_id: str = ""
    comp_selected_theme_id: str = ""

    show_assign_form: bool = False
    assign_formation_id: str = ""
    assign_formation_titre: str = ""
    assign_due_date: str = ""

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

        # ── Compétences (Skill Map) ──────────────────────────────────────────
        self.comp_themes = db.get("skill_themes") or []
        self.comp_formations = db.get("skill_formations") or []
        self.comp_progress = db.get("skill_progress") or []
        self.comp_techs = [
            {
                "id": str(t.get("id") or ""),
                "nom": t.get("nom") or "",
                "color": t.get("color") or "#6366f1",
                "initials": (t.get("nom") or "")[:2].upper(),
            }
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

    # ── Compétences : vars calculées ─────────────────────────────────────────

    @rx.var
    def team_comp_cards(self) -> list[dict]:
        total_formations = len(self.comp_formations)
        by_tech: dict = {}
        for p in self.comp_progress:
            by_tech.setdefault(str(p.get("tech_id")), []).append(p)
        result = []
        for t in self.comp_techs:
            entries = by_tech.get(t["id"], [])
            done = sum(1 for e in entries if e.get("statut") == "completed")
            pending = sum(1 for e in entries if e.get("assigned") and e.get("statut") != "completed")
            pct = round(done * 100 / total_formations) if total_formations else 0
            result.append({**t, "pct": pct, "pending": pending, "has_pending": pending > 0})
        return result

    @rx.var
    def comp_selected_tech(self) -> dict:
        for t in self.comp_techs:
            if t["id"] == self.comp_selected_tech_id:
                return t
        return {}

    @rx.var
    def comp_selected_tech_pct(self) -> int:
        for c in self.team_comp_cards:
            if c["id"] == self.comp_selected_tech_id:
                return c["pct"]
        return 0

    @rx.var
    def comp_theme_nodes(self) -> list[dict]:
        themes = sorted(self.comp_themes, key=lambda t: t.get("ordre", 0))
        n = len(themes)
        if n == 0:
            return []
        tid = self.comp_selected_tech_id
        prog_map = {
            (str(p.get("tech_id")), p.get("formation_id")): p
            for p in self.comp_progress
        }
        result = []
        for i, t in enumerate(themes):
            theme_id = t.get("id")
            theme_forms = [f for f in self.comp_formations if f.get("theme_id") == theme_id]
            total = len(theme_forms)
            done = sum(
                1 for f in theme_forms
                if prog_map.get((tid, f.get("id")), {}).get("statut") == "completed"
            )
            pct = round(done * 100 / total) if total else 0
            angle = math.radians(-90 + i * (360 / n))
            x = RADIAL_SIZE / 2 + RADIAL_RADIUS * math.cos(angle) - LABEL_WIDTH / 2
            y = RADIAL_SIZE / 2 + RADIAL_RADIUS * math.sin(angle) - NODE_SIZE / 2
            color = t.get("color") or "#6366f1"
            result.append({
                "id": theme_id,
                "nom": t.get("nom") or "",
                "icon": t.get("icon") or "book-open",
                "color": color,
                "pct": pct,
                "done": done,
                "total": total,
                "left": f"{x:.1f}px",
                "top": f"{y:.1f}px",
                "ring_bg": _ring_style(pct, color),
                "icon_border": f"2px solid {color}",
            })
        return result

    @rx.var
    def comp_selected_theme(self) -> dict:
        for node in self.comp_theme_nodes:
            if node["id"] == self.comp_selected_theme_id:
                return node
        return {}

    @rx.var
    def comp_theme_formations(self) -> list[dict]:
        if not self.comp_selected_theme_id or not self.comp_selected_tech_id:
            return []
        tid = self.comp_selected_tech_id
        result = []
        theme_forms = sorted(
            [f for f in self.comp_formations if f.get("theme_id") == self.comp_selected_theme_id],
            key=lambda f: f.get("ordre", 0),
        )
        for f in theme_forms:
            entry = next(
                (p for p in self.comp_progress
                 if str(p.get("tech_id")) == tid and p.get("formation_id") == f.get("id")),
                {},
            )
            result.append({
                "id": f.get("id"),
                "titre": f.get("titre") or "",
                "niveau": f.get("niveau") or "Débutant",
                "duree_min": int(f.get("duree_min") or 0),
                "statut": entry.get("statut", "not_started"),
                "assigned": bool(entry.get("assigned")),
                "assigned_by": entry.get("assigned_by") or "",
                "due_date": entry.get("due_date") or "",
            })
        return result

    # ── Compétences : navigation ─────────────────────────────────────────────

    def select_comp_tech(self, tech_id: str):
        self.comp_selected_tech_id = tech_id
        self.comp_selected_theme_id = ""
        self.comp_view = "individuel"

    def back_to_comp_team(self):
        self.comp_view = "equipe"
        self.comp_selected_tech_id = ""
        self.comp_selected_theme_id = ""

    def select_comp_theme(self, theme_id: str):
        self.comp_selected_theme_id = "" if self.comp_selected_theme_id == theme_id else theme_id

    def close_comp_theme(self):
        self.comp_selected_theme_id = ""

    # ── Compétences : assignation ────────────────────────────────────────────

    def open_assign_form(self, formation_id: str):
        if not self.comp_selected_tech_id:
            return
        f = next((f for f in self.comp_formations if f.get("id") == formation_id), {})
        self.assign_formation_id = formation_id
        self.assign_formation_titre = f.get("titre") or ""
        self.assign_due_date = ""
        self.show_assign_form = True

    def close_assign_form(self):
        self.show_assign_form = False

    def set_assign_due_date(self, v: str):
        self.assign_due_date = v

    async def save_assignment(self):
        auth = await self.get_state(AuthState)
        if not auth.can_edit_formation:
            yield rx.toast.error("Droits insuffisants.")
            return
        tech_id = self.comp_selected_tech_id
        if not tech_id or not self.assign_formation_id:
            return
        db = load_db()
        prog = db.setdefault("skill_progress", [])
        now = datetime.now().strftime("%d/%m/%Y")
        existing = next(
            (p for p in prog
             if str(p.get("tech_id")) == str(tech_id) and p.get("formation_id") == self.assign_formation_id),
            None,
        )
        if existing:
            existing["assigned"] = True
            existing["assigned_by"] = auth.user_nom
            existing["assigned_at"] = now
            existing["due_date"] = self.assign_due_date
        else:
            prog.append({
                "id": uuid.uuid4().hex[:8],
                "tech_id": tech_id,
                "formation_id": self.assign_formation_id,
                "statut": "not_started",
                "date_start": "",
                "date_completion": "",
                "score_quiz": 0,
                "assigned": True,
                "assigned_by": auth.user_nom,
                "assigned_at": now,
                "due_date": self.assign_due_date,
            })
        save_db(db)
        log_activity(auth.user_nom, "CREATE", "skill_map", f"Formation assignée: {self.assign_formation_titre}")
        self.show_assign_form = False
        yield rx.toast.success("Formation assignée.")
        await self.load()

    async def unassign_formation(self, formation_id: str):
        auth = await self.get_state(AuthState)
        if not auth.can_edit_formation:
            yield rx.toast.error("Droits insuffisants.")
            return
        tech_id = self.comp_selected_tech_id
        db = load_db()
        for p in db.get("skill_progress") or []:
            if str(p.get("tech_id")) == str(tech_id) and p.get("formation_id") == formation_id:
                p["assigned"] = False
                p["assigned_by"] = ""
                p["due_date"] = ""
                break
        save_db(db)
        yield rx.toast.info("Assignation retirée.")
        await self.load()

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
