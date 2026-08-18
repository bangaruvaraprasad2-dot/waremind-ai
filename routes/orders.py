from flask import Blueprint, render_template, jsonify, request
from datetime import datetime
from database import db
from database.models import (
    Order, OrderItem, Allocation, PickTask, PackTask,
    QualityCheck, Dispatch, WarehouseException, InventoryMovement, Inventory
)
from services.priority_engine import PriorityEngine
from services.allocation_engine import AllocationEngine
from services.picking_engine import PickingEngine
from services.exception_engine import ExceptionEngine

orders_bp = Blueprint("orders", __name__)


@orders_bp.route("/orders")
def orders_page():
    return render_template("orders.html", page="orders")


@orders_bp.route("/orders/<int:order_id>")
def order_detail_page(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template("order_detail.html", page="orders", order=order)


@orders_bp.route("/api/orders")
def api_orders():
    status = request.args.get("status", "")
    priority = request.args.get("priority", "")
    search = request.args.get("search", "").strip()

    query = Order.query
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    if search:
        query = query.filter(
            db.or_(
                Order.order_number.ilike(f"%{search}%"),
                Order.customer_name.ilike(f"%{search}%"),
            )
        )

    orders = query.order_by(Order.priority_score.desc(), Order.created_at.desc()).all()
    now = datetime.utcnow()

    result = []
    for o in orders:
        o_dict = o.to_dict()
        # Add deadline info
        if o.deadline:
            hours_left = (o.deadline - now).total_seconds() / 3600
            o_dict["hours_until_deadline"] = round(hours_left, 1)
            o_dict["deadline_risk"] = hours_left < 3
        else:
            o_dict["hours_until_deadline"] = None
            o_dict["deadline_risk"] = False
        result.append(o_dict)

    return jsonify({"orders": result, "total": len(result)})


@orders_bp.route("/api/orders/<int:order_id>")
def api_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    now = datetime.utcnow()
    data = order.to_dict()

    # Items with availability
    items = []
    for item in order.items:
        item_d = item.to_dict()
        item_d["product_image_url"] = item.product.image_url if item.product else None
        # Check inventory availability
        inv_records = Inventory.query.filter_by(product_id=item.product_id).all()
        total_available = sum(i.available_quantity for i in inv_records)
        item_d["total_available"] = total_available
        item_d["shortage"] = max(0, item.quantity - total_available)
        item_d["inventory_records"] = [
            {"zone": i.zone, "bin": i.bin_location, "available": i.available_quantity,
             "warehouse": i.warehouse.name if i.warehouse else ""}
            for i in inv_records
        ]
        items.append(item_d)

    data["items"] = items

    # Allocations
    data["allocations"] = [a.to_dict() for a in order.allocations]

    # Pick tasks
    data["pick_tasks"] = sorted(
        [p.to_dict() for p in order.pick_tasks], key=lambda x: x["sequence"]
    )

    # Pack tasks
    data["pack_tasks"] = [p.to_dict() for p in order.pack_tasks]

    # Quality checks
    data["quality_checks"] = [q.to_dict() for q in order.quality_checks]

    # Dispatch
    data["dispatch"] = order.dispatch.to_dict() if order.dispatch else None

    # Exceptions
    data["exceptions"] = [e.to_dict() for e in order.exceptions]

    # Timeline
    data["timeline"] = _build_timeline(order)

    # Deadline
    if order.deadline:
        hours_left = (order.deadline - now).total_seconds() / 3600
        data["hours_until_deadline"] = round(hours_left, 1)

    return jsonify(data)


@orders_bp.route("/api/orders", methods=["POST"])
def create_order():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required = ["customer_name", "customer_type", "items"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    # Generate order number
    last_order = Order.query.order_by(Order.id.desc()).first()
    new_num = (last_order.id + 1) if last_order else 1
    order_number = f"ORD-{5000 + new_num:04d}"

    deadline = None
    if data.get("deadline"):
        try:
            deadline = datetime.fromisoformat(data["deadline"])
        except ValueError:
            pass

    order = Order(
        order_number=order_number,
        customer_name=data["customer_name"],
        customer_type=data.get("customer_type", "STANDARD"),
        status="CREATED",
        deadline=deadline,
        notes=data.get("notes", ""),
    )
    db.session.add(order)
    db.session.flush()

    for item_data in data["items"]:
        oi = OrderItem(
            order_id=order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
        )
        db.session.add(oi)

    # Auto-prioritize
    engine = PriorityEngine()
    score, priority, reason = engine.calculate_priority(order)
    order.priority_score = score
    order.priority = priority
    order.priority_reason = reason
    order.status = "PRIORITIZED"

    db.session.commit()
    return jsonify({"success": True, "order": order.to_dict()}), 201


@orders_bp.route("/api/orders/<int:order_id>/prioritize", methods=["POST"])
def prioritize_order(order_id):
    order = Order.query.get_or_404(order_id)
    engine = PriorityEngine()
    score, priority, reason = engine.calculate_priority(order)
    order.priority_score = round(score, 1)
    order.priority = priority
    order.priority_reason = reason
    if order.status == "CREATED":
        order.status = "PRIORITIZED"
    db.session.commit()
    return jsonify({
        "success": True,
        "priority": priority,
        "priority_score": score,
        "priority_reason": reason,
    })


@orders_bp.route("/api/orders/<int:order_id>/allocate", methods=["POST"])
def allocate_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status not in ["CREATED", "PRIORITIZED"]:
        return jsonify({"error": f"Cannot allocate order in status: {order.status}"}), 400

    engine = AllocationEngine()
    result = engine.allocate_order(order)

    exc_engine = ExceptionEngine()
    exc_engine.check_after_allocation(order)

    db.session.commit()
    return jsonify(result)


@orders_bp.route("/api/orders/<int:order_id>/pick", methods=["POST"])
def start_picking(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status != "ALLOCATED":
        return jsonify({"error": f"Cannot start picking for order in status: {order.status}"}), 400

    engine = PickingEngine()
    tasks = engine.generate_pick_tasks(order)
    order.status = "PICKING"
    db.session.commit()
    return jsonify({"success": True, "pick_tasks": tasks, "message": "Picking tasks generated."})


@orders_bp.route("/api/orders/<int:order_id>/complete-picking", methods=["POST"])
def complete_picking(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status != "PICKING":
        return jsonify({"error": f"Order is not in PICKING status"}), 400

    for task in order.pick_tasks:
        task.status = "COMPLETED"
        task.completed_at = datetime.utcnow()

    for item in order.items:
        item.picked_quantity = item.allocated_quantity

    order.status = "PACKING"
    db.session.commit()
    return jsonify({"success": True, "message": "Picking completed. Order moved to PACKING."})


@orders_bp.route("/api/orders/<int:order_id>/pack", methods=["POST"])
def start_packing(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status != "PACKING":
        return jsonify({"error": f"Order is not in PACKING status"}), 400

    data = request.get_json() or {}
    worker = data.get("worker_name", "Auto-assigned")
    station = data.get("packing_station", "PS-01")

    pack = PackTask(
        order_id=order.id,
        packing_station=station,
        worker_name=worker,
        status="IN_PROGRESS",
        started_at=datetime.utcnow(),
    )
    db.session.add(pack)
    db.session.commit()
    return jsonify({"success": True, "message": "Packing started.", "pack_task": pack.to_dict()})


@orders_bp.route("/api/orders/<int:order_id>/complete-packing", methods=["POST"])
def complete_packing(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status != "PACKING":
        return jsonify({"error": f"Order is not in PACKING status"}), 400

    for task in order.pack_tasks:
        if task.status == "IN_PROGRESS":
            task.status = "COMPLETED"
            task.completed_at = datetime.utcnow()

    for item in order.items:
        item.packed_quantity = item.picked_quantity

    order.status = "QUALITY_CHECK"
    db.session.commit()
    return jsonify({"success": True, "message": "Packing completed. Order moved to QUALITY_CHECK."})


@orders_bp.route("/api/orders/<int:order_id>/quality-check", methods=["POST"])
def quality_check(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status != "QUALITY_CHECK":
        return jsonify({"error": f"Order is not in QUALITY_CHECK status"}), 400

    data = request.get_json() or {}
    damaged = int(data.get("damaged_items", 0))
    missing = int(data.get("missing_items", 0))
    checker = data.get("checked_by", "QC Team")
    notes = data.get("notes", "")

    qc_status = "PASSED" if (damaged == 0 and missing == 0) else "FAILED"
    qc = QualityCheck(
        order_id=order.id,
        checked_by=checker,
        status=qc_status,
        damaged_items=damaged,
        missing_items=missing,
        notes=notes or ("All items verified and packaged correctly." if qc_status == "PASSED" else "Issues found."),
        checked_at=datetime.utcnow(),
    )
    db.session.add(qc)

    if qc_status == "PASSED":
        order.status = "READY_TO_DISPATCH"
        msg = "Quality check passed. Order is READY_TO_DISPATCH."
    else:
        order.status = "EXCEPTION"
        exc = WarehouseException(
            order_id=order.id,
            exception_type="QUALITY_FAILURE",
            severity="HIGH",
            description=f"Quality check failed for {order.order_number}. {damaged} damaged, {missing} missing items.",
            recommended_action="Locate replacement stock and re-pack. Re-run quality check.",
            status="OPEN",
        )
        db.session.add(exc)
        msg = "Quality check FAILED. Exception created."

    db.session.commit()
    return jsonify({"success": True, "qc_status": qc_status, "message": msg})


@orders_bp.route("/api/orders/<int:order_id>/dispatch", methods=["POST"])
def dispatch_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status != "READY_TO_DISPATCH":
        return jsonify({"error": f"Order is not READY_TO_DISPATCH"}), 400

    import random, string
    from datetime import timedelta
    data = request.get_json() or {}
    carrier = data.get("carrier", random.choice(["FedEx", "UPS", "DHL", "Royal Mail"]))
    tracking = "".join(random.choices(string.ascii_uppercase + string.digits, k=12))

    disp = Dispatch(
        order_id=order.id,
        carrier=carrier,
        tracking_number=tracking,
        status="IN_TRANSIT",
        dispatch_time=datetime.utcnow(),
        estimated_delivery=datetime.utcnow() + timedelta(days=random.randint(1, 3)),
    )
    db.session.add(disp)

    # Release reserved inventory
    for alloc in order.allocations:
        inv = Inventory.query.get(alloc.inventory_id)
        if inv:
            inv.reserved_quantity = max(0, inv.reserved_quantity - alloc.allocated_quantity)
            inv.quantity = max(0, inv.quantity - alloc.allocated_quantity)
            mov = InventoryMovement(
                product_id=alloc.product_id,
                inventory_id=inv.id,
                movement_type="OUTBOUND",
                quantity=alloc.allocated_quantity,
                reference=order.order_number,
                notes="Dispatched",
            )
            db.session.add(mov)

    order.status = "DISPATCHED"
    db.session.commit()
    return jsonify({
        "success": True,
        "message": f"Order dispatched via {carrier}. Tracking: {tracking}",
        "tracking_number": tracking,
        "carrier": carrier,
    })


def _build_timeline(order):
    """Build the order's status timeline."""
    all_statuses = [
        "CREATED", "PRIORITIZED", "ALLOCATED", "PICKING",
        "PACKING", "QUALITY_CHECK", "READY_TO_DISPATCH", "DISPATCHED", "COMPLETED"
    ]
    current = order.status
    timeline = []
    reached = False
    for s in all_statuses:
        if s == current:
            reached = True
            state = "current" if current not in ["DISPATCHED", "COMPLETED"] else "done"
        elif not reached:
            state = "done"
        else:
            state = "pending"
        if current == "EXCEPTION" and s == current:
            state = "exception"
        timeline.append({"status": s, "state": state})

    if current == "EXCEPTION":
        timeline.append({"status": "EXCEPTION", "state": "exception"})

    return timeline
