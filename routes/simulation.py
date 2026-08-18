from flask import Blueprint, jsonify, request
from database import db
from database.models import (
    Order, OrderItem, Inventory, Product, Allocation,
    WarehouseException, InventoryMovement
)
from services.priority_engine import PriorityEngine
from services.allocation_engine import AllocationEngine
from services.exception_engine import ExceptionEngine
from datetime import datetime, timedelta
import random
import string

simulation_bp = Blueprint("simulation", __name__)


@simulation_bp.route("/api/simulation/crisis", methods=["POST"])
def simulate_crisis():
    """
    Simulate a warehouse inventory conflict:
    - Critical order requires 10 units
    - Only 7 available
    - Normal order also competing for the same stock
    """
    data = request.get_json() or {}

    # Find a product with moderate stock for the simulation
    product = Product.query.join(Inventory).filter(
        (Inventory.quantity - Inventory.reserved_quantity - Inventory.damaged_quantity).between(5, 10)
    ).first()

    if not product:
        # Use the first product and temporarily set its stock
        product = Product.query.first()

    inv = Inventory.query.filter_by(product_id=product.id).first()
    if not inv:
        return jsonify({"error": "No inventory found for simulation"}), 400

    # Set available stock to exactly 7 for the simulation
    inv.quantity = max(inv.quantity, 12)
    inv.reserved_quantity = max(0, inv.quantity - 7)
    inv.damaged_quantity = 0
    db.session.flush()

    now = datetime.utcnow()

    # ── Create Critical Order ──────────────────────────────────────────────────
    last = Order.query.order_by(Order.id.desc()).first()
    base_num = last.id + 1 if last else 9001

    critical_order = Order(
        order_number=f"SIM-{base_num:04d}",
        customer_name="CRISIS DEMO — Apex Technologies Ltd",
        customer_type="PREMIUM",
        priority="CRITICAL",
        priority_score=94.5,
        priority_reason=(
            "Priority Score: 94.5 — CRITICAL because delivery deadline is within 2 hours, "
            "customer is premium, and order value exceeds £2,000 threshold. "
            "Urgency factor: 30pts | Deadline factor: 30pts | Customer factor: 20pts | Value factor: 14.5pts"
        ),
        status="PRIORITIZED",
        deadline=now + timedelta(hours=2),
        notes="SIMULATION: Crisis demo order",
    )
    db.session.add(critical_order)
    db.session.flush()

    critical_item = OrderItem(
        order_id=critical_order.id,
        product_id=product.id,
        quantity=10,
    )
    db.session.add(critical_item)

    # ── Create Normal Order ────────────────────────────────────────────────────
    normal_order = Order(
        order_number=f"SIM-{base_num + 1:04d}",
        customer_name="CRISIS DEMO — Metro Office Solutions",
        customer_type="STANDARD",
        priority="NORMAL",
        priority_score=47.2,
        priority_reason=(
            "Priority Score: 47.2 — NORMAL priority. Standard customer with deadline "
            "in 36 hours. No urgency flags raised."
        ),
        status="PRIORITIZED",
        deadline=now + timedelta(hours=36),
        notes="SIMULATION: Crisis demo order",
    )
    db.session.add(normal_order)
    db.session.flush()

    normal_item = OrderItem(
        order_id=normal_order.id,
        product_id=product.id,
        quantity=5,
    )
    db.session.add(normal_item)
    db.session.flush()

    # ── Run Allocation Engine ──────────────────────────────────────────────────
    alloc_engine = AllocationEngine()

    # Critical order gets priority
    critical_result = alloc_engine.allocate_order(critical_order)
    normal_result = alloc_engine.allocate_order(normal_order)

    # ── Create Conflict Exception ──────────────────────────────────────────────
    exc_engine = ExceptionEngine()
    exc_engine.check_after_allocation(critical_order)
    exc_engine.check_after_allocation(normal_order)

    # Create explicit conflict exception
    conflict_exc = WarehouseException(
        order_id=critical_order.id,
        product_id=product.id,
        exception_type="ALLOCATION_CONFLICT",
        severity="CRITICAL",
        description=(
            f"🚨 INVENTORY CONFLICT DETECTED\n\n"
            f"Critical order {critical_order.order_number} requires 10 units of '{product.name}' "
            f"but only 7 units are available.\n"
            f"Normal order {normal_order.order_number} also requires 5 units of the same product.\n"
            f"Total demand: 15 units | Available: 7 units | Shortfall: 8 units."
        ),
        recommended_action=(
            f"SYSTEM DECISION: Allocate all 7 available units to critical order "
            f"{critical_order.order_number} (Priority: 94.5, Deadline: 2 hours).\n"
            f"Backorder 3 units for {critical_order.order_number}.\n"
            f"Delay {normal_order.order_number} (Priority: 47.2, Deadline: 36 hours) "
            f"until replenishment arrives.\n"
            f"Trigger emergency replenishment for {product.reorder_quantity} units from {product.supplier}."
        ),
        status="OPEN",
    )
    db.session.add(conflict_exc)
    db.session.commit()

    return jsonify({
        "success": True,
        "scenario": {
            "product": product.to_dict(),
            "available_stock": inv.available_quantity,
            "total_demand": 15,
            "shortfall": 8,
        },
        "critical_order": {
            "order_number": critical_order.order_number,
            "order_id": critical_order.id,
            "required": 10,
            "allocated": critical_item.allocated_quantity,
            "shortage": max(0, 10 - critical_item.allocated_quantity),
            "priority_score": critical_order.priority_score,
            "deadline": critical_order.deadline.isoformat(),
        },
        "normal_order": {
            "order_number": normal_order.order_number,
            "order_id": normal_order.id,
            "required": 5,
            "allocated": normal_item.allocated_quantity,
            "shortage": max(0, 5 - normal_item.allocated_quantity),
            "priority_score": normal_order.priority_score,
            "deadline": normal_order.deadline.isoformat(),
        },
        "exception_id": conflict_exc.id,
        "decision": (
            f"Allocate all available 7 units to critical order {critical_order.order_number}. "
            f"Backorder 3 units. Delay normal order {normal_order.order_number}. "
            f"Trigger emergency replenishment for {product.name}."
        ),
        "reason": (
            f"Critical order has priority score 94.5 vs normal order 47.2. "
            f"Critical deadline is in 2 hours vs 36 hours. "
            f"PREMIUM customer vs STANDARD customer. "
            f"System automatically prioritized critical order per business rules."
        ),
    })


