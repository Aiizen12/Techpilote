import uuid
from datetime import datetime
import reflex as rx

from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
from techpilot.db.activity import log_activity
from techpilot.state.auth import AuthState
from techpilot.state.models import MigrationTask

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
CARD_BG = "#111524"
BORDER  = "#1c2138"
PRIMARY = "#6366f1"

COLUMNS = [
    {"statut": "idee",     "label": "Idées",    "color": "#f59e0b", "icon": "lightbulb"},
    {"statut": "en_cours", "label": "En cours", "color": "#3b82f6", "icon": "loader-circle"},
    {"statut": "realise",  "label": "Réalisés", "color": "#22c55e", "icon": "circle-check"},
]

PRIO_COLORS = {
    "haute":   "#ef4444",
    "normale": "#6366f1",
    "basse":   "#94a3b8",
}
PRIO_LABELS = {"haute": "Haute", "normale": "Normale", "basse": "Basse"}

STATUTS = ["idee", "en_cours", "realise"]


class MigrationState(rx.State):
    tasks: list[MigrationTask] = []

    # Formulaire add/edit
    show_form: bool = False
    edit_id: str = ""
    form_titre: str = ""
    form_desc: str = ""
    form_statut: str = "idee"
    form_priorite: str = "normale"

    def load(self):
        db = load_db()
        raw = db.get("migration_tasks") or []
        self.tasks = [MigrationTask(**t) for t in raw]

    def _save_all(self):
        db = load_db()
        db["migration_tasks"] = [t.dict() for t in self.tasks]
        save_db(db)

    # ── Formulaire ────────────────────────────────────────────────────────────

    def open_add_form(self, statut: str):
        self.edit_id    = ""
        self.form_titre = ""
        self.form_desc  = ""
        self.form_statut   = statut
        self.form_priorite = "normale"
        self.show_form  = True

    def open_edit_form(self, task_id: str):
        task = next((t for t in self.tasks if t.id == task_id), None)
        if not task:
            return
        self.edit_id       = task.id
        self.form_titre    = task.titre
        self.form_desc     = task.description
        self.form_statut   = task.statut
        self.form_priorite = task.priorite
        self.show_form     = True

    def close_form(self):
        self.show_form = False

    def set_form_titre(self, v: str):
        self.form_titre = v

    def set_form_desc(self, v: str):
        self.form_desc = v

    def set_form_statut(self, v: str):
        self.form_statut = v

    def set_form_priorite(self, v: str):
        self.form_priorite = v

    def save_task(self):
        titre = self.form_titre.strip()
        if not titre:
            return
        if self.edit_id:
            for t in self.tasks:
                if t.id == self.edit_id:
                    t.titre       = titre
                    t.description = self.form_desc.strip()
                    t.statut      = self.form_statut
                    t.priorite    = self.form_priorite
                    break
        else:
            self.tasks.append(MigrationTask(
                id=str(uuid.uuid4()),
                titre=titre,
                description=self.form_desc.strip(),
                statut=self.form_statut,
                date_creation=datetime.now().strftime("%d/%m/%Y"),
                priorite=self.form_priorite,
            ))
        self._save_all()
        self.show_form = False

    # ── Actions ───────────────────────────────────────────────────────────────

    def delete_task(self, task_id: str):
        self.tasks = [t for t in self.tasks if t.id != task_id]
        self._save_all()

    def move_task(self, task_id: str, direction: int):
        for t in self.tasks:
            if t.id == task_id:
                idx = STATUTS.index(t.statut)
                new_idx = max(0, min(len(STATUTS) - 1, idx + direction))
                t.statut = STATUTS[new_idx]
                break
        self._save_all()


# ── Composants ────────────────────────────────────────────────────────────────

def _prio_badge(prio: str) -> rx.Component:
    return rx.box(
        rx.text(
            rx.cond(prio == "haute", "Haute", rx.cond(prio == "normale", "Normale", "Basse")),
            font_size="0.65rem", font_weight="600",
            color=rx.cond(prio == "haute", "#fca5a5",
                  rx.cond(prio == "normale", "#a5b4fc", MUTED)),
        ),
        background=rx.cond(prio == "haute", "rgba(239,68,68,0.12)",
                   rx.cond(prio == "normale", "rgba(99,102,241,0.12)", "rgba(148,163,184,0.08)")),
        border=rx.cond(prio == "haute", "1px solid rgba(239,68,68,0.3)",
               rx.cond(prio == "normale", "1px solid rgba(99,102,241,0.3)", f"1px solid {BORDER}")),
        border_radius="4px",
        padding="1px 6px",
    )


