import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.components.icons import dyn_icon
from techpilot.state.formation import (
    FormationState, FORMATION_CATEGORIES, ONBOARDING_CATS,
    RADIAL_SIZE, NODE_SIZE, LABEL_WIDTH,
)
from techpilot.state.models import FormationModule, OnboardingStep, OnboardingTechProgress
from techpilot.state.auth import AuthState

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
CARD_BG = "#111524"
BORDER  = "#1c2138"
PRIMARY = "#6366f1"
GREEN   = "#22c55e"
AMBER   = "#f59e0b"
RED     = "#ef4444"
CYAN    = "#06b6d4"

# Couleur par catégorie module
CAT_COLORS = {
    "Réseau":        CYAN,
    "Active Directory": "#8b5cf6",
    "Freshservice":  "#3b82f6",
    "Téléphonie":    GREEN,
    "Sécurité":      RED,
    "Processus N1":  AMBER,
    "Autre":         MUTED,
}

# Couleur par difficulté
DIFF_SCHEME = {
    "Débutant":      "green",
    "Intermédiaire": "amber",
    "Avancé":        "red",
}

ONBOARDING_CAT_COLORS = {
    "Accès":     "#6366f1",
    "Outils":    CYAN,
    "Processus": AMBER,
    "Formation": GREEN,
    "Autre":     MUTED,
}


def _cat_color(cat) -> rx.Component:
    return rx.match(
        cat,
        ("Réseau",         CYAN),
        ("Active Directory", "#8b5cf6"),
        ("Freshservice",   "#3b82f6"),
        ("Téléphonie",     GREEN),
        ("Sécurité",       RED),
        ("Processus N1",   AMBER),
        MUTED,
    )


def _diff_scheme(diff) -> rx.Component:
    return rx.match(
        diff,
        ("Débutant",      "green"),
        ("Intermédiaire", "amber"),
        ("Avancé",        "red"),
        "gray",
    )


def _ob_cat_color(cat) -> rx.Component:
    return rx.match(
        cat,
        ("Accès",     PRIMARY),
        ("Outils",    CYAN),
        ("Processus", AMBER),
        ("Formation", GREEN),
        MUTED,
    )


# ── Carte module ──────────────────────────────────────────────────────────────
def module_card(m: FormationModule) -> rx.Component:
    is_read = FormationState.my_reads.contains(m["id"])
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.badge(
                    m["categorie"],
                    color=_cat_color(m["categorie"]),
                    background="rgba(99,102,241,0.12)",
                    border_radius="full", font_size="0.68rem", padding="2px 8px",
                ),
                rx.spacer(),
                rx.badge(
                    m["difficulte"],
                    color_scheme=_diff_scheme(m["difficulte"]),
                    variant="soft", radius="full", font_size="0.68rem",
                ),
                align="center", width="100%",
            ),
            rx.text(m["titre"], color=TEXT, font_weight="600", font_size="0.9rem",
                    line_height="1.3", margin_top="0.4rem"),
            rx.text(m["description"], color=MUTED, font_size="0.78rem",
                    line_height="1.5", no_of_lines=2),
            rx.spacer(),
            rx.hstack(
                rx.hstack(
                    rx.icon("eye", size=12, color=MUTED),
                    rx.text(m["lu_count"].to_string() + " lu", color=MUTED, font_size="0.72rem"),
                    spacing="1", align="center",
                ),
                rx.spacer(),
                rx.cond(
                    is_read,
                    rx.hstack(
                        rx.icon("check-circle", size=13, color=GREEN),
                        rx.text("Lu", color=GREEN, font_size="0.72rem", font_weight="600"),
                        spacing="1", align="center",
                    ),
                    rx.text("À lire", color=MUTED, font_size="0.72rem"),
                ),
                align="center", width="100%",
            ),
            rx.hstack(
                rx.button(
                    rx.icon("book-open", size=13), "Lire",
                    on_click=FormationState.open_mod_detail(m["id"]),
                    background=f"rgba(99,102,241,0.1)", color=PRIMARY,
                    border=f"1px solid rgba(99,102,241,0.3)", border_radius="6px",
                    font_size="0.78rem", padding="5px 12px", cursor="pointer",
                    _hover={"background": f"rgba(99,102,241,0.2)"},
                ),
                rx.cond(
                    AuthState.is_manager,
                    rx.hstack(
                        rx.icon_button(
                            rx.icon("pencil", size=13),
                            on_click=FormationState.open_mod_edit(m["id"]),
                            background="transparent", color=MUTED,
                            border=f"1px solid {BORDER}", border_radius="6px",
                            size="2", cursor="pointer",
                            _hover={"color": PRIMARY, "border_color": PRIMARY},
                        ),
                        rx.icon_button(
                            rx.icon("trash-2", size=13),
                            on_click=FormationState.delete_module(m["id"]),
                            background="transparent", color=MUTED,
                            border=f"1px solid {BORDER}", border_radius="6px",
                            size="2", cursor="pointer",
                            _hover={"color": RED, "border_color": RED},
                        ),
                        spacing="2",
                    ),
                ),
                spacing="2", align="center", width="100%",
            ),
            spacing="2", align="start", width="100%", height="100%",
        ),
        background=CARD_BG,
        border=rx.cond(
            is_read,
            f"1px solid {GREEN}44",
            f"1px solid {BORDER}",
        ),
        border_radius="14px",
        padding="1.1rem",
        min_height="200px",
        display="flex",
        flex_direction="column",
        _hover={"border_color": PRIMARY},
        transition="border-color 0.2s",
    )


