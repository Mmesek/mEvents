from fasthtml import common as fh
from src.beforeware import beforeware
from src.components.headers import HEADERS

ROUTES = []


def make_app(route: str):
    app, rt = fh.fast_app(
        hdrs=HEADERS,
        before=beforeware,
    )
    add_mount(route, app)
    return rt


def add_mount(route: str, app):
    ROUTES.append(fh.Mount(f"/{route}", app))
