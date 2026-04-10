"""
Sync automatique de la matrice d'escalade depuis Google Sheets (privé).
Authentification via compte de service Google.

Variables d'environnement requises :
  GOOGLE_SERVICE_ACCOUNT_JSON  — contenu du fichier JSON du compte de service
  GOOGLE_SHEET_ID              — ID du spreadsheet (optionnel, sinon valeur par défaut)
"""
import json
import os
import uuid
import logging

logger = logging.getLogger(__name__)

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1MYwvPhtkuQVYSABD2-xJFv2uMQVPglcj2tZKjSqA2Yw")
GID = "2011779898"

_scheduler_started = False
_last_sync_msg = ""
_last_sync_ok = False


def _get_sheet_name(service) -> str:
    """Trouve le nom de l'onglet correspondant au GID."""
    meta = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    for sheet in meta.get("sheets", []):
        props = sheet.get("properties", {})
        if str(props.get("sheetId")) == GID:
            return props.get("title", "")
    # Fallback : premier onglet
    sheets = meta.get("sheets", [])
    if sheets:
        return sheets[0]["properties"]["title"]
    return ""


def _parse_rows(rows: list[list]) -> list[dict]:
    """Parse une liste de lignes (list of lists) en entrées de matrice."""
    if not rows:
        return []

    # Trouver la ligne d'en-tête
    header_row_idx = 0
    for i, row in enumerate(rows[:6]):
        lower = [str(c).lower().strip() for c in row]
        if any("p\u00e9rim" in c or "perim" in c for c in lower):
            header_row_idx = i
            break

    headers = [str(c).strip().lower() for c in rows[header_row_idx]]

    def find_col(keywords):
        for kw in keywords:
            for i, h in enumerate(headers):
                if kw in h:
                    return i
        return -1

    col_perimetre  = find_col(["p\u00e9rim\u00e8tre", "perimetre", "p\u00e9rim"])
    col_typologie  = find_col(["typologie"])
    col_categ      = find_col(["cat\u00e9gorie - fresh", "categorie - fresh", "cat\u00e9gorie fresh", "cat\u00e9g", "categ"])
    col_n1         = find_col(["traitement n1"])
    col_wp         = find_col(["wp"])
    col_interlo    = find_col(["interlocuteur"])
    col_n2n3       = find_col(["traitement n2/3", "traitement n2n3", "traitement n2"])
    col_wp_n2      = find_col(["wp n2"])
    col_referents  = find_col(["r\u00e9f\u00e9rent", "referent"])
    col_conditions = find_col(["conditions"])

    entries = []
    for row in rows[header_row_idx + 1:]:
        def get(col, _row=row):
            if col < 0 or col >= len(_row):
                return ""
            return str(_row[col]).strip() if _row[col] is not None else ""

        perimetre = get(col_perimetre)
        typologie = get(col_typologie)
        if not perimetre and not typologie:
            continue

        entries.append({
            "id":                  str(uuid.uuid4()),
            "perimetre":           perimetre,
            "typologie":           typologie,
            "categorie_fresh":     get(col_categ),
            "traitement_n1":       get(col_n1),
            "wp":                  get(col_wp),
            "interlocuteur":       get(col_interlo),
            "traitement_n2n3":     get(col_n2n3),
            "wp_n2":               get(col_wp_n2),
            "referents":           get(col_referents),
            "conditions_escalade": get(col_conditions),
        })
    return entries


def sync_from_sheets() -> tuple[bool, str]:
    """
    Synchronise la matrice depuis Google Sheets via compte de service.
    Retourne (succès: bool, message: str).
    """
    global _last_sync_msg, _last_sync_ok
    from techpilot.db.database import load_db, save_db

    sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        msg = "Variable GOOGLE_SERVICE_ACCOUNT_JSON manquante"
        logger.error(f"[Sheets Sync] {msg}")
        _last_sync_ok, _last_sync_msg = False, msg
        return False, msg

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds_dict = json.loads(sa_json)
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )
        service = build("sheets", "v4", credentials=creds, cache_discovery=False)

        # Trouver le nom de l'onglet par GID
        sheet_name = _get_sheet_name(service)
        if not sheet_name:
            msg = "Onglet introuvable dans le spreadsheet"
            _last_sync_ok, _last_sync_msg = False, msg
            return False, msg

        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=SHEET_ID, range=sheet_name)
            .execute()
        )
        rows = result.get("values", [])
        entries = _parse_rows(rows)

        if not entries:
            msg = "Aucune entrée trouvée dans l'onglet"
            _last_sync_ok, _last_sync_msg = False, msg
            return False, msg

        db = load_db()
        db["escalation_matrix"] = entries
        save_db(db)
        msg = f"{len(entries)} entrées synchronisées depuis Google Sheets"
        logger.info(f"[Sheets Sync] {msg}")
        _last_sync_ok, _last_sync_msg = True, msg
        return True, msg

    except json.JSONDecodeError:
        msg = "GOOGLE_SERVICE_ACCOUNT_JSON invalide (JSON malformé)"
    except Exception as e:
        msg = f"Erreur: {e}"

    logger.error(f"[Sheets Sync] {msg}")
    _last_sync_ok, _last_sync_msg = False, msg
    return False, msg


def start_scheduler():
    """Démarre APScheduler (60 min) + sync immédiate au démarrage."""
    global _scheduler_started
    if _scheduler_started:
        return
    # Ne pas démarrer si la variable d'env est absente
    if not os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"):
        logger.warning("[Sheets Sync] GOOGLE_SERVICE_ACCOUNT_JSON absent — scheduler non démarré")
        return
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(
            sync_from_sheets,
            trigger="interval",
            minutes=60,
            id="sheets_sync",
            replace_existing=True,
        )
        scheduler.start()
        _scheduler_started = True
        logger.info("[Sheets Sync] Scheduler démarré — toutes les 60 min")
        ok, msg = sync_from_sheets()
        logger.info(f"[Sheets Sync] Sync initiale: {msg}")
    except Exception as e:
        logger.error(f"[Sheets Sync] Impossible de démarrer: {e}")
