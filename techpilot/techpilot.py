import os
import reflex as rx

from techpilot.db.database import init_db

from techpilot.pages.login import login_page
from techpilot.pages.dashboard import dashboard_page
from techpilot.pages.planning import planning_page
from techpilot.pages.escalade import escalade_page
from techpilot.pages.tickets import tickets_page
from techpilot.pages.documents import documents_page
from techpilot.pages.techniciens import techniciens_page
from techpilot.pages.actualites import actualites_page
from techpilot.pages.feedbacks import feedbacks_page
from techpilot.pages.permissions import permissions_page
from techpilot.pages.audit import audit_page
from techpilot.pages.import_excel import import_excel_page
from techpilot.pages.quetes import quetes_page

# Initialisation DB
init_db()


def index() -> rx.Component:
    return rx.box(on_mount=rx.redirect("/login"))


app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="indigo",
        radius="medium",
    ),
    style={
        "font_family": "'Inter', 'Segoe UI', system-ui, sans-serif",
        "background_color": "#0d0f1a",
    },
)

app.add_page(index,            route="/")
app.add_page(login_page,       route="/login")
app.add_page(dashboard_page,   route="/dashboard")
app.add_page(planning_page,    route="/planning")
app.add_page(escalade_page,    route="/escalade")
app.add_page(tickets_page,     route="/tickets")
app.add_page(documents_page,   route="/documents")
app.add_page(techniciens_page, route="/techniciens")
app.add_page(actualites_page,  route="/actualites")
app.add_page(feedbacks_page,   route="/feedbacks")
app.add_page(permissions_page, route="/permissions")
app.add_page(audit_page,       route="/audit")
app.add_page(import_excel_page, route="/import-excel")
app.add_page(quetes_page,      route="/quetes")


@app.api.post("/sync-matrix")
async def sync_matrix(request):
    """Endpoint appelé par Apps Script pour pousser la matrice d'escalade."""
    from fastapi import HTTPException
    from fastapi.responses import JSONResponse

    secret = os.getenv("SYNC_SECRET", "")
    body = await request.json()

    if not secret or body.get("token") != secret:
        raise HTTPException(status_code=401, detail="Unauthorized")

    rows = body.get("values", [])
    if len(rows) < 2:
        return JSONResponse({"ok": False, "msg": "No data"})

    from techpilot.db.sync_sheets import _parse_rows
    from techpilot.db.database import load_db, save_db

    entries = _parse_rows(rows)
    if not entries:
        return JSONResponse({"ok": False, "msg": "No entries parsed"})

    db = load_db()
    db["escalation_matrix"] = entries
    save_db(db)

    return JSONResponse({"ok": True, "msg": f"{len(entries)} entrees synchronisees"})
