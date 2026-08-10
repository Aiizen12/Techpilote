import reflex as rx
from techpilot.components.layout import page_layout
from techpilot.state.auth import AuthState
from techpilot.state.skill_map import SkillMapState, NIVEAUX, CONTENU_TYPES

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
CARD_BG = "#111524"
BORDER  = "#1c2138"
PRIMARY = "#6366f1"
GREEN   = "#22c55e"
AMBER   = "#f59e0b"
RED     = "#ef4444"
BG      = "#0d0f1a"


# ── Helpers ───────────────────────────────────────────────────────────────────

# rx.icon() requires a literal string — use rx.match for dynamic icon names
def _dyn_icon(name, size: int = 16, color: str = "white") -> rx.Component:
    kw = {"size": size, "color": color}
    return rx.match(
        name,
        ("graduation-cap", rx.icon("graduation-cap", **kw)),
        ("users",          rx.icon("users",          **kw)),
        ("mail",           rx.icon("mail",            **kw)),
        ("monitor",        rx.icon("monitor",         **kw)),
        ("phone",          rx.icon("phone",           **kw)),
        ("shield",         rx.icon("shield",          **kw)),
        ("cpu",            rx.icon("cpu",             **kw)),
        ("book-open",      rx.icon("book-open",       **kw)),
        ("map",            rx.icon("map",             **kw)),
        ("phone-call",     rx.icon("phone-call",      **kw)),
        ("key-round",      rx.icon("key-round",       **kw)),
        ("layers",         rx.icon("layers",          **kw)),
        ("star",           rx.icon("star",            **kw)),
        rx.icon("circle", **kw),
    )


def _niveau_badge(niveau: str) -> rx.Component:
    return rx.match(
        niveau,
        ("Débutant",       rx.badge("Débutant",       color_scheme="green",  variant="soft", font_size="0.65rem")),
        ("Intermédiaire",  rx.badge("Intermédiaire",  color_scheme="amber",  variant="soft", font_size="0.65rem")),
        ("Expert",         rx.badge("Expert",         color_scheme="red",    variant="soft", font_size="0.65rem")),
        rx.badge(niveau, color_scheme="gray", variant="soft", font_size="0.65rem"),
    )


def _progress_icon(statut: str) -> rx.Component:
    return rx.match(
        statut,
        ("completed",   rx.icon("circle-check",    size=18, color=GREEN)),
        ("in_progress", rx.icon("circle-dot",      size=18, color=AMBER)),
        rx.icon("circle",  size=18, color=BORDER),
    )


def _label(t: str) -> rx.Component:
    return rx.text(t, color=MUTED, font_size="0.73rem", font_weight="600", margin_bottom="4px")


def _input(value, on_change, placeholder="", **kw) -> rx.Component:
    return rx.input(
        value=value, on_change=on_change, placeholder=placeholder,
        style={"background": "#0d1117", "color": TEXT, "border": f"1px solid {BORDER}",
               "border_radius": "8px", "padding": "7px 10px", "width": "100%",
               "font_size": "0.85rem"},
        **kw,
    )


def _textarea(value, on_change, placeholder="", rows="3") -> rx.Component:
    return rx.text_area(
        value=value, on_change=on_change, placeholder=placeholder, rows=rows,
        style={"background": "#0d1117", "color": TEXT, "border": f"1px solid {BORDER}",
               "border_radius": "8px", "padding": "8px 10px", "width": "100%",
               "font_size": "0.85rem", "resize": "vertical"},
    )


def _select(value, on_change, options, placeholder="") -> rx.Component:
    return rx.select.root(
        rx.select.trigger(
            placeholder=placeholder,
            style={"background": "#0d1117", "color": TEXT, "border": f"1px solid {BORDER}",
                   "border_radius": "8px", "padding": "7px 10px", "width": "100%",
                   "font_size": "0.85rem"},
        ),
        rx.select.content(
            *[rx.select.item(o, value=o) for o in options],
            background=CARD_BG,
        ),
        value=value, on_change=on_change, width="100%",
    )


# ── Carte thème (colonne de la carte) ─────────────────────────────────────────

