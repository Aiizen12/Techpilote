import uuid
from datetime import datetime

import reflex as rx

from techpilot.db.database import load_db, save_db
from techpilot.state.auth import AuthState
from techpilot.state.models import AmeliorationItem, ProcSuiviRow, DocPickerItem, AutoMatchProposal
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
    proc_filter_has_proc: str = ""   # "" | "oui" | "non"
    proc_search: str = ""
    proc_page: int = 1
    proc_limit: int = 30
    proc_total: int = 0

    # ── Formulaire procédure (depuis le tableau) ──────────────────────────
    show_proc_form: bool = False
    proc_form_perimetre: str = ""
    proc_form_typologie: str = ""
    proc_form_steps_text: str = ""

    # ── Liaison document ↔ procédure ──────────────────────────────────────
    show_doc_picker: bool = False
    doc_picker_key: str = ""          # "perimetre|typologie"
    available_proc_docs: list[DocPickerItem] = []
    doc_picker_tab: str = "documents"   # "documents" | "gabarits"
    doc_picker_search: str = ""
    available_gabarits_picker: list[DocPickerItem] = []

    # ── Auto-détection des correspondances documents ↔ matrice ────────────
    show_auto_match: bool = False
    auto_match_proposals: list[AutoMatchProposal] = []
    expanded_proposal_idx: int = -1

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
        self.filter_statut = "" if v == "_all" else v
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
        proc_doc_links = db.get("proc_doc_links") or {}
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

        # Compute has_procedure for each row
        computed = []
        for r in filtered:
            p = r.get("perimetre") or ""
            t = r.get("typologie") or ""
            c = r.get("categorie_fresh") or ""
            key = f"{p}|{t}"

            doc_link = proc_doc_links.get(key) or {}
            doc_name = doc_link.get("doc_name", "")
            doc_url  = doc_link.get("doc_url", "")

            if doc_link:
                has_proc = True
                source = "Document"
            elif custom.get(key):
                has_proc = True
                source = "Personnalisée"
            elif PROCEDURE_MAP.get((p, t)):
                has_proc = True
                source = "Intégrée"
            else:
                t_lower = t.lower()
                found = False
                for (mp, mt) in PROCEDURE_MAP:
                    if mp == p and (mt.lower() in t_lower or t_lower in mt.lower()):
                        found = True
                        break
                has_proc = found
                source = "Intégrée" if found else ""

            computed.append((p, t, c, has_proc, source, doc_name, doc_url, key))

        # Filter by has_procedure
        if self.proc_filter_has_proc == "oui":
            computed = [row for row in computed if row[3]]
        elif self.proc_filter_has_proc == "non":
            computed = [row for row in computed if not row[3]]

        self.proc_total = len(computed)
        offset = (self.proc_page - 1) * self.proc_limit
        page_rows = computed[offset: offset + self.proc_limit]

        self.proc_rows = [
            ProcSuiviRow(
                perimetre=p,
                typologie=t,
                categorie_fresh=c,
                has_procedure=hp,
                procedure_source=s,
                doc_name=dn,
                doc_url=du,
            )
            for p, t, c, hp, s, dn, du, _key in page_rows
        ]

    def set_proc_filter_perimetre(self, v: str):
        self.proc_filter_perimetre = "" if v == "_all" else v
        self.proc_page = 1
        self._load_proc_suivi()

    def set_proc_filter_has_proc(self, v: str):
        self.proc_filter_has_proc = "" if v == "_all" else v
        self.proc_page = 1
        self._load_proc_suivi()

    def clear_proc_filter(self):
        self.proc_filter_perimetre = ""
        self.proc_filter_has_proc = ""
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

    # ── Procédure form (depuis le tableau) ────────────────────────────────

    def open_proc_form(self, perimetre: str, typologie: str):
        db = load_db()
        key = f"{perimetre}|{typologie}"
        custom = (db.get("procedures_custom") or {}).get(key)
        self.proc_form_perimetre = perimetre
        self.proc_form_typologie = typologie
        if custom:
            self.proc_form_steps_text = "\n".join(custom)
        else:
            # Fallback to PROCEDURE_MAP
            exact = PROCEDURE_MAP.get((perimetre, typologie), [])
            if not exact:
                t_lower = typologie.lower()
                for (p, t), steps in PROCEDURE_MAP.items():
                    if p == perimetre and (t.lower() in t_lower or t_lower in t.lower()):
                        exact = steps
                        break
            self.proc_form_steps_text = "\n".join(exact)
        self.show_proc_form = True

    def close_proc_form(self):
        self.show_proc_form = False

    def set_proc_form_steps_text(self, v: str):
        self.proc_form_steps_text = v

    async def save_proc_form(self):
        if not self.proc_form_steps_text.strip():
            yield rx.toast.error("Les étapes sont obligatoires.")
            return
        db = load_db()
        if "procedures_custom" not in db:
            db["procedures_custom"] = {}
        key = f"{self.proc_form_perimetre}|{self.proc_form_typologie}"
        steps = [s.strip() for s in self.proc_form_steps_text.strip().split("\n") if s.strip()]
        db["procedures_custom"][key] = steps
        save_db(db)
        self.show_proc_form = False
        self._load_proc_suivi()
        yield rx.toast.success("Procédure sauvegardée.")

    async def delete_proc_form(self):
        db = load_db()
        key = f"{self.proc_form_perimetre}|{self.proc_form_typologie}"
        customs = db.get("procedures_custom") or {}
        if key in customs:
            del customs[key]
            db["procedures_custom"] = customs
            save_db(db)
        self.show_proc_form = False
        self._load_proc_suivi()
        yield rx.toast.info("Procédure personnalisée supprimée.")

    # ── Liaison document ↔ procédure ──────────────────────────────────────

    def open_doc_picker(self, perimetre: str, typologie: str):
        self.doc_picker_key = f"{perimetre}|{typologie}"
        self.doc_picker_tab = "documents"
        self.doc_picker_search = ""
        self._reload_picker_lists()
        self.show_doc_picker = True

    def _reload_picker_lists(self):
        db = load_db()
        q = self.doc_picker_search.lower()
        docs = sorted(
            [d for d in (db.get("documents") or []) if d.get("url")],
            key=lambda d: d.get("nom_original") or "",
        )
        if q:
            docs = [d for d in docs if q in (d.get("nom_original") or "").lower()
                    or q in (d.get("description") or "").lower()]
        self.available_proc_docs = [
            DocPickerItem(id=str(d.get("id", "")), nom=d.get("nom_original", ""), url=d.get("url", ""))
            for d in docs
        ]
        gabarits = sorted(db.get("gabarits") or [], key=lambda g: g.get("titre") or "")
        if q:
            gabarits = [g for g in gabarits if q in (g.get("titre") or "").lower()
                        or q in (g.get("contenu") or "").lower()]
        self.available_gabarits_picker = [
            DocPickerItem(id=str(g.get("id", "")), nom=g.get("titre", ""), url="")
            for g in gabarits
        ]

    def set_doc_picker_tab(self, t: str):
        self.doc_picker_tab = t

    def set_doc_picker_search(self, v: str):
        self.doc_picker_search = v
        self._reload_picker_lists()

    def close_doc_picker(self):
        self.show_doc_picker = False
        self.doc_picker_key = ""
        self.doc_picker_search = ""

    def link_doc_to_proc(self, doc_id: str, doc_name: str, doc_url: str):
        if not self.doc_picker_key:
            return
        db = load_db()
        if "proc_doc_links" not in db:
            db["proc_doc_links"] = {}
        db["proc_doc_links"][self.doc_picker_key] = {
            "doc_id": doc_id,
            "doc_name": doc_name,
            "doc_url": doc_url,
        }
        save_db(db)
        self.show_doc_picker = False
        self.doc_picker_key = ""
        self.doc_picker_search = ""
        self._load_proc_suivi()

    def link_gabarit_to_proc(self, gabarit_id: str, gabarit_titre: str):
        """Lie un gabarit à une procédure (sans URL, stocké par id)."""
        if not self.doc_picker_key:
            return
        db = load_db()
        if "proc_doc_links" not in db:
            db["proc_doc_links"] = {}
        db["proc_doc_links"][self.doc_picker_key] = {
            "doc_id": gabarit_id,
            "doc_name": gabarit_titre,
            "doc_url": f"#gabarit:{gabarit_id}",
            "type": "gabarit",
        }
        save_db(db)
        self.show_doc_picker = False
        self.doc_picker_key = ""
        self.doc_picker_search = ""
        self._load_proc_suivi()

    def unlink_doc_from_proc(self, perimetre: str, typologie: str):
        key = f"{perimetre}|{typologie}"
        db = load_db()
        links = db.get("proc_doc_links") or {}
        if key in links:
            del links[key]
        db["proc_doc_links"] = links
        save_db(db)
        self._load_proc_suivi()

    # ── Auto-détection ────────────────────────────────────────────────────

    _STOP = {
        "de", "du", "la", "le", "les", "un", "une", "des", "et", "ou", "en",
        "dans", "sur", "pour", "par", "au", "aux", "avec", "sans", "son",
        "sa", "ses", "ce", "qui", "que", "si", "ne", "pas", "se", "à",
        "l", "d", "n1", "n2", "n3", "its", "the",
    }

    def detect_matches(self):
        """Parcourt tous les documents et propose des correspondances avec la matrice."""
        db = load_db()
        docs = [d for d in (db.get("documents") or []) if d.get("url")]
        matrix = db.get("escalation_matrix") or []
        existing_links = set((db.get("proc_doc_links") or {}).keys())

        proposals = []
        used_keys: set = set()

        for doc in docs:
            nom = doc.get("nom_original") or ""
            doc_id = str(doc.get("id") or "")
            doc_url = doc.get("url") or ""
            # Normalise : remplace séparateurs, découpe, filtre stop words
            raw_words = nom.replace("-", " ").replace("/", " ").replace("_", " ").replace("(", " ").replace(")", " ").split()
            words = [w.lower() for w in raw_words if len(w) >= 3 and w.lower() not in self._STOP]
            if not words:
                continue

            best_score = 0
            best_key = ""
            best_p = ""
            best_t = ""
            for r in matrix:
                p = r.get("perimetre") or ""
                t = r.get("typologie") or ""
                key = f"{p}|{t}"
                if key in existing_links or key in used_keys:
                    continue
                target = (p + " " + t).lower()
                score = sum(1 for w in words if w in target)
                if score > best_score:
                    best_score = score
                    best_key = key
                    best_p = p
                    best_t = t

            if best_score >= 2 and best_key:
                proposals.append(AutoMatchProposal(
                    doc_id=doc_id,
                    doc_name=nom,
                    doc_url=doc_url,
                    perimetre=best_p,
                    typologie=best_t,
                    score=best_score,
                ))
                used_keys.add(best_key)

        proposals.sort(key=lambda x: -x.score)
        self.auto_match_proposals = proposals
        self.show_auto_match = True
        if not proposals:
            return rx.toast.info("Aucune correspondance automatique trouvée.")

    def close_auto_match(self):
        self.show_auto_match = False
        self.expanded_proposal_idx = -1

    def toggle_proposal(self, idx: int):
        self.expanded_proposal_idx = -1 if self.expanded_proposal_idx == idx else idx

    def confirm_match_at(self, idx: int):
        """Confirme et sauvegarde la proposition à l'index idx."""
        if idx < 0 or idx >= len(self.auto_match_proposals):
            return
        p = self.auto_match_proposals[idx]
        key = f"{p.perimetre}|{p.typologie}"
        db = load_db()
        if "proc_doc_links" not in db:
            db["proc_doc_links"] = {}
        db["proc_doc_links"][key] = {
            "doc_id": p.doc_id,
            "doc_name": p.doc_name,
            "doc_url": p.doc_url,
        }
        save_db(db)
        self.auto_match_proposals = [r for i, r in enumerate(self.auto_match_proposals) if i != idx]
        self._load_proc_suivi()

    def reject_match_at(self, idx: int):
        """Rejette la proposition à l'index idx."""
        self.auto_match_proposals = [r for i, r in enumerate(self.auto_match_proposals) if i != idx]

    def confirm_all_matches(self):
        """Confirme toutes les propositions restantes en une fois."""
        db = load_db()
        if "proc_doc_links" not in db:
            db["proc_doc_links"] = {}
        for p in self.auto_match_proposals:
            key = f"{p.perimetre}|{p.typologie}"
            db["proc_doc_links"][key] = {
                "doc_id": p.doc_id,
                "doc_name": p.doc_name,
                "doc_url": p.doc_url,
            }
        save_db(db)
        count = len(self.auto_match_proposals)
        self.auto_match_proposals = []
        self.show_auto_match = False
        self._load_proc_suivi()
        return rx.toast.success(f"{count} correspondance(s) enregistrée(s).")

    @rx.var
    def proc_total_pages(self) -> int:
        return max(1, (self.proc_total + self.proc_limit - 1) // self.proc_limit)

    @rx.var
    def proc_count_with(self) -> int:
        return sum(1 for r in self.proc_rows if r.has_procedure)

    @rx.var
    def proc_count_without(self) -> int:
        return sum(1 for r in self.proc_rows if not r.has_procedure)
