import reflex as rx

from techpilot.db.database import load_db
from techpilot.state.models import GlobalSearchResult
from techpilot.gabarits_data import PREDEFINED_GABARITS as _PREDEFINED_GABARITS

_STOP = {"le","la","les","de","du","des","un","une","et","en","à","au","aux",
         "sur","par","pour","dans","avec","est","que","qui","n1","n2","si"}


class GlobalSearchState(rx.State):
    show: bool = False
    query: str = ""
    results: list[GlobalSearchResult] = []

    def open(self):
        self.show = True
        self.query = ""
        self.results = []

    def close(self):
        self.show = False
        self.query = ""
        self.results = []

    def set_query(self, v: str):
        self.query = v
        if len(v.strip()) < 2:
            self.results = []
            return
        self._search(v.strip().lower())

    def _search(self, q: str):
        db = load_db()
        results: list[GlobalSearchResult] = []

        # ── Tickets ──────────────────────────────────────────────────────
        for t in (db.get("tickets") or []):
            titre = (t.get("titre") or "").lower()
            desc  = (t.get("description") or "").lower()
            tech  = (t.get("technicien_nom") or "").lower()
            if q in titre or q in desc or q in tech:
                etat = t.get("etat") or ""
                results.append(GlobalSearchResult(
                    type="ticket",
                    title=t.get("titre") or "",
                    subtitle=(t.get("technicien_nom") or "—") + "  ·  " + ("En cours" if etat == "en_cours" else "Résolu"),
                    href="/tickets",
                    key=str(t.get("id") or ""),
                ))

        # ── Matrice ───────────────────────────────────────────────────────
        for r in (db.get("escalation_matrix") or []):
            perim = (r.get("perimetre") or "").lower()
            typo  = (r.get("typologie") or "").lower()
            cat   = (r.get("categorie_fresh") or "").lower()
            n1    = (r.get("traitement_n1") or "").lower()
            if q in perim or q in typo or q in cat or q in n1:
                results.append(GlobalSearchResult(
                    type="matrice",
                    title=(r.get("perimetre") or "") + "  ·  " + (r.get("typologie") or ""),
                    subtitle=r.get("traitement_n1") or "",
                    href="/escalade",
                    key=(r.get("perimetre") or "") + "|" + (r.get("typologie") or ""),
                ))

        # ── Documents ─────────────────────────────────────────────────────
        for d in (db.get("documents") or []):
            nom  = (d.get("nom_original") or "").lower()
            desc = (d.get("description") or "").lower()
            if q in nom or q in desc:
                results.append(GlobalSearchResult(
                    type="document",
                    title=d.get("nom_original") or "",
                    subtitle=d.get("categorie") or "",
                    href="/documents",
                    key=str(d.get("id") or ""),
                ))

        # ── Gabarits ─────────────────────────────────────────────────────
        hidden = set(db.get("hidden_predefined") or [])
        all_g = [g for g in _PREDEFINED_GABARITS if g.get("id") not in hidden]
        all_g += db.get("gabarits") or []
        for g in all_g:
            titre   = (g.get("titre") or "").lower()
            contenu = (g.get("contenu") or "").lower()
            if q in titre or q in contenu:
                results.append(GlobalSearchResult(
                    type="gabarit",
                    title=g.get("titre") or "",
                    subtitle=g.get("categorie") or "",
                    href="",
                    key=str(g.get("id") or ""),
                    extra=g.get("contenu") or "",
                ))

        # Cap à 5 par type
        by_type: dict[str, list] = {}
        for r in results:
            by_type.setdefault(r.type, []).append(r)
        final = []
        for t in ["ticket", "matrice", "document", "gabarit"]:
            final.extend(by_type.get(t, [])[:5])
        self.results = final

    def navigate(self, href: str, key: str):
        self.show = False
        self.query = ""
        self.results = []
        if href:
            return rx.redirect(href)

    def copy_gabarit(self, contenu: str):
        self.show = False
        self.query = ""
        self.results = []
        yield rx.set_clipboard(contenu)
        yield rx.toast.success("Gabarit copié !")