# ── Modal détail module ───────────────────────────────────────────────────────
def module_detail_dialog() -> rx.Component:
    is_read = FormationState.my_reads.contains(FormationState.detail_mod_id)
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.badge(
                            FormationState.detail_mod_categorie,
                            color=_cat_color(FormationState.detail_mod_categorie),
                            background=f"rgba(99,102,241,0.1)",
                            border_radius="full", font_size="0.7rem",
                        ),
                        rx.badge(
                            FormationState.detail_mod_difficulte,
                            color_scheme=_diff_scheme(FormationState.detail_mod_difficulte),
                            variant="soft", radius="full", font_size="0.7rem",
                        ),
                        spacing="2",
                    ),
                    rx.heading(FormationState.detail_mod_titre, size="5", color=TEXT, font_weight="700"),
                    rx.hstack(
                        rx.icon("user", size=12, color=MUTED),
                        rx.text(FormationState.detail_mod_auteur, color=MUTED, font_size="0.72rem"),
                        rx.text("·", color=MUTED, font_size="0.72rem"),
                        rx.text(FormationState.detail_mod_date, color=MUTED, font_size="0.72rem"),
                        rx.text("·", color=MUTED, font_size="0.72rem"),
                        rx.icon("eye", size=12, color=MUTED),
                        rx.text(FormationState.detail_mod_read_count.to_string() + " lu",
                                color=MUTED, font_size="0.72rem"),
                        spacing="1", align="center",
                    ),
                    spacing="2", align="start",
                ),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("x", size=15),
                    on_click=FormationState.close_mod_detail,
                    background="rgba(255,255,255,0.06)", color=MUTED,
                    border_radius="7px", size="2", cursor="pointer",
                ),
                align="start", width="100%",
            ),
            rx.divider(border_color=BORDER, margin_y="1rem"),
            rx.box(
                rx.markdown(FormationState.detail_mod_contenu),
                max_height="55vh", overflow_y="auto",
                style={
                    "p":    {"color": MUTED, "font_size": "0.875rem", "line_height": "1.7"},
                    "li":   {"color": MUTED, "font_size": "0.875rem"},
                    "h2":   {"color": TEXT, "font_weight": "700", "margin_top": "1.25rem", "margin_bottom": "0.5rem"},
                    "h3":   {"color": TEXT, "font_weight": "600", "margin_top": "1rem"},
                    "code": {"background": "rgba(99,102,241,0.15)", "color": "#a5b4fc",
                             "border_radius": "4px", "padding": "1px 6px"},
                    "strong": {"color": TEXT},
                },
            ),
            rx.divider(border_color=BORDER, margin_y="1rem"),
            rx.hstack(
                rx.button(
                    rx.cond(is_read,
                        rx.hstack(rx.icon("check-circle", size=14), rx.text("Marquer non lu"), spacing="2", align="center"),
                        rx.hstack(rx.icon("circle", size=14), rx.text("Marquer comme lu"), spacing="2", align="center"),
                    ),
                    on_click=FormationState.toggle_read(FormationState.detail_mod_id),
                    background=rx.cond(is_read, f"rgba(34,197,94,0.15)", f"rgba(34,197,94,0.1)"),
                    color=GREEN, border=f"1px solid rgba(34,197,94,0.3)",
                    border_radius="8px", cursor="pointer", font_size="0.85rem",
                    _hover={"background": "rgba(34,197,94,0.25)"},
                ),
                rx.spacer(),
                rx.button(
                    "Fermer", on_click=FormationState.close_mod_detail,
                    background="transparent", color=MUTED,
                    border=f"1px solid {BORDER}", border_radius="8px", cursor="pointer",
                ),
                width="100%", align="center",
            ),
            background="#111524",
            border=f"1px solid {BORDER}",
            border_radius="16px",
            padding="1.5rem",
            max_width="700px",
            width="95vw",
        ),
        open=FormationState.show_mod_detail,
    )


