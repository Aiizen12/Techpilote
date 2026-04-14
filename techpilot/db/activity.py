from datetime import datetime, timezone
from techpilot.db.database import load_db, save_db

MAX_LOG_SIZE = 1000


def log_activity(user_nom: str, action: str, entity: str, detail: str = "") -> None:
    """Enregistre une entrée dans audit_log. Thread-safe via save_db."""
    db = load_db()
    if "audit_log" not in db:
        db["audit_log"] = []
    db["audit_log"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_nom": user_nom,
        "action": action,
        "entity": entity,
        "detail": detail,
    })
    # Garde uniquement les MAX_LOG_SIZE entrées les plus récentes
    if len(db["audit_log"]) > MAX_LOG_SIZE:
        db["audit_log"] = db["audit_log"][-MAX_LOG_SIZE:]
    save_db(db)
