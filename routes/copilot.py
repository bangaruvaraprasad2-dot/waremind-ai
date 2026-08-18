from flask import Blueprint, render_template, jsonify, request
from database.models import Order, Inventory, Product, WarehouseException, PickTask, PackTask
from services.copilot_service import CopilotService

copilot_bp = Blueprint("copilot", __name__)


@copilot_bp.route("/copilot")
def copilot_page():
    return render_template("copilot.html", page="copilot")


@copilot_bp.route("/api/copilot", methods=["POST"])
def api_copilot():
    data = request.get_json()
    if not data or not data.get("message"):
        return jsonify({"error": "No message provided"}), 400

    message = data["message"].strip()
    service = CopilotService()
    response = service.process_query(message)
    return jsonify(response)
