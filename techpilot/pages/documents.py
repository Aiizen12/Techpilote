import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.db.database import load_db, save_db
from techpilot.state.auth import AuthState
from techpilot.state.models import DocumentItem, DocGroup, GabaritItem, GabaritColumn
import uuid
from datetime import datetime
from pathlib import Path

TEXT = "#e2e8f0"
MUTED = "#64748b"
CARD_BG = "#0d1117"
BORDER = "rgba(255,255,255,0.07)"
PRIMARY = "#6366f1"

CATEGORIES = ["Général", "Procédures", "Groupes de droits", "Formations", "Référentiels", "Autre"]
GABARIT_CATEGORIES = ["Ticket", "Mail", "Note", "Escalade", "Autre"]

_PREDEFINED_GABARITS = [
    {"id": "__pre_1", "categorie": "Ticket", "titre": "Ticket générique – Incident logiciel",
     "contenu": "Objet : [NOM APPLICATION] – Incident\n\nUtilisateur :\nMatricule :\nSite / Agence :\nDate et heure de début :\n\nDescription du problème :\n\n\nMessage d'erreur (si applicable) :\n\n\nActions déjà réalisées :\n- Redémarrage poste : Oui / Non\n- Reconnexion application : Oui / Non\n- Autre :\n\nImpact : Utilisateur seul / Plusieurs utilisateurs / Site entier\n\nCaptures d'écran : Oui / Non"},
    {"id": "__pre_2", "categorie": "Ticket", "titre": "Ticket – Réinitialisation mot de passe",
     "contenu": "Objet : Réinitialisation mot de passe – [NOM UTILISATEUR]\n\nUtilisateur :\nMatricule :\nSite :\nApplication concernée :\n\nMotif de la demande :\n☐ Mot de passe oublié\n☐ Compte verrouillé\n☐ Expiration\n\nIdentité vérifiée : Oui / Non\nMoyen de vérification :\n\nAction réalisée :\n☐ Réinitialisation effectuée\n☐ Déverrouillage compte\n☐ Escalade N2 – Motif : "},
    {"id": "__pre_3", "categorie": "Ticket", "titre": "Ticket – Demande d'accès / droits",
     "contenu": "Objet : Demande d'accès – [APPLICATION / RESSOURCE]\n\nDemandeur :\nMatricule :\nManager validant la demande :\nDate de validation manager :\n\nAccès demandé :\nApplication / Partage réseau / Groupe AD :\nNiveau d'accès : Lecture / Écriture / Admin\n\nJustification métier :\n\nDélai souhaité :\n\nPièce jointe (mail de validation) : Oui / Non"},
    {"id": "__pre_4", "categorie": "Escalade", "titre": "Ticket – Panne matériel (escalade N2)",
     "contenu": "Objet : Panne matériel – [TYPE ÉQUIPEMENT] – [SITE]\n\nUtilisateur :\nMatricule :\nSite :\nÉquipement concerné :\nN° de série / Référence :\n\nPanne constatée :\n\n\nDiagnostic N1 effectué :\n- Redémarrage : Oui / Non – Résultat :\n- Vérification câbles : Oui / Non\n- Test sur autre prise / port : Oui / Non\n- Autre :\n\nÉquipement de remplacement disponible sur site : Oui / Non\n\n→ Escalade N2 requise pour intervention sur site."},
    {"id": "__pre_5", "categorie": "Mail", "titre": "Mail – Confirmation prise en charge",
     "contenu": "Objet : Prise en charge de votre demande – Ticket #[NUMÉRO]\n\nBonjour [Prénom],\n\nNous avons bien reçu votre demande concernant [DESCRIPTION COURTE DU PROBLÈME].\n\nVotre ticket a été enregistré sous le numéro #[NUMÉRO] et est actuellement en cours de traitement par notre équipe helpdesk.\n\nNous reviendrons vers vous dans les meilleurs délais.\n\nCordialement,\n[Votre prénom]\nHelpdesk N1"},
    {"id": "__pre_6", "categorie": "Mail", "titre": "Mail – Demande d'informations complémentaires",
     "contenu": "Objet : Informations complémentaires – Ticket #[NUMÉRO]\n\nBonjour [Prénom],\n\nAfin de traiter au mieux votre demande concernant [DESCRIPTION COURTE], nous aurions besoin des informations suivantes :\n\n1.\n2.\n3.\n\nPourriez-vous nous fournir ces éléments afin que nous puissions avancer sur votre ticket ?\n\nMerci d'avance,\n[Votre prénom]\nHelpdesk N1"},
    {"id": "__pre_7", "categorie": "Mail", "titre": "Mail – Résolution et clôture ticket",
     "contenu": "Objet : Résolution – Ticket #[NUMÉRO]\n\nBonjour [Prénom],\n\nNous revenons vers vous concernant votre incident du [DATE].\n\nLa situation a été résolue de la façon suivante :\n[DÉCRIRE LA SOLUTION APPLIQUÉE]\n\nN'hésitez pas à nous recontacter si le problème venait à réapparaître ou si vous avez d'autres questions.\n\nBien cordialement,\n[Votre prénom]\nHelpdesk N1"},
    {"id": "__pre_8", "categorie": "Escalade", "titre": "Note – Escalade vers N2",
     "contenu": "[NOTE INTERNE – ESCALADE N2]\n\nTicket traité en N1 – Escalade nécessaire.\n\nDiagnostic N1 :\n-\n-\n\nRaison de l'escalade :\n\n\nInterlocuteur N2 contacté :\nDate / Heure contact :\nRéférence escalade :\n\nActions en attente :"},
    {"id": "__pre_9", "categorie": "Note", "titre": "Note – Suivi intervention en cours",
     "contenu": "[SUIVI INTERVENTION]\n\nDate :\nTechnicien :\n\nStatut : En cours / En attente utilisateur / En attente N2\n\nDernière action effectuée :\n\n\nProchaine étape :\n\n\nDate de relance prévue :"},
]
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
    show_gabarit_form: bool = False
    gabarit_form: dict = {"titre": "", "categorie": "Ticket", "contenu": ""}

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
        custom = sorted(db.get("gabarits") or [], key=lambda g: g.get("date_creation") or "", reverse=True)
        columns: dict[str, list] = {cat: [] for cat in GABARIT_CATEGORIES}
        for g in _PREDEFINED_GABARITS:
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
        self.gabarit_columns = [
            GabaritColumn(category=cat, items=items)
            for cat, items in columns.items()
        ]

    def open_gabarit_form(self):
        self.gabarit_form = {"titre": "", "categorie": "Ticket", "contenu": ""}
        self.show_gabarit_form = True

    def open_gabarit_form_with_cat(self, cat: str):
        self.gabarit_form = {"titre": "", "categorie": cat, "contenu": ""}
        self.show_gabarit_form = True

    def close_gabarit_form(self):
        self.show_gabarit_form = False

    def set_gabarit_field(self, f: str, v: str):
        self.gabarit_form = {**self.gabarit_form, f: v}

    def create_gabarit(self):
        if not self.gabarit_form.get("titre") or not self.gabarit_form.get("contenu"):
            return
        db = load_db()
        if "gabarits" not in db:
            db["gabarits"] = []
        db["gabarits"].append({
            "id": str(uuid.uuid4()),
            "titre": self.gabarit_form.get("titre") or "",
            "categorie": self.gabarit_form.get("categorie") or "Ticket",
            "contenu": self.gabarit_form.get("contenu") or "",
            "date_creation": datetime.utcnow().isoformat(),
            "auteur_nom": "",
        })
        save_db(db)
        self.show_gabarit_form = False
        self.load_gabarits()

    def delete_gabarit(self, gid: str):
        db = load_db()
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


