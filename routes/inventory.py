from flask import Blueprint, render_template, jsonify, request
from database import db
from database.models import (
    Product, Inventory, Warehouse, WarehouseException, InventoryMovement
)
from services.replenishment_engine import ReplenishmentEngine

inventory_bp = Blueprint("inventory", __name__)


@inventory_bp.route("/inventory")
def inventory_page():
    return render_template("inventory.html", page="inventory")


@inventory_bp.route("/api/inventory")
def api_inventory():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    risk = request.args.get("risk", "").strip()
    warehouse_id = request.args.get("warehouse_id", "").strip()

    query = (
        db.session.query(Product, Inventory)
        .join(Inventory, Inventory.product_id == Product.id)
        .join(Warehouse, Warehouse.id == Inventory.warehouse_id)
    )

    if search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%"),
                Product.category.ilike(f"%{search}%"),
            )
        )
    if category:
        query = query.filter(Product.category == category)
    if warehouse_id:
        query = query.filter(Inventory.warehouse_id == int(warehouse_id))

    results = query.all()

    items = []
    for prod, inv in results:
        avail = inv.available_quantity
        reorder_lv = prod.reorder_level

        if avail <= 0:
            risk_level = "CRITICAL"
        elif avail < reorder_lv:
            risk_level = "LOW"
        else:
            risk_level = "HEALTHY"

        if risk and risk_level != risk:
            continue

        items.append({
            "product_id": prod.id,
            "sku": prod.sku,
            "name": prod.name,
            "category": prod.category,
            "price": prod.price,
            "supplier": prod.supplier,
            "image_url": prod.image_url,
            "warehouse_id": inv.warehouse_id,
            "warehouse_name": inv.warehouse.name if inv.warehouse else "",
            "zone": inv.zone,
            "bin_location": inv.bin_location,
            "quantity": inv.quantity,
            "reserved_quantity": inv.reserved_quantity,
            "damaged_quantity": inv.damaged_quantity,
            "available_quantity": avail,
            "reorder_level": reorder_lv,
            "reorder_quantity": prod.reorder_quantity,
            "risk": risk_level,
            "inventory_id": inv.id,
            "last_updated": inv.last_updated.strftime("%Y-%m-%d %H:%M") if inv.last_updated else "",
        })

    # Summary stats
    total = len(items)
    healthy = sum(1 for i in items if i["risk"] == "HEALTHY")
    low = sum(1 for i in items if i["risk"] == "LOW")
    critical = sum(1 for i in items if i["risk"] == "CRITICAL")

    return jsonify({
        "items": items,
        "summary": {
            "total": total,
            "healthy": healthy,
            "low": low,
            "critical": critical,
        }
    })


@inventory_bp.route("/api/inventory/categories")
def api_categories():
    cats = db.session.query(Product.category).distinct().all()
    return jsonify({"categories": [c[0] for c in cats]})


@inventory_bp.route("/api/inventory/<int:inventory_id>/adjust", methods=["POST"])
def adjust_stock(inventory_id):
    data = request.get_json()
    inv = Inventory.query.get_or_404(inventory_id)
    adjustment = int(data.get("adjustment", 0))
    reason = data.get("reason", "Manual adjustment")

    if inv.quantity + adjustment < 0:
        return jsonify({"error": "Cannot adjust stock to negative quantity"}), 400

    old_qty = inv.quantity
    inv.quantity = max(0, inv.quantity + adjustment)
    db.session.flush()

    mov = InventoryMovement(
        product_id=inv.product_id,
        inventory_id=inv.id,
        movement_type="ADJUSTMENT",
        quantity=adjustment,
        reference="Manual Adjustment",
        notes=reason,
    )
    db.session.add(mov)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Stock adjusted from {old_qty} to {inv.quantity}",
        "new_quantity": inv.quantity,
        "available_quantity": inv.available_quantity,
    })


@inventory_bp.route("/api/inventory/<int:inventory_id>/damage", methods=["POST"])
def report_damage(inventory_id):
    data = request.get_json()
    inv = Inventory.query.get_or_404(inventory_id)
    damage_qty = int(data.get("quantity", 0))
    reason = data.get("reason", "Damage reported")

    if damage_qty <= 0:
        return jsonify({"error": "Damage quantity must be positive"}), 400
    if damage_qty > inv.quantity:
        return jsonify({"error": "Cannot damage more units than are in stock"}), 400

    inv.damaged_quantity = min(inv.quantity, inv.damaged_quantity + damage_qty)

    exc = WarehouseException(
        product_id=inv.product_id,
        exception_type="DAMAGED_ITEM",
        severity="MEDIUM",
        description=f"{damage_qty} units of {inv.product.name} reported as damaged in {inv.zone}-{inv.bin_location}. Reason: {reason}",
        recommended_action="Inspect and quarantine damaged units. File supplier claim if applicable.",
        status="OPEN",
    )
    db.session.add(exc)

    mov = InventoryMovement(
        product_id=inv.product_id,
        inventory_id=inv.id,
        movement_type="DAMAGE",
        quantity=-damage_qty,
        reference="Damage Report",
        notes=reason,
    )
    db.session.add(mov)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"{damage_qty} units marked as damaged",
        "damaged_quantity": inv.damaged_quantity,
        "available_quantity": inv.available_quantity,
    })


@inventory_bp.route("/api/inventory/<int:product_id>/replenishment")
def replenishment_rec(product_id):
    engine = ReplenishmentEngine()
    rec = engine.get_recommendation(product_id)
    return jsonify(rec)


@inventory_bp.route("/api/inventory/replenishment/all")
def all_replenishment():
    engine = ReplenishmentEngine()
    recs = engine.get_all_recommendations()
    return jsonify({"recommendations": recs})
