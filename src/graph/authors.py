import json
from dataclasses import dataclass, field
import logging
from dacite import from_dict
from flask import Blueprint, abort, jsonify, request, Response
import psycopg2

from ..utils.graph import tuples_to_graph_links, tuples_to_graph_nodes

from ..entities.datacls import GraphFilter

from ..database.database import DatabaseService

authors_bp = Blueprint("authors", __name__, url_prefix="/authors")


@dataclass
class AuthorsFilters(GraphFilter):
    authors: list[int] = field(default_factory=list)
    organizations: list[int] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    cities: list[str] = field(default_factory=list)


@dataclass
class CitationsFilters(GraphFilter):
    authors: list[int] = field(default_factory=list)  # цитируемые авторы
    citing_authors: list[int] = field(default_factory=list)  # кто цитирует


def get_filtered_authors(filters: AuthorsFilters, cur: psycopg2.extensions.cursor):
    query_temp_table = """
        CREATE TEMP TABLE filtered_authors AS
        SELECT authorid,
            lastname || ' ' ||
            (SELECT string_agg(LEFT(TRIM(word), 1) || '.', '')
                FROM unnest(string_to_array(regexp_replace(initials, '[.]', ' ', 'g'), ' ')) AS word
                WHERE TRIM(word) <> '') AS name,
            a.itemid
        FROM authors a
                JOIN affiliations aff ON a.id = aff.author
                JOIN keywords k ON a.itemid = k.itemid
        {where_clause};
        
        CREATE TEMP TABLE related_authors AS
        SELECT DISTINCT a.authorid,
            lastname || ' ' ||
            (SELECT string_agg(LEFT(TRIM(word), 1) || '.', '')
                FROM unnest(string_to_array(regexp_replace(a.initials, '[.]', ' ', 'g'), ' ')) AS word
                WHERE TRIM(word) <> '') AS name,
            a.itemid
        FROM authors a
        JOIN filtered_authors fa ON a.itemid = fa.itemid
        WHERE a.authorid NOT IN (SELECT authorid FROM filtered_authors);
    """
    where_clauses = ["authorid IS NOT NULL"]
    params = []
    if filters.authors:
        where_clauses.append("a.authorid IN %s")
        params.append(tuple(filters.authors))
    if filters.organizations:
        where_clauses.append("aff.affiliationid IN %s")
        params.append(tuple(filters.organizations))
    if filters.keywords:
        where_clauses.append("k.keyword IN %s")
        params.append(tuple(filters.keywords))
    if filters.cities:
        where_clauses.append("aff.town IN %s")
        params.append(tuple(filters.cities))

    if where_clauses:
        where_clause = "WHERE " + " AND ".join(where_clauses)
    else:
        where_clause = ""
    query_temp_table = query_temp_table.format(where_clause=where_clause)
    logging.debug(query_temp_table)

    cur.execute(query_temp_table, params)
    query_nodes = """
        SELECT authorid,
            array_agg(DISTINCT INITCAP(name)),
            COUNT(DISTINCT itemid) AS total_publications,
            1 as category
        FROM filtered_authors
        GROUP BY authorid
        UNION
        SELECT authorid,
            array_agg(DISTINCT INITCAP(name)),
            COUNT(DISTINCT itemid) AS total_publications,
            0 as category
        FROM related_authors
        GROUP BY authorid
    """
    cur.execute(query_nodes)
    nodes = tuples_to_graph_nodes(cur.fetchall())

    query_edges = """
        SELECT a1.authorid, a2.authorid, COUNT(DISTINCT a1.itemid)
        FROM (
            SELECT * FROM filtered_authors
            UNION
            SELECT * FROM related_authors
        ) a1
        JOIN (
            SELECT * FROM filtered_authors
            UNION
            SELECT * FROM related_authors
        ) a2 ON a1.itemid = a2.itemid
        WHERE a1.authorid < a2.authorid
        GROUP BY a1.authorid, a2.authorid;
    """
    cur.execute(query_edges)
    edges = tuples_to_graph_links(cur.fetchall())

    return {"nodes": nodes, "links": edges, "categories": [{"name": "Связанные авторы"}, {"name": "Отфильтрованные авторы"}]}


@authors_bp.route("/data", methods=["POST"])
def get_authors_graph_data():
    try:
        filters: AuthorsFilters = from_dict(AuthorsFilters, request.get_json())
        if not filters.has_at_least_one_filter():
            abort(400, "At least one filter is required")
        logging.debug(f"Received filters: {filters}")

        with DatabaseService("new_data") as cur:
            graph_data = get_filtered_authors(filters, cur)
            return jsonify(graph_data)

    except Exception as e:  # pylint: disable=broad-except
        logging.exception(e)
        return jsonify({"error": str(e)}), 500

@authors_bp.route("/citations", methods=["POST"])
def get_citation_graph():
    try:
        filters: CitationsFilters = from_dict(CitationsFilters, request.get_json())
        logging.debug(f"Received citation filters: {filters}")

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
            query += " AND author_id IN %s"
            params.append(tuple(filters.authors))
        if filters.citing_authors:
            query += " AND citing_author IN %s"
            params.append(tuple(filters.citing_authors))

        with DatabaseService("new_data") as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        authors = {}
        for row in rows:
            authors[row[0]] = row[1]
            authors[row[2]] = row[3]

        nodes = [
            {"id": str(aid), "name": name}
            for aid, name in authors.items()
        ]

        links = [
            {
                "source": str(row[2]),
                "target": str(row[0]),
                "title": f"{row[7]} → {row[5]}"
            }
            for row in rows
        ]

        result = {
            "nodes": nodes,
            "links": links,
            "categories": [{"name": "Автор"}]
        }

        return Response(json.dumps(result, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        logging.exception(e)
        return jsonify({"error": str(e)}), 500


