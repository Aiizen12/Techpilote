import os
import copy
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

DEFAULT_DB = {
    "technicians": [
        {"id": "1", "nom": "Bastian",  "matricule": "464", "active": True, "permissions": {}},
        {"id": "2", "nom": "Adrien",   "matricule": "529", "active": True, "permissions": {}},
        {"id": "3", "nom": "Mirgaël",  "matricule": "524", "active": True, "permissions": {}},
        {"id": "4", "nom": "Cédric",   "matricule": "518", "active": True, "permissions": {}},
        {"id": "5", "nom": "Thaïs",    "matricule": "432", "active": True, "permissions": {}},
        {"id": "6", "nom": "Alistair", "matricule": "556", "active": True, "permissions": {}},
        {"id": "7", "nom": "Tiphaine", "matricule": "590", "active": True, "permissions": {}},
        {"id": "8", "nom": "Sabrina",  "matricule": "",    "active": True, "permissions": {}},
    ],
    "planning": [],
    "astreintes": [
        {"id": "1", "period": "Mars 6 et 9",    "slot_matin": "Adrien",  "slot_soir": "Mirgaël"},
        {"id": "2", "period": "Avril 7 et 8",   "slot_matin": "Adrien",  "slot_soir": "Cédric"},
        {"id": "3", "period": "Mai 7 et 8",     "slot_matin": "Mirgaël", "slot_soir": "Cédric"},
        {"id": "4", "period": "Juin 8 et 9",    "slot_matin": "Cédric",  "slot_soir": "Mirgaël"},
        {"id": "5", "period": "Juillet 7 et 8", "slot_matin": "Mirgaël", "slot_soir": "Cédric"},
        {"id": "6", "period": "Août 6 et 7",    "slot_matin": "Adrien",  "slot_soir": "Cédric"},
    ],
    "escalation_matrix": [],
    "tickets": [],
    "documents": [],
    "actualites": [],
    "feedbacks": [],
    "quetes": [],
    "quetes_progress": [],
    "notifications": [],
    "audit_log": [],
    "manager_auth": {},
    "quick_notes": {},
    "quick_links": [],
    "changelog": [
        {
            "id": "cl-001",
            "version": "1.0",
            "date": "2026-03-01",
            "titre": "Lancement de TechPilot",
            "type": "feature",
            "items": [
                "Dashboard avec KPIs et widgets personnalisables",
                "Planning hebdomadaire (import Excel)",
                "Matrice d'escalade N1/N2/N3 — 401 entrées",
                "Gestion des tickets N1",
                "Page Techniciens",
                "Import Excel (planning + matrice)",
            ],
        },
        {
            "id": "cl-002",
            "version": "1.1",
            "date": "2026-03-15",
            "titre": "Documents, Gabarits & Actualités",
            "type": "feature",
            "items": [
                "Base documentaire avec recherche et filtres",
                "Gabarits par catégorie (kanban) avec copie presse-papiers",
                "Page Actualités (info / succès / avertissement / alerte)",
                "Widget Actualités sur le dashboard",
            ],
        },
        {
            "id": "cl-003",
            "version": "1.2",
            "date": "2026-03-28",
            "titre": "Quêtes, Feedbacks & Admin",
            "type": "feature",
            "items": [
                "Système de quêtes et gamification (XP, niveaux, rangs E→S)",
                "Leaderboard de l'équipe",
                "Page Feedbacks (bugs, suggestions, améliorations)",
                "Page Permissions (gestion des droits par technicien)",
                "Journal d'audit (toutes les actions tracées)",
            ],
        },
        {
            "id": "cl-004",
            "version": "1.3",
            "date": "2026-04-07",
            "titre": "Procédures N1, liaisons documents & profil",
            "type": "feature",
            "items": [
                "Procédures N1 éditables dans la matrice d'escalade",
                "Historique des versions de procédure avec restauration",
                "Liaison document/gabarit/URL sur chaque entrée matrice",
                "Tableau de suivi des procédures",
                "Page Profil utilisateur (changement de mot de passe)",
                "Notes rapides auto-sauvegardées (widget + fenêtre dédiée)",
                "Liens rapides personnalisables sur le dashboard",
            ],
        },
        {
            "id": "cl-005",
            "version": "1.4",
            "date": "2026-04-21",
            "titre": "Recherche globale, Stats & Changelog",
            "type": "feature",
            "items": [
                "Recherche globale Ctrl+K (tickets, matrice, documents, gabarits)",
                "Widget Stats techniciens sur le dashboard",
                "Widget Mises à jour (changelog) sur le dashboard",
                "Page Mode Opératoire imprimable (/modop)",
                "Formulaire création ticket redesigné (style Freshservice)",
            ],
        },
    ],
}

_client = None
_collection = None
_cache: dict | None = None


def init_db():
    global _client, _collection, _cache
    uri = os.getenv("MONGODB_URI")
    if not uri:
        print("[DB] Mode mémoire (MONGODB_URI absent)")
        _cache = copy.deepcopy(DEFAULT_DB)
        return
    _client = MongoClient(uri)
    _collection = _client["techpilot"]["techpilot_dbs"]
    doc = _collection.find_one({"_id": "main"})
    if not doc:
        _collection.insert_one({"_id": "main", **DEFAULT_DB})
        doc = _collection.find_one({"_id": "main"})
    _cache = {k: v for k, v in doc.items() if k != "_id"}

    # Ajoute les techniciens du DEFAULT_DB manquants dans la DB existante
    existing_ids = {str(t.get("id")) for t in _cache.get("technicians", [])}
    missing = [t for t in DEFAULT_DB["technicians"] if str(t.get("id")) not in existing_ids]
    if missing:
        _cache.setdefault("technicians", []).extend(missing)
        _collection.update_one(
            {"_id": "main"},
            {"$set": {"technicians": _cache["technicians"]}},
        )
        print(f"[DB] Techniciens ajoutés : {[t['nom'] for t in missing]}")

    # Ajoute les entrées changelog manquantes
    existing_cl_ids = {str(e.get("id")) for e in _cache.get("changelog", [])}
    missing_cl = [e for e in DEFAULT_DB["changelog"] if str(e.get("id")) not in existing_cl_ids]
    if missing_cl:
        _cache.setdefault("changelog", []).extend(missing_cl)
        _cache["changelog"].sort(key=lambda e: e.get("date", ""), reverse=True)
        _collection.update_one(
            {"_id": "main"},
            {"$set": {"changelog": _cache["changelog"]}},
        )
        print(f"[DB] Changelog ajouté : {[e['titre'] for e in missing_cl]}")

    print(f"[DB] MongoDB connecté — {len(_cache.get('technicians', []))} techniciens")


def load_db() -> dict:
    if _cache is None:
        init_db()
    return _cache


def save_db(data: dict):
    global _cache
    _cache = data
    if _collection is not None:
        _collection.update_one(
            {"_id": "main"},
            {"$set": {k: v for k, v in data.items() if k != "_id"}},
            upsert=True,
        )
