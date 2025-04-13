import logging
from typing import Any

from flask import request

from src.database.database import DatabaseService


def fetch_paginated_options(
    query: str, label_column: str, value_column: str, base_filter: str = "", default_per_page: int = 20
) -> dict[str, Any]:
    """Универсальная функция для получения данных с пагинацией и поиском

    Args:
        query: Базовый SQL запрос без условий LIMIT/OFFSET
        label_column: Название колонки с меткой
        value_column: Название колонки со значением
        base_filter: Дополнительные условия WHERE (без WHERE)
        default_per_page: Количество элементов на странице

    Returns:
        Ответ в стандартном формате для фильтров: {"items": list[{"label" | "value": str}], "hasMore": bool, "total": int}
    """
    q = request.args.get("q", "")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", default_per_page))
    offset = (page - 1) * per_page

    try:
        with DatabaseService() as cur:
            where_clauses = [f"{value_column} IS NOT NULL"]
            if base_filter:
                where_clauses.append(base_filter)
            if q:
                where_clauses.append(f"{label_column} ILIKE %s")

            where_stmt = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            full_query = f"""
                {query}
                {where_stmt}
                ORDER BY {label_column}
                LIMIT %s OFFSET %s;
            """

            params = []
            if q:
                params.append(f"%{q}%")
            params.extend([per_page + 1, offset])

            print(full_query)
            cur.execute(full_query, params if params else None)
            rows = cur.fetchall()
            print(rows[:3])
            items = [{"value": row[0], "label": row[1]} for row in rows[:per_page]]
            has_more = len(rows) > per_page

            return {"items": items, "hasMore": has_more, "total": len(items)}
    except Exception as e:  # pylint: disable=broad-except
        logging.exception(f"Error fetching paginated options: {e}")
        return {"items": [], "hasMore": False, "total": 0}
