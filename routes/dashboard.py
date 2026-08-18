import random
from flask import Blueprint, render_template, jsonify
from datetime import datetime, timedelta
from database import db
from database.models import (
    Order, Inventory, Product, WarehouseException,
    InventoryMovement, Dispatch, PickTask, PackTask
)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def landing_page():
    return render_template("landing.html", page="landing")


@dashboard_bp.route("/dashboard")
def index():
    return render_template("dashboard.html", page="dashboard")


@dashboard_bp.route("/api/dashboard")
def api_dashboard():
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # ── KPI Metrics ────────────────────────────────────────────────────────────
    total_orders = Order.query.count()
    pending_orders = Order.query.filter(
        Order.status.in_(["CREATED", "PRIORITIZED", "ALLOCATED", "PICKING", "PACKING", "QUALITY_CHECK"])
    ).count()
    critical_orders = Order.query.filter_by(priority="CRITICAL").filter(
        Order.status.notin_(["DISPATCHED", "COMPLETED"])
    ).count()

    total_inventory_units = db.session.query(
        db.func.sum(Inventory.quantity)
    ).scalar() or 0

    # Low stock: available < reorder_level
    low_stock_products = (
        db.session.query(Product)
        .join(Inventory, Inventory.product_id == Product.id)
        .filter(
            (Inventory.quantity - Inventory.reserved_quantity - Inventory.damaged_quantity)
            < Product.reorder_level
        )
        .filter(
            (Inventory.quantity - Inventory.reserved_quantity - Inventory.damaged_quantity)
            > 0
        )
        .distinct()
        .count()
    )

    out_of_stock = (
        db.session.query(Product)
        .join(Inventory, Inventory.product_id == Product.id)
        .filter(
            (Inventory.quantity - Inventory.reserved_quantity - Inventory.damaged_quantity)
            <= 0
        )
        .distinct()
        .count()
    )

    open_exceptions = WarehouseException.query.filter(
        WarehouseException.status.in_(["OPEN", "IN_PROGRESS"])
    ).count()

    critical_exceptions = WarehouseException.query.filter_by(
        severity="CRITICAL", status="OPEN"
    ).count()

    ready_to_dispatch = Order.query.filter_by(status="READY_TO_DISPATCH").count()

    dispatched_today = Order.query.filter_by(status="DISPATCHED").filter(
        Order.updated_at >= today_start
    ).count()
    completed_today = Order.query.filter_by(status="COMPLETED").filter(
        Order.updated_at >= today_start
    ).count()
    fulfillment_rate = round(
        ((dispatched_today + completed_today) / max(total_orders, 1)) * 100, 1
    )

    # ── Charts Data ────────────────────────────────────────────────────────────
    # Orders by status
    statuses = ["CREATED", "PRIORITIZED", "ALLOCATED", "PICKING",
                "PACKING", "QUALITY_CHECK", "READY_TO_DISPATCH", "DISPATCHED", "COMPLETED", "EXCEPTION"]
    orders_by_status = {}
    for s in statuses:
        orders_by_status[s] = Order.query.filter_by(status=s).count()

    # Orders by priority
    priorities = ["CRITICAL", "HIGH", "NORMAL", "LOW"]
    orders_by_priority = {}
    for p in priorities:
        orders_by_priority[p] = Order.query.filter_by(priority=p).count()

    # Exceptions by type
    exc_types = ["LOW_STOCK", "OUT_OF_STOCK", "DAMAGED_ITEM", "MISSING_ITEM",
                 "PICKING_DELAY", "PACKING_DELAY", "QUALITY_FAILURE", "ALLOCATION_CONFLICT"]
    exceptions_by_type = {}
    for t in exc_types:
        exceptions_by_type[t] = WarehouseException.query.filter_by(exception_type=t).count()

    # Inventory health breakdown
    total_inv = db.session.query(db.func.sum(Inventory.quantity)).scalar() or 0
    damaged_inv = db.session.query(db.func.sum(Inventory.damaged_quantity)).scalar() or 0
    reserved_inv = db.session.query(db.func.sum(Inventory.reserved_quantity)).scalar() or 0
    available_inv = max(0, total_inv - damaged_inv - reserved_inv)

    # Throughput (last 7 days mock)
    throughput = []
    for i in range(7, 0, -1):
        day = now - timedelta(days=i)
        label = day.strftime("%a")
        count = Order.query.filter(
            Order.updated_at >= day.replace(hour=0, minute=0, second=0),
            Order.updated_at < day.replace(hour=23, minute=59, second=59),
            Order.status.in_(["DISPATCHED", "COMPLETED"])
        ).count()
        throughput.append({"day": label, "count": count + random.randint(3, 12)})

    # ── Alerts ─────────────────────────────────────────────────────────────────
    alerts = []
    # Critical orders at risk
    at_risk = Order.query.filter_by(priority="CRITICAL").filter(
        Order.status.notin_(["DISPATCHED", "COMPLETED"]),
        Order.deadline <= now + timedelta(hours=4)
    ).limit(3).all()
    for o in at_risk:
        hours_left = max(0, (o.deadline - now).total_seconds() / 3600)
        alerts.append({
            "type": "danger",
            "icon": "🚨",
            "message": f"{o.order_number} — Critical order, deadline in {hours_left:.1f}h",
            "order_number": o.order_number,
            "order_id": o.id,
        })

    # Open critical exceptions
    crit_exc = WarehouseException.query.filter_by(
        severity="CRITICAL", status="OPEN"
    ).limit(2).all()
    for e in crit_exc:
        alerts.append({
            "type": "danger",
            "icon": "⚠️",
            "message": e.description[:80] + "..." if len(e.description) > 80 else e.description,
            "exception_id": e.id,
        })

    # Low stock alerts
    low_items = (
        db.session.query(Product, Inventory)
        .join(Inventory, Inventory.product_id == Product.id)
        .filter(
            (Inventory.quantity - Inventory.reserved_quantity - Inventory.damaged_quantity)
            < Product.reorder_level
        )
        .limit(3)
        .all()
    )
    for prod, inv in low_items:
        avail = max(0, inv.quantity - inv.reserved_quantity - inv.damaged_quantity)
        alerts.append({
            "type": "warning",
            "icon": "📦",
            "message": f"{prod.name} — {avail} units available (reorder at {prod.reorder_level})",
            "product_id": prod.id,
        })

    # ── Recent Activity ────────────────────────────────────────────────────────
    recent_movements = InventoryMovement.query.order_by(
        InventoryMovement.created_at.desc()
    ).limit(8).all()

    activity = []
    for mov in recent_movements:
        activity.append({
            "time": mov.created_at.strftime("%H:%M"),
            "message": f"{mov.product.name if mov.product else 'Product'} — {mov.movement_type} of {abs(mov.quantity)} units",
            "reference": mov.reference,
            "type": mov.movement_type,
        })

    # Recent order updates
    recent_orders = Order.query.order_by(Order.updated_at.desc()).limit(6).all()
    for o in recent_orders:
        activity.append({
            "time": o.updated_at.strftime("%H:%M"),
            "message": f"{o.order_number} moved to {o.status}",
            "reference": o.order_number,
            "type": "ORDER",
            "order_id": o.id,
        })

    # Sort by time desc (simple string sort is fine for demo)
    activity.sort(key=lambda x: x["time"], reverse=True)
    activity = activity[:10]

    return jsonify({
        "kpis": {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "critical_orders": critical_orders,
            "total_inventory_units": int(total_inventory_units),
            "low_stock_products": low_stock_products,
            "out_of_stock": out_of_stock,
            "open_exceptions": open_exceptions,
            "critical_exceptions": critical_exceptions,
            "ready_to_dispatch": ready_to_dispatch,
            "fulfillment_rate": fulfillment_rate,
            "dispatched_today": dispatched_today + completed_today,
        },
        "charts": {
            "orders_by_status": orders_by_status,
            "orders_by_priority": orders_by_priority,
            "exceptions_by_type": exceptions_by_type,
            "inventory_health": {
                "available": int(available_inv),
                "reserved": int(reserved_inv),
                "damaged": int(damaged_inv),
            },
            "throughput": throughput,
        },
        "alerts": alerts[:8],
        "activity": activity,
    })



