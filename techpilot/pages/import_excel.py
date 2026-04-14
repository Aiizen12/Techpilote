import io
import uuid
import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
from techpilot.db.activity import log_activity
from techpilot.state.auth import AuthState

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
CARD_BG = "#111524"
BORDER  = "#1c2138"
PRIMARY = "#6366f1"

def _get_tech_names() -> list[str]:
    """Charge les noms des techniciens depuis la base de données."""
    db = load_db()
    return [t.get("nom", "") for t in db.get("technicians", []) if t.get("nom")]

COLOR_MATRIX  = "#9333ea"
COLOR_PLANNING = "#059669"


# ── Parsers ───────────────────────────────────────────────────────────────────

def _parse_escalade_matrix(wb) -> list[dict]:
    sheet_name = None
    for name in wb.sheetnames:
        if "matrice de production" in name.lower() or "matrice prod" in name.lower():
            sheet_name = name
            break
    ws = wb[sheet_name or wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    header_row_idx = 0
    for i, row in enumerate(rows[:5]):
        row_vals = [str(c).lower() if c else "" for c in row]
        if any("p" in v and ("rim" in v or "rim\u00e8" in v) for v in row_vals) or any("p\u00e9rim" in v for v in row_vals):
            header_row_idx = i
            break

    headers = [str(c).strip().lower() if c else "" for c in rows[header_row_idx]]

    def find_col(keywords):
        for kw in keywords:
            for i, h in enumerate(headers):
                if kw in h:
                    return i
        return -1

    col_perimetre  = find_col(["périmètre", "perimetre", "p\u00e9rim"])
    col_typologie  = find_col(["typologie"])
    col_categ      = find_col(["catégorie - fresh", "categorie - fresh", "catégorie fresh", "cat\u00e9g"])
    col_n1         = find_col(["traitement n1"])
    col_wp         = find_col(["wp"])
    col_interlo    = find_col(["interlocuteur"])
    col_n2n3       = find_col(["traitement n2/3", "traitement n2n3", "traitement n2"])
    col_wp_n2      = find_col(["wp n2"])
    col_referents  = find_col(["référent", "referent"])
    col_conditions = find_col(["conditions"])
    col_notes      = find_col(["notes"])

    entries = []
    for row in rows[header_row_idx + 1:]:
        def get(col):
            if col < 0 or col >= len(row):
                return ""
            v = row[col]
            return str(v).strip() if v is not None else ""

        perimetre = get(col_perimetre)
        typologie = get(col_typologie)
        if not perimetre and not typologie:
            continue

        entries.append({
            "id": str(uuid.uuid4()),
            "perimetre":          perimetre,
            "typologie":          typologie,
            "categorie_fresh":    get(col_categ),
            "traitement_n1":      get(col_n1),
            "wp":                 get(col_wp),
            "interlocuteur":      get(col_interlo),
            "traitement_n2n3":    get(col_n2n3),
            "wp_n2":              get(col_wp_n2),
            "referents":          get(col_referents),
            "conditions_escalade": get(col_conditions),
            "notes":              get(col_notes),
        })
    return entries


def _parse_planning(wb) -> list[dict]:
    """Parse planning depuis workbook openpyxl.
    Gère plusieurs blocs de semaines dans la même feuille.
    """
    sheet_name = None
    for name in wb.sheetnames:
        nl = name.lower()
        if nl == "planning (test)" or nl == "planning":
            sheet_name = name
            break
    if not sheet_name:
        for name in wb.sheetnames:
            if "planning" in name.lower():
                sheet_name = name
                break
    ws = wb[sheet_name or wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    def is_week_header(row) -> bool:
        return any(c and "semaine" in str(c).lower() for c in row)

    def extract_weeks(header_row) -> list[dict]:
        weeks = []
        for c_idx, cell in enumerate(header_row):
            if cell and "semaine" in str(cell).lower():
                label = str(cell).split("\n")[0].strip()
                weeks.append({"col": c_idx, "label": label})
        return weeks

    # Charger les noms depuis la DB (configurable via page Techniciens)
    tech_names = _get_tech_names()

    # Repérer TOUS les blocs d'en-têtes de semaines dans la feuille
    header_indices = [i for i, row in enumerate(rows) if is_week_header(row)]

    entry_map: dict[str, dict] = {}

    for h_pos, h_idx in enumerate(header_indices):
        weeks = extract_weeks(rows[h_idx])
        if not weeks:
            continue

        # Lignes de données jusqu'au prochain en-tête ou fin de fichier
        next_h = header_indices[h_pos + 1] if h_pos + 1 < len(header_indices) else len(rows)
        data_rows = rows[h_idx + 1: next_h]

        for row in data_rows:
            if not row or all(c is None for c in row):
                continue
            first = str(row[0]).strip() if row[0] else (str(row[1]).strip() if len(row) > 1 and row[1] else "")
            tech_name = next((n for n in tech_names if first.lower().startswith(n.lower())), None)
            if not tech_name:
                continue
            for week in weeks:
                c = week["col"]
                horaire = str(row[c]).strip() if c < len(row) and row[c] else ""
                bendoc  = str(row[c+1]).strip() if c+1 < len(row) and row[c+1] else ""
                tt      = str(row[c+2]).strip() if c+2 < len(row) and row[c+2] else ""
                if not horaire and not tt:
                    continue
                key = f"{tech_name}|{week['label']}"
                if key in entry_map:
                    ex = entry_map[key]
                    if not ex["bendoc_pause"] and bendoc:
                        ex["bendoc_pause"] = bendoc
                    if not ex["telework_days"] and tt:
                        ex["telework_days"] = tt
                else:
                    entry_map[key] = {
                        "id":              str(uuid.uuid4()),
                        "technician_name": tech_name,
                        "week":            week["label"],
                        "horaire":         horaire,
                        "bendoc_pause":    bendoc,
                        "telework_days":   tt,
                    }

    return list(entry_map.values())


# ── State ─────────────────────────────────────────────────────────────────────

class ImportExcelState(rx.State):
    # Matrice
    matrix_status: str = ""
    matrix_msg: str = ""
    matrix_count: int = 0
    matrix_db_count: int = 0
    matrix_filename: str = ""

    # Planning
    planning_status: str = ""
    planning_msg: str = ""
    planning_count: int = 0
    planning_db_count: int = 0
    planning_filename: str = ""

    def load_counts(self):
        db = load_db()
        self.matrix_db_count  = len(db.get("escalation_matrix") or [])
        self.planning_db_count = len(db.get("planning") or [])

    async def handle_matrix_upload(self, files: list[rx.UploadFile]):
        if not files:
            self.matrix_status = "error"
            self.matrix_msg = "Aucun fichier sélectionné. Déposez un fichier avant de cliquer."
            return

        fname = files[0].name
        self.matrix_filename = fname
        self.matrix_status = "loading"
        self.matrix_msg = f"Lecture de « {fname} »…"
        yield

        try:
            import openpyxl
            data = await files[0].read()
            size_kb = round(len(data) / 1024, 1)

            self.matrix_msg = f"Fichier reçu ({size_kb} Ko) — ouverture du classeur…"
            yield

            wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            sheets = wb.sheetnames

            self.matrix_msg = f"Onglets détectés : {', '.join(sheets)} — recherche de la matrice…"
            yield

            entries = _parse_escalade_matrix(wb)

            if not entries:
                self.matrix_status = "error"
                self.matrix_msg = (
                    f"Aucune entrée trouvée dans les onglets : {', '.join(sheets)}. "
                    f"L'onglet doit contenir « Matrice de Production » dans son nom."
                )
                log_activity("import", "LOGIN_FAIL", "import", f"Matrice : 0 entrée — onglets={sheets}")
                return

            self.matrix_msg = f"{len(entries)} lignes parsées — sauvegarde en base…"
            yield

            db = load_db()
            old_count = len(db.get("escalation_matrix") or [])
            db["escalation_matrix"] = entries
            save_db(db)

            self.matrix_count    = len(entries)
            self.matrix_db_count = len(entries)
            self.matrix_status   = "success"
            self.matrix_msg      = (
                f"{len(entries)} procédures importées "
                f"(avant : {old_count}, après : {len(entries)})."
            )
            auth = await self.get_state(AuthState)
            log_activity(
                auth.user_nom, "UPDATE", "import",
                f"Matrice OK : {len(entries)} entrées depuis « {fname} » (onglets : {', '.join(sheets)})"
            )

        except Exception as e:
            import traceback
            detail = traceback.format_exc().splitlines()[-1]
            self.matrix_status = "error"
            self.matrix_msg = f"Erreur : {str(e)} — {detail}"
            log_activity("import", "LOGIN_FAIL", "import", f"Matrice ERREUR : {str(e)}")

    async def handle_planning_upload(self, files: list[rx.UploadFile]):
        if not files:
            self.planning_status = "error"
            self.planning_msg = "Aucun fichier sélectionné. Déposez un fichier avant de cliquer."
            return

        fname = files[0].name
        self.planning_filename = fname
        self.planning_status = "loading"
        self.planning_msg = f"Lecture de « {fname} »…"
        yield

        try:
            import openpyxl
            data = await files[0].read()
            size_kb = round(len(data) / 1024, 1)

            self.planning_msg = f"Fichier reçu ({size_kb} Ko) — ouverture du classeur…"
            yield

            wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            sheets = wb.sheetnames

            self.planning_msg = f"Onglets détectés : {', '.join(sheets)} — recherche des blocs de semaines…"
            yield

            # Compter les blocs avant de parser (pour le message)
            import openpyxl as _ox
            _wb2 = _ox.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            _sheet = next(
                (s for s in _wb2.sheetnames if "planning" in s.lower()),
                _wb2.sheetnames[0]
            )
            _rows = list(_wb2[_sheet].iter_rows(values_only=True))
            _n_blocks = sum(
                1 for row in _rows
                if any(c and "semaine" in str(c).lower() for c in row)
            )
            _tech_names = _get_tech_names()
            self.planning_msg = (
                f"{_n_blocks} bloc(s) de semaines détectés — "
                f"techniciens reconnus : {', '.join(_tech_names)} — parsing…"
            )
            yield

            entries = _parse_planning(wb)

            if not entries:
                self.planning_status = "error"
                self.planning_msg = (
                    f"Aucune entrée trouvée dans les onglets : {', '.join(sheets)}. "
                    f"L'onglet doit s'appeler « planning (TEST) » ou « planning »."
                )
                log_activity("import", "LOGIN_FAIL", "import", f"Planning : 0 entrée — onglets={sheets}")
                return

            self.planning_msg = f"{len(entries)} lignes parsées — sauvegarde en base…"
            yield

            db = load_db()
            old_count = len(db.get("planning") or [])
            db["planning"] = entries
            save_db(db)

            self.planning_count    = len(entries)
            self.planning_db_count = len(entries)
            self.planning_status   = "success"
            self.planning_msg      = (
                f"{len(entries)} entrées importées "
                f"(avant : {old_count}, après : {len(entries)})."
            )
            auth = await self.get_state(AuthState)
            log_activity(
                auth.user_nom, "UPDATE", "import",
                f"Planning OK : {len(entries)} entrées depuis « {fname} » (onglets : {', '.join(sheets)})"
            )

        except Exception as e:
            import traceback
            detail = traceback.format_exc().splitlines()[-1]
            self.planning_status = "error"
            self.planning_msg = f"Erreur : {str(e)} — {detail}"
            log_activity("import", "LOGIN_FAIL", "import", f"Planning ERREUR : {str(e)}")


# ── Composants ────────────────────────────────────────────────────────────────

def _status_banner(status, msg) -> rx.Component:
    return rx.cond(
        status != "",
        rx.hstack(
            rx.cond(
                status == "success",
                rx.icon("circle-check", size=15, color="#22c55e"),
                rx.cond(
                    status == "loading",
                    rx.icon("loader-circle", size=15, color=MUTED),
                    rx.icon("circle-x", size=15, color="#ef4444"),
                ),
            ),
            rx.text(
                msg,
                font_size="0.8rem",
                color=rx.cond(
                    status == "success", "#86efac",
                    rx.cond(status == "loading", MUTED, "#fca5a5"),
                ),
                flex="1",
            ),
            spacing="2",
            align="center",
            background=rx.cond(
                status == "success", "rgba(34,197,94,0.07)",
                rx.cond(status == "loading", "rgba(148,163,184,0.07)", "rgba(239,68,68,0.07)"),
            ),
            border=rx.cond(
                status == "success", "1px solid rgba(34,197,94,0.2)",
                rx.cond(status == "loading", f"1px solid {BORDER}", "1px solid rgba(239,68,68,0.2)"),
            ),
            border_radius="8px",
            padding="0.6rem 0.9rem",
            width="100%",
        ),
    )


def _upload_zone(
    title: str,
    subtitle: str,
    icon_name: str,
    accent: str,
    upload_id: str,
    handler,
    status,
    msg,
    db_count,
    filename,
) -> rx.Component:
    return rx.box(
        rx.vstack(

            # ── En-tête ──────────────────────────────────────────────────────
            rx.hstack(
                rx.box(
                    rx.icon(icon_name, size=22, color=accent),
                    background=f"rgba(99,102,241,0.08)",
                    border_radius="10px",
                    padding="10px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.vstack(
                    rx.text(title, color=TEXT, font_size="1rem", font_weight="700"),
                    rx.text(subtitle, color=MUTED, font_size="0.75rem"),
                    spacing="0",
                    align="start",
                ),
                rx.spacer(),
                # Badge compteur DB
                rx.cond(
                    db_count > 0,
                    rx.box(
                        rx.vstack(
                            rx.text(
                                db_count.to_string(),
                                color=accent,
                                font_size="1.4rem",
                                font_weight="800",
                                line_height="1",
                            ),
                            rx.text("en base", color=MUTED, font_size="0.65rem"),
                            spacing="0",
                            align="center",
                        ),
                        background=f"rgba(99,102,241,0.06)",
                        border=f"1px solid {BORDER}",
                        border_radius="10px",
                        padding="0.5rem 0.9rem",
                        text_align="center",
                    ),
                ),
                spacing="3",
                align="center",
                width="100%",
            ),

            rx.divider(border_color=BORDER),

            # ── Zone de dépôt ─────────────────────────────────────────────────
            rx.upload(
                rx.vstack(
                    rx.box(
                        rx.icon("folder-open", size=38, color=accent),
                        background=f"rgba(99,102,241,0.07)",
                        border_radius="14px",
                        padding="18px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                    rx.text(
                        "Glisser-déposer votre fichier Excel ici",
                        color=TEXT,
                        font_size="0.88rem",
                        font_weight="500",
                        margin_top="0.5rem",
                    ),
                    rx.text(
                        "ou cliquer pour parcourir",
                        color=MUTED,
                        font_size="0.75rem",
                    ),
                    rx.box(
                        rx.text(".xlsx  .xls  .xlsm", color=MUTED, font_size="0.7rem", font_family="monospace"),
                        background="rgba(255,255,255,0.04)",
                        border=f"1px solid {BORDER}",
                        border_radius="5px",
                        padding="3px 10px",
                        margin_top="0.25rem",
                    ),
                    spacing="1",
                    align="center",
                    padding="2rem 1rem",
                ),
                id=upload_id,
                accept={"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx", ".xls", ".xlsm"]},
                max_files=1,
                border=f"2px dashed {BORDER}",
                border_radius="12px",
                width="100%",
                transition="all 0.2s",
                _hover={"border_color": accent, "background": f"rgba(99,102,241,0.03)", "cursor": "pointer"},
            ),

            # ── Fichier sélectionné ───────────────────────────────────────────
            rx.cond(
                filename != "",
                rx.hstack(
                    rx.icon("file-spreadsheet", size=14, color=accent),
                    rx.text(filename, color=TEXT, font_size="0.78rem", font_weight="500"),
                    spacing="2",
                    align="center",
                    background="rgba(255,255,255,0.04)",
                    border=f"1px solid {BORDER}",
                    border_radius="7px",
                    padding="5px 10px",
                ),
            ),

            # ── Bouton ────────────────────────────────────────────────────────
            rx.button(
                rx.cond(
                    status == "loading",
                    rx.icon("loader-circle", size=16),
                    rx.icon("upload", size=16),
                ),
                rx.cond(status == "loading", "Import en cours…", "Lancer l'import"),
                on_click=handler(rx.upload_files(upload_id=upload_id)),
                background=rx.cond(
                    status == "loading",
                    "rgba(148,163,184,0.15)",
                    f"linear-gradient(135deg, {accent}, {accent}bb)",
                ),
                color=rx.cond(status == "loading", MUTED, "white"),
                border_radius="10px",
                padding="10px 20px",
                font_size="0.875rem",
                font_weight="600",
                cursor=rx.cond(status == "loading", "not-allowed", "pointer"),
                width="100%",
                spacing="2",
                _hover={"opacity": rx.cond(status == "loading", "1", "0.88")},
                transition="all 0.15s",
            ),

            # ── Statut ────────────────────────────────────────────────────────
            _status_banner(status, msg),

            spacing="3",
            width="100%",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_top=f"3px solid {accent}",
        border_radius="16px",
        padding="1.5rem",
        flex="1",
        min_width="300px",
    )


def _format_card() -> rx.Component:
    """Carte d'aide sur le format attendu."""
    return rx.box(
        rx.hstack(
            rx.icon("info", size=16, color=PRIMARY),
            rx.text("Format attendu", color=TEXT, font_size="0.85rem", font_weight="600"),
            spacing="2",
            align="center",
            margin_bottom="0.75rem",
        ),
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.icon("git-branch", size=13, color=COLOR_MATRIX),
                    background="rgba(147,51,234,0.1)",
                    border_radius="5px",
                    padding="4px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.vstack(
                    rx.text("Matrice d'escalade", color=TEXT, font_size="0.8rem", font_weight="600"),
                    rx.text(
                        "Onglet contenant « Matrice de Production » — colonnes : Périmètre, Typologie, Catégorie FRESH, Traitement N1, WP, Interlocuteur, Traitement N2/3, Référents, Conditions",
                        color=MUTED, font_size="0.73rem", line_height="1.5",
                    ),
                    spacing="0", align="start",
                ),
                spacing="3",
                align="start",
            ),
            rx.divider(border_color=BORDER),
            rx.hstack(
                rx.box(
                    rx.icon("calendar-days", size=13, color=COLOR_PLANNING),
                    background="rgba(5,150,105,0.1)",
                    border_radius="5px",
                    padding="4px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.vstack(
                    rx.text("Planning", color=TEXT, font_size="0.8rem", font_weight="600"),
                    rx.text(
                        "Onglet « planning (TEST) » — ligne d'en-tête avec « Semaine SXX », noms des techniciens en lignes (Bastian, Adrien, Mirgaël, Cédric, Thaïs, Alistair)",
                        color=MUTED, font_size="0.73rem", line_height="1.5",
                    ),
                    spacing="0", align="start",
                ),
                spacing="3",
                align="start",
            ),
            spacing="3",
        ),
        background="#0d1021",
        border=f"1px solid {BORDER}",
        border_radius="12px",
        padding="1rem 1.25rem",
        width="100%",
    )


