import reflex as rx

config = rx.Config(
    app_name="techpilot",
    db_url=None,  # On utilise MongoDB directement
    tailwind=None,
    cors_allowed_origins=["*"],
)
