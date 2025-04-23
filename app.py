import json
import logging
from datetime import datetime
from typing import Optional

from flask import Flask, Response, abort, jsonify, request, url_for
from flask_cors import CORS

from src.database.database import get_db_connection
from src.graph import graph_bp

RESET = "\033[0m"
COLORS = {
    logging.DEBUG: "\033[90m",  # Grey
    logging.INFO: "\033[97m",  # White
    logging.WARNING: "\033[33m",  # Yellow
    logging.ERROR: "\033[31m",  # Red
    logging.CRITICAL: "\033[1;31m",  # Bold Red
}


class ColorFormatter(logging.Formatter):
    def format(self, record):
        color = COLORS.get(record.levelno, "")
        msg = super().format(record)
        return f"{color}{msg}{RESET}"


handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter("%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"))
logging.basicConfig(level=logging.DEBUG, handlers=[handler])


app = Flask(__name__)

# ------------ DEV ONLY ------------
CORS(app, resources={r"/*": {"origins": "*"}}, methods=["GET", "POST", "PUT", "DELETE"])
# ----------------------------------


class CustomJSONEncoder(json.JSONEncoder):
    def __init__(self, **kwargs):
        kwargs["ensure_ascii"] = False
        super().__init__(**kwargs)


app.json_encoder = CustomJSONEncoder


def validate_int(value: Optional[str], min_val: int, max_val: int, param_name: str) -> Optional[int]:
    try:
        if value is None:
            return None
        num = int(value)
        if not (min_val <= num <= max_val):
            abort(400, description=f"{param_name} must be between {min_val}-{max_val}")
        return num
    except ValueError:
        abort(400, description=f"Invalid {param_name} value")


def validate_enum(value: Optional[str], allowed_values: set, param_name: str):
    if value and value.lower() not in {v.lower() for v in allowed_values}:
        abort(400, description=f"Invalid {param_name}. Allowed values: {', '.join(allowed_values)}")


