import logging
from dataclasses import dataclass, field

import psycopg2
from dacite import from_dict
from flask import Blueprint, abort, jsonify, request

from ..database.database import DatabaseService
from ..entities.datacls import GraphFilter
from ..utils.graph import tuples_to_graph_links, tuples_to_graph_nodes

authors_bp = Blueprint("authors", __name__, url_prefix="/authors")


@dataclass
class AuthorsFilters(GraphFilter):
    authors: list[int] = field(default_factory=list)
    organizations: list[int] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    cities: list[str] = field(default_factory=list)
    min_publications: str = "3"


def get_filtered_authors(filters: AuthorsFilters, cur: psycopg2.extensions.cursor):
    min_publications = int(filters.min_publications)
    query_temp_table = """
        CREATE TEMP TABLE filtered_authors AS
        SELECT DISTINCT authorid,
            lastname || ' ' ||
            (SELECT string_agg(LEFT(TRIM(word), 1) || '.', '')
                FROM unnest(string_to_array(regexp_replace(initials, '[.]', ' ', 'g'), ' ')) AS word
                WHERE TRIM(word) <> '') AS name,
            a.itemid,
            CASE
                WHEN a.language = 'RU' THEN 0
                WHEN a.language = 'EN' THEN 1
                ELSE 2
                END                  as lang_priority
        FROM authors a
                JOIN affiliations aff ON a.id = aff.author
                JOIN keywords k ON a.itemid = k.itemid
        {where_clause};
        
        CREATE TEMP TABLE related_authors AS
        WITH related_authors_ids AS (SELECT a.authorid
                                    FROM authors a
                                            JOIN filtered_authors fa ON a.itemid = fa.itemid
                                    WHERE a.authorid != fa.authorid
                                    GROUP BY a.authorid, fa.authorid
                                    HAVING COUNT(DISTINCT a.itemid) >= %s)
        SELECT DISTINCT ON (a.authorid, a.itemid) a.authorid               as authorid,
                                                lastname || ' ' ||
                                                (SELECT string_agg(LEFT(TRIM(word), 1) || '.', '')
                                                FROM unnest(string_to_array(regexp_replace(a.initials, '[.]', ' ', 'g'), ' ')) AS word
                                                WHERE TRIM(word) <> '') AS name,
                                                a.itemid                 as itemid,
                                                CASE
                                                    WHEN a.language = 'RU' THEN 0
                                                    WHEN a.language = 'EN' THEN 1
                                                    ELSE 2
                                                    END                  as lang_priority
        FROM authors a
                JOIN related_authors_ids rela ON a.authorid = rela.authorid
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

    params.append(min_publications)

    if where_clauses:
        where_clause = "WHERE " + " AND ".join(where_clauses)
    else:
        where_clause = ""
    query_temp_table = query_temp_table.format(where_clause=where_clause)
    logging.debug(query_temp_table)

    cur.execute(query_temp_table, params)
    query_nodes = """
        SELECT authorid,
            get_unique_sorted_names(array_agg(initcap(name)), array_agg(lang_priority)),
            COUNT(DISTINCT itemid) AS total_publications,
            1 as category
        FROM filtered_authors
        GROUP BY authorid
        UNION
        SELECT authorid,
            get_unique_sorted_names(array_agg(initcap(name)), array_agg(lang_priority)),
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
        GROUP BY a1.authorid, a2.authorid
        HAVING COUNT(DISTINCT a1.itemid) >= %s;
    """
    cur.execute(query_edges, (min_publications,))
    edges = tuples_to_graph_links(cur.fetchall())

    return {
        "nodes": nodes,
        "links": edges,
        "categories": [{"name": "Связанные авторы"}, {"name": "Отфильтрованные авторы"}],
    }


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