def _theme_card(t: dict) -> rx.Component:
    is_selected = SkillMapState.selected_theme_id == t["id"]
    return rx.box(
        rx.vstack(
            # Icône + nom
            rx.hstack(
                rx.box(
                    _dyn_icon(t["icon"], size=20, color="white"),
                    background=t["color"],
                    border_radius="10px", padding="8px",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.vstack(
                    rx.text(t["nom"], color=TEXT, font_size="0.88rem", font_weight="700",
                            line_height="1.2"),
                    rx.text(
                        t["count"].to_string(), " ", t["formation_label"],
                        color=MUTED, font_size="0.72rem",
                    ),
                    spacing="0", align="start",
                ),
                spacing="3", align="center",
            ),
            # Barre de progression
            rx.cond(
                t["has_formations"],
                rx.vstack(
                    rx.box(
                        rx.box(
                            height="100%",
                            background=t["color"],
                            border_radius="3px",
                            transition="width 0.4s ease",
                            style={"width": t["progress_width"]},
                        ),
                        background="rgba(255,255,255,0.07)",
                        border_radius="3px",
                        height="4px",
                        width="100%",
                        overflow="hidden",
                    ),
                    rx.text(
                        t["done"].to_string(), "/", t["count"].to_string(), " complétées",
                        color=MUTED, font_size="0.68rem",
                    ),
                    spacing="1", width="100%",
                ),
            ),
            spacing="3", width="100%",
        ),
        on_click=SkillMapState.select_theme(t["id"]),
        cursor="pointer",
        background=rx.cond(is_selected, t["bg_selected"], CARD_BG),
        border=rx.cond(is_selected, t["border_selected"], f"1px solid {BORDER}"),
        border_radius="14px",
        padding="1rem",
        width="100%",
        transition="all 0.2s ease",
        _hover={"border": t["border_hover"], "background": t["bg_hover"]},
        box_shadow=rx.cond(is_selected, t["shadow_selected"], "none"),
    )


def _rgb(color: str) -> str:
    h = color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b}"


# ── Nœud formation (dans la colonne roadmap) ──────────────────────────────────

def _formation_node(f: dict) -> rx.Component:
    statut = f["progress_status"]
    is_sel = SkillMapState.selected_formation_id == f["id"]

    return rx.vstack(
        rx.box(
            width="2px", height="20px",
            background=f"linear-gradient(to bottom, {BORDER}, rgba(255,255,255,0.15))",
            margin_x="auto",
        ),
        rx.hstack(
            rx.box(
                rx.match(
                    statut,
                    ("completed",   rx.icon("circle-check", size=16, color="white")),
                    ("in_progress", rx.icon("circle-dot",   size=16, color=CARD_BG)),
                    rx.icon("circle", size=16, color=MUTED),
                ),
                background=rx.match(
                    statut,
                    ("completed",   GREEN),
                    ("in_progress", AMBER),
                    "transparent",
                ),
                border=rx.match(
                    statut,
                    ("completed",   f"2px solid {GREEN}"),
                    ("in_progress", f"2px solid {AMBER}"),
                    f"2px solid {BORDER}",
                ),
                border_radius="50%", width="28px", height="28px",
                display="flex", align_items="center", justify_content="center",
                flex_shrink="0",
            ),
            rx.vstack(
                rx.text(f["titre"], color=TEXT, font_size="0.84rem", font_weight="600",
                        line_height="1.3"),
                rx.hstack(
                    _niveau_badge(f["niveau"]),
                    rx.hstack(
                        rx.icon("clock", size=11, color=MUTED),
                        rx.text(f["duree_min"].to_string(), " min", color=MUTED, font_size="0.7rem"),
                        spacing="1", align="center",
                    ),
                    spacing="2", align="center",
                ),
                spacing="1", align="start",
            ),
            spacing="3", align="center",
            on_click=SkillMapState.select_formation(f["id"]),
            cursor="pointer",
            background=rx.cond(is_sel, SkillMapState.sel_bg_active, "rgba(255,255,255,0.02)"),
            border=rx.cond(is_sel, SkillMapState.sel_border_active, f"1px solid {BORDER}"),
            border_radius="12px",
            padding="10px 14px",
            width="100%",
            transition="all 0.18s ease",
            _hover={"background": SkillMapState.sel_bg_hover,
                    "border": SkillMapState.sel_border_hover},
        ),
        spacing="0", width="100%", align="stretch",
    )


# ── Panneau détail formation ──────────────────────────────────────────────────

