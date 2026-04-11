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
