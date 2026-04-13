import reflex as rx
import base64
from techpilot.db.database import load_db
from techpilot.state.models import EscaladeEntry

PERIMETRE_COLORS = [
    "#f59e0b", "#8b5cf6", "#f97316", "#64748b", "#06b6d4",
    "#22c55e", "#eab308", "#3b82f6", "#6366f1", "#ef4444",
    "#0891b2", "#a855f7", "#ec4899", "#10b981",
]


class EscaladeState(rx.State):

    # ── Recherche ─────────────────────────────────────────────────────────
    entries: list[EscaladeEntry] = []
    perimetres: list[str] = []
    selected_perimetres: list[str] = []
    search: str = ""
    page: int = 1
    total: int = 0
    limit: int = 25
    selected_entry: EscaladeEntry = EscaladeEntry()
    show_modal: bool = False
    favoris: list[EscaladeEntry] = []

    # ── Mode ──────────────────────────────────────────────────────────────
    mode: str = "recherche"   # recherche | assistant | arbre | interlocuteur | libre
    total_count: int = 0

    # ── Assistant guidé ───────────────────────────────────────────────────
    assistant_step: int = 1
    assistant_perimetre: str = ""
    perimetre_counts: list[dict] = []
    assistant_entries: list[EscaladeEntry] = []

    # ── Par interlocuteur N2 ──────────────────────────────────────────────
    interlocuteur_search: str = ""
    interlocuteurs_list: list[dict] = []
    filtered_interlocuteurs_list: list[dict] = []
    expanded_interlocuteur: str = ""
    interlocuteur_entries: list[EscaladeEntry] = []

    # ── Arbre ─────────────────────────────────────────────────────────────
    arbre_expanded: str = ""
    arbre_entries: list[EscaladeEntry] = []

    # ── Chargement ────────────────────────────────────────────────────────

    def load_data(self):
        db = load_db()
        all_entries = db.get("escalation_matrix") or []
        self.total_count = len(all_entries)

        sorted_perimetres = sorted(set(
            r.get("perimetre", "") for r in all_entries if r.get("perimetre")
        ))
        self.perimetres = sorted_perimetres

        self.perimetre_counts = [
            {
                "name": p,
                "count": sum(1 for r in all_entries if r.get("perimetre") == p),
                "count_str": f"{sum(1 for r in all_entries if r.get('perimetre') == p)} procédures",
                "color": PERIMETRE_COLORS[i % len(PERIMETRE_COLORS)],
                "border_accent": f"3px solid {PERIMETRE_COLORS[i % len(PERIMETRE_COLORS)]}",
            }
            for i, p in enumerate(sorted_perimetres)
        ]

        interlocuteurs: dict = {}
        for r in all_entries:
            interl = (r.get("interlocuteur") or "").strip()
            if not interl:
                continue
            if interl not in interlocuteurs:
                interlocuteurs[interl] = {"nom": interl, "count": 0, "tags_set": set()}
            interlocuteurs[interl]["count"] += 1
            p = r.get("perimetre", "")
            if p:
                interlocuteurs[interl]["tags_set"].add(p)

        self.interlocuteurs_list = [
            {
                "nom": v["nom"],
                "count": v["count"],
                "count_str": f"{v['count']} cas",
                "tags": ", ".join(sorted(v["tags_set"])),
            }
            for v in sorted(interlocuteurs.values(), key=lambda x: -x["count"])
        ]
        self.filtered_interlocuteurs_list = self.interlocuteurs_list

        self._filter(db)

    def _filter(self, db: dict | None = None):
        if db is None:
            db = load_db()
        results = db.get("escalation_matrix") or []

        if self.search:
            q = self.search.lower()
            results = [
                r for r in results
                if q in (r.get("typologie") or "").lower()
                or q in (r.get("perimetre") or "").lower()
                or q in (r.get("categorie_fresh") or "").lower()
                or q in (r.get("traitement_n1") or "").lower()
                or q in (r.get("interlocuteur") or "").lower()
                or q in (r.get("traitement_n2n3") or "").lower()
                or q in (r.get("conditions_escalade") or "").lower()
            ]

        if self.selected_perimetres:
            results = [r for r in results if r.get("perimetre") in self.selected_perimetres]

        self.total = len(results)
        offset = (self.page - 1) * self.limit
        self.entries = [
            EscaladeEntry(
                perimetre=r.get("perimetre") or "",
                typologie=r.get("typologie") or "",
                categorie_fresh=r.get("categorie_fresh") or "",
                traitement_n1=r.get("traitement_n1") or "",
                wp=r.get("wp") or "",
                interlocuteur=r.get("interlocuteur") or "",
                traitement_n2n3=r.get("traitement_n2n3") or "",
                wp_n2=r.get("wp_n2") or "",
                referents=r.get("referents") or "",
                conditions_escalade=r.get("conditions_escalade") or "",
            )
            for r in results[offset: offset + self.limit]
        ]

    # ── Mode ──────────────────────────────────────────────────────────────

    def set_mode(self, m: str):
        self.mode = m

    # ── Recherche ─────────────────────────────────────────────────────────

    def set_search(self, val: str):
        self.search = val
        self.page = 1
        self._filter()

    def toggle_perimetre(self, p: str):
        if p in self.selected_perimetres:
            self.selected_perimetres = [x for x in self.selected_perimetres if x != p]
        else:
            self.selected_perimetres = [*self.selected_perimetres, p]
        self.page = 1
        self._filter()

    def clear_filters(self):
        self.search = ""
        self.selected_perimetres = []
        self.page = 1
        self._filter()

    def go_page(self, p: int):
        self.page = p
        self._filter()

    def open_entry(self, entry: EscaladeEntry):
        self.selected_entry = entry
        self.show_modal = True

    def close_modal(self):
        self.show_modal = False

    def toggle_favori(self):
        key = self.selected_entry.perimetre + "|" + self.selected_entry.typologie
        if any(f.perimetre + "|" + f.typologie == key for f in self.favoris):
            self.favoris = [f for f in self.favoris if f.perimetre + "|" + f.typologie != key]
        else:
            self.favoris = [*self.favoris, self.selected_entry]

    def open_favori(self, entry: EscaladeEntry):
        self.selected_entry = entry
        self.show_modal = True

    def copy_fresh_cat(self):
        yield rx.set_clipboard(self.selected_entry.categorie_fresh)

    @rx.var
    def is_selected_favori(self) -> bool:
        key = self.selected_entry.perimetre + "|" + self.selected_entry.typologie
        return any(f.perimetre + "|" + f.typologie == key for f in self.favoris)

    @rx.var
    def total_pages(self) -> int:
        return max(1, (self.total + self.limit - 1) // self.limit)

    # ── Assistant guidé ───────────────────────────────────────────────────

    def assistant_select_perimetre(self, p: str):
        self.assistant_perimetre = p
        self.assistant_step = 2
        db = load_db()
        entries = [r for r in (db.get("escalation_matrix") or []) if r.get("perimetre") == p]
        self.assistant_entries = [
            EscaladeEntry(
                perimetre=r.get("perimetre") or "",
                typologie=r.get("typologie") or "",
                categorie_fresh=r.get("categorie_fresh") or "",
                traitement_n1=r.get("traitement_n1") or "",
                wp=r.get("wp") or "",
                interlocuteur=r.get("interlocuteur") or "",
                traitement_n2n3=r.get("traitement_n2n3") or "",
                wp_n2=r.get("wp_n2") or "",
                referents=r.get("referents") or "",
                conditions_escalade=r.get("conditions_escalade") or "",
            )
            for r in entries
        ]

    def assistant_back(self):
        self.assistant_step = 1
        self.assistant_perimetre = ""
        self.assistant_entries = []

    # ── Par interlocuteur N2 ──────────────────────────────────────────────

    def set_interlocuteur_search(self, val: str):
        self.interlocuteur_search = val
        if not val:
            self.filtered_interlocuteurs_list = self.interlocuteurs_list
        else:
            q = val.lower()
            self.filtered_interlocuteurs_list = [
                x for x in self.interlocuteurs_list
                if q in x.get("nom", "").lower()
            ]

    def toggle_expand_interlocuteur(self, nom: str):
        if self.expanded_interlocuteur == nom:
            self.expanded_interlocuteur = ""
            self.interlocuteur_entries = []
        else:
            self.expanded_interlocuteur = nom
            db = load_db()
            entries = [
                r for r in (db.get("escalation_matrix") or [])
                if (r.get("interlocuteur") or "").strip() == nom
            ]
            self.interlocuteur_entries = [
                EscaladeEntry(
                    perimetre=r.get("perimetre") or "",
                    typologie=r.get("typologie") or "",
                    categorie_fresh=r.get("categorie_fresh") or "",
                    traitement_n1=r.get("traitement_n1") or "",
                    wp=r.get("wp") or "",
                    interlocuteur=r.get("interlocuteur") or "",
                    traitement_n2n3=r.get("traitement_n2n3") or "",
                    wp_n2=r.get("wp_n2") or "",
                    referents=r.get("referents") or "",
                    conditions_escalade=r.get("conditions_escalade") or "",
                )
                for r in entries
            ]

    # ── Export CSV ────────────────────────────────────────────────────────────

    def export_csv(self):
        def esc(v: str) -> str:
            return '"' + str(v or "").replace('"', '""') + '"'

        db = load_db()
        results = db.get("escalation_matrix") or []

        if self.search:
            q = self.search.lower()
            results = [
                r for r in results
                if q in (r.get("typologie") or "").lower()
                or q in (r.get("perimetre") or "").lower()
                or q in (r.get("categorie_fresh") or "").lower()
                or q in (r.get("traitement_n1") or "").lower()
                or q in (r.get("interlocuteur") or "").lower()
                or q in (r.get("traitement_n2n3") or "").lower()
                or q in (r.get("conditions_escalade") or "").lower()
            ]
        if self.selected_perimetres:
            results = [r for r in results if r.get("perimetre") in self.selected_perimetres]

        rows = ["Périmètre,Typologie,Catégorie FRESH,Traitement N1,WP,Interlocuteur,Traitement N2/N3,WP N2,Référents,Conditions"]
        for r in results:
            rows.append(",".join([
                esc(r.get("perimetre", "")),
                esc(r.get("typologie", "")),
                esc(r.get("categorie_fresh", "")),
                esc(r.get("traitement_n1", "")),
                esc(r.get("wp", "")),
                esc(r.get("interlocuteur", "")),
                esc(r.get("traitement_n2n3", "")),
                esc(r.get("wp_n2", "")),
                esc(r.get("referents", "")),
                esc(r.get("conditions_escalade", "")),
            ]))
        csv = "\n".join(rows)
        b64 = base64.b64encode(csv.encode("utf-8")).decode()
        yield rx.call_script(f"""
var csv = atob('{b64}');
var blob = new Blob([csv], {{type:'text/csv;charset=utf-8;'}});
var url = URL.createObjectURL(blob);
var a = document.createElement('a');
a.href = url;
a.download = 'escalade_' + new Date().toISOString().slice(0,10) + '.csv';
document.body.appendChild(a); a.click();
document.body.removeChild(a); URL.revokeObjectURL(url);
""")

    # ── Arbre ─────────────────────────────────────────────────────────────

    def toggle_arbre_perimetre(self, p: str):
        if self.arbre_expanded == p:
            self.arbre_expanded = ""
            self.arbre_entries = []
        else:
            self.arbre_expanded = p
            db = load_db()
            entries = [r for r in (db.get("escalation_matrix") or []) if r.get("perimetre") == p]
            self.arbre_entries = [
                EscaladeEntry(
                    perimetre=r.get("perimetre") or "",
                    typologie=r.get("typologie") or "",
                    categorie_fresh=r.get("categorie_fresh") or "",
                    traitement_n1=r.get("traitement_n1") or "",
                    wp=r.get("wp") or "",
                    interlocuteur=r.get("interlocuteur") or "",
                    traitement_n2n3=r.get("traitement_n2n3") or "",
                    wp_n2=r.get("wp_n2") or "",
                    referents=r.get("referents") or "",
                    conditions_escalade=r.get("conditions_escalade") or "",
                )
                for r in entries
            ]
