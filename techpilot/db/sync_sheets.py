"""
Sync automatique de la matrice d'escalade depuis Google Sheets.
Utilise une API Key Google (mêmes variables que l'ancienne version Node.js).

Variables d'environnement :
  GOOGLE_API_KEY            — clé API Google Sheets
  GOOGLE_SHEET_MATRIX_ID    — ID du spreadsheet
  GOOGLE_SYNC_INTERVAL_MINUTES — intervalle en minutes (défaut: 60)
"""
import os
import uuid
import logging

import httpx

logger = logging.getLogger(__name__)

BASE = "https://sheets.googleapis.com/v4/spreadsheets"

_scheduler_started = False


def _cfg():
    """Lit les variables d'env au moment de l'appel (pas à l'import)."""
    api_key  = os.getenv("GOOGLE_API_KEY", "")
    sheet_id = os.getenv("GOOGLE_SHEET_MATRIX_ID", "")
    # Debug: log les clés disponibles qui contiennent "GOOGLE"
    google_keys = [k for k in os.environ if "GOOGLE" in k]
    logger.info(f"[GoogleSync] ENV keys with GOOGLE: {google_keys}")
    logger.info(f"[GoogleSync] api_key={'SET' if api_key else 'EMPTY'}, sheet_id={'SET' if sheet_id else 'EMPTY'}")
    return {
        "api_key":  api_key,
        "sheet_id": sheet_id or "1MYwvPhtkuQVYSABD2-xJFv2uMQVPglcj2tZKjSqA2Yw",
        "interval": int(os.getenv("GOOGLE_SYNC_INTERVAL_MINUTES", "60")),
    }


def _find_matrix_sheet(api_key: str, sheet_id: str) -> str:
    """Retourne le nom de l'onglet contenant la matrice."""
    url = f"{BASE}/{sheet_id}?key={api_key}&fields=sheets.properties"
    resp = httpx.get(url, timeout=15)
    resp.raise_for_status()
    sheets = resp.json().get("sheets", [])
    titles = [s["properties"]["title"] for s in sheets]
    keywords = ["matrice", "escalade", "routage"]
    for title in titles:
        if any(k in title.lower() for k in keywords):
            return title
    return titles[0] if titles else ""


def _fetch_rows(sheet_name: str, api_key: str, sheet_id: str) -> list[list]:
    """Récupère toutes les lignes de l'onglet."""
    import urllib.parse
    encoded = urllib.parse.quote(sheet_name)
    url = f"{BASE}/{sheet_id}/values/{encoded}?key={api_key}"
    resp = httpx.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise ValueError(f"Google API: {data['error']['message']}")
    return data.get("values", [])


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

    # La matrice a des positions fixes (comme le JS original)
    COL = {
        "perimetre":        0,
        "typologie":        1,
        "categorie_fresh":  2,
        "traitement_n1":    3,
        "wp":               4,
        "interlocuteur":    5,
        "traitement_n2n3":  6,
        "wp_n2":            7,
        "referents":        8,
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
    """Synchronise la matrice depuis Google Sheets. Retourne (succès, message)."""
    from techpilot.db.database import load_db, save_db

    cfg = _cfg()
    api_key, sheet_id = cfg["api_key"], cfg["sheet_id"]

    if not api_key or not sheet_id:
        msg = "GOOGLE_API_KEY ou GOOGLE_SHEET_MATRIX_ID manquant"
        logger.warning(f"[GoogleSync] {msg}")
        return False, msg

    try:
        sheet_name = _find_matrix_sheet(api_key, sheet_id)
        logger.info(f"[GoogleSync] Onglet trouvé : \"{sheet_name}\"")

        rows = _fetch_rows(sheet_name, api_key, sheet_id)
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
        msg = f"Erreur HTTP {e.response.status_code} — vérifie l'API Key et l'ID du sheet"
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
    if not cfg["api_key"] or not cfg["sheet_id"]:
        logger.warning("[GoogleSync] Désactivé — GOOGLE_API_KEY ou GOOGLE_SHEET_MATRIX_ID non configuré")
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
        logger.info(f"[GoogleSync] Sync initiale: {msg}")
    except Exception as e:
        logger.error(f"[GoogleSync] Impossible de démarrer: {e}")
