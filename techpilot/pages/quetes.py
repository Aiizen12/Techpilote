import uuid
import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
from techpilot.state.auth import AuthState
from techpilot.state.models import QueteItem, LeaderboardEntry, PendingValidation

TEXT = "#e2e8f0"; MUTED = "#64748b"; CARD_BG = "#151728"; BORDER = "#1e2235"; PRIMARY = "#6366f1"

DEFAULT_QUETES = [
    {"titre": "Veilleur de l'Aube",    "description": "Connecte-toi avant 9h",                             "type": "quotidienne",  "categorie": "general",       "xp": 20,   "objectif": 1,  "unite": "connexion",  "difficulte": "E",  "icone": "🌅"},
    {"titre": "Chasseur de Tickets",   "description": "Traiter 5 tickets dans la journée",                 "type": "quotidienne",  "categorie": "tickets",       "xp": 50,   "objectif": 5,  "unite": "ticket",     "difficulte": "D",  "icone": "🎯"},
    {"titre": "Gardien du Rang",       "description": "Aucune escalade non justifiée de la journée",       "type": "quotidienne",  "categorie": "escalade",      "xp": 75,   "objectif": 1,  "unite": "jour",       "difficulte": "C",  "icone": "🛡️"},
    {"titre": "Semaine du Guerrier",   "description": "Présent toute la semaine sans absence",             "type": "hebdomadaire", "categorie": "general",       "xp": 150,  "objectif": 5,  "unite": "jour",       "difficulte": "D",  "icone": "⚔️"},
    {"titre": "Encyclopédiste",        "description": "Documenter une procédure sur Mayday",               "type": "hebdomadaire", "categorie": "documentation", "xp": 200,  "objectif": 1,  "unite": "procédure",  "difficulte": "C",  "icone": "📖"},
    {"titre": "Mentor du Donjon",      "description": "Former un collègue sur un outil ou une procédure", "type": "hebdomadaire", "categorie": "formation",     "xp": 300,  "objectif": 1,  "unite": "formation",  "difficulte": "B",  "icone": "🧑‍🏫"},
    {"titre": "Vingt Tickets",         "description": "Résoudre 20 tickets cette semaine",                 "type": "hebdomadaire", "categorie": "tickets",       "xp": 250,  "objectif": 20, "unite": "ticket",     "difficulte": "B",  "icone": "💪"},
    {"titre": "Premier Sang",          "description": "Résoudre ton premier ticket",                       "type": "achievement",  "categorie": "tickets",       "xp": 50,   "objectif": 1,  "unite": "ticket",     "difficulte": "E",  "icone": "🩸"},
    {"titre": "Série Parfaite",        "description": "5 tickets résolus sans escalade",                   "type": "achievement",  "categorie": "escalade",      "xp": 150,  "objectif": 5,  "unite": "ticket",     "difficulte": "D",  "icone": "✨"},
    {"titre": "Encyclopédie Vivante",  "description": "10 procédures documentées sur Mayday",              "type": "achievement",  "categorie": "documentation", "xp": 500,  "objectif": 10, "unite": "procédure",  "difficulte": "A",  "icone": "📚"},
    {"titre": "Astreinte Accomplie",   "description": "Effectuer sa première astreinte",                   "type": "achievement",  "categorie": "astreinte",     "xp": 100,  "objectif": 1,  "unite": "astreinte",  "difficulte": "D",  "icone": "🌙"},
    {"titre": "Maître N1",             "description": "Avoir validé 50 quêtes au total",                   "type": "achievement",  "categorie": "general",       "xp": 1000, "objectif": 50, "unite": "quête",      "difficulte": "S",  "icone": "👑"},
]


# ── Helpers XP ────────────────────────────────────────────────────────────────

def _xp_for_next(level: int) -> int:
    return int(100 * (1.5 ** (level - 1)))

def _level_from_xp(total_xp: int):
    level, xp = 1, total_xp
    while xp >= _xp_for_next(level):
        xp -= _xp_for_next(level)
        level += 1
    return level, xp, _xp_for_next(level)