# ── Formulaire module ─────────────────────────────────────────────────────────
def module_form_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.text(
                    rx.cond(FormationState.edit_mod_id != "", "Modifier le module", "Nouveau module"),
                    color=TEXT, font_weight="700", font_size="1rem",
                ),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("x", size=15),
                    on_click=FormationState.close_mod_form,
                    background="rgba(255,255,255,0.06)", color=MUTED,
                    border_radius="7px", size="2", cursor="pointer",
                ),
                width="100%", align="center", margin_bottom="1rem",
            ),
            rx.vstack(
                rx.input(
                    placeholder="Titre *",
                    value=FormationState.mod_form["titre"],
                    on_change=lambda v: FormationState.set_mod_field("titre", v),
                    background="#0d1021", color=TEXT, border=f"1px solid {BORDER}",
                    border_radius="8px", width="100%",
                    _focus={"border_color": PRIMARY},
                ),
                rx.select(
                    FORMATION_CATEGORIES,
                    value=FormationState.mod_form["categorie"],
                    on_change=lambda v: FormationState.set_mod_field("categorie", v),
                    background="#0d1021", color=TEXT, border=f"1px solid {BORDER}",
                    border_radius="8px", width="100%",
                ),
                rx.select(
                    ["Débutant", "Intermédiaire", "Avancé"],
                    value=FormationState.mod_form["difficulte"],
                    on_change=lambda v: FormationState.set_mod_field("difficulte", v),
                    background="#0d1021", color=TEXT, border=f"1px solid {BORDER}",
                    border_radius="8px", width="100%",
                ),
                rx.input(
                    placeholder="Description courte",
                    value=FormationState.mod_form["description"],
                    on_change=lambda v: FormationState.set_mod_field("description", v),
                    background="#0d1021", color=TEXT, border=f"1px solid {BORDER}",
                    border_radius="8px", width="100%",
                    _focus={"border_color": PRIMARY},
                ),
                rx.text_area(
                    placeholder="Contenu (Markdown)…",
                    value=FormationState.mod_form["contenu"],
                    on_change=lambda v: FormationState.set_mod_field("contenu", v),
                    background="#0d1021", color=TEXT, border=f"1px solid {BORDER}",
                    border_radius="8px", width="100%", rows="10",
                    font_family="monospace", font_size="0.82rem",
                    _focus={"border_color": PRIMARY},
                ),
                rx.hstack(
                    rx.button("Annuler", on_click=FormationState.close_mod_form,
                              background="transparent", color=MUTED,
                              border=f"1px solid {BORDER}", border_radius="8px", cursor="pointer"),
                    rx.button("Enregistrer", on_click=FormationState.save_module,
                              background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                              color="white", border_radius="8px", cursor="pointer", font_weight="600"),
                    spacing="3", justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            background="#111524", border=f"1px solid {BORDER}",
            border_radius="16px", padding="1.5rem", max_width="620px", width="95vw",
        ),
        open=FormationState.show_mod_form,
    )


# ── Onglet Modules ────────────────────────────────────────────────────────────
def modules_tab() -> rx.Component:
    return rx.vstack(
        # Barre de recherche + filtres
        rx.hstack(
            rx.input(
                placeholder="Rechercher un module…",
                value=FormationState.mod_search,
                on_change=FormationState.set_mod_search,
                background=CARD_BG, color=TEXT, border=f"1px solid {BORDER}",
                border_radius="8px", width="260px", font_size="0.85rem",
                _focus={"border_color": PRIMARY},
            ),
            rx.spacer(),
            rx.cond(
                AuthState.is_manager,
                rx.button(
                    rx.icon("plus", size=15), "Nouveau module",
                    on_click=FormationState.open_mod_create,
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    color="white", border_radius="8px", font_size="0.85rem",
                    padding="8px 16px", cursor="pointer", spacing="2",
                ),
            ),
            width="100%", align="center",
        ),
        # Chips catégories
        rx.hstack(
            *[
                rx.button(
                    cat,
                    on_click=FormationState.set_cat_filter(cat),
                    background=rx.cond(
                        FormationState.cat_filter == cat,
                        "rgba(99,102,241,0.2)", "transparent",
                    ),
                    color=rx.cond(
                        FormationState.cat_filter == cat,
                        PRIMARY, MUTED,
                    ),
                    border=rx.cond(
                        FormationState.cat_filter == cat,
                        "1px solid rgba(99,102,241,0.4)", f"1px solid {BORDER}",
                    ),
                    border_radius="20px", font_size="0.75rem",
                    padding="3px 12px", cursor="pointer",
                    _hover={"border_color": PRIMARY, "color": PRIMARY},
                )
                for cat in FORMATION_CATEGORIES
            ],
            wrap="wrap", spacing="2",
        ),
        # Grille
        rx.cond(
            FormationState.modules_view.length() > 0,
            rx.grid(
                rx.foreach(FormationState.modules_view, module_card),
                columns="3", spacing="4", width="100%",
            ),
            rx.box(
                rx.vstack(
                    rx.icon("book-open", size=32, color=MUTED),
                    rx.text("Aucun module", color=MUTED, font_size="0.9rem"),
                    rx.cond(
                        AuthState.is_manager,
                        rx.text("Créez le premier module avec le bouton ci-dessus.",
                                color=MUTED, font_size="0.8rem"),
                    ),
                    spacing="3", align="center",
                ),
                padding="3rem", text_align="center", width="100%",
            ),
        ),
        module_form_dialog(),
        module_detail_dialog(),
        spacing="4", width="100%",
    )


