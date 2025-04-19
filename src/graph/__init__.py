from flask import Blueprint
from .authors import authors_bp
from .references import references_bp
from .organizations import organizations_bp
from .filters import filters_bp

graph_bp = Blueprint("graph", __name__, url_prefix="/api/graph")

graph_bp.register_blueprint(authors_bp)
graph_bp.register_blueprint(references_bp)
graph_bp.register_blueprint(organizations_bp)
graph_bp.register_blueprint(filters_bp)
