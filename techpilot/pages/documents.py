import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
from techpilot.state.auth import AuthState
from techpilot.state.models import DocumentItem
import uuid
from datetime import datetime
from pathlib import Path

TEXT = "#e2e8f0"; MUTED = "#64748b"; CARD_BG = "#151728"; BORDER = "#1e2235"; PRIMARY = "#6366f1"

CATEGORIES = ["Procédures", "Général", "Formation", "Référentiel", "Compte-rendu"]
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
    documents: list[DocumentItem] = []
    filter_cat: str = ""
    filter_sous_cat: str = ""
    show_link_form: bool = False
    link_form: dict = {"nom": "", "url": "", "categorie": "Procédures", "sous_categorie": "", "description": ""}

    def load(self):
        db = load_db()
        docs = sorted(db.get("documents") or [], key=lambda d: d.get("date_upload") or "", reverse=True)
        if self.filter_cat:
            docs = [d for d in docs if d.get("categorie") == self.filter_cat]
        if self.filter_sous_cat:
            docs = [d for d in docs if d.get("sous_categorie") == self.filter_sous_cat]
        self.documents = [
            DocumentItem(
                id=str(d.get("id") or ""),
                type=d.get("type") or "",
                nom_original=d.get("nom_original") or "",
                url=d.get("url") or "",
                categorie=d.get("categorie") or "",
                sous_categorie=d.get("sous_categorie") or "",
                description=d.get("description") or "",
            )
            for d in docs
        ]

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


def doc_card(doc: DocumentItem) -> rx.Component:
    is_link = doc["type"] == "lien"
    return rx.box(
        rx.hstack(
            rx.box(
                rx.cond(
                    is_link,
                    rx.icon("link-2", size=20, color=PRIMARY),
                    rx.icon("file", size=20, color=MUTED),
                ),
                background=rx.cond(is_link, "rgba(99,102,241,0.1)", "#1e2035"),
                border_radius="8px", padding="8px",
            ),
            rx.vstack(
                rx.hstack(
                    rx.cond(
                        is_link,
                        rx.link(doc["nom_original"], href=doc["url"], color=TEXT, font_weight="600", font_size="0.875rem", target="_blank", _hover={"color": PRIMARY}),
                        rx.text(doc["nom_original"], color=TEXT, font_weight="600", font_size="0.875rem"),
                    ),
                    rx.cond(is_link, rx.badge("Lien", color_scheme="violet", variant="soft", radius="full", font_size="0.65rem")),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.badge(doc["categorie"], color_scheme="gray", variant="soft", radius="full", font_size="0.65rem"),
                    rx.cond(
                        doc["sous_categorie"] != "",
                        rx.badge(doc["sous_categorie"], color_scheme="indigo", variant="soft", radius="full", font_size="0.65rem"),
                    ),
                    spacing="2",
                ),
                rx.text(doc["description"], color=MUTED, font_size="0.78rem"),
                spacing="1", align="start",
            ),
            rx.spacer(),
            rx.icon_button(rx.icon("trash-2", size=14), on_click=DocumentsState.delete_doc(doc["id"]), background="rgba(239,68,68,0.1)", color="#ef4444", border_radius="6px", size="1", cursor="pointer"),
            spacing="3", align="start", width="100%",
        ),
        background=CARD_BG, border=f"1px solid {BORDER}", border_radius="12px", padding="1rem",
    )


def documents_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.select(CATEGORIES, placeholder="Toutes catégories", value=DocumentsState.filter_cat, on_change=DocumentsState.set_cat, background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px"),
            rx.cond(
                DocumentsState.filter_cat != "",
                rx.icon_button(
                    rx.icon("x", size=14),
                    on_click=DocumentsState.set_cat(""),
                    background="transparent", color=MUTED,
                    border=f"1px solid {BORDER}", border_radius="6px", size="2",
                    cursor="pointer", _hover={"color": TEXT},
                ),
            ),
            rx.cond(
                DocumentsState.filter_cat == "Procédures",
                rx.hstack(
                    rx.select(SOUS_CATEGORIES, placeholder="Tous les dossiers", value=DocumentsState.filter_sous_cat, on_change=DocumentsState.set_sous_cat, background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px"),
                    rx.cond(
                        DocumentsState.filter_sous_cat != "",
                        rx.icon_button(
                            rx.icon("x", size=14),
                            on_click=DocumentsState.set_sous_cat(""),
                            background="transparent", color=MUTED,
                            border=f"1px solid {BORDER}", border_radius="6px", size="2",
                            cursor="pointer", _hover={"color": TEXT},
                        ),
                    ),
                    spacing="2", align="center",
                ),
            ),
            rx.spacer(),
            rx.button(rx.icon("link-2", size=16), "Ajouter un lien", on_click=DocumentsState.open_link_form, background="rgba(139,92,246,0.15)", color="#a78bfa", border=f"1px solid rgba(139,92,246,0.3)", border_radius="8px", padding="8px 14px", font_size="0.85rem", cursor="pointer", spacing="2"),
            width="100%", align="center",
        ),
        rx.vstack(rx.foreach(DocumentsState.documents, doc_card), spacing="3", width="100%"),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(rx.text("Ajouter un lien", color=TEXT, font_weight="700")),
                rx.vstack(
                    rx.input(placeholder="Nom *", value=DocumentsState.link_form["nom"], on_change=lambda v: DocumentsState.set_link_field("nom", v), background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px", width="100%"),
                    rx.input(placeholder="URL *", value=DocumentsState.link_form["url"], on_change=lambda v: DocumentsState.set_link_field("url", v), background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px", width="100%"),
                    rx.select(CATEGORIES, value=DocumentsState.link_form["categorie"], on_change=lambda v: DocumentsState.set_link_field("categorie", v), background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px"),
                    rx.select(SOUS_CATEGORIES, placeholder="Dossier (optionnel)", value=DocumentsState.link_form["sous_categorie"], on_change=lambda v: DocumentsState.set_link_field("sous_categorie", v), background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px"),
                    rx.text_area(placeholder="Description (optionnel)", value=DocumentsState.link_form["description"], on_change=lambda v: DocumentsState.set_link_field("description", v), background="#1e2035", color=TEXT, border=f"1px solid {BORDER}", border_radius="8px", width="100%"),
                    rx.hstack(
                        rx.button("Annuler", on_click=DocumentsState.close_link_form, background="transparent", color=MUTED, border=f"1px solid {BORDER}", border_radius="8px", cursor="pointer"),
                        rx.button("Ajouter", on_click=DocumentsState.create_link, background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)", color="white", border_radius="8px", cursor="pointer"),
                        spacing="3", justify="end", width="100%",
                    ),
                    spacing="3", width="100%",
                ),
                background="#151728", border=f"1px solid {BORDER}", border_radius="16px", padding="1.5rem", max_width="480px",
            ),
            open=DocumentsState.show_link_form,
        ),
        spacing="4", width="100%", on_mount=DocumentsState.load,
    )


def documents_page() -> rx.Component:
    return page_layout(documents_content(), "Documents")