# ── Carte tech onboarding ─────────────────────────────────────────────────────
def onboarding_tech_card(p: OnboardingTechProgress) -> rx.Component:
    total = FormationState.onboarding_steps.length()
    done_count = p["steps_done"].length()
    pct = rx.cond(total > 0, (done_count * 100 // total), 0)

    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.text(p["tech_nom"][:2].upper(), color="white",
                            font_weight="700", font_size="0.85rem"),
                    background=rx.cond(p["color"], p["color"], PRIMARY),
                    border_radius="50%", width="38px", height="38px",
                    display="flex", align_items="center", justify_content="center",
                    flex_shrink="0",
                ),
                rx.vstack(
                    rx.text(p["tech_nom"], color=TEXT, font_weight="600", font_size="0.9rem"),
                    rx.cond(
                        p["assigned"],
                        rx.text("Depuis le " + p["date_debut"], color=MUTED, font_size="0.72rem"),
                        rx.text("Pas de parcours assigné", color=MUTED, font_size="0.72rem"),
                    ),
                    spacing="0", align="start",
                ),
                rx.spacer(),
                rx.cond(
                    p["assigned"],
                    rx.vstack(
                        rx.text(pct.to_string() + "%", color=TEXT,
                                font_weight="700", font_size="1rem", text_align="right"),
                        rx.text(done_count.to_string() + "/" + total.to_string(),
                                color=MUTED, font_size="0.72rem", text_align="right"),
                        spacing="0", align="end",
                    ),
                ),
                spacing="3", align="center", width="100%",
            ),
            rx.cond(
                p["assigned"],
                rx.box(
                    rx.box(
                        background=rx.cond(p["color"], p["color"], PRIMARY),
                        width=pct.to_string() + "%",
                        height="4px",
                        border_radius="full",
                        transition="width 0.3s",
                    ),
                    background=f"rgba(255,255,255,0.06)",
                    border_radius="full",
                    width="100%",
                    overflow="hidden",
                ),
            ),
            rx.hstack(
                rx.cond(
                    p["assigned"],
                    rx.hstack(
                        rx.button(
                            rx.icon("list-checks", size=13), "Checklist",
                            on_click=FormationState.open_checklist(p["tech_id"]),
                            background=f"rgba(99,102,241,0.1)", color=PRIMARY,
                            border=f"1px solid rgba(99,102,241,0.3)", border_radius="6px",
                            font_size="0.78rem", padding="5px 12px", cursor="pointer",
                            spacing="2",
                        ),
                        rx.cond(
                            AuthState.is_manager,
                            rx.button(
                                rx.icon("x", size=13),
                                on_click=FormationState.unassign_onboarding(p["tech_id"]),
                                background="transparent", color=MUTED,
                                border=f"1px solid {BORDER}", border_radius="6px",
                                font_size="0.78rem", padding="5px 8px", cursor="pointer",
                                _hover={"color": RED, "border_color": RED},
                            ),
                        ),
                        spacing="2",
                    ),
                    rx.cond(
                        AuthState.is_manager,
                        rx.button(
                            rx.icon("plus", size=13), "Assigner parcours",
                            on_click=FormationState.assign_onboarding(p["tech_id"]),
                            background="transparent", color=MUTED,
                            border=f"1px solid {BORDER}", border_radius="6px",
                            font_size="0.78rem", padding="5px 12px", cursor="pointer",
                            spacing="2",
                            _hover={"color": PRIMARY, "border_color": PRIMARY},
                        ),
                    ),
                ),
                width="100%",
            ),
            spacing="3", width="100%",
        ),
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="14px",
        padding="1.1rem",
        _hover={"border_color": rx.cond(p["color"], p["color"], PRIMARY)},
        transition="border-color 0.2s",
    )


# ── Ligne étape dans checklist ────────────────────────────────────────────────
def checklist_step_row(step: OnboardingStep) -> rx.Component:
    is_done = FormationState.checklist_steps_done.contains(step["id"])
    return rx.hstack(
        rx.box(
            rx.cond(
                is_done,
                rx.icon("check", size=13, color="white"),
                rx.box(width="13px", height="13px"),
            ),
            background=rx.cond(is_done, GREEN, "transparent"),
            border=rx.cond(is_done, f"2px solid {GREEN}", f"2px solid {BORDER}"),
            border_radius="4px",
            width="22px", height="22px",
            display="flex", align_items="center", justify_content="center",
            cursor="pointer",
            on_click=FormationState.toggle_step_done(step["id"]),
            flex_shrink="0",
            _hover={"border_color": GREEN},
            transition="all 0.15s",
        ),
        rx.vstack(
            rx.hstack(
                rx.text(
                    step["titre"],
                    color=rx.cond(is_done, MUTED, TEXT),
                    font_weight="500", font_size="0.875rem",
                    text_decoration=rx.cond(is_done, "line-through", "none"),
                ),
                rx.badge(
                    step["categorie"],
                    color=_ob_cat_color(step["categorie"]),
                    background=f"rgba(99,102,241,0.1)",
                    border_radius="full", font_size="0.65rem",
                ),
                spacing="2", align="center",
            ),
            rx.cond(
                step["description"] != "",
                rx.text(step["description"], color=MUTED, font_size="0.78rem"),
            ),
            spacing="0", align="start",
        ),
        spacing="3", align="start", width="100%",
        padding="0.6rem 0",
        border_bottom=f"1px solid {BORDER}33",
    )


# ── Modal checklist tech ──────────────────────────────────────────────────────
def checklist_dialog() -> rx.Component:
    total = FormationState.onboarding_steps.length()
    done_count = FormationState.checklist_steps_done.length()
    pct = rx.cond(total > 0, (done_count * 100 // total), 0)

    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.box(
                    rx.text(
                        FormationState.checklist_tech_nom[:2].upper(),
                        color="white", font_weight="700",
                    ),
                    background=rx.cond(
                        FormationState.checklist_tech_color,
                        FormationState.checklist_tech_color, PRIMARY,
                    ),
                    border_radius="50%", width="40px", height="40px",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.vstack(
                    rx.text(FormationState.checklist_tech_nom, color=TEXT,
                            font_weight="700", font_size="1rem"),
                    rx.text("Parcours d'intégration", color=MUTED, font_size="0.78rem"),
                    spacing="0", align="start",
                ),
                rx.spacer(),
                rx.vstack(
                    rx.text(pct.to_string() + "%", color=TEXT, font_weight="700",
                            font_size="1.1rem", text_align="right"),
                    rx.text(done_count.to_string() + "/" + total.to_string() + " étapes",
                            color=MUTED, font_size="0.72rem", text_align="right"),
                    spacing="0", align="end",
                ),
                rx.icon_button(
                    rx.icon("x", size=15),
                    on_click=FormationState.close_checklist,
                    background="rgba(255,255,255,0.06)", color=MUTED,
                    border_radius="7px", size="2", cursor="pointer",
                ),
                spacing="3", align="center", width="100%",
            ),
            rx.box(
                rx.box(
                    background=FormationState.checklist_tech_color,
                    width=pct.to_string() + "%",
                    height="4px", border_radius="full", transition="width 0.3s",
                ),
                background=f"rgba(255,255,255,0.06)",
                border_radius="full", width="100%", overflow="hidden",
                margin_y="1rem",
            ),
            rx.box(
                rx.foreach(FormationState.onboarding_steps, checklist_step_row),
                max_height="55vh", overflow_y="auto",
            ),
            background="#111524", border=f"1px solid {BORDER}",
            border_radius="16px", padding="1.5rem",
            max_width="560px", width="95vw",
        ),
        open=FormationState.show_checklist,
    )