def doc_row(doc: DocumentItem) -> rx.Component:
    is_link = doc["type"] == "lien"
    return rx.hstack(
        rx.box(
            rx.cond(
                is_link,
                rx.icon("link-2", size=16, color="#a5b4fc"),
                rx.icon("file", size=16, color=MUTED),
            ),
            flex_shrink="0",
            width="2.25rem",
            height="2.25rem",
            background=rx.cond(is_link, "rgba(99,102,241,0.15)", "rgba(255,255,255,0.05)"),
            border_radius="8px",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
        rx.box(
            rx.cond(
                is_link,
                rx.link(
                    doc["nom_original"],
                    href=doc["url"],
                    color="#a5b4fc",
                    font_weight="600",
                    font_size="0.875rem",
                    target="_blank",
                    display="block",
                    white_space="nowrap",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    _hover={"text_decoration": "underline"},
                ),
                rx.text(
                    doc["nom_original"],
                    color=TEXT,
                    font_weight="600",
                    font_size="0.875rem",
                    white_space="nowrap",
                    overflow="hidden",
                    text_overflow="ellipsis",
                ),
            ),
            rx.cond(
                doc["description"] != "",
                rx.text(doc["description"], color=MUTED, font_size="0.75rem", white_space="nowrap", overflow="hidden", text_overflow="ellipsis"),
            ),
            rx.cond(
                is_link & (doc["url"] != ""),
                rx.text(doc["url"], color="#334155", font_size="0.7rem", white_space="nowrap", overflow="hidden", text_overflow="ellipsis"),
            ),
            flex="1",
            min_width="0",
        ),
        rx.spacer(),
        rx.cond(
            is_link,
            rx.badge("Lien", color_scheme="violet", variant="soft", radius="full", font_size="0.65rem"),
        ),
        rx.icon_button(
            rx.icon("trash-2", size=14),
            on_click=DocumentsState.delete_doc(doc["id"]),
            background="transparent",
            color=MUTED,
            border="none",
            border_radius="6px",
            size="1",
            cursor="pointer",
            _hover={"background": "rgba(239,68,68,0.15)", "color": "#ef4444"},
        ),
        spacing="3",
        align="center",
        width="100%",
        padding="0.75rem 1.25rem",
        border_bottom=f"1px solid {BORDER}",
        _hover={"background": "rgba(255,255,255,0.025)"},
        transition="background 0.1s",
    )


def group_section(group: DocGroup) -> rx.Component:
    return rx.vstack(
        rx.text(
            group["name"],
            color=MUTED,
            font_size="0.7rem",
            font_weight="700",
            text_transform="uppercase",
            letter_spacing="0.07em",
            padding_left="0.25rem",
        ),
        rx.box(
            rx.foreach(group["docs"], doc_row),
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="14px",
            overflow="hidden",
            width="100%",
        ),
        spacing="2",
        width="100%",
        align="start",
    )


def internal_sources_section() -> rx.Component:
    return rx.vstack(
        rx.text("Données internes", color=MUTED, font_size="0.7rem", font_weight="700", text_transform="uppercase", letter_spacing="0.07em", padding_left="0.25rem"),
        rx.box(
            rx.hstack(
                rx.box(
                    rx.icon("git-branch", size=18, color="#a5b4fc"),
                    flex_shrink="0", width="2.25rem", height="2.25rem",
                    background="rgba(99,102,241,0.15)", border_radius="8px",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.vstack(
                    rx.text("Matrice d'escalade", color=TEXT, font_weight="600", font_size="0.875rem"),
                    rx.text(DocumentsState.escalade_count.to_string() + " règles de routage N1/N2/N3", color=MUTED, font_size="0.75rem"),
                    spacing="0", align="start",
                ),
                rx.spacer(),
                rx.badge("Interne", color_scheme="indigo", variant="soft", font_size="0.72rem"),
                rx.icon("external-link", size=14, color=MUTED),
                spacing="3", align="center", width="100%",
                padding="0.875rem 1.25rem",
                border_bottom=f"1px solid {BORDER}",
                cursor="pointer",
                _hover={"background": "rgba(255,255,255,0.03)"},
                on_click=rx.redirect("/escalade"),
            ),
            rx.hstack(
                rx.box(
                    rx.icon("calendar", size=18, color="#7dd3fc"),
                    flex_shrink="0", width="2.25rem", height="2.25rem",
                    background="rgba(14,165,233,0.15)", border_radius="8px",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.vstack(
                    rx.text("Planning", color=TEXT, font_weight="600", font_size="0.875rem"),
                    rx.text("Planning hebdomadaire de l'équipe", color=MUTED, font_size="0.75rem"),
                    spacing="0", align="start",
                ),
                rx.spacer(),
                rx.badge("Interne", color_scheme="cyan", variant="soft", font_size="0.72rem"),
                rx.icon("external-link", size=14, color=MUTED),
                spacing="3", align="center", width="100%",
                padding="0.875rem 1.25rem",
                cursor="pointer",
                _hover={"background": "rgba(255,255,255,0.03)"},
                on_click=rx.redirect("/planning"),
            ),
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="14px",
            overflow="hidden",
            width="100%",
        ),
        spacing="2", width="100%", align="start",
    )


def _gabarit_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.box(
                rx.hstack(
                    rx.box(
                        rx.icon("file-plus", size=18, color="white"),
                        background="rgba(255,255,255,0.2)", border_radius="10px", padding="8px",
                        display="flex", align_items="center", justify_content="center",
                    ),
                    rx.vstack(
                        rx.text("Nouveau gabarit", color="white", font_size="1rem", font_weight="700"),
                        rx.text("Créer un modèle réutilisable", color="rgba(255,255,255,0.7)", font_size="0.72rem"),
                        spacing="0", align="start",
                    ),
                    spacing="3", align="center",
                ),
                background="linear-gradient(135deg, #1e1b4b, #4338ca)",
                border_radius="12px 12px 0 0",
                padding="1.25rem 1.5rem",
                margin="-24px -24px 0 -24px",
            ),
            rx.vstack(
                rx.vstack(
                    rx.hstack(
                        rx.text("TITRE", color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.07em"),
                        rx.text("*", color="#ef4444", font_size="0.75rem"),
                        spacing="1",
                    ),
                    rx.input(
                        placeholder="Ex : Mail – Confirmation prise en charge",
                        value=DocumentsState.gabarit_form["titre"],
                        on_change=lambda v: DocumentsState.set_gabarit_field("titre", v),
                        background="#1e2035", color=TEXT,
                        border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px", width="100%",
                    ),
                    spacing="1", align="start", width="100%",
                ),
                rx.vstack(
                    rx.text("CATÉGORIE", color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.07em"),
                    rx.select(
                        GABARIT_CATEGORIES,
                        value=DocumentsState.gabarit_form["categorie"],
                        on_change=lambda v: DocumentsState.set_gabarit_field("categorie", v),
                        background="#1e2035", color=TEXT,
                        border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px",
                    ),
                    spacing="1", align="start", width="100%",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text("CONTENU", color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.07em"),
                        rx.text("*", color="#ef4444", font_size="0.75rem"),
                        spacing="1",
                    ),
                    rx.text_area(
                        placeholder="Coller ici le texte du gabarit…",
                        value=DocumentsState.gabarit_form["contenu"],
                        on_change=lambda v: DocumentsState.set_gabarit_field("contenu", v),
                        background="#1e2035", color=TEXT,
                        border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px", width="100%",
                        rows="10",
                        font_family="'Courier New', monospace",
                        font_size="0.8rem",
                    ),
                    spacing="1", align="start", width="100%",
                ),
                rx.hstack(
                    rx.button(
                        "Annuler",
                        on_click=DocumentsState.close_gabarit_form,
                        background="transparent", color=MUTED,
                        border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px", cursor="pointer",
                    ),
                    rx.button(
                        rx.icon("save", size=15),
                        "Enregistrer",
                        on_click=DocumentsState.create_gabarit,
                        background="linear-gradient(135deg, #1e1b4b, #4338ca)",
                        color="white", border_radius="8px", cursor="pointer",
                        font_weight="700", spacing="2",
                    ),
                    spacing="3", justify="end", width="100%",
                ),
                spacing="4", width="100%", padding_top="1.25rem",
            ),
            background="#151728",
            border=f"1px solid rgba(255,255,255,0.1)",
            border_radius="16px",
            padding="24px",
            max_width="540px",
            overflow="hidden",
        ),
        open=DocumentsState.show_gabarit_form,
    )


def gabarit_kanban_card(g: GabaritItem) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(
                g["titre"],
                font_size="0.82rem",
                font_weight="500",
                color=TEXT,
                flex="1",
                min_width="0",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
                line_height="1.4",
            ),
            rx.hstack(
                rx.icon_button(
                    rx.icon("copy", size=12),
                    on_click=DocumentsState.copy_gabarit(g["contenu"]),
                    background="transparent",
                    color=MUTED,
                    border="none",
                    size="1",
                    cursor="pointer",
                    _hover={"color": "#22c55e", "background": "rgba(34,197,94,0.12)"},
                ),
                rx.cond(
                    g["is_custom"],
                    rx.icon_button(
                        rx.icon("trash-2", size=12),
                        on_click=DocumentsState.delete_gabarit(g["id"]),
                        background="rgba(239,68,68,0.08)",
                        color="#ef4444",
                        border="1px solid rgba(239,68,68,0.25)",
                        size="1",
                        border_radius="6px",
                        cursor="pointer",
                        _hover={"background": "rgba(239,68,68,0.2)", "border_color": "rgba(239,68,68,0.5)"},
                    ),
                ),
                spacing="1",
                flex_shrink="0",
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="8px",
        padding="0.55rem 0.7rem",
        width="100%",
        transition="all 0.12s",
        _hover={"border_color": "rgba(99,102,241,0.45)", "background": "rgba(99,102,241,0.04)"},
    )


def gabarit_kanban_column(col: GabaritColumn) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(col["category"], font_weight="700", font_size="0.82rem", color=TEXT),
            rx.box(
                rx.text(col["items"].length().to_string(),
                        font_size="0.7rem", font_weight="700", color=MUTED),
                background="rgba(255,255,255,0.06)",
                border_radius="999px",
                padding="1px 8px",
            ),
            rx.spacer(),
            rx.icon_button(
                rx.icon("plus", size=13),
                on_click=DocumentsState.open_gabarit_form_with_cat(col["category"]),
                background="transparent",
                color=MUTED,
                border=f"1px solid {BORDER}",
                size="1",
                border_radius="6px",
                cursor="pointer",
                _hover={"background": "rgba(99,102,241,0.15)", "color": "#a5b4fc",
                        "border_color": "rgba(99,102,241,0.4)"},
            ),
            spacing="2", align="center", width="100%",
            padding_bottom="0.6rem",
            border_bottom=f"1px solid {BORDER}",
        ),
        rx.vstack(
            rx.foreach(col["items"], gabarit_kanban_card),
            spacing="2",
            width="100%",
        ),
        background="rgba(255,255,255,0.015)",
        border=f"1px solid {BORDER}",
        border_radius="12px",
        padding="0.875rem",
        spacing="3",
        width="0",
        flex="1",
        min_width="190px",
        align="start",
    )


def gabarits_tab_view() -> rx.Component:
    return rx.vstack(
        # Header avec bouton d'ajout
        rx.hstack(
            rx.vstack(
                rx.text("Gabarits", color=TEXT, font_weight="700", font_size="1rem"),
                rx.text("Modèles de tickets, mails et notes prêts à copier",
                        color=MUTED, font_size="0.78rem"),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=15),
                "Nouveau gabarit",
                on_click=DocumentsState.open_gabarit_form,
                background="rgba(99,102,241,0.15)",
                color="#a5b4fc",
                border="1.5px solid rgba(99,102,241,0.35)",
                border_radius="10px",
                font_size="0.82rem",
                font_weight="600",
                padding="0.5rem 1.1rem",
                cursor="pointer",
                spacing="2",
                _hover={"background": "rgba(99,102,241,0.28)", "border_color": "rgba(99,102,241,0.6)"},
            ),
            width="100%",
            align="center",
            padding_bottom="0.75rem",
            border_bottom=f"1px solid {BORDER}",
        ),
        # Kanban board
        rx.hstack(
            rx.foreach(DocumentsState.gabarit_columns, gabarit_kanban_column),
            spacing="3",
            align="start",
            width="100%",
        ),
        _gabarit_dialog(),
        spacing="4",
        width="100%",
    )


