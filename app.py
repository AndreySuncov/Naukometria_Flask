import json
import logging
from datetime import datetime
from typing import Optional

from flask import Flask, Response, abort, jsonify, request, url_for
from flask_cors import CORS

from src.database.database import get_db_connection
from src.graph import graph_bp

import pandas as pd
from io import BytesIO
from flask import send_file

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
            "typecode": "SELECT typecode FROM new_data.ref_typecode_mv",
            "genreid": "SELECT genreid FROM new_data.ref_genreid_mv",
            "language": "SELECT language FROM new_data.ref_language_mv",
            "status": "SELECT status FROM new_data.ref_status_mv",
            "countries": "SELECT country FROM new_data.ref_affiliation_countries_mv",
            "towns": "SELECT town FROM new_data.ref_towns_mv",
            "organization_countries": "SELECT countryid FROM new_data.ref_org_countries_mv",
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

# Для распределения по городам
CITY_MAPPING = {
    'moscow': 'Москва',
    'moskva': 'Москва',
    'saint petersburg': 'Санкт-Петербург',
    'saint-petersburg': 'Санкт-Петербург',
    'st petersburg': 'Санкт-Петербург',
    'st. petersburg': 'Санкт-Петербург',
    'spb': 'Санкт-Петербург',
    'krasnodar': 'Краснодар', 
    'novosibirsk': 'Новосибирск',
    'yekaterinburg': 'Екатеринбург',
    'ekaterinburg': 'Екатеринбург',
    'kazan': 'Казань',
    'nizhny novgorod': 'Нижний Новгород',
    'nizhniy novgorod': 'Нижний Новгород',
    'chelyabinsk': 'Челябинск',
    'samara': 'Самара',
    'omsk': 'Омск',
    'rostov-on-don': 'Ростов-на-Дону',
    'rostov on don': 'Ростов-на-Дону',
    'ufa': 'Уфа',
    'krasnoyarsk': 'Красноярск',
    'perm': 'Пермь',
    'voronezh': 'Воронеж',
    'volgograd': 'Волгоград',
    'vladimir': 'Владимир',
    'mytishi': 'Мытищи',
    'vladikavkaz': 'Владикавказ',
    'lipetsk': 'Липецк',
    'kursk': 'Курск',
    'yaroslavl': 'Ярославль',
    'smolensk': 'Смоленск',
    'tula': 'Тула',
    'kaluga': 'Калуга',
    'orel': 'Орел'
    
}

def normalize_city_name(city_name):
    if not city_name:
        return city_name
    
    lower_name = city_name.strip().lower()
    
    # Проверяем полные совпадения
    if lower_name in CITY_MAPPING:
        return CITY_MAPPING[lower_name]
    
    # Проверяем частичные совпадения
    for eng_name, ru_name in CITY_MAPPING.items():
        if eng_name in lower_name:
            return ru_name
    
    # Если не нашли соответствия, возвращаем оригинал с капитализацией
    return city_name.strip().title()

