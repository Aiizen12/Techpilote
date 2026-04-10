import reflex as rx
from techpilot.state.auth import AuthState

# Palette dark
BG = "#0d0f1a"
CARD_BG = "#151728"
BORDER = "#2a2d4a"
PRIMARY = "#6366f1"
TEXT = "#e2e8f0"
MUTED = "#64748b"


def login_page() -> rx.Component:
    return rx.box(
        # Fond gradient
        rx.box(
            style={
                "position": "fixed",
                "inset": "0",
                "background": f"radial-gradient(ellipse at 50% 0%, rgba(99,102,241,0.15) 0%, {BG} 60%)",
                "z_index": "-1",
            }
        ),
        # Carte de connexion
        rx.center(
            rx.box(
                # Logo / titre
                rx.vstack(
                    rx.box(
                        rx.text("⚡", font_size="2.5rem"),
                        background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                        border_radius="16px",
                        padding="12px 18px",
                        display="inline-block",
                    ),
                    rx.heading(
                        "TechPilot",
                        size="8",
                        color=TEXT,
                        font_weight="800",
                    ),
                    rx.text(
                        "Gestion d'équipe Helpdesk N1",
                        color=MUTED,
                        font_size="0.95rem",
                    ),
                    spacing="3",
                    align="center",
                    margin_bottom="2rem",
                ),
                # Erreur
                rx.cond(
                    AuthState.login_error != "",
                    rx.box(
                        rx.hstack(
                            rx.icon("triangle-alert", size=16, color="#f87171"),
                            rx.text(AuthState.login_error, color="#f87171", font_size="0.875rem"),
                            spacing="2",
                        ),
                        background="rgba(239,68,68,0.1)",
                        border="1px solid rgba(239,68,68,0.3)",
                        border_radius="8px",
                        padding="10px 14px",
                        margin_bottom="1rem",
                    ),
                ),
                # Formulaire
                rx.vstack(
                    rx.box(
                        rx.text("Identifiant", color=MUTED, font_size="0.8rem", font_weight="600", margin_bottom="6px"),
                        rx.input(
                            placeholder="manager ou numéro matricule",
                            value=AuthState.login_user_id,
                            on_change=AuthState.set_login_user_id,
                            background="#1e2035",
                            border=f"1px solid {BORDER}",
                            color=TEXT,
                            border_radius="10px",
                            padding="10px 14px",
                            width="100%",
                            _focus={"border_color": PRIMARY, "outline": "none", "box_shadow": f"0 0 0 2px rgba(99,102,241,0.2)"},
                            _placeholder={"color": MUTED},
                        ),
                        width="100%",
                    ),
                    rx.box(
                        rx.text("Mot de passe", color=MUTED, font_size="0.8rem", font_weight="600", margin_bottom="6px"),
                        rx.input(
                            type="password",
                            placeholder="••••••••",
                            value=AuthState.login_password,
                            on_change=AuthState.set_login_password,
                            background="#1e2035",
                            border=f"1px solid {BORDER}",
                            color=TEXT,
                            border_radius="10px",
                            padding="10px 14px",
                            width="100%",
                            on_key_down=lambda e: rx.cond(e == "Enter", AuthState.do_login(), rx.noop()),
                            _focus={"border_color": PRIMARY, "outline": "none", "box_shadow": f"0 0 0 2px rgba(99,102,241,0.2)"},
                            _placeholder={"color": MUTED},
                        ),
                        width="100%",
                    ),
                    rx.button(
                        "Se connecter",
                        on_click=AuthState.do_login,
                        background=f"linear-gradient(135deg, {PRIMARY}, #8b5cf6)",
                        color="white",
                        border_radius="10px",
                        padding="11px",
                        width="100%",
                        font_weight="600",
                        font_size="0.95rem",
                        cursor="pointer",
                        _hover={"opacity": "0.9", "transform": "translateY(-1px)"},
                        transition="all 0.2s",
                    ),
                    spacing="4",
                    width="100%",
                ),
                background=CARD_BG,
                border=f"1px solid {BORDER}",
                border_radius="20px",
                padding="2.5rem",
                width="380px",
                box_shadow="0 25px 50px rgba(0,0,0,0.5)",
            ),
            min_height="100vh",
            background=BG,
        ),
        background=BG,
        min_height="100vh",
    )
