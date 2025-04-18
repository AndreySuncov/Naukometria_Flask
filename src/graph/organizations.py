from dataclasses import dataclass, field
import logging

from dacite import from_dict
from flask import Blueprint, abort, jsonify, request
import psycopg2

from ..utils.graph import tuples_to_graph_links, tuples_to_graph_nodes

from ..entities.datacls import GraphFilter

from ..database.database import DatabaseService


organizations_bp = Blueprint("organizations", __name__, url_prefix="/organizations")


@dataclass
class OrganizationsFilters(GraphFilter):
    keywords: list[str] = field(default_factory=list)


def get_filtered_organizations(filters: OrganizationsFilters, cur: psycopg2.extensions.cursor):
    """
    FIXME: В функции две критические проблемы, связанные с корявостью базы:
    1. Одна и та же организация имеет множество имен, а группировка производится по имени
    2. Authors и affiliations связаны не однозначно.
        Получается, что автор писал статью, например, в МГУ,
        а она зачтётся так же и Финашке, и Плешке, и СПБГУ,
        если эти организции числятся у него а аффилиациях
    """
    logging.critical("Получение данных о совместных работах организаций пока работает некорректно")
    query_temp_table = """
        CREATE TEMP TABLE filtered_orgs AS
        SELECT DISTINCT aff.name AS orgname, a.itemid AS itemid
        FROM affiliations aff
                JOIN authors a ON aff.author = a.id
                JOIN keywords k ON a.itemid = k.itemid
        WHERE k.keyword IN (%s);
        
        CREATE TEMP TABLE related_orgs AS
        SELECT DISTINCT aff.name AS orgname, a.itemid AS itemid
        FROM affiliations aff
                JOIN authors a ON aff.author = a.id
                JOIN authors a2 ON a.authorid = a2.authorid
                JOIN authors a3 ON a2.itemid = a3.itemid
        WHERE EXISTS (
            SELECT 1 FROM filtered_orgs fo WHERE fo.itemid = a3.itemid
        )
        AND NOT EXISTS (
            SELECT 1 FROM filtered_orgs fo WHERE fo.orgname = aff.name
        );
        
        CREATE TEMP TABLE orgs AS 
        SELECT orgname AS id, orgname, itemid, 1 AS category
        FROM filtered_orgs
        UNION
        SELECT orgname AS id, orgname, itemid, 0 AS category
        FROM related_orgs;
    """

    query_nodes = """
        SELECT id, orgname, COUNT(itemid), category
        FROM orgs
        GROUP BY id, orgname, category;
    """

    query_edges = """
        SELECT o1.orgname, o2.orgname, COUNT(DISTINCT o1.itemid)
        FROM filtered_orgs o1
        JOIN authors a1 ON o1.itemid = a1.itemid
        JOIN authors a2 ON a1.authorid = a2.authorid
        JOIN authors a3 ON a2.itemid = a3.itemid
        JOIN orgs o2 ON o1.itemid = a3.itemid
        WHERE o1.orgname < o2.orgname 
        GROUP BY o1.orgname, o2.orgname;
    """

    cur.execute(query_temp_table, filters.keywords)

    cur.execute(query_nodes)
    nodes = tuples_to_graph_nodes(cur.fetchall())

    cur.execute(query_edges)
    edges = tuples_to_graph_links(cur.fetchall())

    return {
        "nodes": nodes,
        "links": edges,
        "categories": [
            {"name": "Связанные организации, не писали на выбранную тему"},
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
