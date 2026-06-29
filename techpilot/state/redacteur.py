import os
import re
import uuid
import httpx
from datetime import datetime

import reflex as rx

from techpilot.db.database import load_db, save_db
from techpilot.state.auth import AuthState

PROC_TYPES   = ["N1", "Fiche N1", "Arbre de décision"]
PROC_STATUTS = ["Brouillon", "Relecture N1", "En attente de validation", "Relecture N2", "Validé", "Publié", "Obsolète"]

# Master Subjects (code → libellé)
MASTER_SUBJECTS: list[tuple[str, str]] = [
    ("AM", "App métiers"),
    ("AC", "App collaboratives"),
    ("PT", "Poste de travail"),
    ("IM", "Imprimantes"),
    ("PE", "Périphériques"),
    ("SY", "Systèmes"),
    ("CI", "Citrix"),
    ("AD", "Accès Droits Comptes"),
    ("RE", "Réseau"),
    ("IN", "Internet"),
    ("SE", "Sécurité"),
    ("TI", "Téléphonie IP"),
    ("TM", "Téléphonie mobile"),
]
MASTER_SUBJECT_LABELS = [f"{code} – {label}" for code, label in MASTER_SUBJECTS]
PROC_NATURES = ["I – Incident", "R – Request (Demande)"]

_SYSTEM_PROMPT = """Tu es expert en rédaction de procédures N1 helpdesk IT en français.
Rédige une procédure N1 structurée en suivant EXACTEMENT ce format utilisé dans notre équipe :

**[TITRE DE LA PROCÉDURE]**

**Résumé**
[1-2 phrases décrivant l'objectif et le contexte de la procédure]

**Situation**
[Description précise du cas déclencheur : symptôme observé, message d'erreur, situation de l'utilisateur]

**À savoir** (si pertinent)
[Cas particuliers, précautions, informations contextuelles importantes avant de commencer]

**Résolution**
1. [Étape 1 — action précise et actionnable]
2. [Étape 2]
3. [...]

**Résultat attendu**
[Ce qui doit se produire une fois les étapes terminées]

**Escalade**
Si non résolu après les étapes → Escalader à [N2/équipe] via [WP/Teams/canal]

Règles impératives :
- Langage simple, accessible à un technicien N1 débutant
- Étapes numérotées et actionnables (verbe d'action : "Ouvrir", "Cliquer", "Saisir"…)
- Mentionner les messages d'erreur exactement comme ils apparaissent à l'écran
- Maximum 15 étapes, rester concis et pratique
- NE PAS inclure de bloc de métadonnées (rédigé par, date, version…), on les gère séparément"""


def _extract_section(text: str, header: str) -> str:
    pattern = rf"\*?\*?{re.escape(header)}\*?\*?\s*\n(.*?)(?=\n\*?\*?(?:Résumé|Situation|À savoir|Résolution|Résultat attendu|Escalade)\*?\*?|\Z)"
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _build_codification(nature: str, master_code: str, numero: str) -> str:
    prefix = nature[0] if nature else "I"   # "I" ou "R"
    return f"{prefix}{master_code}{numero}".upper() if master_code and numero else ""


