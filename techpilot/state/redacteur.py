import os
import re
import uuid
import httpx
from datetime import datetime

import reflex as rx

from techpilot.db.database import load_db, save_db
from techpilot.state.auth import AuthState

PROC_TYPES   = ["N1", "Fiche N1", "Arbre de décision"]
PROC_STATUTS = ["Brouillon", "En attente de validation", "Relecture N1", "Relecture N2", "Validé", "Publié"]

_SYSTEM_PROMPT = """Tu es expert en rédaction de procédures N1 helpdesk IT en français.
Rédige une procédure N1 complète et structurée en suivant EXACTEMENT ce format (conserve les titres ## tels quels) :

## OBJECTIF
[Courte description de l'objectif de la procédure]

## PRÉ-REQUIS
• [Prérequis 1 — accès, droits ou outils nécessaires]
• [Prérequis 2 si pertinent]

## ÉTAPES
1. [Étape 1 claire et actionnable]
2. [Étape 2]
3. [...]

## RÉSULTAT ATTENDU
[Description précise de ce qui doit se produire après les étapes]

## ESCALADE
Si non résolu → Escalader à [N2/équipe/interlocuteur] via [WP/channel/process]
Contact : [email ou Teams si connu]

Règles impératives :
- Langage simple, accessible à un technicien N1 débutant
- Étapes numérotées, précises, actionnables (pas de vague "vérifier")
- Maximum 15 étapes
- Mentionner les messages d'erreur courants si pertinent
- Rester concis et pratique, pas de théorie"""


def _extract_section(text: str, header: str) -> str:
    pattern = rf"##\s+{re.escape(header)}\s*\n(.*?)(?=\n##\s|\Z)"
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""


