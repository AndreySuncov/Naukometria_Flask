import json
import logging
from dataclasses import dataclass, field

from dacite import from_dict
from flask import Blueprint, Response, abort, jsonify, request

from ..database.database import DatabaseService
from ..entities.datacls import GraphFilter

references_bp = Blueprint("references", __name__, url_prefix="/references")


@dataclass
class ReferencesFilters(GraphFilter):
    authors: list[int] = field(default_factory=list)  # цитируемые авторы
    citing_authors: list[int] = field(default_factory=list)  # кто цитирует


def get_filtered_references(filters: ReferencesFilters):
    query = """
            SELECT DISTINCT author_id, \
                            author_name, \
                            citing_author, \
                            citing_author_name, \
                            author_item_id, \
                            author_item_title, \
                            citing, \
                            citing_item_title
            FROM new_data.author_citations_view
            WHERE TRUE \
            """

    params = []
    if filters.authors:
        if len(filters.authors) == 1:
            filters.authors.append(-1)  # добавляем фиктивный ID, чтобы IN (...) работал
        query += " AND author_id IN %s"
        params.append(tuple(filters.authors))

    if filters.citing_authors:
        if len(filters.citing_authors) == 1:
            filters.citing_authors.append(-1)
        query += " AND citing_author IN %s"
        params.append(tuple(filters.citing_authors))

    with DatabaseService("new_data") as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    authors = {}
    for row in rows:
        authors[row[0]] = row[1]
        authors[row[2]] = row[3]

    nodes = [{"id": str(aid), "name": name} for aid, name in authors.items()]

    links_raw = [{"source": str(row[2]), "target": str(row[0]), "title": f"{row[7]} → {row[5]}"} for row in rows]

    # Удаляем дубликаты по source, target, title
    seen = set()
    links = []
    for link in links_raw:
        key = (link["source"], link["target"], link["title"])
        if key not in seen:
            seen.add(key)
            links.append(link)

    return {"nodes": nodes, "links": links, "categories": [{"name": "Автор"}]}


@references_bp.route("/data", methods=["POST"])
def get_references_graph_data():
    try:
        filters: ReferencesFilters = from_dict(ReferencesFilters, request.get_json())
        if not filters.has_at_least_one_filter():
            abort(400, "At least one filter is required")
        logging.debug(f"Received citation filters: {filters}")

        graph_data = get_filtered_references(filters)
        return Response(json.dumps(graph_data, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:  # pylint: disable=broad-except
        logging.exception(e)
        return jsonify({"error": str(e)}), 500