@app.route("/api/authors/by-city", methods=["GET"])
def get_authors_by_city():
    city = request.args.get("city")
    if not city:
        abort(400, description="Parameter 'city' is required")

    city = city.strip().lower()
    if not city:
        abort(400, description="City name cannot be empty")

    limit = validate_int(request.args.get("limit"), 1, 1000, "limit")
    if limit is None:
        limit = 10

    conn = cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT 
                INITCAP(lastname || ' ' || initials) AS name,
                publication_count
            FROM new_data.authors_by_city_full_mv
            WHERE normalized_city = %s
            ORDER BY publication_count DESC
            LIMIT %s
        """
        cur.execute(query, (city, limit))
        data = [
            {"name": row[0], "publications": row[1]}
            for row in cur.fetchall()
        ]
        return Response(json.dumps(data, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        app.logger.error(f"Error in /api/authors/by-city: {str(e)}")
        abort(500, description="Internal server error")
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
                SELECT normalized_city, authors_count
                FROM authors_by_city_mv
                WHERE authors_count >= %s
                ORDER BY authors_count DESC
                """
        cur.execute(query, (min_publications,))

        # Нормализуем названия городов и объединяем данные
        city_stats = {}
        for city, count in cur.fetchall():
            normalized_city = normalize_city_name(city)
            if normalized_city in city_stats:
                city_stats[normalized_city] += count
            else:
                city_stats[normalized_city] = count

        # Преобразуем в список и сортируем
        data = [[city, count] for city, count in city_stats.items()]
        data.sort(key=lambda x: x[1], reverse=True)

        return Response(json.dumps(data, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/map/city-publications", methods=["GET"])
def get_city_publications_map():
    keyword_filter = request.args.get("keyword")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Получаем itemid → keyword (если фильтр передан)
        filtered_itemids = set()
        if keyword_filter:
            cur.execute("""
                SELECT DISTINCT itemid
                FROM new_data.keywords
                WHERE keyword ILIKE %s
            """, (f"%{keyword_filter}%",))
            filtered_itemids = {row[0] for row in cur.fetchall()}
            if not filtered_itemids:
                return jsonify([])  # нет таких публикаций с этим ключевым словом

        # Получаем город → itemid
        cur.execute("""
            SELECT original_city, itemid
            FROM new_data.city_publications_mv
        """)
        city_to_items = {}
        for city, itemid in cur.fetchall():
            if not keyword_filter or itemid in filtered_itemids:
                city_to_items.setdefault(city, set()).add(itemid)

        # Нормализуем названия городов и считаем публикации
        city_stats = {}
        for raw_city, items in city_to_items.items():
            norm_city = normalize_city_name(raw_city)
            city_stats[norm_city] = city_stats.get(norm_city, 0) + len(items)

        # Получаем координаты
        cur.execute("""
            SELECT settlement AS city, 
                   "latitude(dd)" AS lat, 
                   "longitude(dd)" AS lon
            FROM coordinate_data
            WHERE "latitude(dd)" IS NOT NULL AND "longitude(dd)" IS NOT NULL
        """)
        coords = {row[0].strip(): (row[1], row[2]) for row in cur.fetchall()}

        # Сборка результата
        result = []
        for city_ru, count in city_stats.items():
            coord = coords.get(city_ru)
            if coord:
                result.append({
                    "city": city_ru,
                    "publications": count,
                    "lat": coord[0],
                    "lon": coord[1]
                })

        return Response(json.dumps(result, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()


@app.route("/api/map/city-organizations", methods=["GET"])
def get_city_organizations():
    city = request.args.get("city")
    if not city or not city.strip():
        abort(400, description="Parameter 'city' is required")

    keyword = request.args.get("keyword")
    limit = validate_int(request.args.get("limit"), 1, 1000, "limit")
    if limit is None:
        limit = 10

    city = city.strip().lower()

    conn = cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Если есть фильтр по ключевому слову — получаем itemid
        filtered_itemids = set()
        if keyword:
            cur.execute("""
                SELECT DISTINCT itemid
                FROM new_data.keywords
                WHERE keyword ILIKE %s
            """, (f"%{keyword}%",))
            filtered_itemids = {row[0] for row in cur.fetchall()}
            if not filtered_itemids:
                return jsonify([])

        # Основной запрос
        cur.execute("""
            SELECT organizationname, itemid
            FROM new_data.city_organization_items_mv
            WHERE normalized_city = %s
        """, (city,))

        org_to_items = {}
        for org, itemid in cur.fetchall():
            if not keyword or itemid in filtered_itemids:
                org_to_items.setdefault(org, set()).add(itemid)

        # Считаем и сортируем
        sorted_orgs = sorted(
            [{"organization": org, "publications": len(itemids)} for org, itemids in org_to_items.items()],
            key=lambda x: x["publications"],
            reverse=True
        )

        return Response(json.dumps(sorted_orgs[:limit], ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()


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
            SELECT year, publications_count
            FROM new_data.publications_by_year_mv
            WHERE year BETWEEN %s AND %s
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

        year = request.args.get("year")
        if year is not None:
            year = validate_int(year, 1900, 2100, "year")
        else:
            year = datetime.now().year

        limit = validate_int(request.args.get("limit"), 1, 1000000, "limit")

        keyword_filter = request.args.get("keyword")
        language_filter = request.args.get("language")

        query = """
            SELECT keyword, language, count
            FROM new_data.keyword_year_stats_mv
            WHERE year = %s ...
        """
        params = [year]

        if keyword_filter:
            query += " AND keyword ILIKE %s"
            params.append(f"%{keyword_filter}%")
        if language_filter:
            validate_enum(language_filter, {"ru", "en"}, "language")
            query += " AND language = %s"
            params.append(language_filter.upper())

        query += " GROUP BY keyword, language ORDER BY count DESC"

        if limit is not None:
            query += " LIMIT %s"
            params.append(limit)

        cur.execute(query, params)
        results = [
            {
                "keyword": row[0],
                "language": row[1],
                "count": row[2],
                "year": year
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
            SELECT keyword, articles_count
            FROM new_data.all_keywords_mv
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


@app.route('/api/statistics/vak-categories', methods=['GET'])
def get_vak_statistics_by_category():
    conn = cur = None
    try:
        author_id = request.args.get('authorid')
        date_from = request.args.get('date_from')  # формат YYYY-MM-DD
        date_to = request.args.get('date_to')      # формат YYYY-MM-DD
        issn = request.args.get('issn')            # фильтр по журналу

        # Валидации
        if author_id and not author_id.isdigit():
            abort(400, description="authorid must be an integer")
        if issn and not issn.replace('-', '').isalnum():
            abort(400, description="Invalid ISSN format")

        conn = get_db_connection()
        cur = conn.cursor()

        query = """
                SELECT scientificspecialties,
                       category,
                       COUNT(DISTINCT itemid) AS count
                FROM new_data.vak_statistics_mv
                WHERE 1=1
                """

        params = []

        if author_id:
            query += " AND authorid = %s"
            params.append(int(author_id))

        if date_from:
            query += " AND date_start >= %s"
            params.append(date_from)

        if date_to:
            query += " AND (date_end IS NULL OR date_end <= %s)"
            params.append(date_to)

        if issn:
            query += " AND issn = %s"
            params.append(issn)

        query += """
            GROUP BY scientificspecialties, category
            ORDER BY scientificspecialties, category
        """

        cur.execute(query, params)
        data = cur.fetchall()

        result = {}
        for specialty, category, count in data:
            if specialty not in result:
                result[specialty] = {"К1": 0, "К2": 0, "К3": 0}
            result[specialty][category] = count

        return Response(json.dumps(result, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route('/api/export/author-vak-excel', methods=['GET'])
def export_author_vak_excel():
    conn = cur = None
    try:
        author_id = request.args.get('authorid')
        if not author_id or not author_id.isdigit():
            abort(400, description="authorid is required and must be an integer")

        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT * FROM new_data.author_journal_vak
            WHERE authorid = %s
        """
        cur.execute(query, (int(author_id),))
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

        # Создаем DataFrame
        df = pd.DataFrame(rows, columns=columns)

        # Создаем Excel в памяти
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='AuthorData')

        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'author_{author_id}_vak.xlsx'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()


@app.route('/api/references/journals', methods=['GET'])
def get_journals_reference():
    conn = cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT issn, journal_name
            FROM new_data.journals_reference_mv
            ORDER BY journal_name
        """

        cur.execute(query)
        results = [{"issn": row[0], "name": row[1]} for row in cur.fetchall()]

        return Response(json.dumps(results, ensure_ascii=False), mimetype="application/json; charset=utf-8")

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
                organizationid AS organization,
                organizationname AS name,
                COUNT(DISTINCT itemid) AS count
            FROM organization_keyword_items_mv
            WHERE keyword ILIKE %s
            GROUP BY organizationid, organizationname
            HAVING COUNT(DISTINCT itemid) >= %s
            ORDER BY count DESC
            LIMIT %s
        """
        cur.execute(query, (f"%{keyword}%", min_count, limit))
        results = [
            {"organization": row[0], "name": row[1], "count": row[2]}
            for row in cur.fetchall()
        ]

        return Response(json.dumps(results, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()


@app.route('/api/statistics/rating/organizations', methods=['GET'])
def get_popular_organizations():
    """Получение списка организаций с ID"""
    conn = cur = None
    try:
        min_publications = validate_int(request.args.get("min_publications"), 1, 10**6, "min_publications") or 200

        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT id, organization AS name, publications_count
            FROM popular_organizations_mv
            WHERE publications_count >= %s
            ORDER BY name
        """
        cur.execute(query, (min_publications,))
        results = [{"id": row[0], "name": row[1], "count": row[2]} for row in cur.fetchall()]

        return Response(json.dumps(results, ensure_ascii=False), mimetype="application/json; charset=utf-8")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()


@app.route('/api/statistics/rating/keywords', methods=['GET'])
def get_popular_keywords():
    """Получение списка ключевых слов из materialized view"""
    conn = cur = None
    try:
        min_publications = validate_int(request.args.get("min_publications"), 1, 10**6, "min_publications")
        if min_publications is None:
            min_publications = 100

        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT keyword
            FROM popular_keywords_mv
            WHERE publications_count >= %s
            ORDER BY keyword
        """
        cur.execute(query, (min_publications,))
        results = [row[0] for row in cur.fetchall()]

        return Response(json.dumps(results, ensure_ascii=False), mimetype="application/json; charset=utf-8")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()


@app.route('/api/statistics/rating/keywords-by-organization', methods=['GET'])
def get_top_keywords_by_organization():
    """Топ ключевых слов по ID организации"""
    conn = cur = None
    try:
        org_id = request.args.get('organizationid')
        if not org_id or not org_id.isdigit():
            abort(400, description="Parameter 'organizationid' is required and must be integer")

        min_count = validate_int(request.args.get("min_count"), 1, 10**6, "min_count") or 10
        limit = validate_int(request.args.get("limit"), 1, 100, "limit") or 10

        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT keyword, COUNT(DISTINCT itemid) AS count
            FROM organization_keyword_items_mv
            WHERE organizationid = %s
            GROUP BY keyword
            HAVING COUNT(DISTINCT itemid) >= %s
            ORDER BY count DESC
            LIMIT %s;
        """
        cur.execute(query, (int(org_id), min_count, limit))
        results = [{"keyword": row[0], "count": row[1]} for row in cur.fetchall()]

        return Response(json.dumps(results, ensure_ascii=False), mimetype="application/json; charset=utf-8")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()


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
    return "API для ВКР 'Наукометрическая система', Андрей Сунцов, Преснухин Дмитрий, Мерзлова Анастасия, Егорова Ева"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
    # conn = get_db_connection()
    # cur = conn.cursor()