def _contenu_block(c: dict) -> rx.Component:
    return rx.match(
        c["type"],
        ("texte",
         rx.vstack(
             rx.hstack(rx.icon("align-left", size=13, color=PRIMARY),
                       rx.text(c["titre"], color=PRIMARY, font_size="0.72rem", font_weight="700",
                               text_transform="uppercase", letter_spacing="0.06em"),
                       spacing="2", align="center"),
             rx.text(c["body"], color=TEXT, font_size="0.85rem", line_height="1.7",
                     white_space="pre-wrap"),
             spacing="2", width="100%",
             background="rgba(99,102,241,0.05)", border_left=f"3px solid {PRIMARY}",
             border_radius="0 8px 8px 0", padding="10px 14px",
         )),
        ("lien",
         rx.hstack(
             rx.icon("external-link", size=14, color=AMBER),
             rx.link(c["titre"], href=c["body"], target="_blank",
                     color=AMBER, font_size="0.85rem",
                     text_decoration="underline",
                     _hover={"color": "#fbbf24"}),
             spacing="2", align="center",
             background="rgba(245,158,11,0.06)", border=f"1px solid {AMBER}33",
             border_radius="8px", padding="8px 12px",
         )),
        ("procedure",
         rx.hstack(
             rx.badge(c["codification"], color_scheme="cyan", variant="surface",
                      font_size="0.62rem", flex_shrink="0"),
             rx.text(c["titre"], color="#06b6d4", font_size="0.85rem", flex="1",
                     no_of_lines=1),
             rx.cond(
                 c["body"] != "",
                 rx.link(
                     rx.icon("external-link", size=13),
                     href=c["body"], target="_blank",
                     color="#06b6d4", _hover={"color": "#22d3ee"},
                 ),
             ),
             spacing="2", align="center",
             background="rgba(6,182,212,0.06)", border="1px solid #06b6d433",
             border_radius="8px", padding="8px 12px", width="100%",
         )),
        # quiz
        rx.vstack(
            rx.hstack(rx.icon("help-circle", size=13, color="#8b5cf6"),
                      rx.text(c["titre"], color="#8b5cf6", font_size="0.72rem", font_weight="700",
                              text_transform="uppercase", letter_spacing="0.06em"),
                      spacing="2", align="center"),
            rx.text("Quiz interactif", color=MUTED, font_size="0.8rem"),
            spacing="2", background="rgba(139,92,246,0.06)",
            border_left="3px solid #8b5cf6", border_radius="0 8px 8px 0", padding="10px 14px",
            width="100%",
        ),
    )


def _detail_panel() -> rx.Component:
    f      = SkillMapState.selected_formation
    statut = SkillMapState.selected_formation_progress

    return rx.cond(
        SkillMapState.selected_formation_id != "",
        rx.vstack(
            # Header
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        _niveau_badge(f["niveau"]),
                        rx.hstack(
                            rx.icon("clock", size=12, color=MUTED),
                            rx.text(f["duree_min"].to_string(), " min", color=MUTED, font_size="0.75rem"),
                            spacing="1", align="center",
                        ),
                        spacing="2", align="center",
                    ),
                    rx.heading(f["titre"], color=TEXT, size="4", font_weight="800"),
                    rx.cond(
                        f["description"] != "",
                        rx.text(f["description"], color=MUTED, font_size="0.82rem", line_height="1.6"),
                    ),
                    spacing="2", align="start",
                ),
                rx.icon_button(
                    rx.icon("x", size=15),
                    on_click=SkillMapState.close_formation,
                    background="transparent", color=MUTED,
                    border=f"1px solid {BORDER}", border_radius="8px",
                    size="2", cursor="pointer", flex_shrink="0",
                    _hover={"color": TEXT, "background": "rgba(255,255,255,0.05)"},
                ),
                width="100%", align="start", spacing="3",
            ),

            # Boutons progression
            rx.hstack(
                rx.button(
                    rx.icon("play-circle", size=14), "En cours",
                    on_click=SkillMapState.mark_progress(f["id"], "in_progress"),
                    background=rx.cond(statut == "in_progress",
                                       "rgba(245,158,11,0.2)", "rgba(245,158,11,0.08)"),
                    color=AMBER, border=f"1px solid {AMBER}55",
                    border_radius="8px", padding="6px 14px", cursor="pointer",
                    font_size="0.8rem", font_weight="600",
                    _hover={"background": "rgba(245,158,11,0.2)"},
                ),
                rx.button(
                    rx.icon("check-circle", size=14), "Terminé",
                    on_click=SkillMapState.mark_progress(f["id"], "completed"),
                    background=rx.cond(statut == "completed",
                                       f"rgba({_rgb(GREEN)},0.2)", f"rgba({_rgb(GREEN)},0.08)"),
                    color=GREEN, border=f"1px solid {GREEN}55",
                    border_radius="8px", padding="6px 14px", cursor="pointer",
                    font_size="0.8rem", font_weight="600",
                    _hover={"background": f"rgba({_rgb(GREEN)},0.2)"},
                ),
                rx.cond(
                    AuthState.can_edit_formation,
                    rx.icon_button(
                        rx.icon("pencil", size=13),
                        on_click=SkillMapState.open_edit_formation(f["id"]),
                        background="rgba(99,102,241,0.08)", color=PRIMARY,
                        border=f"1px solid rgba(99,102,241,0.25)", size="2",
                        cursor="pointer", border_radius="8px",
                        _hover={"background": "rgba(99,102,241,0.2)"},
                    ),
                ),
                spacing="2", align="center",
            ),

            rx.divider(border_color=BORDER),

            # Contenus
            rx.cond(
                f["contenus"].length() > 0,
                rx.vstack(
                    rx.foreach(f["contenus"], _contenu_block),
                    spacing="3", width="100%",
                ),
                rx.text("Aucun contenu ajouté.", color=MUTED, font_size="0.83rem"),
            ),

            spacing="4", width="100%",
            background=CARD_BG,
            border=f"1px solid {BORDER}",
            border_radius="14px",
            padding="1.25rem",
        ),
    )