def _rank_from_level(level: int) -> str:
    if level >= 25: return "SS"
    if level >= 20: return "S"
    if level >= 15: return "A"
    if level >= 10: return "B"
    if level >= 7:  return "C"
    if level >= 4:  return "D"
    return "E"

def _init_quetes(db: dict):
    if not db.get("quetes"):
        db["quetes"] = [{"id": str(uuid.uuid4()), "actif": True, "created_by": "system",
                         "date_creation": "", **q} for q in DEFAULT_QUETES]
        if "quetes_progress" not in db:
            db["quetes_progress"] = []
        save_db(db)


# ── State ─────────────────────────────────────────────────────────────────────

class QuetesState(rx.State):
    quetes: list[QueteItem] = []
    leaderboard: list[LeaderboardEntry] = []
    pending: list[PendingValidation] = []

    tab: str = "quotidienne"

    my_total_xp: int = 0
    my_level: int = 1
    my_current_xp: int = 0
    my_next_xp: int = 100
    my_rank: str = "E"
    my_quetes_validees: int = 0

    prog_input: str = "0"
    prog_quete_id: str = ""

    show_create: bool = False
    create_form: dict = {
        "titre": "", "description": "", "type": "quotidienne",
        "categorie": "general", "xp": "50", "objectif": "1",
        "unite": "action", "difficulte": "D", "icone": "🎯",
    }

    async def load(self):
        auth = await self.get_state(AuthState)
        user_id = auth.user_id
        is_manager = auth.user_role == "manager"
        db = load_db()
        _init_quetes(db)
        self._refresh_quetes(db, user_id)
        self._refresh_leaderboard(db)
        self._refresh_stats(db, user_id)
        if is_manager:
            self._refresh_pending(db)

    def _refresh_quetes(self, db: dict, user_id: str):
        progress = db.get("quetes_progress") or []
        filtered = [q for q in (db.get("quetes") or []) if q.get("actif") and q.get("type") == self.tab]
        items = []
        for q in filtered:
            prog = next((p for p in progress if p.get("quete_id") == q["id"] and p.get("user_id") == user_id), None)
            items.append(QueteItem(
                id=str(q.get("id") or ""),
                titre=q.get("titre") or "",
                description=q.get("description") or "",
                type=q.get("type") or "",
                categorie=q.get("categorie") or "",
                xp=int(q.get("xp") or 0),
                objectif=int(q.get("objectif") or 1),
                unite=q.get("unite") or "",
                difficulte=q.get("difficulte") or "E",
                icone=q.get("icone") or "🎯",
                prog_progres=int(prog.get("progres") or 0) if prog else 0,
                prog_statut=prog.get("statut") or "en_cours" if prog else "en_cours",
                has_prog=prog is not None,
            ))
        self.quetes = items

    def _refresh_leaderboard(self, db: dict):
        techs = db.get("technicians") or []
        progress = db.get("quetes_progress") or []
        quetes = db.get("quetes") or []
        board = []
        for t in techs:
            uid = str(t.get("id") or "")
            validated = [p for p in progress if p.get("user_id") == uid and p.get("statut") == "valide"]
            total_xp = sum(
                int((next((q for q in quetes if q.get("id") == p.get("quete_id")), {}) or {}).get("xp") or 0)
                for p in validated
            )
            level, _, _ = _level_from_xp(total_xp)
            board.append(LeaderboardEntry(
                user_id=uid,
                nom=t.get("nom") or "",
                color=t.get("color") or PRIMARY,
                total_xp=total_xp,
                level=level,
                rank=_rank_from_level(level),
                quetes_validees=len(validated),
                position=0,
            ))
        board.sort(key=lambda x: x.total_xp, reverse=True)
        for i, entry in enumerate(board):
            entry.position = i + 1
        self.leaderboard = board

    def _refresh_stats(self, db: dict, user_id: str):
        progress = db.get("quetes_progress") or []
        quetes = db.get("quetes") or []
        validated = [p for p in progress if p.get("user_id") == user_id and p.get("statut") == "valide"]
        total_xp = sum(
            int((next((q for q in quetes if q.get("id") == p.get("quete_id")), {}) or {}).get("xp") or 0)
            for p in validated
        )
        level, cur, nxt = _level_from_xp(total_xp)
        self.my_total_xp = total_xp
        self.my_level = level
        self.my_current_xp = cur
        self.my_next_xp = nxt
        self.my_rank = _rank_from_level(level)
        self.my_quetes_validees = len(validated)

    def _refresh_pending(self, db: dict):
        progress = db.get("quetes_progress") or []
        quetes = db.get("quetes") or []
        techs = db.get("technicians") or []
        pending = []
        for p in progress:
            if p.get("statut") == "complete":
                q = next((x for x in quetes if x.get("id") == p.get("quete_id")), None)
                t = next((x for x in techs if str(x.get("id")) == str(p.get("user_id"))), None)
                if q:
                    pending.append(PendingValidation(
                        quete_id=str(p.get("quete_id") or ""),
                        quete_titre=q.get("titre") or "",
                        quete_icone=q.get("icone") or "🎯",
                        xp=int(q.get("xp") or 0),
                        user_id=str(p.get("user_id") or ""),
                        user_nom=t.get("nom") if t else str(p.get("user_id") or ""),
                    ))
        self.pending = pending

    async def set_tab(self, tab: str):
        self.tab = tab
        auth = await self.get_state(AuthState)
        db = load_db()
        self._refresh_quetes(db, auth.user_id)

    async def mark_done(self, quete_id: str):
        auth = await self.get_state(AuthState)
        user_id = auth.user_id
        db = load_db()
        if "quetes_progress" not in db:
            db["quetes_progress"] = []
        quete = next((q for q in db.get("quetes", []) if q["id"] == quete_id), None)
        if not quete:
            return
        prog = next((p for p in db["quetes_progress"] if p.get("quete_id") == quete_id and p.get("user_id") == user_id), None)
        if prog:
            prog["progres"] = quete["objectif"]
            prog["statut"] = "complete"
        else:
            db["quetes_progress"].append({
                "id": str(uuid.uuid4()), "quete_id": quete_id, "user_id": user_id,
                "progres": quete["objectif"], "statut": "complete",
            })
        save_db(db)
        self._refresh_quetes(db, user_id)
        self._refresh_stats(db, user_id)

    def set_prog_input(self, val: str):
        self.prog_input = val

    def open_prog(self, quete_id: str, current: int):
        self.prog_quete_id = quete_id
        self.prog_input = str(current)

    async def update_progress(self):
        auth = await self.get_state(AuthState)
        user_id = auth.user_id
        db = load_db()
        if "quetes_progress" not in db:
            db["quetes_progress"] = []
        quete = next((q for q in db.get("quetes", []) if q["id"] == self.prog_quete_id), None)
        if not quete:
            return
        try:
            val = max(0, min(int(self.prog_input), quete["objectif"]))
        except ValueError:
            return
        statut = "complete" if val >= quete["objectif"] else "en_cours"
        prog = next((p for p in db["quetes_progress"] if p.get("quete_id") == self.prog_quete_id and p.get("user_id") == user_id), None)
        if prog:
            prog["progres"] = val
            prog["statut"] = statut
        else:
            db["quetes_progress"].append({
                "id": str(uuid.uuid4()), "quete_id": self.prog_quete_id,
                "user_id": user_id, "progres": val, "statut": statut,
            })
        save_db(db)
        self.prog_quete_id = ""
        self._refresh_quetes(db, user_id)
        self._refresh_stats(db, user_id)

    def validate_quete(self, quete_id: str, user_id: str):
        db = load_db()
        prog = next((p for p in db.get("quetes_progress", []) if p.get("quete_id") == quete_id and p.get("user_id") == user_id), None)
        if prog:
            prog["statut"] = "valide"
        save_db(db)
        self._refresh_pending(db)
        self._refresh_leaderboard(db)

    def reject_quete(self, quete_id: str, user_id: str):
        db = load_db()
        prog = next((p for p in db.get("quetes_progress", []) if p.get("quete_id") == quete_id and p.get("user_id") == user_id), None)
        if prog:
            prog["statut"] = "refuse"
        save_db(db)
        self._refresh_pending(db)

    def open_create(self):
        self.create_form = {
            "titre": "", "description": "", "type": "quotidienne",
            "categorie": "general", "xp": "50", "objectif": "1",
            "unite": "action", "difficulte": "D", "icone": "🎯",
        }
        self.show_create = True

    def close_create(self):
        self.show_create = False

    def set_create_field(self, f: str, v: str):
        self.create_form = {**self.create_form, f: v}

    async def save_create(self):
        if not self.create_form.get("titre"):
            return
        db = load_db()
        if "quetes" not in db:
            db["quetes"] = []
        db["quetes"].append({
            "id": str(uuid.uuid4()), "actif": True, "created_by": "manager", "date_creation": "",
            "titre": self.create_form.get("titre") or "",
            "description": self.create_form.get("description") or "",
            "type": self.create_form.get("type") or "quotidienne",
            "categorie": self.create_form.get("categorie") or "general",
            "xp": int(self.create_form.get("xp") or 50),
            "objectif": int(self.create_form.get("objectif") or 1),
            "unite": self.create_form.get("unite") or "action",
            "difficulte": self.create_form.get("difficulte") or "D",
            "icone": self.create_form.get("icone") or "🎯",
        })
        save_db(db)
        self.show_create = False
        auth = await self.get_state(AuthState)
        self._refresh_quetes(db, auth.user_id)