class RedacteurState(rx.State):
    # ── Champs formulaire ────────────────────────────────────────────────────
    titre: str = ""
    type_proc: str = "N1"
    nature: str = "I – Incident"        # "I – Incident" | "R – Request (Demande)"
    master_subject: str = ""            # ex: "AC – App collaboratives"
    codification: str = ""              # ex: IAD003 (auto ou saisi)
    perimetre: str = ""
    description_brief: str = ""
    resume: str = ""
    situation: str = ""
    a_savoir: str = ""
    steps_text: str = ""
    resultat_attendu: str = ""
    escalade_info: str = ""
    statut: str = "Brouillon"
    google_doc_url: str = ""
    service: str = ""                   # ex: SI-Travail Numérique

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
    view_id: str = ""

    @rx.var
    def view_procedure(self) -> dict:
        for p in self.procedures:
            if p.get("id") == self.view_id:
                return p
        return {}

    @rx.var
    def view_embed_url(self) -> str:
        p = self.view_procedure
        url: str = p.get("google_doc_url", "") or ""
        if not url:
            return ""
        # Nettoyer les paramètres, forcer /preview
        base = url.split("?")[0].rstrip("/")
        for suffix in ("/edit", "/preview", "/view", "/copy"):
            if base.endswith(suffix):
                base = base[: -len(suffix)]
                break
        return base + "/preview"

    @rx.event
    def open_view(self, proc_id: str):
        self.view_id = proc_id

    @rx.event
    def close_view(self):
        self.view_id = ""

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

    @rx.var
    def ms_counts(self) -> list[dict]:
        counts: dict[str, int] = {}
        for p in self.procedures:
            ms = p.get("master_subject", "") or ""
            if not ms:
                ms = "Sans catégorie"
            counts[ms] = counts.get(ms, 0) + 1
        result = []
        for label, cnt in sorted(counts.items(), key=lambda x: -x[1]):
            code = label.split(" – ")[0] if " – " in label else label
            result.append({"code": code, "label": label, "count": cnt})
        return result

    @rx.var
    def nature_counts(self) -> list[dict]:
        i_c = sum(1 for p in self.procedures if (p.get("nature") or "").startswith("I"))
        r_c = sum(1 for p in self.procedures if (p.get("nature") or "").startswith("R"))
        total = len(self.procedures)
        return [
            {"label": "Incidents",  "count": i_c, "pct": round(i_c * 100 / total) if total else 0, "color": "#ef4444"},
            {"label": "Demandes",   "count": r_c, "pct": round(r_c * 100 / total) if total else 0, "color": "#6366f1"},
        ]

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
        self.nature = "I – Incident"
        self.master_subject = ""
        self.codification = ""
        self.perimetre = ""
        self.service = ""
        self.description_brief = ""
        self.resume = ""
        self.situation = ""
        self.a_savoir = ""
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
                self.nature = p.get("nature", "I – Incident")
                self.master_subject = p.get("master_subject", "")
                self.codification = p.get("codification", "")
                self.perimetre = p.get("perimetre", "")
                self.service = p.get("service", "")
                self.description_brief = p.get("description_brief", "")
                self.resume = p.get("resume", "")
                self.situation = p.get("situation", "")
                self.a_savoir = p.get("a_savoir", "")
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
    def set_nature(self, v: str):
        self.nature = v

    @rx.event
    def set_master_subject(self, v: str):
        self.master_subject = v

    @rx.event
    def set_codification(self, v: str):
        self.codification = v

    @rx.event
    def set_service(self, v: str):
        self.service = v

    @rx.event
    def set_resume(self, v: str):
        self.resume = v

    @rx.event
    def set_situation(self, v: str):
        self.situation = v

    @rx.event
    def set_a_savoir(self, v: str):
        self.a_savoir = v

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
        resume   = _extract_section(text, "Résumé")
        situation = _extract_section(text, "Situation")
        a_savoir  = _extract_section(text, "À savoir")
        etapes    = _extract_section(text, "Résolution")
        resultat  = _extract_section(text, "Résultat attendu")
        escalade  = _extract_section(text, "Escalade")
        if resume:    self.resume = resume
        if situation: self.situation = situation
        if a_savoir:  self.a_savoir = a_savoir
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
        if self.master_subject:
            parts.append(f"Master Subject : {self.master_subject}")
        if self.nature:
            parts.append(f"Nature : {self.nature}")
        if self.codification:
            parts.append(f"Codification : {self.codification}")
        if self.description_brief:
            parts.append(f"Contexte / description : {self.description_brief}")
        if self.situation:
            parts.append(f"Situation décrite par le rédacteur : {self.situation}")

        user_prompt = "\n".join(parts) + "\n\nGénère la procédure complète en suivant le format demandé."

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

        fields = {
            "titre":             self.titre,
            "type_proc":         self.type_proc,
            "nature":            self.nature,
            "master_subject":    self.master_subject,
            "codification":      self.codification,
            "perimetre":         self.perimetre,
            "service":           self.service,
            "description_brief": self.description_brief,
            "resume":            self.resume,
            "situation":         self.situation,
            "a_savoir":          self.a_savoir,
            "steps_text":        self.steps_text,
            "resultat_attendu":  self.resultat_attendu,
            "escalade_info":     self.escalade_info,
            "statut":            self.statut,
            "google_doc_url":    self.google_doc_url,
            "date_maj":          now,
        }

        if self.edit_id:
            for i, p in enumerate(procs):
                if p.get("id") == self.edit_id:
                    procs[i] = {**p, **fields}
                    break
        else:
            new_p = {
                "id":            str(uuid.uuid4()),
                "auteur_nom":    auteur,
                "date_creation": now,
                **fields,
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