class RedacteurState(rx.State):
    # ── Champs formulaire ────────────────────────────────────────────────────
    titre: str = ""
    type_proc: str = "N1"
    perimetre: str = ""
    description_brief: str = ""
    objectif: str = ""
    prerequis: str = ""
    steps_text: str = ""
    resultat_attendu: str = ""
    escalade_info: str = ""
    statut: str = "Brouillon"
    google_doc_url: str = ""

    # ── Mode édition ─────────────────────────────────────────────────────────
    edit_id: str = ""

    # ── Données ──────────────────────────────────────────────────────────────
    procedures: list[dict] = []
    similar_docs: list[dict] = []

    # ── Claude ───────────────────────────────────────────────────────────────
    claude_loading: bool = False
    claude_error: str = ""
    claude_generated: str = ""

    # ── UI ───────────────────────────────────────────────────────────────────
    confirm_delete_id: str = ""
    save_success: bool = False

    # ── Filtres liste ────────────────────────────────────────────────────────
    filter_statut: str = ""
    filter_type: str = ""
    search_list: str = ""

    @rx.var
    def filtered_procedures(self) -> list[dict]:
        procs = self.procedures
        if self.filter_statut:
            procs = [p for p in procs if p.get("statut") == self.filter_statut]
        if self.filter_type:
            procs = [p for p in procs if p.get("type_proc") == self.filter_type]
        if self.search_list:
            q = self.search_list.lower()
            procs = [p for p in procs if q in p.get("titre", "").lower() or q in p.get("perimetre", "").lower()]
        return procs

    @rx.var
    def pending_count(self) -> int:
        return sum(1 for p in self.procedures if p.get("statut") == "En attente de validation")

    # ── Events ───────────────────────────────────────────────────────────────

    @rx.event
    def load(self):
        db = load_db()
        self.procedures = db.get("procedures_content", [])

    @rx.event
    def new_procedure(self):
        self.edit_id = ""
        self.titre = ""
        self.type_proc = "N1"
        self.perimetre = ""
        self.description_brief = ""
        self.objectif = ""
        self.prerequis = ""
        self.steps_text = ""
        self.resultat_attendu = ""
        self.escalade_info = ""
        self.statut = "Brouillon"
        self.google_doc_url = ""
        self.claude_generated = ""
        self.claude_error = ""
        self.similar_docs = []
        self.save_success = False

    @rx.event
    def edit_procedure(self, proc_id: str):
        for p in self.procedures:
            if p.get("id") == proc_id:
                self.edit_id = proc_id
                self.titre = p.get("titre", "")
                self.type_proc = p.get("type_proc", "N1")
                self.perimetre = p.get("perimetre", "")
                self.description_brief = p.get("description_brief", "")
                self.objectif = p.get("objectif", "")
                self.prerequis = p.get("prerequis", "")
                self.steps_text = p.get("steps_text", "")
                self.resultat_attendu = p.get("resultat_attendu", "")
                self.escalade_info = p.get("escalade_info", "")
                self.statut = p.get("statut", "Brouillon")
                self.google_doc_url = p.get("google_doc_url", "")
                self.claude_generated = ""
                self.claude_error = ""
                self.save_success = False
                self._refresh_similar()
                return

    def _refresh_similar(self):
        if not self.titre:
            self.similar_docs = []
            return
        db = load_db()
        docs = db.get("documents", [])
        titre_words = {w for w in self.titre.lower().split() if len(w) > 3}
        results = []
        for d in docs:
            nom = d.get("nom_original", "").lower()
            nom_words = {w for w in nom.split() if len(w) > 3}
            overlap = len(titre_words & nom_words)
            if any(w in nom for w in titre_words):
                overlap += 1
            if overlap >= 2:
                results.append({
                    "nom": d.get("nom_original", ""),
                    "url": d.get("url", ""),
                    "categorie": d.get("categorie", ""),
                    "score": overlap,
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        self.similar_docs = results[:6]

    @rx.event
    def set_titre(self, v: str):
        self.titre = v
        self._refresh_similar()

    @rx.event
    def set_type_proc(self, v: str):
        self.type_proc = v

    @rx.event
    def set_perimetre(self, v: str):
        self.perimetre = v

    @rx.event
    def set_description_brief(self, v: str):
        self.description_brief = v

    @rx.event
    def set_objectif(self, v: str):
        self.objectif = v

    @rx.event
    def set_prerequis(self, v: str):
        self.prerequis = v

    @rx.event
    def set_steps_text(self, v: str):
        self.steps_text = v

    @rx.event
    def set_resultat_attendu(self, v: str):
        self.resultat_attendu = v

    @rx.event
    def set_escalade_info(self, v: str):
        self.escalade_info = v

    @rx.event
    def set_statut(self, v: str):
        self.statut = v

    @rx.event
    def set_google_doc_url(self, v: str):
        self.google_doc_url = v

    @rx.event
    def set_filter_statut(self, v: str):
        self.filter_statut = v

    @rx.event
    def set_filter_type(self, v: str):
        self.filter_type = v

    @rx.event
    def set_search_list(self, v: str):
        self.search_list = v

    @rx.event
    def clear_filters(self):
        self.filter_statut = ""
        self.filter_type = ""
        self.search_list = ""

    @rx.event
    def apply_claude_result(self):
        if not self.claude_generated:
            return
        text = self.claude_generated
        objectif  = _extract_section(text, "OBJECTIF")
        prerequis = _extract_section(text, "PRÉ-REQUIS")
        etapes    = _extract_section(text, "ÉTAPES")
        resultat  = _extract_section(text, "RÉSULTAT ATTENDU")
        escalade  = _extract_section(text, "ESCALADE")
        if objectif:  self.objectif = objectif
        if prerequis: self.prerequis = prerequis
        if etapes:    self.steps_text = etapes
        if resultat:  self.resultat_attendu = resultat
        if escalade:  self.escalade_info = escalade

    @rx.event
    async def generate_with_claude(self):
        if not self.titre and not self.description_brief:
            self.claude_error = "Renseigne au moins le titre ou une description."
            return

        self.claude_loading = True
        self.claude_error = ""
        self.claude_generated = ""
        yield

        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            self.claude_error = "ANTHROPIC_API_KEY non configurée sur Railway."
            self.claude_loading = False
            return

        parts = []
        if self.titre:
            parts.append(f"Titre : {self.titre}")
        if self.perimetre:
            parts.append(f"Application / Périmètre : {self.perimetre}")
        if self.type_proc:
            parts.append(f"Type : {self.type_proc}")
        if self.description_brief:
            parts.append(f"Contexte / description : {self.description_brief}")

        user_prompt = "\n".join(parts) + "\n\nGénère la procédure complète."

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 1800,
                        "system": _SYSTEM_PROMPT,
                        "messages": [{"role": "user", "content": user_prompt}],
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                self.claude_generated = data["content"][0]["text"]
        except httpx.HTTPStatusError as e:
            self.claude_error = f"Erreur API {e.response.status_code} — vérifie la clé."
        except Exception as e:
            self.claude_error = f"Erreur : {str(e)[:120]}"
        finally:
            self.claude_loading = False

    @rx.event
    async def save_procedure(self):
        if not self.titre.strip():
            return

        auth = await self.get_state(AuthState)
        auteur = auth.user_nom or "Manager"

        db = load_db()
        procs = db.get("procedures_content", [])
        now = datetime.now().strftime("%d/%m/%Y")

        if self.edit_id:
            for i, p in enumerate(procs):
                if p.get("id") == self.edit_id:
                    procs[i] = {
                        **p,
                        "titre":             self.titre,
                        "type_proc":         self.type_proc,
                        "perimetre":         self.perimetre,
                        "description_brief": self.description_brief,
                        "objectif":          self.objectif,
                        "prerequis":         self.prerequis,
                        "steps_text":        self.steps_text,
                        "resultat_attendu":  self.resultat_attendu,
                        "escalade_info":     self.escalade_info,
                        "statut":            self.statut,
                        "google_doc_url":    self.google_doc_url,
                        "date_maj":          now,
                    }
                    break
        else:
            new_p = {
                "id":                str(uuid.uuid4()),
                "titre":             self.titre,
                "type_proc":         self.type_proc,
                "perimetre":         self.perimetre,
                "description_brief": self.description_brief,
                "objectif":          self.objectif,
                "prerequis":         self.prerequis,
                "steps_text":        self.steps_text,
                "resultat_attendu":  self.resultat_attendu,
                "escalade_info":     self.escalade_info,
                "statut":            self.statut,
                "google_doc_url":    self.google_doc_url,
                "auteur_nom":        auteur,
                "date_creation":     now,
                "date_maj":          now,
            }
            procs.insert(0, new_p)
            self.edit_id = new_p["id"]

        db["procedures_content"] = procs
        save_db(db)
        self.procedures = procs
        self.save_success = True

    @rx.event
    def ask_delete(self, proc_id: str):
        self.confirm_delete_id = proc_id

    @rx.event
    def cancel_delete(self):
        self.confirm_delete_id = ""

    @rx.event
    def confirm_delete(self):
        db = load_db()
        procs = [p for p in db.get("procedures_content", []) if p.get("id") != self.confirm_delete_id]
        db["procedures_content"] = procs
        save_db(db)
        self.procedures = procs
        if self.edit_id == self.confirm_delete_id:
            self.edit_id = ""
            self.titre = ""
        self.confirm_delete_id = ""

    @rx.event
    def submit_for_validation(self):
        self.statut = "En attente de validation"