# ── Section thème + roadmap vertical ─────────────────────────────────────────

def _theme_roadmap() -> rx.Component:
    return rx.cond(
        SkillMapState.selected_theme_id != "",
        rx.vstack(
            # Header thème sélectionné
            rx.hstack(
                rx.box(
                    _dyn_icon(SkillMapState.selected_theme["icon"], size=18, color="white"),
                    background=SkillMapState.selected_theme["color"],
                    border_radius="10px", padding="8px",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.vstack(
                    rx.text(SkillMapState.selected_theme["nom"], color=TEXT,
                            font_size="1rem", font_weight="800"),
                    rx.text(SkillMapState.selected_theme["description"],
                            color=MUTED, font_size="0.78rem"),
                    spacing="0", align="start",
                ),
                rx.spacer(),
                rx.cond(
                    AuthState.can_edit_formation,
                    rx.button(
                        rx.icon("plus", size=13), "Ajouter une formation",
                        on_click=SkillMapState.open_new_formation(SkillMapState.selected_theme_id),
                        background="rgba(99,102,241,0.1)", color=PRIMARY,
                        border=f"1px solid rgba(99,102,241,0.3)",
                        border_radius="8px", padding="6px 14px",
                        font_size="0.8rem", font_weight="600", cursor="pointer",
                        _hover={"background": "rgba(99,102,241,0.2)"},
                    ),
                ),
                spacing="3", align="center", width="100%",
            ),

            # Roadmap formations
            rx.cond(
                SkillMapState.theme_formations.length() == 0,
                rx.box(
                    rx.vstack(
                        rx.icon("book-open", size=28, color=MUTED),
                        rx.text("Aucune formation dans ce thème.", color=MUTED, font_size="0.85rem"),
                        rx.cond(
                            AuthState.can_edit_formation,
                            rx.text("Commence par en créer une →", color=PRIMARY, font_size="0.8rem"),
                        ),
                        spacing="2", align="center",
                    ),
                    padding="2.5rem 0", text_align="center", width="100%",
                ),
                rx.vstack(
                    # Premier nœud sans ligne au dessus
                    rx.box(
                        rx.foreach(SkillMapState.theme_formations, _formation_node),
                        width="100%",
                    ),
                    spacing="0", width="100%",
                ),
            ),

            spacing="4", width="100%",
        ),
        # Aucun thème sélectionné
        rx.box(
            rx.vstack(
                rx.icon("mouse-pointer-click", size=32, color=MUTED),
                rx.text("Sélectionne un thème pour voir ses formations",
                        color=MUTED, font_size="0.9rem"),
                spacing="3", align="center",
            ),
            padding="4rem 0", text_align="center", width="100%",
        ),
    )


# ── Bande parcours ────────────────────────────────────────────────────────────

def _parcours_card(pc: dict) -> rx.Component:
    pct   = pc["pct"]
    color = pc["color"]
    return rx.vstack(
        rx.hstack(
            rx.box(
                _dyn_icon(pc["icon"], size=16, color="white"),
                background=color, border_radius="8px", padding="6px",
                display="flex", align_items="center", justify_content="center",
            ),
            rx.vstack(
                rx.text(pc["nom"], color=TEXT, font_size="0.85rem", font_weight="700"),
                rx.text(pc["done"].to_string(), "/", pc["total"].to_string(), " formations",
                        color=MUTED, font_size="0.72rem"),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.text(pct.to_string(), "%", color=color, font_size="0.9rem", font_weight="800"),
            spacing="2", align="center", width="100%",
        ),
        rx.box(
            rx.box(
                height="100%", background=color, border_radius="3px",
                transition="width 0.5s ease",
                style={"width": pct.to_string() + "%"},
            ),
            background="rgba(255,255,255,0.07)", border_radius="3px",
            height="5px", width="100%", overflow="hidden",
        ),
        rx.cond(
            AuthState.can_edit_formation,
            rx.hstack(
                rx.button(
                    rx.icon("pencil", size=11), "Modifier",
                    on_click=SkillMapState.open_edit_parcours(pc["id"]),
                    background="transparent", color=MUTED,
                    border=f"1px solid {BORDER}", border_radius="6px",
                    font_size="0.72rem", padding="3px 10px", cursor="pointer",
                    _hover={"color": TEXT},
                ),
                spacing="2",
            ),
        ),
        spacing="3", width="100%",
        background=CARD_BG, border=f"1px solid {BORDER}",
        border_radius="12px", padding="1rem",
        min_width="220px", flex="1",
    )


def _parcours_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.icon("map", size=16, color=AMBER),
                rx.text("Parcours", color=TEXT, font_size="0.95rem", font_weight="700"),
                spacing="2", align="center",
            ),
            rx.spacer(),
            rx.cond(
                AuthState.can_edit_formation,
                rx.button(
                    rx.icon("plus", size=13), "Nouveau parcours",
                    on_click=SkillMapState.open_new_parcours,
                    background="transparent", color=MUTED,
                    border=f"1px solid {BORDER}", border_radius="8px",
                    font_size="0.78rem", padding="5px 12px", cursor="pointer",
                    _hover={"color": TEXT, "background": "rgba(255,255,255,0.04)"},
                ),
            ),
            width="100%", align="center",
        ),
        rx.flex(
            rx.foreach(SkillMapState.parcours_with_progress, _parcours_card),
            gap="1rem", flex_wrap="wrap", width="100%",
        ),
        spacing="3", width="100%",
        background=CARD_BG, border=f"1px solid {BORDER}",
        border_radius="14px", padding="1.25rem",
    )