# ── Composants visuels ────────────────────────────────────────────────────────

def rank_badge(rank, size: str = "md") -> rx.Component:
    sizes = {"sm": ("22px", "0.62rem"), "md": ("34px", "0.8rem"), "lg": ("50px", "1.1rem")}
    w, fs = sizes.get(size, ("34px", "0.8rem"))
    color = rx.match(rank, ("E","#6b7280"),("D","#22c55e"),("C","#3b82f6"),("B","#a855f7"),("A","#f59e0b"),("S","#ef4444"),("SS","#f97316"),"#6b7280")
    bg    = rx.match(rank, ("E","rgba(107,114,128,0.15)"),("D","rgba(34,197,94,0.15)"),("C","rgba(59,130,246,0.15)"),("B","rgba(168,85,247,0.15)"),("A","rgba(245,158,11,0.15)"),("S","rgba(239,68,68,0.15)"),("SS","rgba(249,115,22,0.15)"),"rgba(107,114,128,0.15)")
    brd   = rx.match(rank, ("E","1.5px solid rgba(107,114,128,0.5)"),("D","1.5px solid rgba(34,197,94,0.5)"),("C","1.5px solid rgba(59,130,246,0.5)"),("B","1.5px solid rgba(168,85,247,0.5)"),("A","1.5px solid rgba(245,158,11,0.5)"),("S","1.5px solid rgba(239,68,68,0.5)"),("SS","1.5px solid rgba(249,115,22,0.5)"),"1.5px solid rgba(107,114,128,0.5)")
    return rx.box(rx.text(rank, color=color, font_weight="900", font_size=fs), width=w, height=w, background=bg, border=brd, border_radius="7px", display="flex", align_items="center", justify_content="center", flex_shrink="0")


