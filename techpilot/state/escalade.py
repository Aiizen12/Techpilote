import reflex as rx
import base64
from techpilot.db.database import load_db, save_db
from techpilot.state.models import EscaladeEntry, DocPickerItem, ProcVersionItem
from datetime import datetime

# ── Procédures N1 — réseau / hardware (source : docs procédures internes) ─────
# Clé : (perimetre, typologie)  →  liste d'étapes ordonnées
PROCEDURE_MAP: dict[tuple[str, str], list[str]] = {

    # ── RÉSEAU ────────────────────────────────────────────────────────────────

    ("Réseau", "Incident réseau agence"): [
        "Qualifier : combien d'utilisateurs impactés ? Toute l'agence ou un seul poste ?",
        "Si plusieurs utilisateurs → vérifier auprès du SPOC Support Actual si incident général connu avant de continuer.",
        "Si 1 seul poste impacté → traiter comme 'Pas de réseau sur un seul poste', pas comme coupure agence.",
        "Demander si une modification / intervention / déménagement récent a eu lieu sur le site.",
        "Vérifier les voyants du routeur : Power, Internet/WAN sont-ils allumés et fixes ?",
        "Tenter un redémarrage routeur : éteindre 30 s, rallumer, patienter 2 minutes.",
        "Si coupure totale persistante → proposer un hotspot 4G (smartphone) pour pallier le temps de la résolution.",
        "Collecter avant escalade : nom agence, code agence, heure de début, nb utilisateurs, modèle routeur, FAI.",
        "Escalader selon la matrice : BT Blue si réseau BT (ticket TXXXXXXXXXXX), DSI Exploitation sinon.",
    ],

    ("Réseau", "Lenteurs poste"): [
        "Qualifier : lenteurs sur tout le site ou uniquement sur ce poste ?",
        "Si tous les postes sont lents → traiter comme 'Incident réseau agence', ne pas poursuivre sur le poste seul.",
        "Récupérer le nom du poste : clic droit 'Ce PC' > Propriétés, ou taper 'hostname' dans cmd.",
        "Ouvrir le Gestionnaire des tâches (Ctrl+Shift+Esc) > onglet Performances.",
        "Prendre une capture d'écran : CPU %, RAM utilisée (Go), Disque à 100 % ?",
        "Vérifier l'onglet Démarrage : désactiver les programmes non essentiels au démarrage.",
        "Vider les condensateurs : éteindre + débrancher adaptateur + maintenir bouton Power 30 s + rebrancher.",
        "Si les lenteurs persistent après redémarrage → escalader avec nom du poste + capture Gestionnaire des tâches.",
    ],

    ("Réseau", "Incident routeur 4G/5G - Hors BT"): [
        "Vérifier les voyants du routeur : Power (vert fixe ?), Signal 4G/5G (barres affichées ?), WiFi (allumé ?).",
        "Demander depuis quand la panne est survenue et si une coupure physique (câble, déplacement) a eu lieu.",
        "Redémarrer le routeur : éteindre 30 s, rallumer, patienter 2 minutes.",
        "Si accessible : retirer et remettre la carte SIM du routeur.",
        "Tester un autre appareil connecté au même routeur pour isoler (problème poste vs routeur).",
        "Vérifier la couverture opérateur sur le site (test smartphone en 4G/5G).",
        "Collecter : modèle routeur, opérateur, code agence, heure de début, signalement d'autres utilisateurs.",
        "Escalader à Support DSI Exploitation avec ces informations.",
    ],

    ("Réseau", "Incident routeur 4G/5G - Réseau BT"): [
        "Vérifier les voyants du routeur BT Blue : Power, Signal, WiFi.",
        "Redémarrer le routeur : éteindre 30 s, rallumer, patienter 2 minutes.",
        "Si la coupure persiste → rechercher si une référence de maintenance BT (TXXXXXXXXXXX) est connue.",
        "Collecter : modèle routeur, code agence, nom agence, heure de début, référence maintenance si connue.",
        "Escalader au groupe dédié BT Blue en précisant la référence de maintenance si disponible.",
        "En attente de résolution → proposer hotspot 4G en solution de contournement.",
    ],

    ("Réseau", "Wifi visiteurs"): [
        "Demander quel réseau WiFi l'utilisateur essaie d'atteindre (visiteurs, invités, métier ?).",
        "Vérifier que le SSID visiteurs est bien diffusé (un autre appareil le voit-il ?).",
        "Désactiver puis réactiver le WiFi sur le poste de l'utilisateur.",
        "Si le SSID visiteurs n'apparaît pas → suspecter la borne WiFi (OMADA) ou sa configuration.",
        "Si le SSID est absent sur tout le site → escalader à Support DSI Exploitation.",
    ],

    # ── POSTE DE TRAVAIL ──────────────────────────────────────────────────────

    ("Poste de travail", "Demande de matériel"): [
        "Qualifier la demande : panne/remplacement suite à dysfonctionnement ou nouveau besoin ?",
        "Si panne → diagnostiquer le matériel défaillant (symptôme précis, depuis quand, reproductible ?).",
        "Vérifier l'âge du matériel : > 5 ans = potentiellement éligible au remplacement (valider avec N2, ne pas annoncer à l'utilisateur).",
        "Collecter obligatoirement : adresse complète agence, code agence, numéro de contact sur site.",
        "Ajouter le code agence dans le ticket FreshService avant d'escalader.",
        "Escalader à SI-TRAVAIL NUMERIQUE avec adresse + contact + description du besoin.",
        "Ne jamais commander directement : toujours passer par SI-TRAVAIL NUMERIQUE.",
    ],

    ("Poste de travail", "Pas de réseau sur un seul poste"): [
        "Qualifier : WiFi ou câble réseau ? Problème apparu après une modification récente ?",
        "WiFi : vérifier que le WiFi est activé et le mode avion désactivé.",
        "Câble : rebrancher côté poste et côté prise murale. Tester un autre câble et une autre prise.",
        "Redémarrer le poste + vérifier si une mise à jour Windows est en cours (peut bloquer le réseau).",
        "Vérifier l'adresse IP (ipconfig) : si 169.254.x.x → problème DHCP, escalader à DSI Exploitation.",
        "Tests ping : passerelle par défaut → réseau local OK/KO. Ping 8.8.8.8 → internet OK/KO.",
        "Tests croisés : brancher le poste sur une autre prise fonctionnelle ; brancher un autre poste sur la prise incriminée.",
        "Si toujours KO → escalader avec : ID poste, résultats ping, type connexion, prises testées.",
    ],

    ("Poste de travail", "Problème de caméra sur les Latitude 3540 côté Leader"): [
        "Défaut connu sur Latitude 3540 : la nappe caméra/micro se débranche en ouvrant/fermant le capot.",
        "Vérifier le numéro de série (S/N) sur l'étiquette du PC ou dans Paramètres > Système > Informations.",
        "Contrôler la garantie sur le site DELL (onglet 'Vérifier la garantie') avec le S/N.",
        "Créer un ticket d'intervention DELL en collectant : Nom/Prénom contact sur site, adresse complète, disponibilités, horaires site, numéro de contact.",
        "L'intervention se fait sur site (technicien DELL déplacement) : pas de renvoi du matériel.",
        "Informer l'utilisateur que c'est un défaut reconnu par DELL, une intervention est planifiée.",
        "Renseigner le ticket FreshService avec la référence du ticket DELL créé.",
    ],

    ("Poste de travail", "Batterie PC Portable ne charge pas"): [
        "Qualifier : la batterie ne se charge jamais OU elle se charge mais se décharge trop vite ?",
        "Vérifier que l'adaptateur secteur est correctement branché côté PC et côté prise.",
        "Tester avec un autre adaptateur compatible si disponible.",
        "Vider les condensateurs : éteindre, débrancher l'adaptateur, maintenir le bouton Power 30 s, rebrancher.",
        "Vérifier l'état de la batterie : Paramètres > Système > Alimentation & mise en veille.",
        "Si batterie HS ou PC sous garantie → escalader à SI-TRAVAIL NUMERIQUE avec S/N + description.",
    ],

    # ── TÉLÉPHONIE MOBILE ─────────────────────────────────────────────────────

    ("Téléphonie mobile", "Incident lié à la carte SIM"): [
        "Qualifier : problème d'appels uniquement, de données, ou les deux ?",
        "iPhone : retirer l'ancienne carte SIM physique si encore présente (crée des conflits avec l'eSIM).",
        "iPhone : forcer la ligne eSIM sur les contacts problématiques → Contacts > contact > Ligne préférée > eSIM.",
        "Android (Samsung) : Paramètres > Connexions > Gestionnaire carte SIM > vérifier que l'eSIM est la ligne active.",
        "Réinitialiser les paramètres réseau (efface les mots de passe WiFi, mais résout les conflits SIM) :",
        "  iPhone : Réglages > Général > Transférer ou réinitialiser > Réinitialiser les réglages réseau.",
        "  Android Samsung : Paramètres > Gestion générale > Réinitialiser > Réinitialiser les paramètres réseau.",
        "Test mode avion : activer > éteindre l'appareil > rallumer > désactiver mode avion.",
        "Si non résolu → escalader avec : modèle, OS, opérateur, description précise (appels ? données ? les deux ?).",
    ],
}