# ── Formulaire étape onboarding ───────────────────────────────────────────────
def step_form_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.text(
                    rx.cond(FormationState.edit_step_id != "", "Modifier l'étape", "Nouvelle étape"),
                    color=TEXT, font_weight="700", font_size="1rem",
                ),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("x", size=15),
                    on_click=FormationState.close_step_form,
                    background="rgba(255,255,255,0.06)", color=MUTED,
                    border_radius="7px", size="2", cursor="pointer",
                ),
                width="100%", align="center", margin_bottom="1rem",
            ),
            rx.vstack(
                rx.input(
                    placeholder="Titre *",
                    value=FormationState.step_form["titre"],
                    on_change=lambda v: FormationState.set_step_field("titre", v),
                    background="#0d1021", color=TEXT, border=f"1px solid {BORDER}",
                    border_radius="8px", width="100%",
                    _focus={"border_color": PRIMARY},
                ),
                rx.select(
                    ONBOARDING_CATS,
                    value=FormationState.step_form["categorie"],
                    on_change=lambda v: FormationState.set_step_field("categorie", v),
                    background="#0d1021", color=TEXT, border=f"1px solid {BORDER}",
                    border_radius="8px", width="100%",
                ),
                rx.input(
                    placeholder="Description (optionnelle)",
                    value=FormationState.step_form["description"],
                    on_change=lambda v: FormationState.set_step_field("description", v),
                    background="#0d1021", color=TEXT, border=f"1px solid {BORDER}",
                    border_radius="8px", width="100%",
                    _focus={"border_color": PRIMARY},
                ),
                rx.input(
                    placeholder="Ordre (0, 1, 2…)",
                    value=FormationState.step_form["ordre"],
                    on_change=lambda v: FormationState.set_step_field("ordre", v),
                    background="#0d1021", color=TEXT, border=f"1px solid {BORDER}",
                    border_radius="8px", width="100%",
                    _focus={"border_color": PRIMARY},
                ),
                rx.hstack(
                    rx.button("Annuler", on_click=FormationState.close_step_form,
                              background="transparent", color=MUTED,
                              border=f"1px solid {BORDER}", border_radius="8px", cursor="pointer"),
                    rx.button("Enregistrer", on_click=FormationState.save_step,
                              background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                              color="white", border_radius="8px", cursor="pointer", font_weight="600"),
                    spacing="3", justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            background="#111524", border=f"1px solid {BORDER}",
            border_radius="16px", padding="1.5rem", max_width="480px", width="95vw",
        ),
        open=FormationState.show_step_form,
    )


# ── Ligne étape dans la liste template ───────────────────────────────────────
def step_template_row(step: OnboardingStep) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(str(step["ordre"] + 1), color=MUTED, font_size="0.72rem", font_weight="600"),
            background=f"rgba(255,255,255,0.05)", border=f"1px solid {BORDER}",
            border_radius="6px", width="28px", height="28px",
            display="flex", align_items="center", justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.hstack(
                rx.text(step["titre"], color=TEXT, font_weight="500", font_size="0.875rem"),
                rx.badge(
                    step["categorie"],
                    color=_ob_cat_color(step["categorie"]),
                    background=f"rgba(99,102,241,0.08)",
                    border_radius="full", font_size="0.65rem",
                ),
                spacing="2", align="center",
            ),
            rx.cond(
                step["description"] != "",
                rx.text(step["description"], color=MUTED, font_size="0.78rem"),
            ),
            spacing="0", align="start",
        ),
        rx.spacer(),
        rx.cond(
            AuthState.is_manager,
            rx.hstack(
                rx.icon_button(
                    rx.icon("pencil", size=13),
                    on_click=FormationState.open_step_edit(step["id"]),
                    background="transparent", color=MUTED,
                    border=f"1px solid {BORDER}", border_radius="6px",
                    size="2", cursor="pointer",
                    _hover={"color": PRIMARY, "border_color": PRIMARY},
                ),
                rx.icon_button(
                    rx.icon("trash-2", size=13),
                    on_click=FormationState.delete_step(step["id"]),
                    background="transparent", color=MUTED,
                    border=f"1px solid {BORDER}", border_radius="6px",
                    size="2", cursor="pointer",
                    _hover={"color": RED, "border_color": RED},
                ),
                spacing="2",
            ),
        ),
        spacing="3", align="center", width="100%",
        padding="0.7rem 1rem",
        border_bottom=f"1px solid {BORDER}",
    )


