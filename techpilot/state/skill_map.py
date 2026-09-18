import uuid
from datetime import datetime

import reflex as rx

from techpilot.db.database import load_db, save_db
from techpilot.state.auth import AuthState

NIVEAUX   = ["Débutant", "Intermédiaire", "Expert"]
CONTENU_TYPES = ["texte", "lien", "procedure", "quiz"]


def _rgb_str(color: str) -> str:
    h = color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b}"


class SkillMapState(rx.State):
    # ── Données ──────────────────────────────────────────────────────────────
    themes:      list[dict] = []
    formations:  list[dict] = []
    parcours:    list[dict] = []
    progress:    list[dict] = []

    # ── Navigation carte ─────────────────────────────────────────────────────
    selected_theme_id:    str = ""   # thème cliqué → affiche ses formations
    selected_formation_id: str = ""  # formation cliquée → panneau détail

    # ── Edition thème ─────────────────────────────────────────────────────────
    show_theme_form: bool = False
    edit_theme_id:   str = ""
    th_nom:          str = ""
    th_icon:         str = "book-open"
    th_color:        str = "#6366f1"
    th_description:  str = ""

    # ── Edition formation ─────────────────────────────────────────────────────
    show_formation_form: bool = False
    edit_formation_id:   str = ""
    fm_titre:            str = ""
    fm_theme_id:         str = ""
    fm_niveau:           str = "Débutant"
    fm_duree_min:        str = "30"
    fm_description:      str = ""
    # Contenus : list de dicts {type, titre, contenu/url/proc_id/questions}
    fm_contenus:         list[dict] = []
    # Contenu en cours d'ajout
    new_contenu_type:    str = "texte"
    new_contenu_titre:   str = ""
    new_contenu_body:    str = ""
    new_contenu_codif:   str = ""   # pour les blocs de type "procedure"

    # ── Procédures (pour la liaison dans les formations) ──────────────────────
    procedures_all:      list[dict] = []
    proc_search_query:   str = ""

    # ── Edition parcours ──────────────────────────────────────────────────────
    show_parcours_form: bool = False
    edit_parcours_id:   str = ""
    pc_nom:             str = ""
    pc_description:     str = ""
    pc_icon:            str = "map"
    pc_color:           str = "#6366f1"
    pc_etapes:          list[str] = []  # formation_ids ordonnées

    # ── Vue quiz (tech) ───────────────────────────────────────────────────────
    quiz_answers: list[int] = []   # réponse sélectionnée par question (-1 = pas encore)
    quiz_submitted: bool = False
    quiz_score: int = 0

    # ── Confirm delete ────────────────────────────────────────────────────────
    confirm_delete_type: str = ""  # "theme" | "formation" | "parcours"
    confirm_delete_id:   str = ""

    # ── Computed vars ─────────────────────────────────────────────────────────

    @rx.var
    def selected_theme(self) -> dict:
        for t in self.themes:
            if t.get("id") == self.selected_theme_id:
                return t
        return {}

    @rx.var
    def theme_formations(self) -> list[dict]:
        if not self.selected_theme_id:
            return []
        result = []
        for f in sorted(
            [f for f in self.formations if f.get("theme_id") == self.selected_theme_id],
            key=lambda f: f.get("ordre", 0),
        ):
            fid    = f.get("id", "")
            status = self.my_progress_map.get(fid, "not_started")
            result.append({**f, "progress_status": status})
        return result

    @rx.var
    def selected_formation_progress(self) -> str:
        return self.my_progress_map.get(self.selected_formation_id, "not_started")

    @rx.var
    def selected_formation_my_assignment(self) -> dict:
        for p in self.progress:
            if p.get("formation_id") == self.selected_formation_id and p.get("assigned"):
                return p
        return {}

    @rx.var
    def selected_formation_is_assigned(self) -> bool:
        return bool(self.selected_formation_my_assignment)

    @rx.var
    def selected_formation_contenus(self) -> list[dict]:
        return self.selected_formation.get("contenus", [])

    @rx.var
    def selected_has_contenus(self) -> bool:
        return bool(self.selected_formation.get("contenus", []))

    @rx.var
    def selected_formation(self) -> dict:
        for f in self.formations:
            if f.get("id") == self.selected_formation_id:
                return f
        return {}

    @rx.var
    def themes_with_counts(self) -> list[dict]:
        result = []
        for t in sorted(self.themes, key=lambda x: x.get("ordre", 0)):
            count = sum(1 for f in self.formations if f.get("theme_id") == t["id"])
            done  = sum(1 for p in self.progress
                        if p.get("statut") == "completed"
                        and any(f.get("id") == p.get("formation_id") and f.get("theme_id") == t["id"]
                                for f in self.formations))
            pct   = round(done * 100 / count) if count else 0
            color = t.get("color", "#6366f1")
            rgb   = _rgb_str(color)
            result.append({
                **t,
                "count":            count,
                "done":             done,
                "pct":              pct,
                "has_formations":   count > 0,
                "formation_label":  "formations" if count != 1 else "formation",
                "progress_width":   f"{pct}%",
                "bg_selected":      f"rgba({rgb},0.12)",
                "bg_hover":         f"rgba({rgb},0.07)",
                "border_selected":  f"1px solid {color}",
                "border_hover":     f"1px solid {color}88",
                "shadow_selected":  f"0 0 0 2px {color}33",
            })
        return result

    @rx.var
    def sel_color(self) -> str:
        return self.selected_theme.get("color", "#6366f1")

    @rx.var
    def sel_bg_active(self) -> str:
        c = self.selected_theme.get("color", "#6366f1")
        return f"rgba({_rgb_str(c)},0.1)"

    @rx.var
    def sel_bg_hover(self) -> str:
        c = self.selected_theme.get("color", "#6366f1")
        return f"rgba({_rgb_str(c)},0.07)"

    @rx.var
    def sel_border_active(self) -> str:
        c = self.selected_theme.get("color", "#6366f1")
        return f"1px solid {c}88"

    @rx.var
    def sel_border_hover(self) -> str:
        c = self.selected_theme.get("color", "#6366f1")
        return f"1px solid {c}55"

    @rx.var
    def my_progress_map(self) -> dict:
        auth = self._get_auth_snapshot()
        uid = auth.get("user_id", "")
        result = {}
        for p in self.progress:
            if str(p.get("tech_id")) == str(uid):
                result[p["formation_id"]] = p.get("statut", "not_started")
        return result

    def _get_auth_snapshot(self) -> dict:
        db = load_db()
        return {"user_id": "", "user_role": ""}

    @rx.var
    def total_progress_pct(self) -> int:
        total = len(self.formations)
        if total == 0:
            return 0
        done = sum(1 for f in self.formations
                   if self.my_progress_map.get(f["id"]) == "completed")
        return round(done * 100 / total)

    @rx.var
    def parcours_with_progress(self) -> list[dict]:
        result = []
        for pc in self.parcours:
            etapes = pc.get("etapes", [])
            total  = len(etapes)
            done   = sum(1 for fid in etapes
                        if self.my_progress_map.get(fid) == "completed")
            result.append({**pc, "total": total, "done": done,
                           "pct": round(done * 100 / total) if total else 0})
        return result

    @rx.var
    def filtered_procedures(self) -> list[dict]:
        q = self.proc_search_query.lower().strip()
        if not q:
            return self.procedures_all[:12]
        result = []
        for p in self.procedures_all:
            t  = (p.get("titre") or "").lower()
            c  = (p.get("codification") or "").lower()
            ms = (p.get("master_subject") or "").lower()
            if q in t or q in c or q in ms:
                result.append(p)
            if len(result) >= 15:
                break
        return result

    # ── Load ──────────────────────────────────────────────────────────────────

    @rx.event
    async def load(self):
        db = load_db()
        self.themes         = db.get("skill_themes", [])
        self.formations     = db.get("skill_formations", [])
        self.parcours       = db.get("skill_parcours", [])
        self.procedures_all = db.get("procedures_content", [])
        auth = await self.get_state(AuthState)
        uid  = auth.user_id
        self.progress = [p for p in db.get("skill_progress", [])
                         if str(p.get("tech_id")) == str(uid)]

    # ── Navigation ────────────────────────────────────────────────────────────

    @rx.event
    def select_theme(self, theme_id: str):
        self.selected_theme_id = theme_id
        self.selected_formation_id = ""

    @rx.event
    def select_formation(self, formation_id: str):
        self.selected_formation_id = formation_id
        self.quiz_answers = []
        self.quiz_submitted = False
        self.quiz_score = 0

    @rx.event
    def close_formation(self):
        self.selected_formation_id = ""

    # ── Thème CRUD ────────────────────────────────────────────────────────────

    @rx.event
    def open_new_theme(self):
        self.edit_theme_id  = ""
        self.th_nom         = ""
        self.th_icon        = "book-open"
        self.th_color       = "#6366f1"
        self.th_description = ""
        self.show_theme_form = True

    @rx.event
    def open_edit_theme(self, theme_id: str):
        for t in self.themes:
            if t.get("id") == theme_id:
                self.edit_theme_id  = theme_id
                self.th_nom         = t.get("nom", "")
                self.th_icon        = t.get("icon", "book-open")
                self.th_color       = t.get("color", "#6366f1")
                self.th_description = t.get("description", "")
                self.show_theme_form = True
                return

    @rx.event
    def close_theme_form(self):
        self.show_theme_form = False

    @rx.event
    def save_theme(self):
        if not self.th_nom.strip():
            return
        db = load_db()
        themes = db.get("skill_themes", [])
        if self.edit_theme_id:
            for i, t in enumerate(themes):
                if t.get("id") == self.edit_theme_id:
                    themes[i] = {**t, "nom": self.th_nom, "icon": self.th_icon,
                                  "color": self.th_color, "description": self.th_description}
                    break
        else:
            themes.append({"id": f"sth-{uuid.uuid4().hex[:8]}", "nom": self.th_nom,
                           "icon": self.th_icon, "color": self.th_color,
                           "description": self.th_description, "ordre": len(themes)})
        db["skill_themes"] = themes
        save_db(db)
        self.themes = themes
        self.show_theme_form = False

    # ── Formation CRUD ────────────────────────────────────────────────────────

    @rx.event
    def open_new_formation(self, theme_id: str = ""):
        self.edit_formation_id = ""
        self.fm_titre          = ""
        self.fm_theme_id       = theme_id or (self.selected_theme_id)
        self.fm_niveau         = "Débutant"
        self.fm_duree_min      = "30"
        self.fm_description    = ""
        self.fm_contenus       = []
        self.new_contenu_type  = "texte"
        self.new_contenu_titre = ""
        self.new_contenu_body  = ""
        self.new_contenu_codif = ""
        self.proc_search_query = ""
        self.show_formation_form = True

    @rx.event
    def open_edit_formation(self, formation_id: str):
        for f in self.formations:
            if f.get("id") == formation_id:
                self.edit_formation_id = formation_id
                self.fm_titre          = f.get("titre", "")
                self.fm_theme_id       = f.get("theme_id", "")
                self.fm_niveau         = f.get("niveau", "Débutant")
                self.fm_duree_min      = str(f.get("duree_min", 30))
                self.fm_description    = f.get("description", "")
                self.fm_contenus       = list(f.get("contenus", []))
                self.new_contenu_type  = "texte"
                self.new_contenu_titre = ""
                self.new_contenu_body  = ""
                self.new_contenu_codif = ""
                self.proc_search_query = ""
                self.show_formation_form = True
                return

    @rx.event
    def close_formation_form(self):
        self.show_formation_form = False

    @rx.event
    def set_fm_titre(self, v: str):       self.fm_titre = v
    @rx.event
    def set_fm_theme_id(self, v: str):    self.fm_theme_id = v
    @rx.event
    def set_fm_niveau(self, v: str):      self.fm_niveau = v
    @rx.event
    def set_fm_duree_min(self, v: str):   self.fm_duree_min = v
    @rx.event
    def set_fm_description(self, v: str): self.fm_description = v
    @rx.event
    def set_th_nom(self, v: str):         self.th_nom = v
    @rx.event
    def set_th_icon(self, v: str):        self.th_icon = v
    @rx.event
    def set_th_color(self, v: str):       self.th_color = v
    @rx.event
    def set_th_description(self, v: str): self.th_description = v
    @rx.event
    def set_new_contenu_type(self, v: str):
        self.new_contenu_type  = v
        self.proc_search_query = ""
        self.new_contenu_codif = ""
        self.new_contenu_titre = ""
        self.new_contenu_body  = ""
    @rx.event
    def set_new_contenu_titre(self, v: str): self.new_contenu_titre = v
    @rx.event
    def set_new_contenu_body(self, v: str):  self.new_contenu_body = v
    @rx.event
    def set_proc_search_query(self, v: str): self.proc_search_query = v
    @rx.event
    def select_procedure_for_content(self, proc_id: str):
        for p in self.procedures_all:
            if p.get("id") == proc_id:
                self.new_contenu_titre = p.get("titre", "")
                self.new_contenu_codif = p.get("codification", "")
                self.new_contenu_body  = p.get("google_doc_url", "")
                self.proc_search_query = ""
                return

    @rx.event
    def add_contenu(self):
        if self.new_contenu_type == "procedure":
            if not self.new_contenu_titre.strip():
                return
            c = {
                "id":           uuid.uuid4().hex[:8],
                "type":         "procedure",
                "titre":        self.new_contenu_titre,
                "codification": self.new_contenu_codif or "Sans",
                "body":         self.new_contenu_body,
            }
        else:
            if not self.new_contenu_body.strip():
                return
            c = {
                "id":    uuid.uuid4().hex[:8],
                "type":  self.new_contenu_type,
                "titre": self.new_contenu_titre or self.new_contenu_type.capitalize(),
                "body":  self.new_contenu_body,
            }
            if self.new_contenu_type == "quiz":
                c["questions"] = []
        self.fm_contenus       = [*self.fm_contenus, c]
        self.new_contenu_titre = ""
        self.new_contenu_body  = ""
        self.new_contenu_codif = ""
        self.proc_search_query = ""

    @rx.event
    def remove_contenu(self, cid: str):
        self.fm_contenus = [c for c in self.fm_contenus if c.get("id") != cid]

    @rx.event
    def save_formation(self):
        if not self.fm_titre.strip() or not self.fm_theme_id:
            return
        db = load_db()
        formations = db.get("skill_formations", [])
        fields = {
            "titre":       self.fm_titre,
            "theme_id":    self.fm_theme_id,
            "niveau":      self.fm_niveau,
            "duree_min":   int(self.fm_duree_min or "30"),
            "description": self.fm_description,
            "contenus":    self.fm_contenus,
        }
        if self.edit_formation_id:
            for i, f in enumerate(formations):
                if f.get("id") == self.edit_formation_id:
                    formations[i] = {**f, **fields}
                    break
        else:
            formations.append({
                "id":            f"sf-{uuid.uuid4().hex[:8]}",
                "ordre":         len([x for x in formations if x.get("theme_id") == self.fm_theme_id]),
                "date_creation": datetime.now().strftime("%d/%m/%Y"),
                **fields,
            })
        db["skill_formations"] = formations
        save_db(db)
        self.formations = formations
        self.show_formation_form = False

    # ── Parcours CRUD ─────────────────────────────────────────────────────────

    @rx.event
    def set_pc_nom(self, v: str):         self.pc_nom = v
    @rx.event
    def set_pc_description(self, v: str): self.pc_description = v
    @rx.event
    def set_pc_icon(self, v: str):        self.pc_icon = v
    @rx.event
    def set_pc_color(self, v: str):       self.pc_color = v

    @rx.event
    def open_new_parcours(self):
        self.edit_parcours_id = ""
        self.pc_nom           = ""
        self.pc_description   = ""
        self.pc_icon          = "map"
        self.pc_color         = "#6366f1"
        self.pc_etapes        = []
        self.show_parcours_form = True

    @rx.event
    def open_edit_parcours(self, parcours_id: str):
        for pc in self.parcours:
            if pc.get("id") == parcours_id:
                self.edit_parcours_id = parcours_id
                self.pc_nom           = pc.get("nom", "")
                self.pc_description   = pc.get("description", "")
                self.pc_icon          = pc.get("icon", "map")
                self.pc_color         = pc.get("color", "#6366f1")
                self.pc_etapes        = list(pc.get("etapes", []))
                self.show_parcours_form = True
                return

    @rx.event
    def close_parcours_form(self):
        self.show_parcours_form = False

    @rx.event
    def toggle_etape(self, formation_id: str):
        if formation_id in self.pc_etapes:
            self.pc_etapes = [e for e in self.pc_etapes if e != formation_id]
        else:
            self.pc_etapes = [*self.pc_etapes, formation_id]

    @rx.event
    def save_parcours(self):
        if not self.pc_nom.strip():
            return
        db = load_db()
        parcours = db.get("skill_parcours", [])
        fields = {"nom": self.pc_nom, "description": self.pc_description,
                  "icon": self.pc_icon, "color": self.pc_color, "etapes": self.pc_etapes}
        if self.edit_parcours_id:
            for i, pc in enumerate(parcours):
                if pc.get("id") == self.edit_parcours_id:
                    parcours[i] = {**pc, **fields}
                    break
        else:
            parcours.append({"id": f"sp-{uuid.uuid4().hex[:8]}", **fields})
        db["skill_parcours"] = parcours
        save_db(db)
        self.parcours = parcours
        self.show_parcours_form = False

    # ── Progression (tech) ────────────────────────────────────────────────────

    @rx.event
    async def mark_progress(self, formation_id: str, statut: str):
        auth = await self.get_state(AuthState)
        uid  = auth.user_id
        db   = load_db()
        prog = db.get("skill_progress", [])
        existing = next((p for p in prog
                         if str(p.get("tech_id")) == str(uid)
                         and p.get("formation_id") == formation_id), None)
        now = datetime.now().strftime("%d/%m/%Y")
        if existing:
            existing["statut"] = statut
            if statut == "completed":
                existing["date_completion"] = now
        else:
            prog.append({
                "id":            uuid.uuid4().hex[:8],
                "tech_id":       uid,
                "formation_id":  formation_id,
                "statut":        statut,
                "date_start":    now,
                "date_completion": now if statut == "completed" else "",
                "score_quiz":    0,
            })
        db["skill_progress"] = prog
        save_db(db)
        self.progress = [p for p in prog if str(p.get("tech_id")) == str(uid)]

    # ── Delete ────────────────────────────────────────────────────────────────

    @rx.event
    def ask_delete(self, dtype: str, did: str):
        self.confirm_delete_type = dtype
        self.confirm_delete_id   = did

    @rx.event
    def cancel_delete(self):
        self.confirm_delete_type = ""
        self.confirm_delete_id   = ""

    @rx.event
    def confirm_delete(self):
        db  = load_db()
        key = {"theme": "skill_themes", "formation": "skill_formations",
               "parcours": "skill_parcours"}.get(self.confirm_delete_type)
        if key:
            db[key] = [x for x in db.get(key, []) if x.get("id") != self.confirm_delete_id]
            save_db(db)
            self.themes     = db.get("skill_themes", [])
            self.formations = db.get("skill_formations", [])
            self.parcours   = db.get("skill_parcours", [])
            if self.selected_theme_id == self.confirm_delete_id:
                self.selected_theme_id = ""
            if self.selected_formation_id == self.confirm_delete_id:
                self.selected_formation_id = ""
        self.confirm_delete_type = ""
        self.confirm_delete_id   = ""
