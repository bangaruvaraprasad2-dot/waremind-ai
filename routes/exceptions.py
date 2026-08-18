from flask import Blueprint, render_template, jsonify, request
from datetime import datetime
from database import db
from database.models import WarehouseException, Order, Inventory, InventoryMovement, OrderItem
from services.exception_engine import ExceptionEngine

exceptions_bp = Blueprint("exceptions", __name__)


@exceptions_bp.route("/exceptions")
def exceptions_page():
    return render_template("exceptions.html", page="exceptions")


@exceptions_bp.route("/api/exceptions")
def api_exceptions():
    status = request.args.get("status", "")
    severity = request.args.get("severity", "")
    exc_type = request.args.get("type", "")

    query = WarehouseException.query
    if status:
        query = query.filter_by(status=status)
    if severity:
        query = query.filter_by(severity=severity)
    if exc_type:
        query = query.filter_by(exception_type=exc_type)

    exceptions = query.order_by(
        db.case(
            {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3},
            value=WarehouseException.severity,
        ),
        WarehouseException.created_at.desc(),
    ).all()

    # Summary counts
    open_count = WarehouseException.query.filter_by(status="OPEN").count()
    in_progress = WarehouseException.query.filter_by(status="IN_PROGRESS").count()
    critical_count = WarehouseException.query.filter(
        WarehouseException.severity == "CRITICAL",
        WarehouseException.status.in_(["OPEN", "IN_PROGRESS"])
    ).count()
    high_count = WarehouseException.query.filter(
        WarehouseException.severity == "HIGH",
        WarehouseException.status.in_(["OPEN", "IN_PROGRESS"])
    ).count()
    medium_count = WarehouseException.query.filter(
        WarehouseException.severity == "MEDIUM",
        WarehouseException.status.in_(["OPEN", "IN_PROGRESS"])
    ).count()

    from datetime import timedelta
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    resolved_today = WarehouseException.query.filter(
        WarehouseException.status == "RESOLVED",
        WarehouseException.resolved_at >= today_start
    ).count()

    return jsonify({
        "exceptions": [e.to_dict() for e in exceptions],
        "summary": {
            "open": open_count,
            "in_progress": in_progress,
            "critical": critical_count,
            "high": high_count,
            "medium": medium_count,
            "resolved_today": resolved_today,
        }
    })


@exceptions_bp.route("/api/exceptions/<int:exc_id>/apply-recommendation", methods=["POST"])
def apply_recommendation(exc_id):
    exc = WarehouseException.query.get_or_404(exc_id)

    if exc.status == "RESOLVED":
        return jsonify({"error": "Exception is already resolved"}), 400

    engine = ExceptionEngine()
    result = engine.apply_recommendation(exc)
    db.session.commit()
    return jsonify(result)


@exceptions_bp.route("/api/exceptions/<int:exc_id>/resolve", methods=["POST"])
def resolve_manually(exc_id):
    exc = WarehouseException.query.get_or_404(exc_id)
    data = request.get_json() or {}
    resolution = data.get("resolution", "Resolved manually by warehouse manager.")

    exc.status = "RESOLVED"
    exc.resolution = resolution
    exc.resolved_at = datetime.utcnow()

    if exc.order_id:
        order = Order.query.get(exc.order_id)
        if order and order.status == "EXCEPTION":
            order.status = "ALLOCATED"

    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Exception resolved manually.",
        "exception_id": exc_id,
    })


@exceptions_bp.route("/api/exceptions/scan", methods=["POST"])
def scan_exceptions():
    """Run the exception engine to detect new exceptions."""
    engine = ExceptionEngine()
    new_exceptions = engine.run_full_scan()
    db.session.commit()
    return jsonify({
        "success": True,
        "new_exceptions": len(new_exceptions),
        "exceptions": [e.to_dict() for e in new_exceptions],
    })
