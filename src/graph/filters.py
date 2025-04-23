from flask import Blueprint, jsonify

from ..utils.databse import fetch_paginated_options


filters_bp = Blueprint("graph_filters", __name__, url_prefix="/filters")


@filters_bp.route("/authors", methods=["GET"])
def get_authors_filter():
    query = """
        SELECT DISTINCT value, name
        FROM (
            SELECT DISTINCT ON (authorid)
                   authorid AS value,
                   INITCAP(COALESCE(lastname, '') || ' ' || COALESCE(initials, '')) AS name,
                   CASE
                       WHEN language = 'RU' THEN 0
                       WHEN language = 'EN' THEN 1
                       ELSE 2
                   END AS lang_priority,
                   LENGTH(COALESCE(lastname, '') || ' ' || COALESCE(initials, '')) AS name_length
            FROM authors
            ORDER BY authorid, lang_priority, name_length DESC  # Добавлено для корректного DISTINCT ON
        ) AS sub
        {where_clauses}
        ORDER BY lang_priority, name_length DESC
    """
    data = fetch_paginated_options(
        query=query,
        label_column="name",
        value_column="value",
        order_by_label=False  # Отключаем автоматический ORDER BY
    )
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
