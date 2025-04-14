from flask import Blueprint, jsonify

from ..utils.databse import fetch_paginated_options
from .authors import authors_bp

graph_bp = Blueprint("graph", __name__, url_prefix="/api/graph")

graph_bp.register_blueprint(authors_bp)


@graph_bp.route("/filters/authors", methods=["GET"])
def get_authors_filter():
    query = """
        SELECT authorid AS value, 
               lastname || ' ' || 
               (SELECT string_agg(LEFT(TRIM(word), 1) || '.', '')
               FROM unnest(string_to_array(regexp_replace(initials, '[.]', ' ', 'g'), ' ')) AS word
               WHERE TRIM(word) <> '') AS label
        FROM (
            SELECT DISTINCT ON (authorid) *
            FROM authors
            WHERE authorid IS NOT NULL
            ORDER BY authorid,
                    CASE WHEN language = 'RU' THEN 0 ELSE 1 END
        ) AS preferred_authors
    """
    data = fetch_paginated_options(query=query, label_column="lastname", value_column="authorid")
    return jsonify(data)


@graph_bp.route("/filters/organizations", methods=["GET"])
def get_organizations_filter():
    query = """
        SELECT 
            organizationid,
            organizationname 
        FROM elibrary_organizations 
    """
    data = fetch_paginated_options(query=query, label_column="organizationname", value_column="organizationid")
    return jsonify(data)


@graph_bp.route("/filters/keywords", methods=["GET"])
def get_keywords_filter():
    query = """
        SELECT DISTINCT 
            keyword AS label,
            keyword AS value
        FROM keywords
    """
    data = fetch_paginated_options(query=query, label_column="keyword", value_column="itemid")
    return jsonify(data)


@graph_bp.route("/filters/cities", methods=["GET"])
def get_cities_filter():
    query = """
        SELECT DISTINCT
            town AS label, 
            town as value 
        FROM affiliations
    """
    data = fetch_paginated_options(query=query, label_column="town", value_column="town")
    return jsonify(data)
