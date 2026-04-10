"""
Sync automatique de la matrice d'escalade via Google Apps Script Web App.

Variables d'environnement :
  GOOGLE_APPS_SCRIPT_URL        — URL de déploiement Apps Script (/exec)
  GOOGLE_SYNC_INTERVAL_MINUTES  — intervalle en minutes (défaut: 60)
"""
import os
import uuid
import logging

import httpx

logger = logging.getLogger(__name__)

_scheduler_started = False


def _cfg():
    return {
        "url":      os.getenv("GOOGLE_APPS_SCRIPT_URL", ""),
        "interval": int(os.getenv("GOOGLE_SYNC_INTERVAL_MINUTES", "60")),
    }


def _parse_rows(rows: list[list]) -> list[dict]:
    if not rows:
        return []

    # Trouver la ligne d'en-tête
    header_row_idx = 0
    for i, row in enumerate(rows[:6]):
        joined = "|".join(str(c).lower() for c in row)
        if "rimetre" in joined or "typolog" in joined:
            header_row_idx = i
            break

    COL = {
        "perimetre":           0,
        "typologie":           1,
        "categorie_fresh":     2,
        "traitement_n1":       3,
        "wp":                  4,
        "interlocuteur":       5,
        "traitement_n2n3":     6,
        "wp_n2":               7,
        "referents":           8,
        "conditions_escalade": 9,
    }

    entries = []
    for row in rows[header_row_idx + 1:]:
        if not any(c and str(c).strip() for c in row):
            continue

        def get(col, _row=row):
            if col >= len(_row):
                return ""
            return str(_row[col]).strip() if _row[col] else ""

        perimetre = get(COL["perimetre"])
        typologie = get(COL["typologie"])
        if not perimetre and not typologie:
            continue

        entries.append({
            "id":                  str(uuid.uuid4()),
            "perimetre":           perimetre,
            "typologie":           typologie,
            "categorie_fresh":     get(COL["categorie_fresh"]),
            "traitement_n1":       get(COL["traitement_n1"]),
            "wp":                  get(COL["wp"]),
            "interlocuteur":       get(COL["interlocuteur"]),
            "traitement_n2n3":     get(COL["traitement_n2n3"]),
            "wp_n2":               get(COL["wp_n2"]),
            "referents":           get(COL["referents"]),
            "conditions_escalade": get(COL["conditions_escalade"]),
        })
    return entries


def sync_from_sheets() -> tuple[bool, str]:
    """Synchronise la matrice via Apps Script Web App."""
    from techpilot.db.database import load_db, save_db

    cfg = _cfg()
    url = cfg["url"]

    if not url:
        msg = "GOOGLE_APPS_SCRIPT_URL manquant"
        logger.warning(f"[GoogleSync] {msg}")
        return False, msg

    try:
        resp = httpx.get(url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()
        rows = data.get("values", [])

        if len(rows) < 2:
            return False, "Feuille vide ou sans données"

        entries = _parse_rows(rows)
        if not entries:
            return False, "Aucune entrée trouvée"

        db = load_db()
        db["escalation_matrix"] = entries
        save_db(db)

        msg = f"{len(entries)} entrées synchronisées depuis Google Sheets"
        logger.info(f"[GoogleSync] ✓ {msg}")
        return True, msg

    except httpx.HTTPStatusError as e:
        msg = f"Erreur HTTP {e.response.status_code}"
        logger.error(f"[GoogleSync] {msg}")
        return False, msg
    except Exception as e:
        msg = f"Erreur: {e}"
        logger.error(f"[GoogleSync] {msg}")
        return False, msg


def start_scheduler():
    """Démarre APScheduler + sync immédiate au démarrage."""
    global _scheduler_started
    if _scheduler_started:
        return
    cfg = _cfg()
    if not cfg["url"]:
        logger.warning("[GoogleSync] Désactivé — GOOGLE_APPS_SCRIPT_URL non configuré")
        return
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(
            sync_from_sheets,
            trigger="interval",
            minutes=cfg["interval"],
            id="sheets_sync",
            replace_existing=True,
        )
        scheduler.start()
        _scheduler_started = True
        logger.info(f"[GoogleSync] Scheduler démarré — toutes les {cfg['interval']} min")
        ok, msg = sync_from_sheets()
        logger.warning(f"[GoogleSync] Sync initiale: {msg}")
    except Exception as e:
        logger.error(f"[GoogleSync] Impossible de démarrer: {e}")
