from flask import Blueprint, render_template, jsonify
from database import db
from database.models import (
    Order, Inventory, Product, WarehouseException, PickTask, PackTask, QualityCheck
)
from datetime import datetime, timedelta

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
def analytics_page():
    return render_template("analytics.html", page="analytics")


@analytics_bp.route("/api/analytics")
def api_analytics():
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # ── Order Fulfillment Rate ─────────────────────────────────────────────────
    total_orders = Order.query.count()
    completed = Order.query.filter(Order.status.in_(["DISPATCHED", "COMPLETED"])).count()
    fulfillment_rate = round((completed / max(total_orders, 1)) * 100, 1)

    # ── On-time Dispatch Rate ──────────────────────────────────────────────────
    dispatched_orders = Order.query.filter(Order.status.in_(["DISPATCHED", "COMPLETED"])).all()
    on_time = sum(
        1 for o in dispatched_orders
        if o.deadline and o.updated_at and o.updated_at <= o.deadline
    )
    on_time_rate = round((on_time / max(len(dispatched_orders), 1)) * 100, 1)

    # ── Exception Rate ─────────────────────────────────────────────────────────
    exception_orders = Order.query.filter(
        Order.status == "EXCEPTION"
    ).count()
    exception_rate = round((exception_orders / max(total_orders, 1)) * 100, 1)

    # ── Inventory Stats ────────────────────────────────────────────────────────
    total_units = db.session.query(db.func.sum(Inventory.quantity)).scalar() or 0
    damaged_units = db.session.query(db.func.sum(Inventory.damaged_quantity)).scalar() or 0
    damage_rate = round((damaged_units / max(total_units, 1)) * 100, 1)

    total_products = Product.query.count()
    out_of_stock = db.session.query(Product).join(Inventory).filter(
        (Inventory.quantity - Inventory.reserved_quantity - Inventory.damaged_quantity) <= 0
    ).distinct().count()
    stockout_rate = round((out_of_stock / max(total_products, 1)) * 100, 1)

    # ── Picking Performance ────────────────────────────────────────────────────
    completed_picks = PickTask.query.filter_by(status="COMPLETED").filter(
        PickTask.started_at.isnot(None),
        PickTask.completed_at.isnot(None),
    ).all()
    avg_pick_time = 0
    if completed_picks:
        times = [(p.completed_at - p.started_at).total_seconds() / 60 for p in completed_picks]
        avg_pick_time = round(sum(times) / len(times), 1)

    # ── Packing Performance ───────────────────────────────────────────────────
    completed_packs = PackTask.query.filter_by(status="COMPLETED").filter(
        PackTask.started_at.isnot(None),
        PackTask.completed_at.isnot(None),
    ).all()
    avg_pack_time = 0
    if completed_packs:
        times = [(p.completed_at - p.started_at).total_seconds() / 60 for p in completed_packs]
        avg_pack_time = round(sum(times) / len(times), 1)

    # ── QC Stats ──────────────────────────────────────────────────────────────
    total_qc = QualityCheck.query.count()
    failed_qc = QualityCheck.query.filter_by(status="FAILED").count()
    qc_fail_rate = round((failed_qc / max(total_qc, 1)) * 100, 1)

    # ── Order volume by day (last 14 days) ────────────────────────────────────
    daily_orders = []
    for i in range(13, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = Order.query.filter(
            Order.created_at >= day_start,
            Order.created_at < day_end
        ).count()
        daily_orders.append({
            "date": day.strftime("%m/%d"),
            "orders": count,
        })

    # ── Exceptions trend ──────────────────────────────────────────────────────
    exc_trend = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = WarehouseException.query.filter(
            WarehouseException.created_at >= day_start,
            WarehouseException.created_at < day_end
        ).count()
        exc_trend.append({"date": day.strftime("%a"), "count": count})

    # ── Category breakdown ─────────────────────────────────────────────────────
    cats = db.session.query(Product.category, db.func.count(Product.id)).group_by(Product.category).all()

    # ── Priority breakdown ─────────────────────────────────────────────────────
    priority_stats = {}
    for p in ["CRITICAL", "HIGH", "NORMAL", "LOW"]:
        priority_stats[p] = {
            "total": Order.query.filter_by(priority=p).count(),
            "completed": Order.query.filter_by(priority=p).filter(
                Order.status.in_(["DISPATCHED", "COMPLETED"])
            ).count(),
        }

    # ── Bottleneck analysis ────────────────────────────────────────────────────
    from services.bottleneck_engine import BottleneckEngine
    bottleneck = BottleneckEngine().analyze()

    return jsonify({
        "summary": {
            "total_orders": total_orders,
            "fulfillment_rate": fulfillment_rate,
            "on_time_rate": on_time_rate,
            "exception_rate": exception_rate,
            "avg_pick_time": avg_pick_time,
            "avg_pack_time": avg_pack_time,
            "damage_rate": damage_rate,
            "stockout_rate": stockout_rate,
            "qc_fail_rate": qc_fail_rate,
            "total_units": int(total_units),
        },
        "charts": {
            "daily_orders": daily_orders,
            "exception_trend": exc_trend,
            "category_breakdown": [{"category": c[0], "count": c[1]} for c in cats],
            "priority_stats": priority_stats,
        },
        "bottleneck": bottleneck,
    })
