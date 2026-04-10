"""
Sync automatique de la matrice d'escalade depuis Google Sheets.
Le sheet doit être partagé en lecture publique ("Tout le monde avec le lien").
"""
import csv
import io
import uuid
import logging

import httpx

logger = logging.getLogger(__name__)

SHEET_ID = "1MYwvPhtkuQVYSABD2-xJFv2uMQVPglcj2tZKjSqA2Yw"
GID = "2011779898"
EXPORT_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    f"/export?format=csv&gid={GID}"
)

_scheduler_started = False


def _parse_csv(content: str) -> list[dict]:
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return []

    # Trouver la ligne d'en-tête (contient "périmètre")
    header_row_idx = 0
    for i, row in enumerate(rows[:6]):
        lower = [c.lower().strip() for c in row]
        if any("p\u00e9rim" in c or "perim" in c for c in lower):
            header_row_idx = i
            break

    headers = [c.strip().lower() for c in rows[header_row_idx]]

    def find_col(keywords):
        for kw in keywords:
            for i, h in enumerate(headers):
                if kw in h:
                    return i
        return -1

    col_perimetre = find_col(["p\u00e9rim\u00e8tre", "perimetre", "p\u00e9rim"])
    col_typologie = find_col(["typologie"])
    col_categ     = find_col(["cat\u00e9gorie - fresh", "categorie - fresh", "cat\u00e9gorie fresh", "cat\u00e9g", "categ"])
    col_n1        = find_col(["traitement n1"])
    col_wp        = find_col(["wp"])
    col_interlo   = find_col(["interlocuteur"])
    col_n2n3      = find_col(["traitement n2/3", "traitement n2n3", "traitement n2"])
    col_wp_n2     = find_col(["wp n2"])
    col_referents = find_col(["r\u00e9f\u00e9rent", "referent"])
    col_conditions= find_col(["conditions"])

    entries = []
    for row in rows[header_row_idx + 1:]:
        def get(col, _row=row):
            if col < 0 or col >= len(_row):
                return ""
            return _row[col].strip()

        perimetre = get(col_perimetre)
        typologie = get(col_typologie)
        if not perimetre and not typologie:
            continue

        entries.append({
            "id": str(uuid.uuid4()),
            "perimetre":        perimetre,
            "typologie":        typologie,
            "categorie_fresh":  get(col_categ),
            "traitement_n1":    get(col_n1),
            "wp":               get(col_wp),
            "interlocuteur":    get(col_interlo),
            "traitement_n2n3":  get(col_n2n3),
            "wp_n2":            get(col_wp_n2),
            "referents":        get(col_referents),
            "conditions_escalade": get(col_conditions),
        })
    return entries


def sync_from_sheets() -> tuple[bool, str]:
    """
    Télécharge et importe la matrice depuis Google Sheets.
    Retourne (succès: bool, message: str).
    """
    # Import ici pour éviter les imports circulaires
    from techpilot.db.database import load_db, save_db
    try:
        resp = httpx.get(EXPORT_URL, timeout=20, follow_redirects=True)
        resp.raise_for_status()
        content = resp.content.decode("utf-8")
        entries = _parse_csv(content)
        if not entries:
            return False, "Aucune entrée trouvée dans le sheet"
        db = load_db()
        db["escalation_matrix"] = entries
        save_db(db)
        msg = f"{len(entries)} entrées synchronisées depuis Google Sheets"
        logger.info(f"[Sheets Sync] {msg}")
        return True, msg
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            msg = "Sheet non public — partage le sheet en lecture publique"
        else:
            msg = f"Erreur HTTP {e.response.status_code}"
        logger.error(f"[Sheets Sync] {msg}")
        return False, msg
    except Exception as e:
        msg = f"Erreur: {e}"
        logger.error(f"[Sheets Sync] {msg}")
        return False, msg


def start_scheduler():
    """Démarre le scheduler APScheduler (toutes les 60 min) + sync immédiate."""
    global _scheduler_started
    if _scheduler_started:
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
        logger.info("[Sheets Sync] Scheduler démarré — sync toutes les 60 min")
        # Sync immédiate au démarrage de l'app
        ok, msg = sync_from_sheets()
        logger.info(f"[Sheets Sync] Sync initiale: {msg}")
    except Exception as e:
        logger.error(f"[Sheets Sync] Impossible de démarrer: {e}")