@simulation_bp.route("/api/simulation/crisis/apply", methods=["POST"])
def apply_crisis_decision():
    """Apply the crisis decision from a simulation."""
    data = request.get_json()
    critical_order_id = data.get("critical_order_id")
    normal_order_id = data.get("normal_order_id")
    exception_id = data.get("exception_id")

    if not all([critical_order_id, exception_id]):
        return jsonify({"error": "Missing required parameters"}), 400

    critical_order = Order.query.get(critical_order_id)
    exc = WarehouseException.query.get(exception_id)

    if not critical_order or not exc:
        return jsonify({"error": "Order or exception not found"}), 404

    # Resolve the exception
    exc.status = "RESOLVED"
    exc.resolution = (
        "Crisis decision applied: Critical order allocated maximum available stock. "
        "Normal order delayed. Emergency replenishment triggered."
    )
    exc.resolved_at = datetime.utcnow()

    # Move critical order forward
    critical_order.status = "PICKING"

    # Move normal order to wait
    if normal_order_id:
        normal_order = Order.query.get(normal_order_id)
        if normal_order:
            normal_order.status = "CREATED"
            normal_order.notes = "Delayed by crisis reallocation. Awaiting replenishment."

    # Create inventory movement record
    for alloc in critical_order.allocations:
        inv = Inventory.query.get(alloc.inventory_id)
        if inv:
            mov = InventoryMovement(
                product_id=alloc.product_id,
                inventory_id=inv.id,
                movement_type="ALLOCATION",
                quantity=alloc.allocated_quantity,
                reference=critical_order.order_number,
                notes="Crisis simulation — priority allocation applied",
            )
            db.session.add(mov)

    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Crisis decision applied successfully.",
        "critical_order_status": critical_order.status,
        "exception_status": exc.status,
    })
