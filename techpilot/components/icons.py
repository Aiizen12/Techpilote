import reflex as rx

# rx.icon() requires a literal string — use rx.match for dynamic icon names
def dyn_icon(name, size: int = 16, color: str = "white") -> rx.Component:
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
        ("briefcase",      rx.icon("briefcase",       **kw)),
        ("laptop",         rx.icon("laptop",          **kw)),
        ("printer",        rx.icon("printer",         **kw)),
        ("network",        rx.icon("network",         **kw)),
        ("globe",          rx.icon("globe",           **kw)),
        ("smartphone",     rx.icon("smartphone",      **kw)),
        rx.icon("circle", **kw),
    )