@app.route("/api/references/<ref_type>", methods=["GET"])
def get_references(ref_type):
    allowed_refs = {"typecode", "genreid", "language", "status", "countries", "towns", "organization_countries"}

    if ref_type not in allowed_refs:
        abort(404, description="Reference type not found")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query_map = {
            "typecode": "SELECT DISTINCT typecode FROM items WHERE typecode IS NOT NULL",
            "genreid": "SELECT DISTINCT genreid FROM items WHERE genreid IS NOT NULL",
            "language": "SELECT DISTINCT language FROM authors UNION SELECT DISTINCT language FROM items",
            "status": "SELECT DISTINCT status FROM authors WHERE status IS NOT NULL",
            "countries": "SELECT DISTINCT country FROM affiliations WHERE country IS NOT NULL",
            "towns": "SELECT DISTINCT town FROM affiliations WHERE town IS NOT NULL",
            "organization_countries": "SELECT DISTINCT countryid FROM elibrary_organizations",
        }

        cur.execute(query_map[ref_type])
        results = [row[0] for row in cur.fetchall()]
        result = {ref_type: sorted(filter(None, results))}

        return Response(json.dumps(result, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if "cur" in locals():
            cur.close()
        if "conn" in locals():
            conn.close()


@app.route("/api/authors", methods=["GET"])
def get_authors():
    conn = cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        limit = validate_int(request.args.get("limit"), 1, 10**6, "limit")
        offset = validate_int(request.args.get("offset"), 0, 10**6, "offset")
        status = request.args.get("status")

        cur.execute("SELECT DISTINCT status FROM authors WHERE status IS NOT NULL")
        allowed_statuses = {str(row[0]) for row in cur.fetchall()}
        validate_enum(status, allowed_statuses, "status")

        filters = {
            "authorid": request.args.get("authorid"),
            "lastname": request.args.get("lastname"),
            "itemid": request.args.get("itemid"),
            "email": request.args.get("email"),
            "status": status,
            "language": request.args.get("language"),
        }

        base_query = """
            SELECT authorid, itemid, num, language, status, 
                   lastname, initials, email
            FROM authors
            WHERE 1=1
        """
        params = []

        for field, value in filters.items():
            if not value:
                continue

            if field in ["authorid", "itemid", "num"]:
                if not value.isdigit():
                    abort(400, description=f"{field} must be integer")
                base_query += f" AND {field} = %s"
                params.append(int(value))
            elif field == "language":
                validate_enum(value, {"ru", "en"}, "language")
                base_query += " AND language = %s"
                params.append(value.upper())
            elif field == "status":
                base_query += f" AND {field} = %s"
                params.append(int(value))
            else:
                base_query += f" AND {field} ILIKE %s"
                params.append(f"%{value}%")

        if limit is not None or offset is not None:
            base_query += " LIMIT %s OFFSET %s"
            params.extend([limit if limit is not None else "ALL", offset if offset is not None else 0])

        cur.execute(base_query, params)
        columns = [desc[0] for desc in cur.description]
        authors = [dict(zip(columns, row)) for row in cur.fetchall()]

        return Response(json.dumps(authors, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/items", methods=["GET"])
def get_items():
    conn = cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        limit = validate_int(request.args.get("limit"), 1, 10**6, "limit")
        offset = validate_int(request.args.get("offset"), 0, 10**6, "offset")

        year_from = request.args.get("year_from")
        year_to = request.args.get("year_to")

        if year_from:
            year_from = validate_int(year_from, 1900, 2100, "year_from")
        if year_to:
            year_to = validate_int(year_to, 1900, 2100, "year_to")

        filters = {
            "itemid": request.args.get("itemid"),
            "title": request.args.get("title"),
            "year_from": year_from,
            "year_to": year_to,
            "keyword": request.args.get("keyword"),
            "genreid": request.args.get("genreid"),
            "typecode": request.args.get("typecode"),
            "isbn": request.args.get("isbn"),
            "placeofpublication": request.args.get("placeofpublication"),
            "language": request.args.get("language"),
        }

        query = """
            SELECT DISTINCT 
                i.itemid, i.title, i.year, i.language, i.genreid, 
                i.typecode, i.isbn, i.placeofpublication, i.pages, i.volume
            FROM items i
            LEFT JOIN keywords k ON i.itemid = k.itemid
            WHERE 1=1
        """
        params = []

        if filters["itemid"]:
            if not filters["itemid"].isdigit():
                abort(400, description="itemid must be integer")
            query += " AND i.itemid = %s"
            params.append(int(filters["itemid"]))

        if filters["title"]:
            query += " AND i.title ILIKE %s"
            params.append(f"%{filters['title']}%")

        if filters["year_from"] is not None:
            query += " AND i.year >= %s"
            params.append(filters["year_from"])

        if filters["year_to"] is not None:
            query += " AND i.year <= %s"
            params.append(filters["year_to"])

        if filters["keyword"]:
            query += " AND k.keyword ILIKE %s"
            params.append(f"%{filters['keyword']}%")

        if filters["genreid"]:
            query += " AND i.genreid = %s"
            params.append(filters["genreid"])

        if filters["typecode"]:
            query += " AND i.typecode = %s"
            params.append(filters["typecode"])

        if filters["isbn"]:
            query += " AND i.isbn ILIKE %s"
            params.append(f"%{filters['isbn']}%")

        if filters["placeofpublication"]:
            query += " AND i.placeofpublication ILIKE %s"
            params.append(f"%{filters['placeofpublication']}%")

        if filters["language"]:
            validate_enum(filters["language"], {"ru", "en"}, "language")
            query += " AND i.language = %s"
            params.append(filters["language"].upper())

        if limit is not None or offset is not None:
            query += " LIMIT %s OFFSET %s"
            params.extend([limit if limit is not None else "ALL", offset if offset is not None else 0])

        cur.execute(query, params)
        columns = [desc[0] for desc in cur.description]
        items = [dict(zip(columns, row)) for row in cur.fetchall()]

        return Response(json.dumps(items, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/affiliations", methods=["GET"])
def get_affiliations():
    conn = cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        limit = validate_int(request.args.get("limit"), 1, 10**6, "limit")
        offset = validate_int(request.args.get("offset"), 0, 10**6, "offset")

        filters = {
            "author": request.args.get("author"),
            "num": request.args.get("num"),
            "language": request.args.get("language"),
            "affiliationid": request.args.get("affiliationid"),
            "name": request.args.get("name"),
            "country": request.args.get("country"),
            "town": request.args.get("town"),
            "address": request.args.get("address"),
        }

        query = "SELECT * FROM affiliations WHERE 1=1"
        params = []

        for field in ["author", "num", "affiliationid"]:
            if filters[field]:
                if not filters[field].isdigit():
                    abort(400, description=f"{field} must be integer")
                query += f" AND {field} = %s"
                params.append(int(filters[field]))

        for field in ["name", "country", "town", "address"]:
            if filters[field]:
                query += f" AND {field} ILIKE %s"
                params.append(f"%{filters[field]}%")

        if filters["language"]:
            query += " AND language = %s"
            params.append(filters["language"].upper())

        if limit is not None or offset is not None:
            query += " LIMIT %s OFFSET %s"
            params.extend([limit if limit is not None else "ALL", offset if offset is not None else 0])

        cur.execute(query, params)
        columns = [desc[0] for desc in cur.description]
        result = [dict(zip(columns, row)) for row in cur.fetchall()]

        return Response(json.dumps(result, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/organizations", methods=["GET"])
def get_organizations():
    conn = cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        limit = validate_int(request.args.get("limit"), 1, 10**6, "limit")
        offset = validate_int(request.args.get("offset"), 0, 10**6, "offset")

        filters = {
            "countryid": request.args.get("countryid"),
            "organizationid": request.args.get("organizationid"),
            "organizationname": request.args.get("organizationname"),
        }

        query = "SELECT * FROM elibrary_organizations WHERE 1=1"
        params = []

        if filters["organizationid"]:
            if not filters["organizationid"].isdigit():
                abort(400, description="organizationid must be integer")
            query += " AND organizationid = %s"
            params.append(int(filters["organizationid"]))

        if filters["countryid"]:
            query += " AND countryid = %s"
            params.append(filters["countryid"].upper())

        if filters["organizationname"]:
            query += " AND organizationname ILIKE %s"
            params.append(f"%{filters['organizationname']}%")

        if limit is not None or offset is not None:
            query += " LIMIT %s OFFSET %s"
            params.extend([limit if limit is not None else "ALL", offset if offset is not None else 0])

        cur.execute(query, params)
        columns = [desc[0] for desc in cur.description]
        result = [dict(zip(columns, row)) for row in cur.fetchall()]

        return Response(json.dumps(result, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/authors/by-city", methods=["GET"])
def get_authors_by_city():
    # Валидация параметра ДО подключения к БД
    city = request.args.get("city")
    if not city:
        abort(400, description="Parameter 'city' is required")

    city = city.strip()
    if not city:
        abort(400, description="City name cannot be empty")

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT 
                a.lastname, 
                a.initials 
            FROM authors a
            JOIN affiliations af ON a.authorid = af.author
            WHERE af.town ILIKE %s
        """
        cur.execute(query, (f"%{city}%",))

        unique_names = set()
        for lastname, initials in cur.fetchall():
            normalized_lastname = lastname.strip().lower() if lastname else ""
            normalized_initials = initials.strip().lower() if initials else ""

            if normalized_initials:
                normalized_initials = normalized_initials.replace(".", "").replace("-", "")

            name_key = f"{normalized_lastname} {normalized_initials}".strip()

            if name_key:
                unique_names.add(name_key.title())

        sorted_authors = sorted(unique_names)

        return Response(json.dumps(sorted_authors, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        app.logger.error(f"Error in /api/authors/by-city: {str(e)}")
        abort(500, description="Internal server error")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/statistics/publications-by-year", methods=["GET"])
def get_publications_by_year():
    conn = cur = None
    try:
        current_year = datetime.now().year
        year_from = validate_int(request.args.get("year_from"), 1900, current_year, "year_from")
        year_to = validate_int(request.args.get("year_to"), 1900, current_year, "year_to")

        if year_from is None:
            year_from = 2000
        if year_to is None:
            year_to = current_year
        if year_from > year_to:
            abort(400, description="year_from cannot be greater than year_to")

        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT year, COUNT(*) as publications_count 
            FROM items 
            WHERE year BETWEEN %s AND %s
            GROUP BY year 
            ORDER BY year
        """
        cur.execute(query, (year_from, year_to))
        result = cur.fetchall()

        data = {row[0]: row[1] for row in result}

        return Response(json.dumps(data, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/statistics/keywords", methods=["GET"])
def get_keywords_statistics():
    conn = cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Если год не указан — берем текущий
        year = request.args.get("year")
        if year is not None:
            year = validate_int(year, 1900, 2100, "year")
        else:
            year = datetime.now().year

        keyword_filter = request.args.get("keyword")
        language_filter = request.args.get("language")

        query = """
            SELECT keyword, language, COUNT(*) AS count
            FROM keyword_year_view
            WHERE year = %s
        """
        params = [year]

        if keyword_filter:
            query += " AND keyword ILIKE %s"
            params.append(f"%{keyword_filter}%")
        if language_filter:
            validate_enum(language_filter, {"ru", "en"}, "language")
            query += " AND language = %s"
            params.append(language_filter.upper())

        query += " GROUP BY keyword, language ORDER BY count DESC LIMIT 150"

        cur.execute(query, params)
        results = [
            {
                "keyword": row[0],
                "language": row[1],
                "count": row[2],
                "year": year  # добавляем год в каждый объект
            }
            for row in cur.fetchall()
        ]

        return Response(json.dumps(results, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/keywords/all", methods=["GET"])
def get_all_keywords():
    conn = cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT 
                keyword, 
                COUNT(DISTINCT itemid) AS articles_count 
            FROM keywords 
            WHERE keyword IS NOT NULL 
            GROUP BY keyword 
            ORDER BY keyword
        """
        cur.execute(query)
        results = [[row[0], row[1]] for row in cur.fetchall()]

        return Response(json.dumps(results, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/statistics/authors-by-city", methods=["GET"])
def get_author_distribution_by_city():
    conn = cur = None
    try:
        min_publications = validate_int(request.args.get("min_publications"), 1, 10**6, "min_publications")
        if min_publications is None:
            min_publications = 10

        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT 
                a.town AS city,
                COUNT(DISTINCT au.itemid) AS publications_count
            FROM affiliations a
            JOIN authors au ON a.author = au.authorid
            WHERE a.town IS NOT NULL
            GROUP BY a.town
            HAVING COUNT(DISTINCT au.itemid) >= %s
            ORDER BY publications_count DESC
        """
        cur.execute(query, (min_publications,))
        results = cur.fetchall()

        data = [[row[0], row[1]] for row in results]

        return Response(json.dumps(data, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/keywords", methods=["GET"])
def get_keywords():
    conn = cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        limit = validate_int(request.args.get("limit"), 1, 10**6, "limit")
        offset = validate_int(request.args.get("offset"), 0, 10**6, "offset")

        filters = {
            "itemid": request.args.get("itemid"),
            "language": request.args.get("language"),
            "keyword": request.args.get("keyword"),
        }

        query = "SELECT * FROM keywords WHERE 1=1"
        params = []

        if filters["itemid"]:
            if not filters["itemid"].isdigit():
                abort(400, description="itemid must be integer")
            query += " AND itemid = %s"
            params.append(int(filters["itemid"]))

        if filters["language"]:
            query += " AND language = %s"
            params.append(filters["language"].upper())

        if filters["keyword"]:
            query += " AND keyword ILIKE %s"
            params.append(f"%{filters['keyword']}%")

        if limit is not None or offset is not None:
            query += " LIMIT %s OFFSET %s"
            params.extend([limit if limit is not None else "ALL", offset if offset is not None else 0])

        cur.execute(query, params)
        columns = [desc[0] for desc in cur.description]
        result = [dict(zip(columns, row)) for row in cur.fetchall()]

        return Response(json.dumps(result, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/statistics/rating/organizations', methods=['GET'])
def get_popular_organizations():
    """Получение списка организаций для выпадающего списка с фильтром по минимальному количеству публикаций"""
    conn = cur = None
    try:
        min_publications = validate_int(request.args.get("min_publications"), 1, 10**6, "min_publications")
        if min_publications is None:
            min_publications = 200

        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT DISTINCT e.organizationname
            FROM elibrary_organizations e
            JOIN affiliations af ON e.organizationid = af.affiliationid
            JOIN authors a ON af.author = a.authorid
            GROUP BY e.organizationname
            HAVING COUNT(DISTINCT a.itemid) >= %s
            ORDER BY e.organizationname
        """
        cur.execute(query, (min_publications,))
        results = [row[0] for row in cur.fetchall()]

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()

@app.route('/api/statistics/rating/keywords', methods=['GET'])
def get_popular_keywords():
    """Получение списка ключевых слов для выпадающего списка с фильтром по минимальному количеству публикаций"""
    conn = cur = None
    try:
        min_publications = validate_int(request.args.get("min_publications"), 1, 10**6, "min_publications")
        if min_publications is None:
            min_publications = 100  

        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT keyword
            FROM keywords
            WHERE keyword IS NOT NULL
            GROUP BY keyword
            HAVING COUNT(DISTINCT itemid) >= %s
            ORDER BY keyword
        """
        cur.execute(query, (min_publications,))
        results = [row[0] for row in cur.fetchall()]

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()

@app.route('/api/statistics/rating/organizations-by-keyword', methods=['GET'])
def get_top_organizations_by_keyword():
    """Топ организаций по ключевому слову"""
    conn = cur = None
    try:
        keyword = request.args.get('keyword')
        if not keyword:
            abort(400, description="Parameter 'keyword' is required")

        min_count = validate_int(request.args.get("min_count"), 1, 10**6, "min_count") or 10
        limit = validate_int(request.args.get("limit"), 1, 100, "limit") or 10

        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT 
                e.organizationname AS organization,
                COUNT(DISTINCT k.itemid) AS count
            FROM keywords k
            JOIN authors a ON k.itemid = a.itemid
            JOIN affiliations af ON a.authorid = af.author
            JOIN elibrary_organizations e ON af.affiliationid = e.organizationid
            WHERE k.keyword ILIKE %s
            GROUP BY e.organizationname
            HAVING COUNT(DISTINCT k.itemid) >= %s
            ORDER BY count DESC
            LIMIT %s
        """
        cur.execute(query, (f"%{keyword}%", min_count, limit))
        results = [[row[0], row[1]] for row in cur.fetchall()]

        return jsonify(results)  # Возвращаем массив напрямую

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()
        
@app.route('/api/statistics/rating/keywords-by-organization', methods=['GET'])
def get_top_keywords_by_organization():
    """Топ ключевых слов по организации"""
    conn = cur = None
    try:
        organization = request.args.get('organization')
        if not organization:
            abort(400, description="Parameter 'organization' is required")

        min_count = validate_int(request.args.get("min_count"), 1, 10**6, "min_count") or 10
        limit = validate_int(request.args.get("limit"), 1, 100, "limit") or 10

        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT 
                k.keyword,
                COUNT(DISTINCT a.itemid) AS count
            FROM elibrary_organizations e
            JOIN affiliations af ON e.organizationid = af.affiliationid
            JOIN authors a ON af.author = a.authorid
            JOIN keywords k ON a.itemid = k.itemid
            WHERE e.organizationname ILIKE %s
            GROUP BY k.keyword
            HAVING COUNT(DISTINCT a.itemid) >= %s
            ORDER BY count DESC
            LIMIT %s
        """
        cur.execute(query, (f"%{organization}%", min_count, limit))
        results = [[row[0], row[1]] for row in cur.fetchall()]

        return jsonify(results)  # Возвращаем массив напрямую

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()

app.register_blueprint(graph_bp)


def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()

    return len(defaults) >= len(arguments)


@app.route("/site-map")
def site_map_route():
    routes = []

    for rule in app.url_map.iter_rules():
        if "GET" in rule.methods and has_no_empty_params(rule):  # type: ignore
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            routes.append((url, rule.endpoint))

    return routes


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.route("/")
def home():
    return "Электронная библиотека API v2.6 Андрей Сунцов"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
    # conn = get_db_connection()
    # cur = conn.cursor()