# ── Onglet Onboarding ─────────────────────────────────────────────────────────
def onboarding_tab() -> rx.Component:
    return rx.hstack(
        # Colonne gauche — Techs
        rx.vstack(
            rx.hstack(
                rx.icon("users", size=15, color=PRIMARY),
                rx.text("Suivi par technicien", color=TEXT, font_weight="600", font_size="0.875rem"),
                spacing="2", align="center",
            ),
            rx.vstack(
                rx.foreach(FormationState.onboarding_progress, onboarding_tech_card),
                spacing="3", width="100%",
            ),
            checklist_dialog(),
            spacing="4", width="55%",
        ),

        # Colonne droite — Template étapes
        rx.vstack(
            rx.hstack(
                rx.icon("list-checks", size=15, color=CYAN),
                rx.text("Étapes du parcours", color=TEXT, font_weight="600", font_size="0.875rem"),
                rx.spacer(),
                rx.cond(
                    AuthState.is_manager,
                    rx.button(
                        rx.icon("plus", size=14), "Étape",
                        on_click=FormationState.open_step_create,
                        background=f"rgba(6,182,212,0.1)", color=CYAN,
                        border=f"1px solid rgba(6,182,212,0.3)", border_radius="6px",
                        font_size="0.78rem", padding="5px 12px", cursor="pointer",
                        spacing="2",
                    ),
                ),
                spacing="2", align="center", width="100%",
            ),
            rx.box(
                rx.cond(
                    FormationState.onboarding_steps.length() > 0,
                    rx.foreach(FormationState.onboarding_steps, step_template_row),
                    rx.box(
                        rx.vstack(
                            rx.icon("list-checks", size=28, color=MUTED),
                            rx.text("Aucune étape définie", color=MUTED, font_size="0.85rem"),
                            rx.cond(
                                AuthState.is_manager,
                                rx.text("Ajoutez des étapes avec le bouton ci-dessus.",
                                        color=MUTED, font_size="0.78rem"),
                            ),
                            spacing="2", align="center",
                        ),
                        padding="2rem", text_align="center",
                    ),
                ),
                background=CARD_BG, border=f"1px solid {BORDER}",
                border_radius="14px", overflow="hidden", width="100%",
            ),
            step_form_dialog(),
            spacing="4", width="45%",
        ),

        spacing="5", align="start", width="100%",
    )


def _statut_icon(statut: str, size: int = 15) -> rx.Component:
    return rx.match(
        statut,
        ("completed",   rx.icon("circle-check", size=size, color=GREEN)),
        ("in_progress", rx.icon("circle-dot",   size=size, color=AMBER)),
        rx.icon("circle", size=size, color=MUTED),
    )


def _niveau_badge2(niveau: str) -> rx.Component:
    return rx.match(
        niveau,
        ("Débutant",      rx.badge("Débutant",      color_scheme="green", variant="soft", font_size="0.62rem")),
        ("Intermédiaire", rx.badge("Intermédiaire", color_scheme="amber", variant="soft", font_size="0.62rem")),
        ("Expert",        rx.badge("Expert",        color_scheme="red",   variant="soft", font_size="0.62rem")),
        rx.badge(niveau, color_scheme="gray", variant="soft", font_size="0.62rem"),
    )


# ── Carte tech — vue équipe compétences ───────────────────────────────────────
def team_comp_card(c: dict) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(
                rx.text(c["initials"], color="white", font_weight="700", font_size="0.85rem"),
                background=c["color"],
                border_radius="50%", width="38px", height="38px",
                display="flex", align_items="center", justify_content="center",
                flex_shrink="0",
            ),
            rx.vstack(
                rx.text(c["nom"], color=TEXT, font_weight="600", font_size="0.9rem"),
                rx.cond(
                    c["pending"] > 0,
                    rx.hstack(
                        rx.icon("circle-alert", size=11, color=AMBER),
                        rx.text(c["pending"].to_string() + " assignée(s) en attente",
                                color=AMBER, font_size="0.7rem"),
                        spacing="1", align="center",
                    ),
                    rx.text("Aucune assignation en attente", color=MUTED, font_size="0.7rem"),
                ),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.text(c["pct"].to_string() + "%", color=TEXT, font_weight="700", font_size="1rem"),
            spacing="3", align="center", width="100%",
        ),
        rx.box(
            rx.box(
                background=c["color"],
                width=c["pct"].to_string() + "%",
                height="4px", border_radius="full", transition="width 0.3s",
            ),
            background="rgba(255,255,255,0.06)", border_radius="full",
            width="100%", overflow="hidden", margin_top="0.7rem",
        ),
        on_click=FormationState.select_comp_tech(c["id"]),
        cursor="pointer",
        background=CARD_BG, border=f"1px solid {BORDER}",
        border_radius="14px", padding="1.1rem",
        _hover={"border_color": c["color"]},
        transition="border-color 0.2s",
    )


def comp_team_view() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon("users", size=15, color=PRIMARY),
            rx.text("Couverture des compétences par technicien", color=TEXT,
                    font_weight="600", font_size="0.875rem"),
            spacing="2", align="center",
        ),
        rx.cond(
            FormationState.team_comp_cards.length() > 0,
            rx.grid(
                rx.foreach(FormationState.team_comp_cards, team_comp_card),
                columns="3", spacing="4", width="100%",
            ),
            rx.box(
                rx.vstack(
                    rx.icon("map", size=28, color=MUTED),
                    rx.text("Aucun thème dans le Skill Map pour l'instant.", color=MUTED, font_size="0.85rem"),
                    spacing="2", align="center",
                ),
                padding="2rem", text_align="center", width="100%",
            ),
        ),
        spacing="4", width="100%",
    )