PERIMETRE_COLORS = [
    "#f59e0b", "#8b5cf6", "#f97316", "#64748b", "#06b6d4",
    "#22c55e", "#eab308", "#3b82f6", "#6366f1", "#ef4444",
    "#0891b2", "#a855f7", "#ec4899", "#10b981",
]


class EscaladeState(rx.State):

    # ── Recherche ─────────────────────────────────────────────────────────
    entries: list[EscaladeEntry] = []
    perimetres: list[str] = []
    selected_perimetres: list[str] = []
    search: str = ""
    page: int = 1
    total: int = 0
    limit: int = 25
    selected_entry: EscaladeEntry = EscaladeEntry()
    show_modal: bool = False
    favoris: list[EscaladeEntry] = []

    # ── Mode ──────────────────────────────────────────────────────────────
    mode: str = "recherche"   # recherche | assistant | arbre | interlocuteur | libre
    total_count: int = 0

    # ── Assistant guidé ───────────────────────────────────────────────────
    assistant_step: int = 1
    assistant_perimetre: str = ""
    perimetre_counts: list[dict] = []
    assistant_entries: list[EscaladeEntry] = []

    # ── Par interlocuteur N2 ──────────────────────────────────────────────
    interlocuteur_search: str = ""
    interlocuteurs_list: list[dict] = []
    filtered_interlocuteurs_list: list[dict] = []
    expanded_interlocuteur: str = ""
    interlocuteur_entries: list[EscaladeEntry] = []

    # ── Arbre ─────────────────────────────────────────────────────────────
    arbre_expanded: str = ""
    arbre_entries: list[EscaladeEntry] = []

    # ── Édition procédure ─────────────────────────────────────────────────
    editing_procedure: bool = False
    edit_steps_text: str = ""   # étapes séparées par \n

    # ── Historique / versioning procédure ────────────────────────────────
    show_history: bool = False
    procedure_versions: list[ProcVersionItem] = []
    proc_current_version: int = 0

    # ── Liaison document ─────────────────────────────────────────────────
    show_link_panel: bool = False
    link_search: str = ""
    link_results: list[DocPickerItem] = []
    link_custom_name: str = ""
    link_custom_url: str = ""

    # ── Chargement ────────────────────────────────────────────────────────

    def load_data(self):
        db = load_db()
        all_entries = db.get("escalation_matrix") or []
        self.total_count = len(all_entries)

        sorted_perimetres = sorted(set(
            r.get("perimetre", "") for r in all_entries if r.get("perimetre")
        ))
        self.perimetres = sorted_perimetres

        self.perimetre_counts = [
            {
                "name": p,
                "count": sum(1 for r in all_entries if r.get("perimetre") == p),
                "count_str": f"{sum(1 for r in all_entries if r.get('perimetre') == p)} lignes",
                "color": PERIMETRE_COLORS[i % len(PERIMETRE_COLORS)],
                "border_accent": f"3px solid {PERIMETRE_COLORS[i % len(PERIMETRE_COLORS)]}",
            }
            for i, p in enumerate(sorted_perimetres)
        ]

        interlocuteurs: dict = {}
        for r in all_entries:
            interl = (r.get("interlocuteur") or "").strip()
            if not interl:
                continue
            if interl not in interlocuteurs:
                interlocuteurs[interl] = {"nom": interl, "count": 0, "tags_set": set()}
            interlocuteurs[interl]["count"] += 1
            p = r.get("perimetre", "")
            if p:
                interlocuteurs[interl]["tags_set"].add(p)

        self.interlocuteurs_list = [
            {
                "nom": v["nom"],
                "count": v["count"],
                "count_str": f"{v['count']} cas",
                "tags": ", ".join(sorted(v["tags_set"])),
            }
            for v in sorted(interlocuteurs.values(), key=lambda x: -x["count"])
        ]
        self.filtered_interlocuteurs_list = self.interlocuteurs_list

        self._filter(db)

    def _filter(self, db: dict | None = None):
        if db is None:
            db = load_db()
        results = db.get("escalation_matrix") or []

        if self.search:
            q = self.search.lower()
            results = [
                r for r in results
                if q in (r.get("typologie") or "").lower()
                or q in (r.get("perimetre") or "").lower()
                or q in (r.get("categorie_fresh") or "").lower()
                or q in (r.get("traitement_n1") or "").lower()
                or q in (r.get("interlocuteur") or "").lower()
                or q in (r.get("traitement_n2n3") or "").lower()
                or q in (r.get("conditions_escalade") or "").lower()
            ]

        if self.selected_perimetres:
            results = [r for r in results if r.get("perimetre") in self.selected_perimetres]

        self.total = len(results)
        offset = (self.page - 1) * self.limit
        self.entries = [
            EscaladeEntry(
                perimetre=r.get("perimetre") or "",
                typologie=r.get("typologie") or "",
                categorie_fresh=r.get("categorie_fresh") or "",
                traitement_n1=r.get("traitement_n1") or "",
                wp=r.get("wp") or "",
                interlocuteur=r.get("interlocuteur") or "",
                traitement_n2n3=r.get("traitement_n2n3") or "",
                wp_n2=r.get("wp_n2") or "",
                referents=r.get("referents") or "",
                conditions_escalade=r.get("conditions_escalade") or "",
                notes=r.get("notes") or "",
            )
            for r in results[offset: offset + self.limit]
        ]

    # ── Mode ──────────────────────────────────────────────────────────────

    def set_mode(self, m: str):
        self.mode = m

    # ── Recherche ─────────────────────────────────────────────────────────

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

    @staticmethod
    def _find_procedure(perimetre: str, typologie: str, db: dict | None = None) -> list[str]:
        """Procédures custom DB en priorité, puis PROCEDURE_MAP exact, puis fuzzy."""
        if db is None:
            db = load_db()
        key = f"{perimetre}|{typologie}"
        custom = (db.get("procedures_custom") or {}).get(key)
        if custom:
            return custom
        exact = PROCEDURE_MAP.get((perimetre, typologie), [])
        if exact:
            return exact
        t_lower = typologie.lower()
        for (p, t), steps in PROCEDURE_MAP.items():
            if p == perimetre and (t.lower() in t_lower or t_lower in t.lower()):
                return steps
        return []

    def _open_escalade_entry(self, e: "EscaladeEntry"):
        """Logique commune : charge la procédure, le document lié et ouvre la modale."""
        db = load_db()
        steps = EscaladeState._find_procedure(e.perimetre, e.typologie, db)
        key = f"{e.perimetre}|{e.typologie}"
        doc_link = (db.get("proc_doc_links") or {}).get(key) or {}
        versions = (db.get("procedures_versions") or {}).get(key) or []
        self.proc_current_version = len(versions)
        self.show_history = False
        self.editing_procedure = False
        self.selected_entry = EscaladeEntry(
            perimetre=e.perimetre,
            typologie=e.typologie,
            categorie_fresh=e.categorie_fresh,
            traitement_n1=e.traitement_n1,
            wp=e.wp,
            interlocuteur=e.interlocuteur,
            traitement_n2n3=e.traitement_n2n3,
            wp_n2=e.wp_n2,
            referents=e.referents,
            conditions_escalade=e.conditions_escalade,
            notes=e.notes,
            procedure_n1=steps,
            doc_name=doc_link.get("doc_name", ""),
            doc_url=doc_link.get("doc_url", ""),
        )
        self.show_modal = True

    # ── Ouverture par index (int) — le type le plus fiable dans rx.foreach ───

    def open_entry_at(self, idx: int):
        """Ouvre l'entrée entries[idx]."""
        if 0 <= idx < len(self.entries):
            self._open_escalade_entry(self.entries[idx])

    def open_arbre_entry_at(self, idx: int):
        """Ouvre l'entrée arbre_entries[idx]."""
        if 0 <= idx < len(self.arbre_entries):
            self._open_escalade_entry(self.arbre_entries[idx])

    def open_interlocuteur_entry_at(self, idx: int):
        """Ouvre l'entrée interlocuteur_entries[idx]."""
        if 0 <= idx < len(self.interlocuteur_entries):
            self._open_escalade_entry(self.interlocuteur_entries[idx])

    def open_assistant_entry_at(self, idx: int):
        """Ouvre l'entrée assistant_entries[idx]."""
        if 0 <= idx < len(self.assistant_entries):
            self._open_escalade_entry(self.assistant_entries[idx])

    def open_favori(self, perimetre: str, typologie: str):
        """Favoris : lookup DB car la liste favoris n'a pas d'index fixe."""
        db = load_db()
        all_entries = db.get("escalation_matrix") or []
        raw = next(
            (r for r in all_entries
             if (r.get("perimetre") or "").strip() == perimetre.strip()
             and (r.get("typologie") or "").strip() == typologie.strip()),
            None,
        )
        if raw is None:
            return
        e = EscaladeEntry(
            perimetre=raw.get("perimetre") or "",
            typologie=raw.get("typologie") or "",
            categorie_fresh=raw.get("categorie_fresh") or "",
            traitement_n1=raw.get("traitement_n1") or "",
            wp=raw.get("wp") or "",
            interlocuteur=raw.get("interlocuteur") or "",
            traitement_n2n3=raw.get("traitement_n2n3") or "",
            wp_n2=raw.get("wp_n2") or "",
            referents=raw.get("referents") or "",
            conditions_escalade=raw.get("conditions_escalade") or "",
            notes=raw.get("notes") or "",
        )
        self._open_escalade_entry(e)

    def close_modal(self):
        self.show_modal = False
        self.editing_procedure = False
        self.show_link_panel = False
        self.link_search = ""
        self.link_results = []
        self.link_custom_name = ""
        self.link_custom_url = ""

    # ── Édition procédure ─────────────────────────────────────────────────

    def start_edit_procedure(self):
        self.edit_steps_text = "\n".join(self.selected_entry.procedure_n1)
        self.editing_procedure = True

    def cancel_edit_procedure(self):
        self.editing_procedure = False

    # ── Liaison document ─────────────────────────────────────────────────

    def open_link_panel(self):
        self.show_link_panel = True
        self.link_search = ""
        self.link_results = []
        self.link_custom_name = ""
        self.link_custom_url = ""

    def close_link_panel(self):
        self.show_link_panel = False
        self.link_search = ""
        self.link_results = []

    def set_link_search(self, val: str):
        self.link_search = val
        if not val.strip():
            self.link_results = []
            return
        db = load_db()
        q = val.lower()
        results = []
        for d in (db.get("documents") or []):
            nom = (d.get("nom_original") or "").lower()
            desc = (d.get("description") or "").lower()
            if q in nom or q in desc:
                results.append(DocPickerItem(
                    id=str(d.get("id") or ""),
                    nom=d.get("nom_original") or "",
                    url=d.get("url") or "",
                ))
        self.link_results = results[:10]

    def set_link_custom_name(self, val: str):
        self.link_custom_name = val

    def set_link_custom_url(self, val: str):
        self.link_custom_url = val

    def _save_doc_link(self, name: str, url: str, doc_id: str = ""):
        key = f"{self.selected_entry.perimetre}|{self.selected_entry.typologie}"
        db = load_db()
        if "proc_doc_links" not in db:
            db["proc_doc_links"] = {}
        db["proc_doc_links"][key] = {"doc_id": doc_id, "doc_name": name, "doc_url": url}
        save_db(db)
        self.selected_entry = EscaladeEntry(
            perimetre=self.selected_entry.perimetre,
            typologie=self.selected_entry.typologie,
            categorie_fresh=self.selected_entry.categorie_fresh,
            traitement_n1=self.selected_entry.traitement_n1,
            wp=self.selected_entry.wp,
            interlocuteur=self.selected_entry.interlocuteur,
            traitement_n2n3=self.selected_entry.traitement_n2n3,
            wp_n2=self.selected_entry.wp_n2,
            referents=self.selected_entry.referents,
            conditions_escalade=self.selected_entry.conditions_escalade,
            notes=self.selected_entry.notes,
            procedure_n1=self.selected_entry.procedure_n1,
            doc_name=name,
            doc_url=url,
        )
        self.show_link_panel = False
        self.link_search = ""
        self.link_results = []
        self.link_custom_name = ""
        self.link_custom_url = ""
        yield rx.toast.success("Document lié.")

    def link_from_picker(self, doc_id: str):
        doc = next((d for d in self.link_results if d.id == doc_id), None)
        if doc:
            yield EscaladeState._save_doc_link(self, doc.nom, doc.url, doc.id)

    def save_custom_link(self):
        name = self.link_custom_name.strip()
        url = self.link_custom_url.strip()
        if not name or not url:
            yield rx.toast.error("Nom et URL requis.")
            return
        yield EscaladeState._save_doc_link(self, name, url)

    def unlink_doc(self):
        key = f"{self.selected_entry.perimetre}|{self.selected_entry.typologie}"
        db = load_db()
        links = db.get("proc_doc_links") or {}
        links.pop(key, None)
        db["proc_doc_links"] = links
        save_db(db)
        self.selected_entry = EscaladeEntry(
            perimetre=self.selected_entry.perimetre,
            typologie=self.selected_entry.typologie,
            categorie_fresh=self.selected_entry.categorie_fresh,
            traitement_n1=self.selected_entry.traitement_n1,
            wp=self.selected_entry.wp,
            interlocuteur=self.selected_entry.interlocuteur,
            traitement_n2n3=self.selected_entry.traitement_n2n3,
            wp_n2=self.selected_entry.wp_n2,
            referents=self.selected_entry.referents,
            conditions_escalade=self.selected_entry.conditions_escalade,
            notes=self.selected_entry.notes,
            procedure_n1=self.selected_entry.procedure_n1,
            doc_name="",
            doc_url="",
        )
        yield rx.toast.success("Lien supprimé.")

    def set_edit_steps_text(self, val: str):
        self.edit_steps_text = val

    async def save_procedure(self):
        steps = [s.strip() for s in self.edit_steps_text.split("\n") if s.strip()]
        key = f"{self.selected_entry.perimetre}|{self.selected_entry.typologie}"
        db = load_db()
        if "procedures_custom" not in db:
            db["procedures_custom"] = {}
        db["procedures_custom"][key] = steps

        # ── Versioning ─────────────────────────────────────────────────
        auth = await self.get_state(AuthState)
        versions = list((db.get("procedures_versions") or {}).get(key) or [])
        new_v = len(versions) + 1
        versions.append({
            "version": new_v,
            "steps": steps,
            "date": datetime.utcnow().strftime("%d/%m/%Y %H:%M"),
            "auteur": auth.user_nom,
        })
        if "procedures_versions" not in db:
            db["procedures_versions"] = {}
        db["procedures_versions"][key] = versions
        save_db(db)

        self.proc_current_version = new_v
        self.selected_entry = EscaladeEntry(
            perimetre=self.selected_entry.perimetre,
            typologie=self.selected_entry.typologie,
            categorie_fresh=self.selected_entry.categorie_fresh,
            traitement_n1=self.selected_entry.traitement_n1,
            wp=self.selected_entry.wp,
            interlocuteur=self.selected_entry.interlocuteur,
            traitement_n2n3=self.selected_entry.traitement_n2n3,
            wp_n2=self.selected_entry.wp_n2,
            referents=self.selected_entry.referents,
            conditions_escalade=self.selected_entry.conditions_escalade,
            notes=self.selected_entry.notes,
            procedure_n1=steps,
            doc_name=self.selected_entry.doc_name,
            doc_url=self.selected_entry.doc_url,
        )
        self.editing_procedure = False
        yield rx.toast.success(f"Procédure sauvegardée — v{new_v}.")

    def open_history(self):
        key = f"{self.selected_entry.perimetre}|{self.selected_entry.typologie}"
        db = load_db()
        versions = (db.get("procedures_versions") or {}).get(key) or []
        self.procedure_versions = [
            ProcVersionItem(
                version=v.get("version", 0),
                steps=v.get("steps") or [],
                date=v.get("date") or "",
                auteur=v.get("auteur") or "",
            )
            for v in reversed(versions)
        ]
        self.show_history = True

    def close_history(self):
        self.show_history = False

    def restore_version(self, v: int):
        key = f"{self.selected_entry.perimetre}|{self.selected_entry.typologie}"
        db = load_db()
        versions = (db.get("procedures_versions") or {}).get(key) or []
        target = next((x for x in versions if x.get("version") == v), None)
        if not target:
            return
        steps = target.get("steps") or []
        if "procedures_custom" not in db:
            db["procedures_custom"] = {}
        db["procedures_custom"][key] = steps
        save_db(db)
        self.selected_entry = EscaladeEntry(
            perimetre=self.selected_entry.perimetre,
            typologie=self.selected_entry.typologie,
            categorie_fresh=self.selected_entry.categorie_fresh,
            traitement_n1=self.selected_entry.traitement_n1,
            wp=self.selected_entry.wp,
            interlocuteur=self.selected_entry.interlocuteur,
            traitement_n2n3=self.selected_entry.traitement_n2n3,
            wp_n2=self.selected_entry.wp_n2,
            referents=self.selected_entry.referents,
            conditions_escalade=self.selected_entry.conditions_escalade,
            notes=self.selected_entry.notes,
            procedure_n1=steps,
            doc_name=self.selected_entry.doc_name,
            doc_url=self.selected_entry.doc_url,
        )
        self.proc_current_version = v
        self.show_history = False
        yield rx.toast.success(f"Version {v} restaurée.")

    def toggle_favori(self):
        key = self.selected_entry.perimetre + "|" + self.selected_entry.typologie
        if any(f.perimetre + "|" + f.typologie == key for f in self.favoris):
            self.favoris = [f for f in self.favoris if f.perimetre + "|" + f.typologie != key]
        else:
            self.favoris = [*self.favoris, self.selected_entry]

    def open_favori(self, perimetre: str, typologie: str):
        """Ouvre la modale depuis les favoris."""
        self.open_entry(perimetre, typologie)

    def copy_fresh_cat(self):
        yield rx.set_clipboard(self.selected_entry.categorie_fresh)

    @rx.var
    def is_selected_favori(self) -> bool:
        key = self.selected_entry.perimetre + "|" + self.selected_entry.typologie
        return any(f.perimetre + "|" + f.typologie == key for f in self.favoris)

    @rx.var
    def has_procedure(self) -> bool:
        return len(self.selected_entry.procedure_n1) > 0

    @rx.var
    def total_pages(self) -> int:
        return max(1, (self.total + self.limit - 1) // self.limit)

    # ── Assistant guidé ───────────────────────────────────────────────────

    def assistant_select_perimetre(self, p: str):
        self.assistant_perimetre = p
        self.assistant_step = 2
        db = load_db()
        entries = [r for r in (db.get("escalation_matrix") or []) if r.get("perimetre") == p]
        self.assistant_entries = [
            EscaladeEntry(
                perimetre=r.get("perimetre") or "",
                typologie=r.get("typologie") or "",
                categorie_fresh=r.get("categorie_fresh") or "",
                traitement_n1=r.get("traitement_n1") or "",
                wp=r.get("wp") or "",
                interlocuteur=r.get("interlocuteur") or "",
                traitement_n2n3=r.get("traitement_n2n3") or "",
                wp_n2=r.get("wp_n2") or "",
                referents=r.get("referents") or "",
                conditions_escalade=r.get("conditions_escalade") or "",
                notes=r.get("notes") or "",
            )
            for r in entries
        ]

    def assistant_back(self):
        self.assistant_step = 1
        self.assistant_perimetre = ""
        self.assistant_entries = []

    # ── Par interlocuteur N2 ──────────────────────────────────────────────

    def set_interlocuteur_search(self, val: str):
        self.interlocuteur_search = val
        if not val:
            self.filtered_interlocuteurs_list = self.interlocuteurs_list
        else:
            q = val.lower()
            self.filtered_interlocuteurs_list = [
                x for x in self.interlocuteurs_list
                if q in x.get("nom", "").lower()
            ]

    def toggle_expand_interlocuteur(self, nom: str):
        if self.expanded_interlocuteur == nom:
            self.expanded_interlocuteur = ""
            self.interlocuteur_entries = []
        else:
            self.expanded_interlocuteur = nom
            db = load_db()
            entries = [
                r for r in (db.get("escalation_matrix") or [])
                if (r.get("interlocuteur") or "").strip() == nom
            ]
            self.interlocuteur_entries = [
                EscaladeEntry(
                    perimetre=r.get("perimetre") or "",
                    typologie=r.get("typologie") or "",
                    categorie_fresh=r.get("categorie_fresh") or "",
                    traitement_n1=r.get("traitement_n1") or "",
                    wp=r.get("wp") or "",
                    interlocuteur=r.get("interlocuteur") or "",
                    traitement_n2n3=r.get("traitement_n2n3") or "",
                    wp_n2=r.get("wp_n2") or "",
                    referents=r.get("referents") or "",
                    conditions_escalade=r.get("conditions_escalade") or "",
                    notes=r.get("notes") or "",
                )
                for r in entries
            ]

    # ── Export CSV ────────────────────────────────────────────────────────────

    def export_csv(self):
        def esc(v: str) -> str:
            return '"' + str(v or "").replace('"', '""') + '"'

        db = load_db()
        results = db.get("escalation_matrix") or []

        if self.search:
            q = self.search.lower()
            results = [
                r for r in results
                if q in (r.get("typologie") or "").lower()
                or q in (r.get("perimetre") or "").lower()
                or q in (r.get("categorie_fresh") or "").lower()
                or q in (r.get("traitement_n1") or "").lower()
                or q in (r.get("interlocuteur") or "").lower()
                or q in (r.get("traitement_n2n3") or "").lower()
                or q in (r.get("conditions_escalade") or "").lower()
            ]
        if self.selected_perimetres:
            results = [r for r in results if r.get("perimetre") in self.selected_perimetres]

        rows = ["Périmètre,Typologie,Catégorie FRESH,Traitement N1,WP,Interlocuteur,Traitement N2/N3,WP N2,Référents,Conditions"]
        for r in results:
            rows.append(",".join([
                esc(r.get("perimetre", "")),
                esc(r.get("typologie", "")),
                esc(r.get("categorie_fresh", "")),
                esc(r.get("traitement_n1", "")),
                esc(r.get("wp", "")),
                esc(r.get("interlocuteur", "")),
                esc(r.get("traitement_n2n3", "")),
                esc(r.get("wp_n2", "")),
                esc(r.get("referents", "")),
                esc(r.get("conditions_escalade", "")),
            ]))
        csv = "\n".join(rows)
        b64 = base64.b64encode(csv.encode("utf-8")).decode()
        yield rx.call_script(f"""
var csv = atob('{b64}');
var blob = new Blob([csv], {{type:'text/csv;charset=utf-8;'}});
var url = URL.createObjectURL(blob);
var a = document.createElement('a');
a.href = url;
a.download = 'escalade_' + new Date().toISOString().slice(0,10) + '.csv';
document.body.appendChild(a); a.click();
document.body.removeChild(a); URL.revokeObjectURL(url);
""")

    # ── Arbre ─────────────────────────────────────────────────────────────

    def toggle_arbre_perimetre(self, p: str):
        if self.arbre_expanded == p:
            self.arbre_expanded = ""
            self.arbre_entries = []
        else:
            self.arbre_expanded = p
            db = load_db()
            entries = [r for r in (db.get("escalation_matrix") or []) if r.get("perimetre") == p]
            self.arbre_entries = [
                EscaladeEntry(
                    perimetre=r.get("perimetre") or "",
                    typologie=r.get("typologie") or "",
                    categorie_fresh=r.get("categorie_fresh") or "",
                    traitement_n1=r.get("traitement_n1") or "",
                    wp=r.get("wp") or "",
                    interlocuteur=r.get("interlocuteur") or "",
                    traitement_n2n3=r.get("traitement_n2n3") or "",
                    wp_n2=r.get("wp_n2") or "",
                    referents=r.get("referents") or "",
                    conditions_escalade=r.get("conditions_escalade") or "",
                    notes=r.get("notes") or "",
                )
                for r in entries
            ]