def tab_bar() -> rx.Component:
    tabs = [
        ("documents", "folder-open", "Documents"),
        ("gabarits", "file-text", "Gabarits"),
    ]
    return rx.hstack(
        *[
            rx.button(
                rx.icon(icon, size=14),
                label,
                on_click=DocumentsState.set_tab(key),
                background=rx.cond(DocumentsState.current_tab == key, "rgba(99,102,241,0.18)", "transparent"),
                color=rx.cond(DocumentsState.current_tab == key, "#a5b4fc", MUTED),
                border=rx.cond(DocumentsState.current_tab == key, "1px solid rgba(99,102,241,0.4)", f"1px solid {BORDER}"),
                border_radius="8px",
                font_size="0.8rem",
                font_weight="600",
                padding="0.35rem 0.875rem",
                cursor="pointer",
                spacing="2",
                _hover={"background": "rgba(99,102,241,0.1)", "color": "#a5b4fc"},
            )
            for key, icon, label in tabs
        ],
        spacing="2",
        padding_bottom="0.5rem",
        border_bottom=f"1px solid {BORDER}",
        width="100%",
    )


def documents_content() -> rx.Component:
    return rx.vstack(
        # Barre d'onglets
        tab_bar(),
        # Vue Gabarits
        rx.cond(
            DocumentsState.current_tab == "gabarits",
            gabarits_tab_view(),
        ),
        # Vue Documents
        rx.cond(
            DocumentsState.current_tab == "documents",
            rx.vstack(
        # Header
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.icon("folder-open", size=22, color="#7dd3fc"),
                    rx.heading("Documents partagés", size="5", color=TEXT, font_weight="800"),
                    spacing="2", align="center",
                ),
                rx.text(
                    DocumentsState.total_count.to_string() + " document(s) disponible(s)",
                    color=MUTED, font_size="0.875rem",
                ),
                spacing="1", align="start",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("link-2", size=16),
                "Ajouter un lien",
                on_click=DocumentsState.open_link_form,
                background="rgba(99,102,241,0.15)",
                color="#a5b4fc",
                border="1.5px solid rgba(99,102,241,0.3)",
                border_radius="10px",
                font_size="0.875rem",
                font_weight="600",
                padding="0.6rem 1.25rem",
                cursor="pointer",
                spacing="2",
                _hover={"background": "rgba(99,102,241,0.25)", "border_color": "rgba(99,102,241,0.5)"},
            ),
            width="100%", align="center",
        ),
        # Filtres catégorie (pills)
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text("Catégorie", color=MUTED, font_size="0.72rem", font_weight="700", text_transform="uppercase", letter_spacing="0.05em"),
                    *[
                        rx.button(
                            cat or "Tous",
                            on_click=DocumentsState.set_cat(cat),
                            background=rx.cond(DocumentsState.filter_cat == cat, "#2563eb", "rgba(255,255,255,0.05)"),
                            color=rx.cond(DocumentsState.filter_cat == cat, "white", MUTED),
                            border="none",
                            border_radius="999px",
                            font_size="0.8rem",
                            font_weight="600",
                            padding="0.3rem 0.875rem",
                            cursor="pointer",
                            _hover={"background": rx.cond(DocumentsState.filter_cat == cat, "#1d4ed8", "rgba(255,255,255,0.1)")},
                        )
                        for cat in ["", *CATEGORIES]
                    ],
                    spacing="2",
                    align="center",
                    wrap="wrap",
                ),
                rx.cond(
                    DocumentsState.filter_cat == "Procédures",
                    rx.hstack(
                        rx.text("Dossier", color="#334155", font_size="0.7rem", font_weight="700", text_transform="uppercase", letter_spacing="0.05em"),
                        *[
                            rx.button(
                                sc or "Tous",
                                on_click=DocumentsState.set_sous_cat(sc),
                                background=rx.cond(DocumentsState.filter_sous_cat == sc, "rgba(99,102,241,0.8)", "rgba(255,255,255,0.04)"),
                                color=rx.cond(DocumentsState.filter_sous_cat == sc, "white", MUTED),
                                border="none",
                                border_radius="999px",
                                font_size="0.75rem",
                                font_weight="600",
                                padding="0.2rem 0.7rem",
                                cursor="pointer",
                                white_space="nowrap",
                                _hover={"background": rx.cond(DocumentsState.filter_sous_cat == sc, "rgba(99,102,241,0.9)", "rgba(255,255,255,0.08)")},
                            )
                            for sc in ["", *SOUS_CATEGORIES]
                        ],
                        spacing="2",
                        align="center",
                        wrap="wrap",
                        padding_top="0.5rem",
                        border_top=f"1px solid {BORDER}",
                    ),
                ),
                spacing="3", align="start",
            ),
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="12px",
            padding="0.75rem 1rem",
            width="100%",
        ),
        # Données internes (seulement sans filtre catégorie)
        rx.cond(
            DocumentsState.filter_cat == "",
            internal_sources_section(),
        ),
        # Documents groupés
        rx.cond(
            DocumentsState.doc_groups.length() == 0,
            rx.box(
                rx.vstack(
                    rx.icon("folder-open", size=48, color=MUTED),
                    rx.text("Aucun document disponible", color=MUTED, font_size="0.875rem"),
                    spacing="3", align="center",
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="14px",
                padding="5rem",
                display="flex",
                justify_content="center",
                width="100%",
            ),
            rx.vstack(
                rx.foreach(DocumentsState.doc_groups, group_section),
                spacing="4",
                width="100%",
            ),
        ),
        # Dialog ajout lien
        rx.dialog.root(
            rx.dialog.content(

                # Header gradient
                rx.box(
                    rx.hstack(
                        rx.box(
                            rx.icon("link-2", size=18, color="white"),
                            background="rgba(255,255,255,0.2)",
                            border_radius="10px",
                            padding="8px",
                            display="flex", align_items="center", justify_content="center",
                        ),
                        rx.vstack(
                            rx.text("Ajouter un lien", color="white", font_size="1rem", font_weight="700"),
                            rx.text("Référencer une ressource externe",
                                    color="rgba(255,255,255,0.7)", font_size="0.72rem"),
                            spacing="0", align="start",
                        ),
                        spacing="3", align="center",
                    ),
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    border_radius="12px 12px 0 0",
                    padding="1.25rem 1.5rem",
                    margin="-24px -24px 0 -24px",
                ),

                rx.vstack(
                    rx.vstack(
                        rx.hstack(
                            rx.text("NOM", color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.07em"),
                            rx.text("*", color="#ef4444", font_size="0.75rem"),
                            spacing="1",
                        ),
                        rx.input(
                            placeholder="Nom du document ou lien…",
                            value=DocumentsState.link_form["nom"],
                            on_change=lambda v: DocumentsState.set_link_field("nom", v),
                            background="#1e2035", color=TEXT,
                            border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px", width="100%",
                        ),
                        spacing="1", align="start", width="100%",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.text("URL", color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.07em"),
                            rx.text("*", color="#ef4444", font_size="0.75rem"),
                            spacing="1",
                        ),
                        rx.input(
                            placeholder="https://…",
                            value=DocumentsState.link_form["url"],
                            on_change=lambda v: DocumentsState.set_link_field("url", v),
                            background="#1e2035", color=TEXT,
                            border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px", width="100%",
                        ),
                        spacing="1", align="start", width="100%",
                    ),
                    rx.hstack(
                        rx.vstack(
                            rx.text("CATÉGORIE", color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.07em"),
                            rx.select(
                                CATEGORIES,
                                value=DocumentsState.link_form["categorie"],
                                on_change=lambda v: DocumentsState.set_link_field("categorie", v),
                                background="#1e2035", color=TEXT,
                                border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px",
                            ),
                            spacing="1", align="start", flex="1",
                        ),
                        rx.vstack(
                            rx.text("DOSSIER", color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.07em"),
                            rx.select(
                                SOUS_CATEGORIES,
                                placeholder="Optionnel",
                                value=DocumentsState.link_form["sous_categorie"],
                                on_change=lambda v: DocumentsState.set_link_field("sous_categorie", v),
                                background="#1e2035", color=TEXT,
                                border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px",
                            ),
                            spacing="1", align="start", flex="1",
                        ),
                        spacing="3", width="100%",
                    ),
                    rx.vstack(
                        rx.text("DESCRIPTION", color=MUTED, font_size="0.68rem", font_weight="700", letter_spacing="0.07em"),
                        rx.text_area(
                            placeholder="Description optionnelle…",
                            value=DocumentsState.link_form["description"],
                            on_change=lambda v: DocumentsState.set_link_field("description", v),
                            background="#1e2035", color=TEXT,
                            border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px", width="100%",
                            rows="2",
                        ),
                        spacing="1", align="start", width="100%",
                    ),
                    rx.hstack(
                        rx.button("Annuler", on_click=DocumentsState.close_link_form,
                                  background="transparent", color=MUTED,
                                  border=f"1px solid rgba(255,255,255,0.12)", border_radius="8px", cursor="pointer"),
                        rx.button(
                            rx.icon("plus", size=15),
                            "Ajouter",
                            on_click=DocumentsState.create_link,
                            background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                            color="white", border_radius="8px", cursor="pointer",
                            font_weight="700", spacing="2",
                        ),
                        spacing="3", justify="end", width="100%",
                    ),
                    spacing="4", width="100%", padding_top="1.25rem",
                ),

                background="#151728",
                border=f"1px solid rgba(255,255,255,0.1)",
                border_radius="16px",
                padding="24px",
                max_width="480px",
                overflow="hidden",
            ),
            open=DocumentsState.show_link_form,
        ),
            spacing="5",
            width="100%",
            align="start",
        ),  # fin rx.vstack documents
        ),  # fin rx.cond documents
        spacing="5",
        width="100%",
        on_mount=DocumentsState.load,
    )


def documents_page() -> rx.Component:
    return page_layout(documents_content(), "Documents")