# ── Nœud thème (roue radiale) ─────────────────────────────────────────────────
def comp_theme_node(node: dict) -> rx.Component:
    inner = NODE_SIZE - 12
    icon_box = NODE_SIZE - 26
    return rx.vstack(
        rx.box(
            rx.box(
                rx.box(
                    dyn_icon(node["icon"], size=20, color="white"),
                    background=CARD_BG,
                    border=node["icon_border"],
                    border_radius="50%",
                    width=f"{icon_box}px", height=f"{icon_box}px",
                    display="flex", align_items="center", justify_content="center",
                ),
                background="#080b14",
                border_radius="50%",
                width=f"{inner}px", height=f"{inner}px",
                display="flex", align_items="center", justify_content="center",
            ),
            background=node["ring_bg"],
            border_radius="50%",
            width=f"{NODE_SIZE}px", height=f"{NODE_SIZE}px",
            display="flex", align_items="center", justify_content="center",
        ),
        rx.text(node["nom"], color=TEXT, font_size="0.7rem", font_weight="600",
                text_align="center", no_of_lines=2, line_height="1.2"),
        rx.text(node["pct"].to_string() + "%", color=MUTED, font_size="0.65rem", font_weight="700"),
        spacing="1", align="center",
        position="absolute",
        left=node["left"], top=node["top"],
        width=f"{LABEL_WIDTH}px",
        cursor="pointer",
        on_click=FormationState.select_comp_theme(node["id"]),
        _hover={"opacity": "0.85"},
        transition="opacity 0.15s",
    )


def _comp_radial_wheel() -> rx.Component:
    t = FormationState.comp_selected_tech
    return rx.box(
        # Nœud central — le tech
        rx.vstack(
            rx.box(
                rx.text(t["initials"], color="white", font_weight="800", font_size="1.3rem"),
                background=t["color"],
                border_radius="50%", width="96px", height="96px",
                display="flex", align_items="center", justify_content="center",
                border=f"3px solid {BORDER}",
            ),
            rx.text(t["nom"], color=TEXT, font_weight="700", font_size="0.95rem"),
            rx.text(FormationState.comp_selected_tech_pct.to_string() + "% global",
                    color=MUTED, font_size="0.75rem"),
            spacing="1", align="center",
            position="absolute", top="50%", left="50%",
            transform="translate(-50%, -50%)",
        ),
        rx.foreach(FormationState.comp_theme_nodes, comp_theme_node),
        position="relative",
        width=f"{RADIAL_SIZE}px", height=f"{RADIAL_SIZE}px",
        margin="0 auto",
    )


# ── Panneau formations d'un thème ─────────────────────────────────────────────
def comp_formation_row(f: dict) -> rx.Component:
    return rx.hstack(
        _statut_icon(f["statut"]),
        rx.vstack(
            rx.text(f["titre"], color=TEXT, font_size="0.85rem", font_weight="600"),
            rx.hstack(
                _niveau_badge2(f["niveau"]),
                rx.hstack(
                    rx.icon("clock", size=11, color=MUTED),
                    rx.text(f["duree_min"].to_string() + " min", color=MUTED, font_size="0.7rem"),
                    spacing="1", align="center",
                ),
                spacing="2", align="center",
            ),
            spacing="1", align="start",
        ),
        rx.spacer(),
        rx.cond(
            f["assigned"],
            rx.hstack(
                rx.vstack(
                    rx.text("Assigné par ", f["assigned_by"], color=PRIMARY, font_size="0.68rem", font_weight="600"),
                    rx.cond(
                        f["due_date"] != "",
                        rx.text("Échéance ", f["due_date"], color=MUTED, font_size="0.66rem"),
                    ),
                    spacing="0", align="end",
                ),
                rx.cond(
                    AuthState.can_edit_formation,
                    rx.icon_button(
                        rx.icon("x", size=12),
                        on_click=FormationState.unassign_formation(f["id"]),
                        background="transparent", color=MUTED,
                        border=f"1px solid {BORDER}", border_radius="6px",
                        size="1", cursor="pointer",
                        _hover={"color": RED, "border_color": RED},
                    ),
                ),
                spacing="2", align="center",
            ),
            rx.cond(
                AuthState.can_edit_formation,
                rx.button(
                    rx.icon("send", size=12), "Assigner",
                    on_click=FormationState.open_assign_form(f["id"]),
                    background="rgba(99,102,241,0.1)", color=PRIMARY,
                    border=f"1px solid rgba(99,102,241,0.3)", border_radius="6px",
                    font_size="0.72rem", padding="4px 10px", cursor="pointer",
                    spacing="1",
                ),
            ),
        ),
        spacing="3", align="center", width="100%",
        padding="0.65rem 0",
        border_bottom=f"1px solid {BORDER}33",
    )


