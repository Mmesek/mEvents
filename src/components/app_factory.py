from fasthtml import common as fh
from monsterui import all as mui
from src.beforeware import beforeware, refreshware
from src.components.headers import HEADERS
from functools import wraps
from src.components.translations import Translation
from inspect import signature

from fasthtml.core import _special_names

_special_names.update({"t"})
ROUTES = []


def dependency_injection(rt):
    @wraps(rt)
    def register_wrapper(cls=None, *path_args, **path_kwargs):
        def func_wrapper(f):
            @wraps(f)
            def injector(*args, **kwargs):
                _locale = kwargs.get("session", {}).get("locale", "en")
                params = signature(f).parameters
                if "t" in params and not kwargs.get("t"):
                    kwargs["t"] = Translation(_locale)

                return f(*args, **kwargs)

            return rt(*path_args, **path_kwargs)(injector)

        if cls is not None and callable(cls) and not isinstance(cls, str):
            return func_wrapper(cls)
        if cls is not None:
            path_args = (cls, *path_args)
        return func_wrapper

    return register_wrapper


def server_error(request: fh.Request, exc: fh.HTTPException):
    return mui.Card("Error! Jeśli problem będzie się powtarzał, skontakuj się ze mną bezpośrednio!")


def make_app(route: str):
    app, rt = fh.fast_app(hdrs=HEADERS, before=[refreshware, beforeware], exception_handlers={500: server_error})
    add_mount(route, app)
    return dependency_injection(rt)


def add_mount(route: str, app):
    ROUTES.append(fh.Mount(f"/{route}", app))
