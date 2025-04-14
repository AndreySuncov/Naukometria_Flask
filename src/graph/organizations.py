from dataclasses import dataclass, field
import logging

from dacite import from_dict
from flask import Blueprint, jsonify, request

from ..database.database import DatabaseService


organizations_bp = Blueprint("organizations", __name__, url_prefix="/organizations")


@dataclass
class OrganizationsFilters:
    keywords: list[str] = field(default_factory=list)


def get_filtered_organizations(filters: OrganizationsFilters, cur):
    raise NotImplementedError("get_filtered_organizations is not implemented yet")


@organizations_bp.route("/data", methods=["POST"])
def get_organizations_graph_data():
    try:
        filters: OrganizationsFilters = from_dict(OrganizationsFilters, request.get_json())
        logging.debug(f"Received filters: {filters}")
        with DatabaseService() as cur:
            # organizations = get_filtered_organizations(filters, cur)
            # nodes = []
            graph_data = {}
            return jsonify(graph_data)

    except Exception as e:  # pylint: disable=broad-except
        return jsonify({"error": str(e)}), 500
