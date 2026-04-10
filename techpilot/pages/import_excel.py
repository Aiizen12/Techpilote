import io
import uuid
import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db

TEXT = "#e2e8f0"; MUTED = "#64748b"; CARD_BG = "#151728"; BORDER = "#1e2235"; PRIMARY = "#6366f1"

TECH_NAMES = ["Bastian", "Adrien", "Mirgaël", "Cédric", "Thaïs", "Alistair"]


def _parse_escalade_matrix(wb) -> list[dict]:
    """Parse matrice d'escalade depuis workbook openpyxl."""
    sheet_name = None
    for name in wb.sheetnames:
        if "matrice de production" in name.lower() or "matrice prod" in name.lower():
            sheet_name = name
            break
    ws = wb[sheet_name or wb.sheetnames[0]]

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    # Trouver ligne d'en-tête
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

    col_perimetre    = find_col(["périmètre", "perimetre", "p\u00e9rim"])
    col_typologie    = find_col(["typologie"])
    col_categ        = find_col(["catégorie - fresh", "categorie - fresh", "catégorie fresh", "cat\u00e9g"])
    col_n1           = find_col(["traitement n1"])
    col_wp           = find_col(["wp"])
    col_interlo      = find_col(["interlocuteur"])
    col_n2n3         = find_col(["traitement n2/3", "traitement n2n3", "traitement n2"])
    col_wp_n2        = find_col(["wp n2"])
    col_referents    = find_col(["référent", "referent"])
    col_conditions   = find_col(["conditions"])

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
            "perimetre": perimetre,
            "typologie": typologie,
            "categorie_fresh": get(col_categ),
            "traitement_n1": get(col_n1),
            "wp": get(col_wp),
            "interlocuteur": get(col_interlo),
            "traitement_n2n3": get(col_n2n3),
            "wp_n2": get(col_wp_n2),
            "referents": get(col_referents),
            "conditions_escalade": get(col_conditions),
        })
    return entries


def _parse_planning(wb) -> list[dict]:
    """Parse planning depuis workbook openpyxl."""
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

    # Trouver ligne semaines
    week_row_idx = 0
    for i, row in enumerate(rows[:5]):
        if any(c and "semaine" in str(c).lower() for c in row):
            week_row_idx = i
            break

    header = rows[week_row_idx]
    weeks = []
    for c_idx, cell in enumerate(header):
        if cell and "semaine" in str(cell).lower():
            label = str(cell).split("\n")[0].strip()
            weeks.append({"col": c_idx, "label": label})

    entry_map: dict[str, dict] = {}
    for row in rows[week_row_idx + 1:]:
        first = str(row[0]).strip() if row[0] else (str(row[1]).strip() if len(row) > 1 and row[1] else "")
        tech_name = next((n for n in TECH_NAMES if first.lower().startswith(n.lower())), None)
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
                    "id": str(uuid.uuid4()),
                    "technician_name": tech_name,
                    "week": week["label"],
                    "horaire": horaire,
                    "bendoc_pause": bendoc,
                    "telework_days": tt,
                }
    return list(entry_map.values())


class ImportExcelState(rx.State):
    matrix_status: str = ""   # "", "loading", "success", "error"
    matrix_msg: str = ""
    matrix_count: int = 0

    planning_status: str = ""
    planning_msg: str = ""
    planning_count: int = 0

    async def handle_matrix_upload(self, files: list[rx.UploadFile]):
        if not files:
            self.matrix_status = "error"
            self.matrix_msg = "Aucun fichier sélectionné."
            return
        self.matrix_status = "loading"
        self.matrix_msg = "Import en cours..."
        yield

        try:
            import openpyxl
            data = await files[0].read()
            wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            entries = _parse_escalade_matrix(wb)
            if not entries:
                self.matrix_status = "error"
                self.matrix_msg = "Aucune entrée trouvée. Vérifiez l'onglet 'Matrice de Production'."
                return
            db = load_db()
            db["escalation_matrix"] = entries
            save_db(db)
            self.matrix_count = len(entries)
            self.matrix_status = "success"
            self.matrix_msg = f"{len(entries)} entrées importées dans la matrice d'escalade."
        except Exception as e:
            self.matrix_status = "error"
            self.matrix_msg = f"Erreur : {str(e)}"

    async def handle_planning_upload(self, files: list[rx.UploadFile]):
        if not files:
            self.planning_status = "error"
            self.planning_msg = "Aucun fichier sélectionné."
            return
        self.planning_status = "loading"
        self.planning_msg = "Import en cours..."
        yield

        try:
            import openpyxl
            data = await files[0].read()
            wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            entries = _parse_planning(wb)
            if not entries:
                self.planning_status = "error"
                self.planning_msg = "Aucune entrée trouvée. Vérifiez l'onglet 'planning (TEST)'."
                return
            db = load_db()
            db["planning"] = entries
            save_db(db)
            self.planning_count = len(entries)
            self.planning_status = "success"
            self.planning_msg = f"{len(entries)} entrées importées dans le planning."
        except Exception as e:
            self.planning_status = "error"
            self.planning_msg = f"Erreur : {str(e)}"