# ── Modals form ───────────────────────────────────────────────────────────────

def _theme_form_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.text(
                        rx.cond(SkillMapState.edit_theme_id != "", "Modifier le thème", "Nouveau thème"),
                        color=TEXT, font_size="1rem", font_weight="700",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.icon_button(rx.icon("x", size=15), on_click=SkillMapState.close_theme_form,
                                       background="transparent", color=MUTED,
                                       border=f"1px solid {BORDER}", border_radius="8px",
                                       size="2", cursor="pointer"),
                    ),
                    width="100%", align="center",
                ),
                rx.vstack(_label("Nom *"), _input(SkillMapState.th_nom, SkillMapState.set_th_nom, "Ex : Active Directory"), spacing="0", width="100%"),
                rx.hstack(
                    rx.vstack(_label("Icône (Lucide)"), _input(SkillMapState.th_icon, SkillMapState.set_th_icon, "Ex: users, shield…"), spacing="0", width="100%"),
                    rx.vstack(_label("Couleur"), _input(SkillMapState.th_color, SkillMapState.set_th_color, "#6366f1"), spacing="0", width="120px"),
                    spacing="3", width="100%",
                ),
                rx.vstack(_label("Description"), _textarea(SkillMapState.th_description, SkillMapState.set_th_description, "Périmètre couvert par ce thème…", rows="2"), spacing="0", width="100%"),
                rx.button(
                    "Enregistrer",
                    on_click=SkillMapState.save_theme,
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    color="white", border="none", border_radius="8px",
                    padding="8px 20px", cursor="pointer", font_weight="700",
                    width="100%",
                ),
                spacing="4", width="100%",
            ),
            background=CARD_BG, border=f"1px solid {BORDER}",
            border_radius="14px", padding="1.5rem", max_width="480px",
        ),
        open=SkillMapState.show_theme_form,
    )


def _contenu_type_label(t: str) -> str:
    return {"texte": "📄 Texte / cours", "lien": "🔗 Lien externe", "procedure": "📋 Procédure", "quiz": "❓ Quiz"}.get(t, t)


