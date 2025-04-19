from dataclasses import dataclass, field
import logging

from dacite import from_dict
from flask import Blueprint, abort, jsonify, request

from ..entities.datacls import GraphFilter

from ..database.database import DatabaseService


references_bp = Blueprint("references", __name__, url_prefix="/references")


@dataclass
class ReferencesFilters(GraphFilter):
    authors: list[str] = field(default_factory=list)


def get_filtered_references(filters: ReferencesFilters, cur):
    """
    Пока невозможно получить данные о цитированиях авторов
    """
    logging.critical("Получение данных о цитированиях авторов невозможно с текущеми данными")
    raise NotImplementedError("get_filtered_references is not implemented yet")
    return {
        "nodes": [],
        "links": [],
        "categories": [],
    }


@references_bp.route("/data", methods=["POST"])
def get_references_graph_data():
    try:
        filters: ReferencesFilters = from_dict(ReferencesFilters, request.get_json())
        if not filters.has_at_least_one_filter():
            abort(400, "At least one filter is required")

        logging.debug(f"Received filters: {filters}")
        with DatabaseService("new_data") as cur:
            graph_data = get_filtered_references(filters, cur)
            return jsonify(graph_data)

    except Exception as e:  # pylint: disable=broad-except
        logging.exception(e)
        return jsonify({"error": str(e)}), 500