def _status_box(status, msg) -> rx.Component:
    return rx.cond(
        status != "",
        rx.box(
            rx.hstack(
                rx.cond(
                    status == "success",
                    rx.icon("check-circle", size=16, color="#22c55e"),
                    rx.cond(
                        status == "loading",
                        rx.icon("loader", size=16, color=MUTED),
                        rx.icon("x-circle", size=16, color="#ef4444"),
                    ),
                ),
                rx.text(msg, font_size="0.82rem", color=rx.cond(status == "success", "#86efac", rx.cond(status == "loading", MUTED, "#fca5a5"))),
                spacing="2", align="center",
            ),
            background=rx.cond(
                status == "success", "rgba(34,197,94,0.08)",
                rx.cond(status == "loading", "rgba(100,116,139,0.08)", "rgba(239,68,68,0.08)")
            ),
            border=rx.cond(
                status == "success", "1px solid rgba(34,197,94,0.25)",
                rx.cond(status == "loading", f"1px solid {BORDER}", "1px solid rgba(239,68,68,0.25)")
            ),
            border_radius="8px",
            padding="10px 14px",
            margin_top="0.5rem",
        ),
    )


def _upload_card(
    title: str,
    icon: str,
    accent: str,
    upload_id: str,
    handler,
    status,
    msg,
) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.icon(icon, size=20, color=accent),
                    background=f"rgba(99,102,241,0.1)",
                    border_radius="8px",
                    padding="8px",
                ),
                rx.vstack(
                    rx.text(title, color=TEXT, font_weight="700", font_size="0.95rem"),
                    rx.text(
                        rx.cond(upload_id == "matrix_upload", "Onglet : Matrice de Production", "Onglet : planning (TEST)"),
                        color=MUTED, font_size="0.75rem",
                    ),
                    spacing="0", align="start",
                ),
                spacing="3", align="center",
            ),
            rx.divider(border_color=BORDER),
            rx.upload(
                rx.box(
                    rx.icon("upload", size=28, color=MUTED),
                    rx.text("Glisser-déposer un fichier Excel", color=MUTED, font_size="0.82rem", margin_top="0.5rem"),
                    rx.text(".xlsx, .xls, .xlsm", color="#334155", font_size="0.72rem"),
                    display="flex",
                    flex_direction="column",
                    align_items="center",
                    padding="1.5rem",
                ),
                id=upload_id,
                accept={"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx", ".xls", ".xlsm"]},
                max_files=1,
                border=f"2px dashed {BORDER}",
                border_radius="10px",
                _hover={"border_color": accent, "cursor": "pointer"},
                width="100%",
            ),
            rx.button(
                rx.icon("download", size=16),
                "Importer",
                on_click=handler(rx.upload_files(upload_id=upload_id)),
                background=f"linear-gradient(135deg, {accent}, {accent}cc)",
                color="white",
                border_radius="8px",
                padding="9px 18px",
                font_size="0.85rem",
                font_weight="600",
                cursor="pointer",
                width="100%",
                spacing="2",
                _hover={"opacity": "0.85"},
            ),
            _status_box(status, msg),
            spacing="3",
            width="100%",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_top=f"3px solid {accent}",
        border_radius="14px",
        padding="1.25rem",
        flex="1",
        min_width="280px",
    )


def import_excel_content() -> rx.Component:
    return rx.vstack(
        rx.text(
            "Importez vos fichiers Excel pour mettre à jour la matrice d'escalade ou le planning.",
            color=MUTED, font_size="0.875rem",
        ),
        rx.hstack(
            _upload_card(
                "Matrice d'escalade",
                "git-branch",
                "#9333ea",
                "matrix_upload",
                ImportExcelState.handle_matrix_upload,
                ImportExcelState.matrix_status,
                ImportExcelState.matrix_msg,
            ),
            _upload_card(
                "Planning",
                "calendar-days",
                "#059669",
                "planning_upload",
                ImportExcelState.handle_planning_upload,
                ImportExcelState.planning_status,
                ImportExcelState.planning_msg,
            ),
            spacing="4",
            width="100%",
            wrap="wrap",
            align="start",
        ),
        rx.box(
            rx.text("Format attendu", color=TEXT, font_weight="600", font_size="0.85rem", margin_bottom="0.5rem"),
            rx.vstack(
                rx.hstack(rx.icon("git-branch", size=14, color="#c4b5fd"), rx.text("Matrice : fichier avec un onglet contenant 'Matrice de Production' — colonnes Périmètre, Typologie, Traitement N1, etc.", color=MUTED, font_size="0.78rem"), spacing="2", align="center"),
                rx.hstack(rx.icon("calendar-days", size=14, color="#6ee7b7"), rx.text("Planning : fichier avec un onglet 'planning (TEST)' — colonnes Semaine, noms des techniciens en lignes.", color=MUTED, font_size="0.78rem"), spacing="2", align="center"),
                spacing="2",
            ),
            background="#10121f",
            border=f"1px solid {BORDER}",
            border_radius="10px",
            padding="1rem",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def import_excel_page() -> rx.Component:
    return page_layout(import_excel_content(), "Import Excel")
