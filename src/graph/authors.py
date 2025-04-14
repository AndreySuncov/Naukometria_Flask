from dataclasses import dataclass, field
import logging
from dacite import from_dict
from flask import Blueprint, jsonify, request

from ..database.database import DatabaseService

authors_bp = Blueprint("authors", __name__, url_prefix="/authors")


@dataclass
class AuthorsFilters:
    authors: list[int] = field(default_factory=list)
    organizations: list[int] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    cities: list[str] = field(default_factory=list)


def get_filtered_authors(filters: AuthorsFilters, cur):
    query = """
        SELECT a.authorid,
            a.lastname,
            COUNT(DISTINCT art.itemid) as total_articles
        FROM authors a
                JOIN affiliations aff ON a.authorid = aff.author
                JOIN items art ON aff.affiliationid = art.itemid
                JOIN elibrary_organizations org ON org.organizationname = aff.name
                JOIN keywords k ON art.itemid = k.itemid
        {where_clause}
        GROUP BY a.authorid, a.lastname
    """
    where_clauses = []
    if filters.authors:
        where_clauses.append("a.authorid IN %s")
    if filters.organizations:
        where_clauses.append("org.organizationid IN %s")
    if filters.keywords:
        where_clauses.append("k.keyword IN %s")
    if filters.cities:
        where_clauses.append("aff.town IN %s")

    if where_clauses:
        where_clause = "WHERE " + " AND ".join(where_clauses)
    else:
        where_clause = ""
    query = query.format(where_clause=where_clause)
    logging.debug(query)

    cur.execute(
        query,
        *[
            tuple(filter_list)
            for filter_list in (filters.authors, filters.organizations, filters.keywords, filters.cities)
        ],
    )
    rows = cur.fetchall()
    authors = [
        {
            "authorid": row[0],
            "lastname": row[1],
            "total_articles": row[2],
        }
        for row in rows
    ]


@authors_bp.route("/data", methods=["POST"])
def get_authors_graph_data():
    try:
        filters: AuthorsFilters = from_dict(AuthorsFilters, request.get_json())
        logging.info(f"Received filters: {filters}")

        with DatabaseService() as cur:
            authors_query = """

            """

            min_common_works = 5
            query = """
                WITH author_pairs AS (
                    SELECT
                        affiliationid,
                        LEAST(a1.author, a2.author) AS author1,
                        GREATEST(a1.author, a2.author) AS author2
                    FROM
                        affiliations a1
                    JOIN
                        affiliations a2 USING(affiliationid)
                    WHERE
                        a1.author < a2.author
                )

                SELECT
                    author1,
                    author2,
                    COUNT(*) AS joint_works_count
                FROM
                    author_pairs
                GROUP BY
                    author1, author2
                HAVING
                    COUNT(*) > %d
                ORDER BY
                    joint_works_count DESC, author1, author2;
            """
            graph_data = {
                "nodes": [
                    {"id": "1", "name": "Author 1", "value": 10, "category": 0},
                    {"id": "2", "name": "Author 2", "value": 8, "category": 0},
                    {"id": "org1", "name": "Organization 1", "value": 15, "category": 1},
                ],
                "links": [
                    {"source": "1", "target": "org1", "weight": 5},
                    {"source": "2", "target": "org1", "weight": 3},
                ],
                "categories": [{"name": "Authors"}, {"name": "Organizations"}],
            }

            return jsonify(graph_data)

    except Exception as e:  # pylint: disable=broad-except
        return jsonify({"error": str(e)}), 500