def _formation_form_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.text(
                        rx.cond(SkillMapState.edit_formation_id != "", "Modifier la formation", "Nouvelle formation"),
                        color=TEXT, font_size="1rem", font_weight="700",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.icon_button(rx.icon("x", size=15), on_click=SkillMapState.close_formation_form,
                                       background="transparent", color=MUTED,
                                       border=f"1px solid {BORDER}", border_radius="8px",
                                       size="2", cursor="pointer"),
                    ),
                    width="100%", align="center",
                ),

                # Titre + Thème
                rx.vstack(_label("Titre *"), _input(SkillMapState.fm_titre, SkillMapState.set_fm_titre, "Ex : Créer un compte AD"), spacing="0", width="100%"),
                rx.hstack(
                    rx.vstack(
                        _label("Niveau"),
                        _select(SkillMapState.fm_niveau, SkillMapState.set_fm_niveau, NIVEAUX),
                        spacing="0", width="100%",
                    ),
                    rx.vstack(
                        _label("Durée (min)"),
                        _input(SkillMapState.fm_duree_min, SkillMapState.set_fm_duree_min, "30"),
                        spacing="0", width="110px",
                    ),
                    spacing="3", width="100%",
                ),
                rx.vstack(_label("Description courte"), _textarea(SkillMapState.fm_description, SkillMapState.set_fm_description, "Ce que le technicien va apprendre…", rows="2"), spacing="0", width="100%"),

                rx.divider(border_color=BORDER),

                # Bloc ajout contenu
                rx.vstack(
                    rx.text("Contenus", color=TEXT, font_size="0.88rem", font_weight="700"),
                    rx.hstack(
                        rx.select.root(
                            rx.select.trigger(
                                style={"background": "#0d1117", "color": TEXT,
                                       "border": f"1px solid {BORDER}", "border_radius": "8px",
                                       "padding": "7px 10px", "font_size": "0.82rem"},
                            ),
                            rx.select.content(
                                rx.select.item("📄 Texte / cours",  value="texte"),
                                rx.select.item("🔗 Lien externe",   value="lien"),
                                rx.select.item("📋 Procédure",      value="procedure"),
                                rx.select.item("❓ Quiz",           value="quiz"),
                                background=CARD_BG,
                            ),
                            value=SkillMapState.new_contenu_type,
                            on_change=SkillMapState.set_new_contenu_type,
                        ),
                        rx.cond(
                            SkillMapState.new_contenu_type != "procedure",
                            _input(SkillMapState.new_contenu_titre, SkillMapState.set_new_contenu_titre, "Titre du bloc…"),
                        ),
                        spacing="2", width="100%",
                    ),
                    # Procedure picker OU textarea selon le type
                    rx.cond(
                        SkillMapState.new_contenu_type == "procedure",
                        rx.vstack(
                            _input(SkillMapState.proc_search_query,
                                   SkillMapState.set_proc_search_query,
                                   "Rechercher par titre ou codification (IAC, RAD…)"),
                            rx.cond(
                                SkillMapState.filtered_procedures.length() > 0,
                                rx.box(
                                    rx.foreach(
                                        SkillMapState.filtered_procedures,
                                        lambda p: rx.hstack(
                                            rx.badge(p["codification"], color_scheme="cyan",
                                                     variant="soft", font_size="0.62rem",
                                                     flex_shrink="0"),
                                            rx.text(p["titre"], color=TEXT, font_size="0.78rem",
                                                    flex="1", no_of_lines=1),
                                            on_click=SkillMapState.select_procedure_for_content(p["id"]),
                                            cursor="pointer",
                                            padding="5px 8px",
                                            border_radius="6px",
                                            spacing="2", align="center", width="100%",
                                            _hover={"background": "rgba(255,255,255,0.06)"},
                                        ),
                                    ),
                                    max_height="180px", overflow_y="auto",
                                    background="#0a0c17",
                                    border=f"1px solid {BORDER}",
                                    border_radius="8px", padding="4px",
                                    width="100%",
                                ),
                            ),
                            rx.cond(
                                SkillMapState.new_contenu_titre != "",
                                rx.hstack(
                                    rx.icon("check-circle", size=13, color=GREEN),
                                    rx.text(
                                        SkillMapState.new_contenu_codif, " – ",
                                        SkillMapState.new_contenu_titre,
                                        color=GREEN, font_size="0.75rem", no_of_lines=1,
                                    ),
                                    spacing="2", align="center",
                                    padding="5px 8px",
                                    background="rgba(34,197,94,0.06)",
                                    border=f"1px solid {GREEN}33",
                                    border_radius="6px",
                                ),
                            ),
                            spacing="2", width="100%",
                        ),
                        _textarea(SkillMapState.new_contenu_body,
                                  SkillMapState.set_new_contenu_body,
                                  "Contenu ou URL…", rows="3"),
                    ),
                    rx.button(
                        rx.icon("plus", size=13), "Ajouter ce bloc",
                        on_click=SkillMapState.add_contenu,
                        background="rgba(99,102,241,0.1)", color=PRIMARY,
                        border=f"1px solid rgba(99,102,241,0.3)", border_radius="8px",
                        font_size="0.8rem", padding="5px 14px", cursor="pointer",
                        _hover={"background": "rgba(99,102,241,0.2)"},
                    ),
                    # Liste des contenus ajoutés
                    rx.cond(
                        SkillMapState.fm_contenus.length() > 0,
                        rx.vstack(
                            rx.foreach(
                                SkillMapState.fm_contenus,
                                lambda c: rx.hstack(
                                    rx.text(c["titre"], color=TEXT, font_size="0.8rem", flex="1"),
                                    rx.badge(c["type"], color_scheme="indigo", variant="soft", font_size="0.65rem"),
                                    rx.icon_button(
                                        rx.icon("x", size=11),
                                        on_click=SkillMapState.remove_contenu(c["id"]),
                                        background="transparent", color=RED,
                                        size="1", cursor="pointer",
                                    ),
                                    spacing="2", align="center", width="100%",
                                    padding="5px 8px",
                                    background="rgba(255,255,255,0.02)",
                                    border=f"1px solid {BORDER}",
                                    border_radius="6px",
                                ),
                            ),
                            spacing="2", width="100%",
                        ),
                    ),
                    spacing="3", width="100%",
                ),

                rx.button(
                    "Enregistrer la formation",
                    on_click=SkillMapState.save_formation,
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    color="white", border="none", border_radius="8px",
                    padding="8px 20px", cursor="pointer", font_weight="700", width="100%",
                ),
                spacing="4", width="100%",
            ),
            background=CARD_BG, border=f"1px solid {BORDER}",
            border_radius="14px", padding="1.5rem",
            max_width="560px", max_height="90vh", overflow_y="auto",
        ),
        open=SkillMapState.show_formation_form,
    )


