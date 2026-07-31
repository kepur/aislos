"""Route introspection helpers.

FastAPI 0.138 mounts sub-routers lazily as `_IncludedRouter` objects (no
`.path`), so `{r.path for r in app.routes}` no longer sees included routes.
These helpers walk the lazy includes recursively.
"""
from __future__ import annotations

from typing import Any, Iterator


def iter_registered_routes(app_or_routes: Any, prefix: str = "") -> Iterator[tuple[str, Any]]:
    """Yield (full_path, route) for every concrete route, expanding lazy includes."""
    routes = getattr(app_or_routes, "routes", app_or_routes)
    for route in routes:
        if hasattr(route, "path"):
            yield prefix + route.path, route
        elif hasattr(route, "original_router"):
            ctx_prefix = getattr(getattr(route, "include_context", None), "prefix", "") or ""
            yield from iter_registered_routes(route.original_router.routes, prefix + ctx_prefix)


def registered_route_paths(app: Any) -> set[str]:
    return {path for path, _route in iter_registered_routes(app)}
