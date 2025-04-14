from dataclasses import dataclass, field
import logging

from dacite import from_dict
from flask import Blueprint, jsonify, request

from ..database.database import DatabaseService


references_bp = Blueprint("references", __name__, url_prefix="/references")


@dataclass
class ReferencesFilters:
    authors: list[str] = field(default_factory=list)


def get_filtered_references(filters: ReferencesFilters, cur):
    raise NotImplementedError("get_filtered_references is not implemented yet")


@references_bp.route("/data", methods=["POST"])
def get_references_graph_data():
    try:
        filters: ReferencesFilters = from_dict(ReferencesFilters, request.get_json())
        logging.debug(f"Received filters: {filters}")
        with DatabaseService() as cur:
            # references = get_filtered_references(filters, cur)
            # nodes = []
            graph_data = {}
            return jsonify(graph_data)

    except Exception as e:  # pylint: disable=broad-except
        return jsonify({"error": str(e)}), 500
