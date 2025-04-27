import logging
from dataclasses import dataclass, field

import psycopg2
from dacite import from_dict
from flask import Blueprint, abort, jsonify, request

from ..database.database import DatabaseService
from ..entities.datacls import GraphFilter
from ..utils.database import fetch_paginated
from ..utils.graph import tuples_to_graph_links, tuples_to_graph_nodes

organizations_bp = Blueprint("organizations", __name__, url_prefix="/organizations")


@dataclass
class OrganizationsFilters(GraphFilter):
    keywords: list[str] = field(default_factory=list)
    min_publications: str = "3"


def get_filtered_organizations(filters: OrganizationsFilters, cur: psycopg2.extensions.cursor):
    """
    FIXME: В функции две критические проблемы, связанные с корявостью базы:
    1. Authors и affiliations не всегда связаны однозначно.
        Получается, что автор писал статью, например, в МГУ,
        а она зачтётся так же и Финашке, и Плешке, и СПБГУ,
        если эти организции числятся у него а аффилиациях
    """
    logging.critical("Получение данных о совместных работах организаций пока работает некорректно")
    min_publications = int(filters.min_publications)

    query_temp_table = """
        CREATE TEMP TABLE filtered_orgs AS
        SELECT DISTINCT eo.organizationid AS id, eo.organizationname AS orgname, a.itemid AS itemid
        FROM elibrary_organizations eo
            JOIN affiliations aff ON aff.affiliationid = eo.organizationid
            JOIN authors a ON aff.author = a.id
            LEFT JOIN keywords k ON a.itemid = k.itemid
        WHERE k.keyword IN (%s);
        
        CREATE TEMP TABLE orgs_with_min_count AS
        SELECT id, orgname, COUNT(itemid) as weight, 0 AS category
        FROM filtered_orgs
        GROUP BY id, orgname
        HAVING COUNT(itemid) >= %s;
    """

    query_nodes = """
        SELECT id, orgname, weight, category
        FROM orgs_with_min_count;
    """

    query_edges = """
        SELECT o1.id, o2.id, COUNT(DISTINCT o1.itemid)
        FROM filtered_orgs o1
            JOIN filtered_orgs o2 ON o1.itemid = o2.itemid
            JOIN orgs_with_min_count owc1 ON o1.id = owc1.id
            JOIN orgs_with_min_count owc2 ON o2.id = owc2.id
        WHERE o1.id < o2.id
        GROUP BY o1.id, o2.id;
    """

    cur.execute(query_temp_table, (tuple(filters.keywords), min_publications))

    cur.execute(query_nodes)
    nodes = tuples_to_graph_nodes(cur.fetchall())

    cur.execute(query_edges)
    edges = tuples_to_graph_links(cur.fetchall())

    return {
        "nodes": nodes,
        "links": edges,
        "categories": [
            {"name": "Отфильтрованные организации"},
        ],
    }


@organizations_bp.route("/data", methods=["POST"])
def get_organizations_graph_data():
    try:
        filters: OrganizationsFilters = from_dict(OrganizationsFilters, request.get_json())
        if not filters.has_at_least_one_filter():
            abort(400, "At least one filter is required")

        logging.debug(f"Received filters: {filters}")
        with DatabaseService("new_data") as cur:
            graph_data = get_filtered_organizations(filters, cur)
            return jsonify(graph_data)

    except Exception as e:  # pylint: disable=broad-except
        logging.exception(e)
        return jsonify({"error": str(e)}), 500


@organizations_bp.route("/table/node", methods=["GET"])
def get_author_table_nodes():
    try:
        organizationid = request.args.get("id", "")
        page = int(request.args.get("page", 1))

        if not organizationid:
            return abort(400, description="organizationid is required")

        with DatabaseService("new_data") as cur:
            query = """
                SELECT DISTINCT a.itemid as key, i.title, i.year, j.name as journal, i.link
                FROM elibrary_organizations eo
                        JOIN affiliations aff ON aff.affiliationid = eo.organizationid
                        JOIN authors a ON aff.author = a.id
                        JOIN items i ON a.itemid = i.itemid
                        LEFT JOIN journals j ON a.itemid = j.itemid
                WHERE eo.organizationid = %s
                ORDER BY i.year DESC, i.title
            """
            rows, has_more = fetch_paginated(query, page=page, items_on_page=5, params=(organizationid,), cursor=cur)

            if not cur.description:
                return abort(500, description="Не удалось получить описание столбцов")

            column_names = [desc[0] for desc in cur.description]

            result = [dict(zip(column_names, row)) for row in rows]

            return jsonify({"items": result, "hasMore": has_more})

    except Exception as e:  # pylint: disable=broad-except
        logging.exception(e)
        return jsonify({"error": str(e)}), 500


@organizations_bp.route("/table/link", methods=["GET"])
def get_author_table_links():
    try:
        source = request.args.get("source", "")
        target = request.args.get("target", "")
        page = int(request.args.get("page", 1))

        if not source or not target:
            return abort(400, description="source and target are required")

        with DatabaseService("new_data") as cur:
            query = """
                WITH source_publications AS (SELECT DISTINCT eo.organizationid, a.itemid
                                            FROM elibrary_organizations eo
                                                    JOIN affiliations aff ON aff.affiliationid = eo.organizationid
                                                    JOIN authors a ON aff.author = a.id
                                            WHERE organizationid = %s),
                    target_publications AS (SELECT DISTINCT eo.organizationid, a.itemid
                                            FROM elibrary_organizations eo
                                                    JOIN affiliations aff ON aff.affiliationid = eo.organizationid
                                                    JOIN authors a ON aff.author = a.id
                                            WHERE organizationid = %s)
                SELECT DISTINCT i.itemid as key, i.title, i.year, j.name as journal, i.link
                FROM source_publications sp
                        JOIN target_publications tp ON sp.itemid = tp.itemid
                        JOIN items i ON sp.itemid = i.itemid
                        LEFT JOIN journals j ON i.itemid = j.itemid
                ORDER BY i.year DESC, i.title
            """
            rows, has_more = fetch_paginated(query, page=page, items_on_page=5, params=(source, target), cursor=cur)

            if not cur.description:
                return abort(500, description="Не удалось получить описание столбцов")

            column_names = [desc[0] for desc in cur.description]

            result = [dict(zip(column_names, row)) for row in rows]

            return jsonify({"items": result, "hasMore": has_more})

    except Exception as e:  # pylint: disable=broad-except
        logging.exception(e)
        return jsonify({"error": str(e)}), 500
