import uuid
from datetime import datetime
from pathlib import Path

import reflex as rx

from techpilot.db.database import load_db, save_db
from techpilot.state.auth import AuthState
from techpilot.state.models import DocumentItem, DocGroup, GabaritItem, GabaritColumn
from techpilot.gabarits_data import GABARIT_CATEGORIES_DEFAULT, PREDEFINED_GABARITS as _PREDEFINED_GABARITS

CATEGORIES = ["Général", "Procédures", "Groupes de droits", "Formations", "Référentiels", "Autre"]
GABARIT_CATEGORIES = GABARIT_CATEGORIES_DEFAULT
SOUS_CATEGORIES = [
    "SI - Téléphonie",
    "SI - Sécurité",
    "SI - Réseau et internet",
    "SI - Poste de travail et périphériques",
    "SI - Outils collaboratifs",
    "SI - CRM",
    "SI - AUTRES APPLICATIONS",
    "SI - AE",
    "RH PERMANENTS",
    "Ressources",
    "Procédures en attente de validation",
    "Généralités",
    "Fiches Applications pour le N1",
    "Arbres & process N1",
]


class DocumentsState(rx.State):
    doc_groups: list[DocGroup] = []
    total_count: int = 0
    filter_cat: str = ""
    filter_sous_cat: str = ""
    show_link_form: bool = False
    link_form: dict = {"nom": "", "url": "", "categorie": "Procédures", "sous_categorie": "", "description": ""}
    current_tab: str = "documents"
    escalade_count: int = 0
    gabarit_columns: list[GabaritColumn] = []
    gabarit_categories: list[str] = ["Ticket", "Mail", "Note", "Escalade", "Autre"]
    show_gabarit_form: bool = False
    gabarit_form: dict = {"titre": "", "categorie": "Ticket", "contenu": ""}
    editing_gabarit_id: str = ""
    editing_col_cat: str = ""
    editing_col_new_name: str = ""
    show_add_cat_input: bool = False
    new_cat_name: str = ""

    def set_tab(self, tab: str):
        self.current_tab = tab

    def load(self):
        self.load_gabarits()
        db = load_db()
        self.escalade_count = len(db.get("escalade") or [])
        docs = sorted(db.get("documents") or [], key=lambda d: d.get("date_upload") or "", reverse=True)
        if self.filter_cat:
            docs = [d for d in docs if d.get("categorie") == self.filter_cat]
        if self.filter_sous_cat:
            docs = [d for d in docs if d.get("sous_categorie") == self.filter_sous_cat]
        self.total_count = len(docs)

        groups: dict[str, list] = {}
        for d in docs:
            if self.filter_cat == "Procédures" and d.get("sous_categorie"):
                key = d["sous_categorie"]
            else:
                key = d.get("categorie") or "Sans catégorie"
            if key not in groups:
                groups[key] = []
            groups[key].append(d)

        self.doc_groups = [
            DocGroup(
                name=key,
                docs=[
                    DocumentItem(
                        id=str(d.get("id") or ""),
                        type=d.get("type") or "",
                        nom_original=d.get("nom_original") or "",
                        url=d.get("url") or "",
                        categorie=d.get("categorie") or "",
                        sous_categorie=d.get("sous_categorie") or "",
                        description=d.get("description") or "",
                    )
                    for d in grp_docs
                ],
            )
            for key, grp_docs in groups.items()
        ]

    def load_gabarits(self):
        db = load_db()
        saved_cats = db.get("gabarit_categories")
        if saved_cats is None:
            saved_cats = list(GABARIT_CATEGORIES)
            db["gabarit_categories"] = saved_cats
            save_db(db)
        self.gabarit_categories = saved_cats
        hidden = set(db.get("hidden_predefined") or [])
        custom = sorted(db.get("gabarits") or [], key=lambda g: g.get("date_creation") or "", reverse=True)
        columns: dict[str, list] = {cat: [] for cat in saved_cats}
        for g in _PREDEFINED_GABARITS:
            if g.get("id") in hidden:
                continue
            cat = g.get("categorie") or "Autre"
            if cat not in columns:
                columns[cat] = []
            columns[cat].append(GabaritItem(
                id=g.get("id") or "",
                titre=g.get("titre") or "",
                categorie=cat,
                contenu=g.get("contenu") or "",
                is_custom=False,
            ))
        for g in custom:
            cat = g.get("categorie") or "Autre"
            if cat not in columns:
                columns[cat] = []
            columns[cat].append(GabaritItem(
                id=str(g.get("id") or ""),
                titre=g.get("titre") or "",
                categorie=cat,
                contenu=g.get("contenu") or "",
                date_creation=g.get("date_creation") or "",
                auteur_nom=g.get("auteur_nom") or "",
                is_custom=True,
            ))
        all_cats = list(saved_cats)
        for cat in columns:
            if cat not in all_cats:
                all_cats.append(cat)
        self.gabarit_columns = [
            GabaritColumn(category=cat, items=columns.get(cat, []))
            for cat in all_cats
        ]

    def start_edit_col(self, cat: str):
        self.editing_col_cat = cat
        self.editing_col_new_name = cat

    def set_edit_col_name(self, v: str):
        self.editing_col_new_name = v

    def save_col_rename(self):
        new_name = self.editing_col_new_name.strip()
        if not new_name or new_name == self.editing_col_cat:
            self.editing_col_cat = ""
            return
        db = load_db()
        cats = db.get("gabarit_categories") or list(GABARIT_CATEGORIES)
        if self.editing_col_cat in cats:
            cats[cats.index(self.editing_col_cat)] = new_name
        db["gabarit_categories"] = cats
        for g in db.get("gabarits", []):
            if g.get("categorie") == self.editing_col_cat:
                g["categorie"] = new_name
        save_db(db)
        self.editing_col_cat = ""
        self.load_gabarits()

    def cancel_col_edit(self):
        self.editing_col_cat = ""
        self.editing_col_new_name = ""

    def set_new_cat_name(self, v: str):
        self.new_cat_name = v

    def toggle_add_cat(self):
        self.show_add_cat_input = not self.show_add_cat_input
        self.new_cat_name = ""

    def add_category(self):
        name = self.new_cat_name.strip()
        if not name:
            return
        db = load_db()
        cats = db.get("gabarit_categories") or list(GABARIT_CATEGORIES)
        if name not in cats:
            cats.append(name)
        db["gabarit_categories"] = cats
        self.new_cat_name = ""
        self.show_add_cat_input = False
        save_db(db)
        self.load_gabarits()

    def open_gabarit_form(self):
        self.gabarit_form = {"titre": "", "categorie": "Ticket", "contenu": ""}
        self.editing_gabarit_id = ""
        self.show_gabarit_form = True

    def open_gabarit_form_with_cat(self, cat: str):
        self.gabarit_form = {"titre": "", "categorie": cat, "contenu": ""}
        self.editing_gabarit_id = ""
        self.show_gabarit_form = True

    def open_edit_gabarit_form(self, gid: str, titre: str, categorie: str, contenu: str):
        self.gabarit_form = {"titre": titre, "categorie": categorie, "contenu": contenu}
        self.editing_gabarit_id = gid
        self.show_gabarit_form = True

    def close_gabarit_form(self):
        self.editing_gabarit_id = ""
        self.show_gabarit_form = False

    def set_gabarit_field(self, f: str, v: str):
        self.gabarit_form = {**self.gabarit_form, f: v}

    def save_gabarit(self):
        if not self.gabarit_form.get("titre") or not self.gabarit_form.get("contenu"):
            return
        db = load_db()
        cat = self.gabarit_form.get("categorie") or "Autre"
        if self.editing_gabarit_id and self.editing_gabarit_id.startswith("__pre_"):
            hidden = db.get("hidden_predefined") or []
            if self.editing_gabarit_id not in hidden:
                hidden.append(self.editing_gabarit_id)
            db["hidden_predefined"] = hidden
            if "gabarits" not in db:
                db["gabarits"] = []
            db["gabarits"].append({
                "id": str(uuid.uuid4()),
                "titre": self.gabarit_form.get("titre") or "",
                "categorie": cat,
                "contenu": self.gabarit_form.get("contenu") or "",
                "date_creation": datetime.utcnow().isoformat(),
                "auteur_nom": "",
            })
        elif self.editing_gabarit_id:
            for g in db.get("gabarits", []):
                if g.get("id") == self.editing_gabarit_id:
                    g["titre"] = self.gabarit_form.get("titre") or g["titre"]
                    g["categorie"] = cat
                    g["contenu"] = self.gabarit_form.get("contenu") or g["contenu"]
                    break
        else:
            if "gabarits" not in db:
                db["gabarits"] = []
            db["gabarits"].append({
                "id": str(uuid.uuid4()),
                "titre": self.gabarit_form.get("titre") or "",
                "categorie": cat,
                "contenu": self.gabarit_form.get("contenu") or "",
                "date_creation": datetime.utcnow().isoformat(),
                "auteur_nom": "",
            })
        save_db(db)
        self.editing_gabarit_id = ""
        self.show_gabarit_form = False
        self.load_gabarits()

    def delete_gabarit(self, gid: str):
        db = load_db()
        if gid.startswith("__pre_"):
            hidden = db.get("hidden_predefined") or []
            if gid not in hidden:
                hidden.append(gid)
            db["hidden_predefined"] = hidden
        else:
            db["gabarits"] = [g for g in db.get("gabarits", []) if g.get("id") != gid]
        save_db(db)
        self.load_gabarits()

    def copy_gabarit(self, contenu: str):
        yield rx.set_clipboard(contenu)

    def set_cat(self, v: str):
        self.filter_cat = v
        self.filter_sous_cat = ""
        self.load()

    def set_sous_cat(self, v: str):
        self.filter_sous_cat = v
        self.load()

    def open_link_form(self):
        self.link_form = {"nom": "", "url": "", "categorie": "Procédures", "sous_categorie": "", "description": ""}
        self.show_link_form = True

    def close_link_form(self):
        self.show_link_form = False

    def set_link_field(self, f: str, v: str):
        self.link_form = {**self.link_form, f: v}

    def create_link(self):
        if not self.link_form.get("nom") or not self.link_form.get("url"):
            return
        db = load_db()
        if "documents" not in db:
            db["documents"] = []
        db["documents"].append({
            "id": str(uuid.uuid4()),
            "type": "lien",
            "nom_original": self.link_form.get("nom") or "",
            "nom_stockage": "",
            "url": self.link_form.get("url") or "",
            "categorie": self.link_form.get("categorie") or "Procédures",
            "sous_categorie": self.link_form.get("sous_categorie") or "",
            "description": self.link_form.get("description") or "",
            "uploade_par_id": AuthState.user_id,
            "uploade_par_nom": AuthState.user_nom,
            "date_upload": datetime.utcnow().isoformat(),
        })
        save_db(db)
        self.show_link_form = False
        self.load()

    def delete_doc(self, did: str):
        db = load_db()
        doc = next((d for d in db.get("documents", []) if d.get("id") == did), None)
        if doc and doc.get("nom_stockage"):
            p = Path(__file__).parent.parent.parent / "data" / "documents" / doc["nom_stockage"]
            if p.exists():
                p.unlink()
        db["documents"] = [d for d in db.get("documents", []) if d.get("id") != did]
        save_db(db)
        self.load()