def _parcours_form_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.text(
                        rx.cond(SkillMapState.edit_parcours_id != "", "Modifier le parcours", "Nouveau parcours"),
                        color=TEXT, font_size="1rem", font_weight="700",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.icon_button(rx.icon("x", size=15), on_click=SkillMapState.close_parcours_form,
                                       background="transparent", color=MUTED,
                                       border=f"1px solid {BORDER}", border_radius="8px",
                                       size="2", cursor="pointer"),
                    ),
                    width="100%", align="center",
                ),
                rx.vstack(_label("Nom *"), _input(SkillMapState.pc_nom, SkillMapState.set_pc_nom, "Ex : Onboarding N1"), spacing="0", width="100%"),
                rx.vstack(_label("Description"), _textarea(SkillMapState.pc_description, SkillMapState.set_pc_description, "Objectif du parcours…", rows="2"), spacing="0", width="100%"),
                rx.hstack(
                    rx.vstack(_label("Icône"), _input(SkillMapState.pc_icon, SkillMapState.set_pc_icon, "map"), spacing="0", width="100%"),
                    rx.vstack(_label("Couleur"), _input(SkillMapState.pc_color, SkillMapState.set_pc_color, "#6366f1"), spacing="0", width="120px"),
                    spacing="3", width="100%",
                ),
                # Sélection des formations
                rx.vstack(
                    rx.text("Formations incluses", color=TEXT, font_size="0.85rem", font_weight="600"),
                    rx.box(
                        rx.foreach(
                            SkillMapState.formations,
                            lambda f: rx.hstack(
                                rx.checkbox(
                                    checked=SkillMapState.pc_etapes.contains(f["id"]),
                                    on_change=lambda _: SkillMapState.toggle_etape(f["id"]),
                                ),
                                rx.text(f["titre"], color=TEXT, font_size="0.82rem"),
                                rx.badge(f["niveau"], color_scheme="gray", variant="soft", font_size="0.65rem"),
                                spacing="2", align="center",
                                padding="5px 0",
                            ),
                        ),
                        max_height="200px", overflow_y="auto", width="100%",
                    ),
                    spacing="2", width="100%",
                ),
                rx.button(
                    "Enregistrer le parcours",
                    on_click=SkillMapState.save_parcours,
                    background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                    color="white", border="none", border_radius="8px",
                    padding="8px 20px", cursor="pointer", font_weight="700", width="100%",
                ),
                spacing="4", width="100%",
            ),
            background=CARD_BG, border=f"1px solid {BORDER}",
            border_radius="14px", padding="1.5rem",
            max_width="500px", max_height="90vh", overflow_y="auto",
        ),
        open=SkillMapState.show_parcours_form,
    )


