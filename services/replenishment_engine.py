"""
Replenishment Engine — Detects products requiring restocking.
"""
from database import db
from database.models import Product, Inventory, OrderItem, Order


class ReplenishmentEngine:

    def get_recommendation(self, product_id: int) -> dict:
        """Get replenishment recommendation for a specific product."""
        product = Product.query.get(product_id)
        if not product:
            return {"error": "Product not found"}

        inv_records = Inventory.query.filter_by(product_id=product_id).all()
        total_qty = sum(i.quantity for i in inv_records)
        total_reserved = sum(i.reserved_quantity for i in inv_records)
        total_damaged = sum(i.damaged_quantity for i in inv_records)
        total_available = sum(i.available_quantity for i in inv_records)

        # Pending demand
        pending_demand = db.session.query(
            db.func.sum(OrderItem.quantity - OrderItem.allocated_quantity)
        ).join(Order).filter(
            OrderItem.product_id == product_id,
            Order.status.in_(["CREATED", "PRIORITIZED"]),
        ).scalar() or 0

        # Risk assessment
        if total_available <= 0:
            risk = "CRITICAL"
            urgency = "IMMEDIATE"
        elif total_available < product.reorder_level:
            risk = "HIGH"
            urgency = "URGENT"
        elif total_available < product.reorder_level * 1.5:
            risk = "MEDIUM"
            urgency = "SOON"
        else:
            risk = "LOW"
            urgency = "ROUTINE"

        # Recommended quantity
        recommended_qty = max(
            product.reorder_quantity,
            int(pending_demand * 1.5),
        )

        reason = self._build_reason(
            product, total_available, total_reserved, total_damaged,
            pending_demand, risk
        )

        return {
            "product_id": product.id,
            "sku": product.sku,
            "name": product.name,
            "supplier": product.supplier,
            "current_stock": total_qty,
            "available_stock": total_available,
            "reserved_stock": total_reserved,
            "damaged_stock": total_damaged,
            "reorder_level": product.reorder_level,
            "pending_demand": int(pending_demand),
            "recommended_quantity": recommended_qty,
            "risk": risk,
            "urgency": urgency,
            "reason": reason,
            "needs_replenishment": risk in ["CRITICAL", "HIGH", "MEDIUM"],
        }

    def get_all_recommendations(self) -> list:
        """Get replenishment recommendations for all products that need it."""
        products = Product.query.all()
        recommendations = []
        for prod in products:
            rec = self.get_recommendation(prod.id)
            if rec.get("needs_replenishment"):
                recommendations.append(rec)

        # Sort by risk level
        risk_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        recommendations.sort(key=lambda r: risk_order.get(r["risk"], 4))
        return recommendations

    def _build_reason(self, product, available, reserved, damaged, pending, risk) -> str:
        parts = [f"'{product.name}': "]
        if available <= 0:
            parts.append(f"out of stock (0 units available).")
        else:
            parts.append(f"{available} units available.")

        if reserved > 0:
            parts.append(f"{reserved} units reserved for pending orders.")
        if damaged > 0:
            parts.append(f"{damaged} units are damaged.")
        if pending > 0:
            parts.append(f"{int(pending)} units required by unfulfilled orders.")

        parts.append(
            f"Reorder level is {product.reorder_level} units. "
            f"Recommend ordering {product.reorder_quantity} units from {product.supplier}."
        )
        return " ".join(parts)