def comp_theme_dialog() -> rx.Component:
    t = FormationState.comp_selected_theme
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.hstack(
                    dyn_icon(t["icon"], size=16, color="white"),
                    rx.text(t["nom"], color=TEXT, font_weight="700", font_size="1rem"),
                    spacing="2", align="center",
                ),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("x", size=15),
                    on_click=FormationState.close_comp_theme,
                    background="rgba(255,255,255,0.06)", color=MUTED,
                    border_radius="7px", size="2", cursor="pointer",
                ),
                width="100%", align="center", margin_bottom="0.75rem",
            ),
            rx.cond(
                FormationState.comp_theme_formations.length() > 0,
                rx.box(
                    rx.foreach(FormationState.comp_theme_formations, comp_formation_row),
                    max_height="55vh", overflow_y="auto",
                ),
                rx.text("Aucune formation dans ce thème.", color=MUTED, font_size="0.85rem"),
            ),
            background="#111524", border=f"1px solid {BORDER}",
            border_radius="16px", padding="1.5rem", max_width="560px", width="95vw",
        ),
        open=FormationState.comp_selected_theme_id != "",
    )


def assign_form_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.text("Assigner une formation", color=TEXT, font_weight="700", font_size="1rem"),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=15),
                        on_click=FormationState.close_assign_form,
                        background="rgba(255,255,255,0.06)", color=MUTED,
                        border_radius="7px", size="2", cursor="pointer",
                    ),
                    width="100%", align="center",
                ),
                rx.text(FormationState.assign_formation_titre, color=PRIMARY, font_size="0.9rem", font_weight="600"),
                rx.vstack(
                    rx.text("Échéance (optionnelle)", color=MUTED, font_size="0.75rem"),
                    rx.input(
                        type="date",
                        value=FormationState.assign_due_date,
                        on_change=FormationState.set_assign_due_date,
                        background="#0d1021", color=TEXT, border=f"1px solid {BORDER}",
                        border_radius="8px", width="100%",
                    ),
                    spacing="1", width="100%", align="start",
                ),
                rx.hstack(
                    rx.button("Annuler", on_click=FormationState.close_assign_form,
                              background="transparent", color=MUTED,
                              border=f"1px solid {BORDER}", border_radius="8px", cursor="pointer"),
                    rx.button("Assigner", on_click=FormationState.save_assignment,
                              background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                              color="white", border_radius="8px", cursor="pointer", font_weight="600"),
                    spacing="3", justify="end", width="100%",
                ),
                spacing="4", width="100%",
            ),
            background="#111524", border=f"1px solid {BORDER}",
            border_radius="16px", padding="1.5rem", max_width="420px", width="95vw",
        ),
        open=FormationState.show_assign_form,
    )


def comp_individual_view() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.button(
                rx.icon("arrow-left", size=14), "Retour à l'équipe",
                on_click=FormationState.back_to_comp_team,
                background="transparent", color=MUTED,
                border=f"1px solid {BORDER}", border_radius="8px",
                font_size="0.8rem", padding="6px 14px", cursor="pointer", spacing="2",
                _hover={"color": TEXT, "border_color": PRIMARY},
            ),
            width="100%",
        ),
        _comp_radial_wheel(),
        comp_theme_dialog(),
        assign_form_dialog(),
        spacing="4", width="100%", align="center",
    )


def competences_tab() -> rx.Component:
    return rx.cond(
        FormationState.comp_view == "equipe",
        comp_team_view(),
        comp_individual_view(),
    )


# ── Page principale ───────────────────────────────────────────────────────────
def formation_content() -> rx.Component:
    return rx.vstack(
        # Tabs
        rx.hstack(
            rx.button(
                rx.icon("book-open", size=15), "Modules de formation",
                on_click=FormationState.set_tab("modules"),
                background=rx.cond(
                    FormationState.tab == "modules",
                    f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)", "transparent",
                ),
                color=rx.cond(FormationState.tab == "modules", "white", MUTED),
                border=rx.cond(
                    FormationState.tab == "modules",
                    "none", f"1px solid {BORDER}",
                ),
                border_radius="8px", font_size="0.875rem",
                padding="8px 18px", cursor="pointer", spacing="2",
                _hover={"color": "white" if True else MUTED},
            ),
            rx.button(
                rx.icon("graduation-cap", size=15), "Parcours d'intégration",
                on_click=FormationState.set_tab("onboarding"),
                background=rx.cond(
                    FormationState.tab == "onboarding",
                    f"linear-gradient(135deg, {CYAN}, #0891b2)", "transparent",
                ),
                color=rx.cond(FormationState.tab == "onboarding", "white", MUTED),
                border=rx.cond(
                    FormationState.tab == "onboarding",
                    "none", f"1px solid {BORDER}",
                ),
                border_radius="8px", font_size="0.875rem",
                padding="8px 18px", cursor="pointer", spacing="2",
            ),
            rx.button(
                rx.icon("compass", size=15), "Compétences",
                on_click=FormationState.set_tab("competences"),
                background=rx.cond(
                    FormationState.tab == "competences",
                    f"linear-gradient(135deg, {AMBER}, #ea580c)", "transparent",
                ),
                color=rx.cond(FormationState.tab == "competences", "white", MUTED),
                border=rx.cond(
                    FormationState.tab == "competences",
                    "none", f"1px solid {BORDER}",
                ),
                border_radius="8px", font_size="0.875rem",
                padding="8px 18px", cursor="pointer", spacing="2",
            ),
            spacing="3", margin_bottom="0.5rem",
        ),

        # Contenu
        rx.match(
            FormationState.tab,
            ("modules", modules_tab()),
            ("competences", competences_tab()),
            onboarding_tab(),
        ),

        spacing="4", width="100%",
        on_mount=FormationState.load,
    )


def formation_page() -> rx.Component:
    return page_layout(formation_content(), "Formation")
