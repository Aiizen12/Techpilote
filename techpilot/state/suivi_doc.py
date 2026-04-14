import uuid
from datetime import datetime

import reflex as rx

from techpilot.db.database import load_db, save_db
from techpilot.state.auth import AuthState
from techpilot.state.models import AmeliorationItem, ProcSuiviRow
from techpilot.state.escalade import PROCEDURE_MAP

CATEGORIES  = ["Process", "UX", "Technique", "Formation", "Autre"]
PRIORITES   = ["Basse", "Normale", "Haute", "Critique"]
STATUTS_AM  = ["Ouvert", "En cours", "Résolu", "Fermé"]


class SuiviDocState(rx.State):

    # ── Navigation onglets ────────────────────────────────────────────────
    tab: str = "amelioration"   # amelioration | procedures

    # ── Amélioration Desk ─────────────────────────────────────────────────
    items: list[AmeliorationItem] = []
    filter_statut: str = ""

    show_form: bool = False
    edit_id: str = ""           # vide = nouvelle fiche
    form_titre: str = ""
    form_description: str = ""
    form_categorie: str = "Process"
    form_priorite: str = "Normale"
    form_statut: str = "Ouvert"

    confirm_delete_id: str = ""   # id en attente de confirmation suppression

    # ── Suivi des Procédures ──────────────────────────────────────────────
    proc_rows: list[ProcSuiviRow] = []
    proc_perimetres: list[str] = []
    proc_filter_perimetre: str = ""
    proc_search: str = ""
    proc_page: int = 1
    proc_limit: int = 30
    proc_total: int = 0

    # ── Chargement ────────────────────────────────────────────────────────

    def load(self):
        self._load_amelioration()
        self._load_proc_suivi()

    def set_tab(self, t: str):
        self.tab = t

    # ── Amélioration Desk ─────────────────────────────────────────────────

    def _load_amelioration(self):
        db = load_db()
        items = sorted(
            db.get("amelioration_desk") or [],
            key=lambda x: x.get("date_creation") or "",
            reverse=True,
        )
        if self.filter_statut:
            items = [i for i in items if i.get("statut") == self.filter_statut]
        self.items = [
            AmeliorationItem(
                id=str(i.get("id") or ""),
                titre=i.get("titre") or "",
                description=i.get("description") or "",
                categorie=i.get("categorie") or "",
                priorite=i.get("priorite") or "",
                statut=i.get("statut") or "",
                auteur_nom=i.get("auteur_nom") or "",
                date_creation=(i.get("date_creation") or "")[:10],
            )
            for i in items
        ]

    def set_filter_statut(self, v: str):
        self.filter_statut = v
        self._load_amelioration()

    def clear_filter_statut(self):
        self.filter_statut = ""
        self._load_amelioration()

    def open_new_form(self):
        self.edit_id = ""
        self.form_titre = ""
        self.form_description = ""
        self.form_categorie = "Process"
        self.form_priorite = "Normale"
        self.form_statut = "Ouvert"
        self.show_form = True

    def open_edit_form(self, item_id: str):
        db = load_db()
        item = next(
            (i for i in (db.get("amelioration_desk") or []) if str(i.get("id")) == item_id),
            None,
        )
        if not item:
            return
        self.edit_id = item_id
        self.form_titre = item.get("titre") or ""
        self.form_description = item.get("description") or ""
        self.form_categorie = item.get("categorie") or "Process"
        self.form_priorite = item.get("priorite") or "Normale"
        self.form_statut = item.get("statut") or "Ouvert"
        self.show_form = True

    def close_form(self):
        self.show_form = False

    def set_form_titre(self, v: str):
        self.form_titre = v

    def set_form_description(self, v: str):
        self.form_description = v

    def set_form_categorie(self, v: str):
        self.form_categorie = v

    def set_form_priorite(self, v: str):
        self.form_priorite = v

    def set_form_statut(self, v: str):
        self.form_statut = v

    async def save_form(self):
        if not self.form_titre.strip():
            yield rx.toast.error("Le titre est obligatoire.")
            return
        auth = await self.get_state(AuthState)
        db = load_db()
        if "amelioration_desk" not in db:
            db["amelioration_desk"] = []

        if self.edit_id:
            for item in db["amelioration_desk"]:
                if str(item.get("id")) == self.edit_id:
                    item["titre"] = self.form_titre.strip()
                    item["description"] = self.form_description.strip()
                    item["categorie"] = self.form_categorie
                    item["priorite"] = self.form_priorite
                    item["statut"] = self.form_statut
                    break
        else:
            db["amelioration_desk"].append({
                "id": str(uuid.uuid4()),
                "titre": self.form_titre.strip(),
                "description": self.form_description.strip(),
                "categorie": self.form_categorie,
                "priorite": self.form_priorite,
                "statut": self.form_statut,
                "auteur_nom": auth.user_nom,
                "date_creation": datetime.utcnow().isoformat(),
            })

        save_db(db)
        self.show_form = False
        self._load_amelioration()
        label = "Fiche mise à jour." if self.edit_id else "Fiche ajoutée."
        yield rx.toast.success(label)

    def ask_delete(self, item_id: str):
        self.confirm_delete_id = item_id

    def cancel_delete(self):
        self.confirm_delete_id = ""

    def confirm_delete(self):
        if not self.confirm_delete_id:
            return
        db = load_db()
        db["amelioration_desk"] = [
            i for i in (db.get("amelioration_desk") or [])
            if str(i.get("id")) != self.confirm_delete_id
        ]
        save_db(db)
        self.confirm_delete_id = ""
        self._load_amelioration()
        return rx.toast.info("Fiche supprimée.")

    # ── Suivi des Procédures ──────────────────────────────────────────────

    def _load_proc_suivi(self):
        db = load_db()
        custom = db.get("procedures_custom") or {}
        all_rows = db.get("escalation_matrix") or []

        perimetres = sorted(set(r.get("perimetre", "") for r in all_rows if r.get("perimetre")))
        self.proc_perimetres = perimetres

        filtered = all_rows
        if self.proc_filter_perimetre:
            filtered = [r for r in filtered if r.get("perimetre") == self.proc_filter_perimetre]
        if self.proc_search:
            q = self.proc_search.lower()
            filtered = [
                r for r in filtered
                if q in (r.get("perimetre") or "").lower()
                or q in (r.get("typologie") or "").lower()
                or q in (r.get("categorie_fresh") or "").lower()
            ]

        self.proc_total = len(filtered)
        offset = (self.proc_page - 1) * self.proc_limit
        page_rows = filtered[offset: offset + self.proc_limit]

        result = []
        for r in page_rows:
            p = r.get("perimetre") or ""
            t = r.get("typologie") or ""
            c = r.get("categorie_fresh") or ""
            key = f"{p}|{t}"

            if custom.get(key):
                has_proc = True
                source = "Personnalisée"
            elif PROCEDURE_MAP.get((p, t)):
                has_proc = True
                source = "Intégrée"
            else:
                # Fuzzy fallback
                t_lower = t.lower()
                found = False
                for (mp, mt) in PROCEDURE_MAP:
                    if mp == p and (mt.lower() in t_lower or t_lower in mt.lower()):
                        found = True
                        break
                has_proc = found
                source = "Intégrée" if found else ""

            result.append(ProcSuiviRow(
                perimetre=p,
                typologie=t,
                categorie_fresh=c,
                has_procedure=has_proc,
                procedure_source=source,
            ))
        self.proc_rows = result

    def set_proc_filter_perimetre(self, v: str):
        self.proc_filter_perimetre = v
        self.proc_page = 1
        self._load_proc_suivi()

    def clear_proc_filter(self):
        self.proc_filter_perimetre = ""
        self.proc_search = ""
        self.proc_page = 1
        self._load_proc_suivi()

    def set_proc_search(self, v: str):
        self.proc_search = v
        self.proc_page = 1
        self._load_proc_suivi()

    def proc_go_page(self, p: int):
        self.proc_page = p
        self._load_proc_suivi()

    @rx.var
    def proc_total_pages(self) -> int:
        return max(1, (self.proc_total + self.proc_limit - 1) // self.proc_limit)

    @rx.var
    def proc_count_with(self) -> int:
        return sum(1 for r in self.proc_rows if r.has_procedure)

    @rx.var
    def proc_count_without(self) -> int:
        return sum(1 for r in self.proc_rows if not r.has_procedure)
