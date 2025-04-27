from flask import Blueprint, jsonify

from ..utils.database import fetch_paginated_filter_options


filters_bp = Blueprint("graph_filters", __name__, url_prefix="/filters")


@filters_bp.route("/authors", methods=["GET"])
def get_authors_filter():
    query = """
        WITH matched_authors AS (
            SELECT DISTINCT value
            FROM authors_names_with_priority_view
            {where_clauses}
        )
        SELECT value, name FROM (
            SELECT DISTINCT ON (auv.value)
                auv.value,
                auv.name
            FROM authors_names_with_priority_view auv
            JOIN matched_authors ma ON auv.value = ma.value
            ORDER BY auv.value, auv.lang_priority, auv.name_length DESC
        ) AS sub
        ORDER BY 
            (name ~ '^[а-яА-ЯёЁ]') DESC,  -- Сначала кириллица (TRUE идет раньше FALSE)
            name     -- Затем сортировка по алфавиту

    """

    data = fetch_paginated_filter_options(
        query=query,
        label_column="name",
        value_column="value",
        order_by_label=False,
    )
    return jsonify(data)


@filters_bp.route("/cited_authors", methods=["GET"])
def get_cited_authors():
    """
    Возвращает авторов, которые цитируются другими
    """
    query = """
        WITH matched_authors AS (
            SELECT DISTINCT value
            FROM authors_names_with_priority_view
            JOIN (
                SELECT DISTINCT author_id as authorid
                FROM author_citations_view
            ) citing ON authors_names_with_priority_view.value = citing.authorid
            {where_clauses}
        )
        SELECT value, name FROM (
            SELECT DISTINCT ON (auv.value)
                auv.value,
                auv.name
            FROM authors_names_with_priority_view auv
            JOIN matched_authors ma ON auv.value = ma.value
            ORDER BY auv.value, auv.lang_priority, auv.name_length DESC
        ) AS sub
        ORDER BY 
            (name ~ '^[а-яА-ЯёЁ]') DESC,  -- Сначала кириллица (TRUE идет раньше FALSE)
            name     -- Затем сортировка по алфавиту
    """

    data = fetch_paginated_filter_options(
        query=query,
        label_column="name",
        value_column="value",
        order_by_label=False,
    )
    return jsonify(data)


@filters_bp.route("/citing_authors", methods=["GET"])
def get_citing_authors():
    """
    Возвращает авторов, которые цитируют другие статьи
    """
    query = """
        WITH matched_authors AS (
            SELECT DISTINCT value
            FROM authors_names_with_priority_view
            JOIN (
                SELECT DISTINCT citing_author as authorid
                FROM author_citations_view
            ) citing ON authors_names_with_priority_view.value = citing.authorid
            {where_clauses}
        )
        SELECT value, name FROM (
            SELECT DISTINCT ON (auv.value)
                auv.value,
                auv.name
            FROM authors_names_with_priority_view auv
            JOIN matched_authors ma ON auv.value = ma.value
            ORDER BY auv.value, auv.lang_priority, auv.name_length DESC
        ) AS sub
        ORDER BY 
            (name ~ '^[а-яА-ЯёЁ]') DESC,  -- Сначала кириллица (TRUE идет раньше FALSE)
            name     -- Затем сортировка по алфавиту
    """

    data = fetch_paginated_filter_options(
        query=query,
        label_column="name",
        value_column="value",
        order_by_label=False,
    )
    return jsonify(data)


@filters_bp.route("/organizations", methods=["GET"])
def get_organizations_filter():
    query = """
        SELECT DISTINCT organizationid, organizationname
        FROM elibrary_organizations
        {where_clauses}
    """
    data = fetch_paginated_filter_options(query=query, label_column="organizationname", value_column="organizationid")
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
    data = fetch_paginated_filter_options(query=query, label_column="keyword", value_column="itemid")
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
    data = fetch_paginated_filter_options(query=query, label_column="town", value_column="town", order_by_label=False)
    return jsonify(data)