def import_excel_content() -> rx.Component:
    return rx.vstack(

        # ── Header ────────────────────────────────────────────────────────────
        rx.hstack(
            rx.hstack(
                rx.box(
                    rx.icon("file-up", size=20, color="white"),
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    border_radius="10px",
                    padding="8px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.vstack(
                    rx.text("Import de données", color=TEXT, font_size="1.1rem", font_weight="700"),
                    rx.text("Déposez vos fichiers Excel pour mettre à jour la base", color=MUTED, font_size="0.78rem"),
                    spacing="0",
                    align="start",
                ),
                spacing="3",
                align="center",
            ),
            width="100%",
            align="center",
        ),

        # ── Deux zones de dépôt ───────────────────────────────────────────────
        rx.hstack(
            _upload_zone(
                title="Matrice d'escalade",
                subtitle="Onglet : Matrice de Production",
                icon_name="git-branch",
                accent=COLOR_MATRIX,
                upload_id="matrix_upload",
                handler=ImportExcelState.handle_matrix_upload,
                status=ImportExcelState.matrix_status,
                msg=ImportExcelState.matrix_msg,
                db_count=ImportExcelState.matrix_db_count,
                filename=ImportExcelState.matrix_filename,
            ),
            _upload_zone(
                title="Planning",
                subtitle="Onglet : planning (TEST)",
                icon_name="calendar-days",
                accent=COLOR_PLANNING,
                upload_id="planning_upload",
                handler=ImportExcelState.handle_planning_upload,
                status=ImportExcelState.planning_status,
                msg=ImportExcelState.planning_msg,
                db_count=ImportExcelState.planning_db_count,
                filename=ImportExcelState.planning_filename,
            ),
            spacing="5",
            width="100%",
            wrap="wrap",
            align="start",
        ),

        # ── Format attendu ────────────────────────────────────────────────────
        _format_card(),

        spacing="5",
        width="100%",
        on_mount=ImportExcelState.load_counts,
    )


def import_excel_page() -> rx.Component:
    return page_layout(import_excel_content(), "Import de données")
