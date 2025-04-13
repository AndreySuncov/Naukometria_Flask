from flask import Blueprint
from .authors import authors_bp

graph_bp = Blueprint("graph", __name__, url_prefix="/api/graph")

graph_bp.register_blueprint(authors_bp)