def _task_card(task: MigrationTask, col_idx: int) -> rx.Component:
    return rx.box(
        rx.vstack(
            # En-tête : titre + actions
            rx.hstack(
                rx.text(
                    task["titre"],
                    font_size="0.83rem",
                    font_weight="600",
                    color=TEXT,
                    flex="1",
                    min_width="0",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                    cursor="pointer",
                    on_click=MigrationState.open_edit_form(task["id"]),
                    _hover={"color": "#a5b4fc"},
                ),
                # Bouton déplacer ←
                rx.cond(
                    col_idx > 0,
                    rx.icon_button(
                        rx.icon("chevron-left", size=12),
                        on_click=MigrationState.move_task(task["id"], -1),
                        background="transparent", color=MUTED, border="none", size="1",
                        cursor="pointer",
                        _hover={"color": TEXT, "background": "rgba(255,255,255,0.08)"},
                    ),
                ),
                # Bouton déplacer →
                rx.cond(
                    col_idx < 2,
                    rx.icon_button(
                        rx.icon("chevron-right", size=12),
                        on_click=MigrationState.move_task(task["id"], 1),
                        background="transparent", color=MUTED, border="none", size="1",
                        cursor="pointer",
                        _hover={"color": TEXT, "background": "rgba(255,255,255,0.08)"},
                    ),
                ),
                # Supprimer
                rx.icon_button(
                    rx.icon("x", size=11),
                    on_click=MigrationState.delete_task(task["id"]),
                    background="transparent", color="rgba(148,163,184,0.25)", border="none", size="1",
                    cursor="pointer",
                    _hover={"color": "#ef4444", "background": "rgba(239,68,68,0.12)"},
                ),
                spacing="1",
                align="center",
                width="100%",
            ),
            # Description (si présente)
            rx.cond(
                task["description"] != "",
                rx.text(
                    task["description"],
                    font_size="0.74rem",
                    color=MUTED,
                    line_height="1.5",
                    overflow="hidden",
                    display="-webkit-box",
                    style={"-webkit-line-clamp": "2", "-webkit-box-orient": "vertical"},
                ),
            ),
            # Pied : priorité + date
            rx.hstack(
                _prio_badge(task["priorite"]),
                rx.spacer(),
                rx.cond(
                    task["date_creation"] != "",
                    rx.text(task["date_creation"], font_size="0.65rem", color=MUTED),
                ),
                width="100%",
                align="center",
            ),
            spacing="2",
            width="100%",
            align="start",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="10px",
        padding="0.75rem",
        width="100%",
        transition="all 0.12s",
        _hover={"border_color": "rgba(99,102,241,0.4)", "background": "rgba(99,102,241,0.03)"},
    )


def _column(col: dict, tasks: list, col_idx: int) -> rx.Component:
    color = col["color"]
    return rx.box(
        rx.vstack(
            # En-tête colonne
            rx.hstack(
                rx.box(
                    rx.icon(col["icon"], size=14, color=color),
                    background=f"rgba(99,102,241,0.08)",
                    border_radius="6px",
                    padding="5px",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.text(col["label"], color=TEXT, font_size="0.88rem", font_weight="700"),
                rx.box(
                    rx.text(
                        str(len(tasks)),
                        font_size="0.72rem", font_weight="700",
                        color=color,
                    ),
                    background=f"rgba(99,102,241,0.08)",
                    border=f"1px solid {BORDER}",
                    border_radius="20px",
                    padding="1px 8px",
                ),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("plus", size=14),
                    on_click=MigrationState.open_add_form(col["statut"]),
                    background="transparent",
                    color=MUTED,
                    border="none",
                    size="1",
                    cursor="pointer",
                    _hover={"color": color, "background": f"rgba(99,102,241,0.1)"},
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.divider(border_color=f"rgba(99,102,241,0.15)"),
            # Cartes
            rx.vstack(
                rx.foreach(tasks, lambda t: _task_card(t, col_idx)),
                spacing="2",
                width="100%",
                align="start",
            ),
            rx.cond(
                len(tasks) == 0,
                rx.box(
                    rx.text("Aucune tâche", color=MUTED, font_size="0.78rem"),
                    text_align="center",
                    padding="1.5rem 0",
                    width="100%",
                ),
            ),
            spacing="3",
            width="100%",
            align="start",
        ),
        background="#0d1021",
        border=f"1px solid {BORDER}",
        border_top=f"3px solid {color}",
        border_radius="14px",
        padding="1rem",
        flex="1",
        min_width="260px",
    )


def _form_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Titre modal
                rx.hstack(
                    rx.icon(
                        rx.cond(MigrationState.edit_id != "", "pencil", "plus"),
                        size=16, color="#a5b4fc",
                    ),
                    rx.text(
                        rx.cond(MigrationState.edit_id != "", "Modifier la tâche", "Nouvelle tâche"),
                        color=TEXT, font_size="1rem", font_weight="700",
                    ),
                    spacing="2", align="center",
                ),
                rx.divider(border_color=BORDER),

                # Titre
                rx.vstack(
                    rx.text("Titre", color=MUTED, font_size="0.78rem", font_weight="600"),
                    rx.input(
                        placeholder="Titre de la tâche…",
                        value=MigrationState.form_titre,
                        on_change=MigrationState.set_form_titre,
                        background="#0d1021", color=TEXT,
                        border=f"1px solid {BORDER}",
                        border_radius="8px",
                        _focus={"border_color": PRIMARY, "outline": "none"},
                        width="100%",
                    ),
                    spacing="1", width="100%", align="start",
                ),

                # Description
                rx.vstack(
                    rx.text("Description", color=MUTED, font_size="0.78rem", font_weight="600"),
                    rx.text_area(
                        placeholder="Détails optionnels…",
                        value=MigrationState.form_desc,
                        on_change=MigrationState.set_form_desc,
                        background="#0d1021", color=TEXT,
                        border=f"1px solid {BORDER}",
                        border_radius="8px",
                        rows="3",
                        resize="vertical",
                        _focus={"border_color": PRIMARY, "outline": "none"},
                        width="100%",
                    ),
                    spacing="1", width="100%", align="start",
                ),

                # Statut + Priorité
                rx.hstack(
                    rx.vstack(
                        rx.text("Colonne", color=MUTED, font_size="0.78rem", font_weight="600"),
                        rx.select(
                            ["idee", "en_cours", "realise"],
                            value=MigrationState.form_statut,
                            on_change=MigrationState.set_form_statut,
                            background="#0d1021", color=TEXT,
                            border=f"1px solid {BORDER}",
                        ),
                        spacing="1", align="start", flex="1",
                    ),
                    rx.vstack(
                        rx.text("Priorité", color=MUTED, font_size="0.78rem", font_weight="600"),
                        rx.select(
                            ["basse", "normale", "haute"],
                            value=MigrationState.form_priorite,
                            on_change=MigrationState.set_form_priorite,
                            background="#0d1021", color=TEXT,
                            border=f"1px solid {BORDER}",
                        ),
                        spacing="1", align="start", flex="1",
                    ),
                    spacing="3", width="100%",
                ),

                # Boutons
                rx.hstack(
                    rx.button(
                        "Annuler",
                        on_click=MigrationState.close_form,
                        background="rgba(255,255,255,0.06)",
                        color=MUTED, border_radius="8px",
                        cursor="pointer",
                        _hover={"background": "rgba(255,255,255,0.1)"},
                    ),
                    rx.button(
                        rx.icon("save", size=14),
                        rx.cond(MigrationState.edit_id != "", "Enregistrer", "Ajouter"),
                        on_click=MigrationState.save_task,
                        background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                        color="white", border_radius="8px",
                        cursor="pointer", spacing="2",
                        _hover={"opacity": "0.88"},
                    ),
                    spacing="3", justify="end", width="100%",
                ),

                spacing="4", width="100%",
            ),
            background="#111524",
            border=f"1px solid {BORDER}",
            border_radius="16px",
            padding="1.5rem",
            max_width="480px",
            width="95vw",
        ),
        open=MigrationState.show_form,
        on_open_change=MigrationState.close_form,
    )


