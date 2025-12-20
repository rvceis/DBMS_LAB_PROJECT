from flask import Blueprint, jsonify

uploads_bp = Blueprint("uploads", __name__)


@uploads_bp.route("/", methods=["POST"])
def upload_disabled():
    return jsonify({"error": "uploads disabled", "details": "This deployment does not accept file uploads."}), 403

