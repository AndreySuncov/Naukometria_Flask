from flask import Blueprint, jsonify

from ..utils.databse import fetch_paginated_options


filters_bp = Blueprint("graph_filters", __name__, url_prefix="/filters")


@filters_bp.route("/authors", methods=["GET"])
def get_authors_filter():
    query = """
        SELECT authorid                             AS value,
            string_agg(name, ', ' ORDER BY name) AS name
        FROM (SELECT DISTINCT ON (authorid, INITCAP(lastname || ' ' || initials)) authorid,
                                                                                INITCAP(lastname || ' ' || initials)        AS name,
                                                                                CASE WHEN language = 'RU' THEN 0 ELSE 1 END AS lang_priority
            FROM authors) AS sub
        {where_clauses}
        GROUP BY authorid
    """
    data = fetch_paginated_options(query=query, label_column="name", value_column="authorid")
    return jsonify(data)


@filters_bp.route("/organizations", methods=["GET"])
def get_organizations_filter():
    query = """
        SELECT DISTINCT organizationid, organizationname
        FROM elibrary_organizations
        {where_clauses}
    """
    data = fetch_paginated_options(query=query, label_column="organizationname", value_column="organizationid")
    return jsonify(data)


@filters_bp.route("/keywords", methods=["GET"])
def get_keywords_filter():
    query = """
        SELECT DISTINCT 
            keyword AS label,
            keyword AS value
        FROM keywords
        {where_clauses}
    """
    data = fetch_paginated_options(query=query, label_column="keyword", value_column="itemid")
    return jsonify(data)


@filters_bp.route("/cities", methods=["GET"])
def get_cities_filter():
    query = """
        SELECT DISTINCT
            town AS label, 
            town as value,
            CASE WHEN language = 'RU' THEN 0 ELSE 1 END AS lang_priority
        FROM affiliations
        {where_clauses}
        ORDER BY lang_priority, town
    """
    data = fetch_paginated_options(query=query, label_column="town", value_column="town", order_by_label=False)
    return jsonify(data)