def _confirm_delete_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.text("Supprimer cet élément ?", color=TEXT, font_size="1rem", font_weight="700"),
                rx.text("Cette action est irréversible.", color=MUTED, font_size="0.85rem"),
                rx.hstack(
                    rx.button("Supprimer", on_click=SkillMapState.confirm_delete,
                              background="rgba(239,68,68,0.14)", color=RED,
                              border=f"1px solid {RED}44", border_radius="8px",
                              padding="5px 14px", font_size="0.82rem", cursor="pointer"),
                    rx.dialog.close(
                        rx.button("Annuler", on_click=SkillMapState.cancel_delete,
                                  background="transparent", color=MUTED,
                                  border=f"1px solid {BORDER}", border_radius="8px",
                                  padding="5px 14px", font_size="0.82rem", cursor="pointer"),
                    ),
                    spacing="2", justify="end", margin_top="0.5rem",
                ),
                spacing="3", width="100%",
            ),
            background=CARD_BG, border=f"1px solid {BORDER}",
            border_radius="12px", padding="1.25rem", max_width="340px",
        ),
        open=SkillMapState.confirm_delete_id != "",
    )


# ── Page principale ───────────────────────────────────────────────────────────

def skill_map_page() -> rx.Component:
    return page_layout(
        rx.vstack(
            # ── Header ────────────────────────────────────────────────────
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.icon("map", size=20, color=PRIMARY),
                        rx.heading("Skill Map", color=TEXT, size="5"),
                        spacing="2", align="center",
                    ),
                    rx.text("Carte des compétences et parcours de formation N1",
                            color=MUTED, font_size="0.82rem"),
                    spacing="1",
                ),
                rx.spacer(),
                # Progression globale
                rx.cond(
                    SkillMapState.formations.length() > 0,
                    rx.hstack(
                        rx.vstack(
                            rx.text("Ta progression", color=MUTED, font_size="0.72rem"),
                            rx.hstack(
                                rx.box(
                                    rx.box(
                                        height="100%", background=PRIMARY, border_radius="3px",
                                        transition="width 0.5s ease",
                                        style={"width": SkillMapState.total_progress_pct.to_string() + "%"},
                                    ),
                                    background="rgba(255,255,255,0.08)",
                                    border_radius="3px", height="6px", width="140px",
                                    overflow="hidden",
                                ),
                                rx.text(SkillMapState.total_progress_pct.to_string(), "%",
                                        color=PRIMARY, font_size="0.85rem", font_weight="800"),
                                spacing="2", align="center",
                            ),
                            spacing="1", align="end",
                        ),
                        rx.cond(
                            AuthState.can_edit_formation,
                            rx.button(
                                rx.icon("plus", size=14), "Nouveau thème",
                                on_click=SkillMapState.open_new_theme,
                                background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                                color="white", border="none", border_radius="9px",
                                padding="7px 16px", cursor="pointer", font_weight="700",
                                font_size="0.82rem",
                                _hover={"opacity": "0.88"},
                            ),
                        ),
                        spacing="3", align="center",
                    ),
                ),
                width="100%", align="center",
            ),

            # ── Grille des thèmes ──────────────────────────────────────────
            rx.cond(
                SkillMapState.themes_with_counts.length() == 0,
                rx.box(
                    rx.vstack(
                        rx.icon("map", size=36, color=MUTED),
                        rx.text("Aucun thème pour l'instant.", color=MUTED, font_size="0.9rem"),
                        rx.cond(
                            AuthState.can_edit_formation,
                            rx.button(
                                rx.icon("plus", size=13), "Créer le premier thème",
                                on_click=SkillMapState.open_new_theme,
                                background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                                color="white", border="none", border_radius="9px",
                                padding="8px 18px", cursor="pointer", font_weight="700",
                            ),
                        ),
                        spacing="3", align="center",
                    ),
                    padding="3rem 0", text_align="center", width="100%",
                    background=CARD_BG, border=f"1px solid {BORDER}", border_radius="14px",
                ),
                rx.grid(
                    rx.foreach(SkillMapState.themes_with_counts, _theme_card),
                    columns="4",
                    spacing="4",
                    width="100%",
                ),
            ),

            # ── Zone centrale : roadmap + détail ──────────────────────────
            rx.flex(
                # Colonne roadmap (formations du thème)
                rx.box(
                    _theme_roadmap(),
                    flex="1", min_width="0",
                    background=CARD_BG, border=f"1px solid {BORDER}",
                    border_radius="14px", padding="1.25rem",
                ),
                # Panneau détail (si formation sélectionnée)
                rx.cond(
                    SkillMapState.selected_formation_id != "",
                    rx.box(
                        _detail_panel(),
                        flex="0 0 360px", min_width="0",
                    ),
                ),
                gap="1.25rem", width="100%", align_items="start",
            ),

            # ── Parcours ──────────────────────────────────────────────────
            _parcours_section(),

            # ── Modals ────────────────────────────────────────────────────
            _theme_form_modal(),
            _formation_form_modal(),
            _parcours_form_modal(),
            _confirm_delete_modal(),

            spacing="5", width="100%",
            on_mount=SkillMapState.load,
        ),
        title="Skill Map",
    )