def diff_color(diff) -> rx.Component:
    return rx.match(diff, ("E","#6b7280"),("D","#22c55e"),("C","#3b82f6"),("B","#a855f7"),("A","#f59e0b"),("S","#ef4444"),("SS","#f97316"),"#6b7280")


def statut_badge(statut) -> rx.Component:
    return rx.match(
        statut,
        ("valide",   rx.badge("✅ Validé",               color_scheme="green", variant="soft", radius="full", font_size="0.68rem")),
        ("complete", rx.badge("⏳ En attente validation", color_scheme="amber", variant="soft", radius="full", font_size="0.68rem")),
        ("refuse",   rx.badge("❌ Refusé",                color_scheme="gray",  variant="soft", radius="full", font_size="0.68rem")),
        rx.badge("En cours", color_scheme="blue", variant="soft", radius="full", font_size="0.68rem"),
    )


# ── Carte quête ───────────────────────────────────────────────────────────────

def quete_card(q: QueteItem) -> rx.Component:
    border_c = diff_color(q["difficulte"])
    is_valide  = q["prog_statut"] == "valide"
    is_refuse  = q["prog_statut"] == "refuse"
    is_complete = q["prog_statut"] == "complete"
    is_en_cours = q["prog_statut"] == "en_cours"
    show_done = (q["objectif"] == 1) & is_en_cours
    show_multi = (q["objectif"] > 1) & is_en_cours

    pct = rx.cond(
        q["objectif"] > 0,
        (q["prog_progres"].to(float) / q["objectif"].to(float) * 100).to(str) + "%",
        "0%",
    )

    return rx.box(
        rx.hstack(
            rx.text(q["icone"], font_size="1.4rem", flex_shrink="0"),
            rx.vstack(
                rx.hstack(
                    rx.text(q["titre"], color=TEXT, font_weight="700", font_size="0.875rem"),
                    rank_badge(q["difficulte"], "sm"),
                    rx.spacer(),
                    rx.badge("+" + q["xp"].to_string() + " XP", color_scheme="violet", variant="soft", radius="full", font_size="0.65rem"),
                    spacing="2", align="center", width="100%",
                ),
                rx.text(q["description"], color=MUTED, font_size="0.75rem"),
                spacing="1", align="start", width="100%",
            ),
            spacing="3", align="start", width="100%",
        ),
        rx.cond(
            q["objectif"] > 1,
            rx.vstack(
                rx.hstack(
                    rx.text("Progression", color=MUTED, font_size="0.65rem"),
                    rx.spacer(),
                    rx.text(q["prog_progres"].to_string() + "/" + q["objectif"].to_string() + " " + q["unite"], color=border_c, font_size="0.65rem", font_weight="600"),
                    width="100%",
                ),
                rx.box(
                    rx.box(width=pct, height="100%", background=f"linear-gradient(90deg,{PRIMARY},#8b5cf6)", border_radius="3px", transition="width 0.3s"),
                    height="5px", background="rgba(255,255,255,0.07)", border_radius="3px", overflow="hidden", width="100%",
                ),
                spacing="1", width="100%", margin_top="0.5rem",
            ),
        ),
        rx.hstack(
            statut_badge(q["prog_statut"]),
            rx.spacer(),
            rx.cond(show_done,
                rx.button(rx.icon("check",size=12),"Fait!",on_click=QuetesState.mark_done(q["id"]),
                    background="rgba(34,197,94,0.15)",color="#22c55e",border="1px solid rgba(34,197,94,0.4)",
                    border_radius="7px",font_size="0.72rem",font_weight="600",padding="4px 10px",cursor="pointer",spacing="1"),
            ),
            rx.cond(show_multi,
                rx.cond(
                    q["id"] == QuetesState.prog_quete_id,
                    rx.hstack(
                        rx.input(value=QuetesState.prog_input, on_change=QuetesState.set_prog_input, type="number",
                            width="54px", font_size="0.78rem", background="#1e2035", color=TEXT,
                            border=f"1px solid {BORDER}", border_radius="6px", padding="3px 6px", text_align="center"),
                        rx.icon_button(rx.icon("check",size=12), on_click=QuetesState.update_progress,
                            background="rgba(99,102,241,0.15)", color=PRIMARY, border_radius="6px", size="1", cursor="pointer"),
                        spacing="1", align="center",
                    ),
                    rx.button(rx.icon("pencil",size=12),"Màj",on_click=QuetesState.open_prog(q["id"],q["prog_progres"]),
                        background="rgba(99,102,241,0.1)",color=PRIMARY,border=f"1px solid rgba(99,102,241,0.3)",
                        border_radius="7px",font_size="0.72rem",padding="4px 10px",cursor="pointer",spacing="1"),
                ),
            ),
            spacing="2", align="center", margin_top="0.5rem", width="100%",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_left="4px solid " + border_c,
        border_radius="12px",
        padding="0.9rem",
        opacity=rx.cond(is_refuse, "0.55", "1"),
        transition="transform 0.15s",
        _hover={"transform": rx.cond(is_refuse, "none", "translateY(-2px)")},
    )


def pending_card(p: PendingValidation) -> rx.Component:
    return rx.hstack(
        rx.text(p["quete_icone"], font_size="1.1rem"),
        rx.vstack(
            rx.text(p["quete_titre"], color=TEXT, font_size="0.8rem", font_weight="600"),
            rx.text(p["user_nom"] + " · +" + p["xp"].to_string() + " XP", color=MUTED, font_size="0.7rem"),
            spacing="0", align="start",
        ),
        rx.spacer(),
        rx.button(rx.icon("check",size=12),"Valider",on_click=QuetesState.validate_quete(p["quete_id"],p["user_id"]),
            background="rgba(34,197,94,0.15)",color="#22c55e",border="1px solid rgba(34,197,94,0.3)",
            border_radius="6px",font_size="0.72rem",font_weight="600",padding="4px 10px",cursor="pointer",spacing="1"),
        rx.button(rx.icon("x",size=12),on_click=QuetesState.reject_quete(p["quete_id"],p["user_id"]),
            background="rgba(239,68,68,0.1)",color="#ef4444",border="1px solid rgba(239,68,68,0.3)",
            border_radius="6px",font_size="0.72rem",padding="4px 8px",cursor="pointer"),
        spacing="2", align="center", width="100%",
        background="#10121f", border="1px solid rgba(245,158,11,0.2)",
        border_radius="8px", padding="0.6rem 0.8rem",
    )


def lb_row(entry: LeaderboardEntry) -> rx.Component:
    medal = rx.match(
        entry["position"],
        (1, rx.text("🥇", font_size="1rem")),
        (2, rx.text("🥈", font_size="1rem")),
        (3, rx.text("🥉", font_size="1rem")),
        rx.text(entry["position"].to_string(), color=MUTED, font_size="0.78rem", font_weight="600"),
    )
    return rx.hstack(
        rx.box(medal, width="22px", text_align="center", flex_shrink="0"),
        rx.box(
            rx.text(entry["nom"][:2].upper(), color="white", font_size="0.68rem", font_weight="700"),
            background=rx.cond(entry["color"] != "", entry["color"], PRIMARY),
            border_radius="50%", width="24px", height="24px",
            display="flex", align_items="center", justify_content="center", flex_shrink="0",
        ),
        rx.text(entry["nom"], color=TEXT, font_size="0.8rem", font_weight="500"),
        rx.spacer(),
        rank_badge(entry["rank"], "sm"),
        rx.text(entry["total_xp"].to_string() + " XP", color=MUTED, font_size="0.7rem", white_space="nowrap"),
        spacing="2", align="center", width="100%",
        padding="0.45rem 0", border_bottom=f"1px solid {BORDER}",
    )


# ── Page ──────────────────────────────────────────────────────────────────────

def quetes_content() -> rx.Component:
    def tab_btn(key: str, icon: str, label: str) -> rx.Component:
        active = QuetesState.tab == key
        return rx.button(
            rx.icon(icon, size=13), label,
            on_click=QuetesState.set_tab(key),
            background=rx.cond(active, "rgba(99,102,241,0.2)", "transparent"),
            color=rx.cond(active, TEXT, MUTED),
            border=rx.cond(active, "1px solid rgba(99,102,241,0.4)", f"1px solid {BORDER}"),
            border_radius="8px", padding="7px 14px", font_size="0.82rem",
            font_weight=rx.cond(active, "600", "400"), cursor="pointer", spacing="2",
            _hover={"color": TEXT},
        )

    xp_pct = rx.cond(
        QuetesState.my_next_xp > 0,
        (QuetesState.my_current_xp.to(float) / QuetesState.my_next_xp.to(float) * 100).to(str) + "%",
        "0%",
    )

    return rx.hstack(
        # Gauche
        rx.vstack(
            # Stats
            rx.box(
                rx.hstack(
                    rank_badge(QuetesState.my_rank, "lg"),
                    rx.vstack(
                        rx.hstack(
                            rx.text("Niveau " + QuetesState.my_level.to_string(), color=TEXT, font_weight="700", font_size="1.05rem"),
                            rx.badge(QuetesState.my_rank, color_scheme="indigo", variant="soft", radius="full"),
                            spacing="2", align="center",
                        ),
                        rx.hstack(
                            rx.text(QuetesState.my_current_xp.to_string() + " / " + QuetesState.my_next_xp.to_string() + " XP", color=MUTED, font_size="0.75rem"),
                            rx.text("·", color=MUTED),
                            rx.text(QuetesState.my_quetes_validees.to_string() + " validées", color=MUTED, font_size="0.75rem"),
                            spacing="2",
                        ),
                        rx.box(
                            rx.box(width=xp_pct, height="100%", background=f"linear-gradient(90deg,{PRIMARY},#8b5cf6)", border_radius="3px"),
                            height="5px", background="rgba(255,255,255,0.08)", border_radius="3px", overflow="hidden", width="100%",
                        ),
                        spacing="2", align="start", flex="1",
                    ),
                    rx.text(QuetesState.my_total_xp.to_string() + " XP", color=PRIMARY, font_weight="800", font_size="1.4rem", white_space="nowrap"),
                    spacing="4", align="center", width="100%",
                ),
                background=CARD_BG, border=f"1px solid {BORDER}", border_radius="14px", padding="1.2rem", width="100%",
            ),
            # Validations en attente
            rx.cond(
                QuetesState.pending.length() > 0,
                rx.box(
                    rx.hstack(
                        rx.icon("clock", size=15, color="#f59e0b"),
                        rx.text("En attente de validation", color="#f59e0b", font_size="0.82rem", font_weight="600"),
                        rx.badge(QuetesState.pending.length().to_string(), color_scheme="amber", variant="solid", radius="full", font_size="0.65rem"),
                        spacing="2", align="center",
                    ),
                    rx.vstack(rx.foreach(QuetesState.pending, pending_card), spacing="2", margin_top="0.75rem", width="100%"),
                    background=CARD_BG, border="1px solid rgba(245,158,11,0.25)", border_radius="12px", padding="1rem", width="100%",
                ),
            ),
            # Tabs + créer
            rx.hstack(
                tab_btn("quotidienne",  "zap",   "Quotidiennes"),
                tab_btn("hebdomadaire", "star",  "Hebdomadaires"),
                tab_btn("achievement",  "crown", "Achievements"),
                rx.spacer(),
                rx.cond(
                    AuthState.is_manager,
                    rx.button(rx.icon("plus",size=13),"Créer",on_click=QuetesState.open_create,
                        background=f"linear-gradient(135deg,{PRIMARY},#8b5cf6)",color="white",
                        border_radius="8px",padding="7px 14px",font_size="0.82rem",cursor="pointer",spacing="2"),
                ),
                spacing="2", wrap="wrap", width="100%",
            ),
            # Quêtes
            rx.cond(
                QuetesState.quetes.length() == 0,
                rx.box(
                    rx.vstack(rx.icon("trophy",size=32,color=MUTED), rx.text("Aucune quête dans cet onglet",color=MUTED,font_size="0.875rem"), spacing="2",align="center"),
                    background=CARD_BG, border=f"1px solid {BORDER}", border_radius="12px", padding="3rem", text_align="center", width="100%",
                ),
                rx.grid(rx.foreach(QuetesState.quetes, quete_card), columns="2", spacing="3", width="100%"),
            ),
            # Modal création
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title(rx.text("Nouvelle quête", color=TEXT, font_weight="700")),
                    rx.vstack(
                        rx.input(placeholder="Titre *", value=QuetesState.create_form["titre"], on_change=lambda v: QuetesState.set_create_field("titre",v), background="#1e2035",color=TEXT,border=f"1px solid {BORDER}",border_radius="8px",width="100%"),
                        rx.text_area(placeholder="Description", value=QuetesState.create_form["description"], on_change=lambda v: QuetesState.set_create_field("description",v), background="#1e2035",color=TEXT,border=f"1px solid {BORDER}",border_radius="8px",width="100%"),
                        rx.hstack(
                            rx.vstack(rx.text("Type",color=MUTED,font_size="0.75rem"), rx.select(["quotidienne","hebdomadaire","achievement"],value=QuetesState.create_form["type"],on_change=lambda v:QuetesState.set_create_field("type",v),background="#1e2035",color=TEXT,border=f"1px solid {BORDER}",border_radius="8px"),spacing="1"),
                            rx.vstack(rx.text("Difficulté",color=MUTED,font_size="0.75rem"), rx.select(["E","D","C","B","A","S","SS"],value=QuetesState.create_form["difficulte"],on_change=lambda v:QuetesState.set_create_field("difficulte",v),background="#1e2035",color=TEXT,border=f"1px solid {BORDER}",border_radius="8px"),spacing="1"),
                            spacing="3",width="100%",
                        ),
                        rx.hstack(
                            rx.vstack(rx.text("XP",color=MUTED,font_size="0.75rem"), rx.input(placeholder="50",value=QuetesState.create_form["xp"],on_change=lambda v:QuetesState.set_create_field("xp",v),type="number",background="#1e2035",color=TEXT,border=f"1px solid {BORDER}",border_radius="8px"),spacing="1"),
                            rx.vstack(rx.text("Objectif",color=MUTED,font_size="0.75rem"), rx.input(placeholder="1",value=QuetesState.create_form["objectif"],on_change=lambda v:QuetesState.set_create_field("objectif",v),type="number",background="#1e2035",color=TEXT,border=f"1px solid {BORDER}",border_radius="8px"),spacing="1"),
                            rx.vstack(rx.text("Unité",color=MUTED,font_size="0.75rem"), rx.input(placeholder="action",value=QuetesState.create_form["unite"],on_change=lambda v:QuetesState.set_create_field("unite",v),background="#1e2035",color=TEXT,border=f"1px solid {BORDER}",border_radius="8px"),spacing="1"),
                            rx.vstack(rx.text("Icône",color=MUTED,font_size="0.75rem"), rx.input(placeholder="🎯",value=QuetesState.create_form["icone"],on_change=lambda v:QuetesState.set_create_field("icone",v),background="#1e2035",color=TEXT,border=f"1px solid {BORDER}",border_radius="8px",width="70px"),spacing="1"),
                            spacing="3",width="100%",
                        ),
                        rx.hstack(
                            rx.button("Annuler",on_click=QuetesState.close_create,background="transparent",color=MUTED,border=f"1px solid {BORDER}",border_radius="8px",cursor="pointer"),
                            rx.button("Créer",on_click=QuetesState.save_create,background=f"linear-gradient(135deg,{PRIMARY},#8b5cf6)",color="white",border_radius="8px",cursor="pointer"),
                            spacing="3",justify="end",width="100%",
                        ),
                        spacing="3",width="100%",
                    ),
                    background="#151728",border=f"1px solid {BORDER}",border_radius="16px",padding="1.5rem",max_width="520px",
                ),
                open=QuetesState.show_create,
            ),
            spacing="4", flex="1", min_width="0",
        ),
        # Leaderboard
        rx.box(
            rx.text("Classement", color=TEXT, font_weight="700", font_size="0.9rem", margin_bottom="0.8rem"),
            rx.vstack(rx.foreach(QuetesState.leaderboard, lb_row), spacing="0", width="100%"),
            background=CARD_BG, border=f"1px solid {BORDER}", border_radius="14px", padding="1.2rem",
            width="260px", flex_shrink="0", align_self="flex-start", position="sticky", top="80px",
        ),
        spacing="4", width="100%", align="start", on_mount=QuetesState.load,
    )


def quetes_page() -> rx.Component:
    return page_layout(quetes_content(), "Quêtes")
