import reflex as rx
from techpilot.state.dashboard import DashboardState

TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
BORDER  = "#1c2138"
BG      = "#080b14"
CARD_BG = "#111524"


def notes_window_page() -> rx.Component:
    return rx.box(
        # Header
        rx.hstack(
            rx.box(
                rx.icon("notebook-pen", size=16, color="#f59e0b"),
                background="rgba(245,158,11,0.15)",
                border_radius="8px",
                padding="6px",
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.text("Notes rapides", color=TEXT, font_size="0.9rem", font_weight="700"),
            rx.spacer(),
            rx.hstack(
                rx.icon("save", size=12, color="#22c55e"),
                rx.text("Auto-sauvegardé", color="#22c55e", font_size="0.7rem"),
                spacing="1",
                align="center",
                id="save-indicator",
                opacity="0",
                transition="opacity 0.4s",
            ),
            spacing="2",
            align="center",
            padding="0.75rem 1rem",
            background=f"linear-gradient(135deg, rgba(245,158,11,0.12), rgba(245,158,11,0.04))",
            border_bottom=f"1px solid {BORDER}",
        ),

        # Textarea
        rx.text_area(
            placeholder="Tes notes, rappels, astuces du jour…",
            value=DashboardState.quick_notes,
            on_change=DashboardState.set_quick_notes,
            on_blur=DashboardState.save_notes,
            background=BG,
            color=TEXT,
            border="none",
            border_radius="0",
            padding="1rem",
            font_size="0.875rem",
            line_height="1.7",
            width="100%",
            height="calc(100vh - 52px)",
            resize="none",
            _placeholder={"color": "#475569"},
            _focus={"outline": "none", "box_shadow": "none"},
        ),

        # Script : flash "Auto-sauvegardé" après blur + on_mount pour charger les notes
        rx.script("""
(function() {
  // Flash save indicator after textarea blur
  document.addEventListener('focusout', function(e) {
    if (e.target.tagName === 'TEXTAREA') {
      var ind = document.getElementById('save-indicator');
      if (ind) {
        ind.style.opacity = '1';
        setTimeout(function() { ind.style.opacity = '0'; }, 1800);
      }
    }
  });
})();
"""),

        background=BG,
        min_height="100vh",
        width="100%",
        overflow="hidden",
        on_mount=DashboardState.load_data,
    )
