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
        SELECT author_id,       -- кого цитируют
               author_name,
               citing_author,   -- кто цитирует
               citing_author_name
        FROM new_data.author_citations_view
        WHERE TRUE
    """

    params = []
    if filters.authors:
        if len(filters.authors) == 1:
            filters.authors.append(-1)
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

    # Считаем веса
    from collections import defaultdict

    cited_weights = defaultdict(int)
    citing_weights = defaultdict(int)
    links_map = defaultdict(int)
    author_names = {}

    for author_id, author_name, citing_id, citing_name in rows:
        # Вес — сколько раз этого автора цитировали
        cited_weights[author_id] += 1
        # Вес — сколько раз автор кого-то цитировал
        citing_weights[citing_id] += 1
        # Сколько раз одна и та же пара авторов
        links_map[(citing_id, author_id)] += 1

        # Имя сохраняем для обоих
        author_names[author_id] = author_name
        author_names[citing_id] = citing_name

    # Собираем ноды
    unique_ids = set(list(cited_weights.keys()) + list(citing_weights.keys()))
    nodes = []
    for aid in unique_ids:
        name = author_names.get(aid, f"Author {aid}")
        weight = cited_weights.get(aid, 0) or citing_weights.get(aid, 0)
        nodes.append({
            "id": str(aid),
            "name": name,
            "weight": weight
        })

    # Собираем связи
    links = [
        {
            "source": str(src),
            "target": str(tgt),
            "weight": count
        }
        for (src, tgt), count in links_map.items()
    ]

    return {
        "nodes": nodes,
        "links": links,
        "categories": [{"name": "Автор"}]
    }


@references_bp.route("/articles", methods=["POST"])
def get_articles_between_authors():
    try:
        data = request.get_json()
        citing_author = data.get("citing_author")
        cited_author = data.get("cited_author")

        if not (isinstance(citing_author, int) and isinstance(cited_author, int)):
            abort(400, description="Both citing_author and cited_author must be integers")

        query = """
            SELECT DISTINCT author_item_title, citing_item_title
            FROM new_data.author_citations_view
            WHERE citing_author = %s AND author_id = %s
        """

        with DatabaseService("new_data") as cur:
            cur.execute(query, (citing_author, cited_author))
            articles = [
                {
                    "cited_title": row[0],
                    "citing_title": row[1]
                }
                for row in cur.fetchall()
            ]

        return jsonify(articles)

    except Exception as e:
        logging.exception(e)
        return jsonify({"error": str(e)}), 500


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
