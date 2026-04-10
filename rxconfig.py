import reflex as rx

config = rx.Config(
    app_name="techpilot",
    db_url=None,
    tailwind=None,
    cors_allowed_origins=["*"],
    api_url="https://techpilote-production.up.railway.app",
    frontend_port=3000,
    backend_port=8000,
)
