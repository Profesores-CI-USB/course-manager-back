from typing import Any


def _is_admin(user: Any) -> bool:
    return getattr(user, "role", None) == "admin"


def _resolve_order_column(order_by: str, allowed_columns: dict[str, object], default_column: object):
    return allowed_columns.get(order_by, default_column)


def _apply_pagination(query, limit: int, offset: int):
    return query.limit(limit).offset(offset)