def _tasks_for_col(tasks: list[MigrationTask], statut: str) -> list[MigrationTask]:
    return [t for t in tasks if t.statut == statut]


def migration_content() -> rx.Component:
    idees    = MigrationState.tasks.filter(lambda t: t["statut"] == "idee")
    en_cours = MigrationState.tasks.filter(lambda t: t["statut"] == "en_cours")
    realises = MigrationState.tasks.filter(lambda t: t["statut"] == "realise")

    return rx.vstack(
        _form_modal(),

        # En-tête
        rx.hstack(
            rx.hstack(
                rx.box(
                    rx.icon("git-branch", size=20, color="white"),
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    border_radius="10px", padding="8px",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.vstack(
                    rx.text("Migration Loop → Drive", color=TEXT, font_size="1.1rem", font_weight="700"),
                    rx.text("Suivi des tâches de migration", color=MUTED, font_size="0.78rem"),
                    spacing="0", align="start",
                ),
                spacing="3", align="center",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=15),
                "Ajouter une tâche",
                on_click=MigrationState.open_add_form("idee"),
                background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                color="white", border_radius="10px",
                padding="8px 16px", font_size="0.85rem", font_weight="600",
                cursor="pointer", spacing="2",
                _hover={"opacity": "0.88"},
            ),
            width="100%", align="center",
        ),

        # Kanban
        rx.hstack(
            _column(COLUMNS[0], idees,    0),
            _column(COLUMNS[1], en_cours, 1),
            _column(COLUMNS[2], realises, 2),
            spacing="4",
            width="100%",
            align="start",
            wrap="wrap",
        ),

        spacing="5",
        width="100%",
        on_mount=[AuthState.require_manager, MigrationState.load],
    )


def migration_page() -> rx.Component:
    return page_layout(migration_content(), "Migration Loop → Drive")
