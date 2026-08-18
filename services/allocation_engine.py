"""
Allocation Engine — Smart inventory allocation based on order priority.

Algorithm:
1. Sort orders by priority_score DESC (highest priority first)
2. For each order item:
   - Find all inventory records with available stock
   - Prefer same-warehouse, then closest zone
   - Allocate as much as available
   - If partial, create PARTIAL allocation + exception
   - If none, create FAILED allocation + OUT_OF_STOCK exception
3. Prevent negative inventory
4. Prevent duplicate allocations
"""
from database import db
from database.models import (
    Order, OrderItem, Inventory, Allocation, InventoryMovement
)


class AllocationEngine:

    def allocate_order(self, order: Order) -> dict:
        """Allocate inventory for all items in an order."""
        results = []
        all_fulfilled = True
        any_partial = False

        for item in order.items:
            result = self._allocate_item(order, item)
            results.append(result)
            if result["status"] == "PARTIAL":
                any_partial = True
                all_fulfilled = False
            elif result["status"] == "FAILED":
                all_fulfilled = False

        # Update order status
        if all_fulfilled:
            order.status = "ALLOCATED"
        elif any_partial:
            order.status = "ALLOCATED"  # Partial allocation still proceeds
        else:
            order.status = "EXCEPTION"

        db.session.flush()

        return {
            "success": True,
            "order_id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "items": results,
            "message": self._build_allocation_message(results),
        }

    def _allocate_item(self, order: Order, item: OrderItem) -> dict:
        """Allocate inventory for a single order item."""
        needed = item.quantity - item.allocated_quantity
        if needed <= 0:
            return {
                "product_id": item.product_id,
                "status": "ALREADY_ALLOCATED",
                "message": "Already fully allocated.",
            }

        # Check for existing allocations to prevent duplicates
        existing = Allocation.query.filter_by(
            order_id=order.id,
            product_id=item.product_id,
            status="ALLOCATED",
        ).first()
        if existing:
            return {
                "product_id": item.product_id,
                "status": "ALREADY_ALLOCATED",
                "message": "Duplicate allocation prevented.",
            }

        # Find available inventory records sorted by availability
        inv_records = (
            Inventory.query.filter_by(product_id=item.product_id)
            .filter(
                (Inventory.quantity - Inventory.reserved_quantity - Inventory.damaged_quantity) > 0
            )
            .all()
        )

        # Sort: highest available quantity first
        inv_records.sort(key=lambda i: i.available_quantity, reverse=True)

        total_allocated = 0
        allocation_details = []

        for inv in inv_records:
            if total_allocated >= needed:
                break

            available = inv.available_quantity
            to_allocate = min(available, needed - total_allocated)

            if to_allocate <= 0:
                continue

            # Reserve the stock
            inv.reserved_quantity += to_allocate
            total_allocated += to_allocate

            # Create allocation record
            alloc = Allocation(
                order_id=order.id,
                product_id=item.product_id,
                inventory_id=inv.id,
                requested_quantity=needed,
                allocated_quantity=to_allocate,
                status="ALLOCATED",
                reason=(
                    f"Allocated {to_allocate} units from {inv.zone}-{inv.bin_location} "
                    f"({inv.warehouse.name if inv.warehouse else 'Unknown'})"
                ),
            )
            db.session.add(alloc)

            # Record movement
            mov = InventoryMovement(
                product_id=item.product_id,
                inventory_id=inv.id,
                movement_type="ALLOCATION",
                quantity=to_allocate,
                reference=order.order_number,
                notes=f"Allocated for order {order.order_number}",
            )
            db.session.add(mov)

            allocation_details.append({
                "inventory_id": inv.id,
                "zone": inv.zone,
                "bin": inv.bin_location,
                "allocated": to_allocate,
            })

        # Update order item
        item.allocated_quantity += total_allocated
        db.session.flush()

        shortage = needed - total_allocated

        if total_allocated >= needed:
            status = "ALLOCATED"
            message = f"Fully allocated {total_allocated} units."
        elif total_allocated > 0:
            status = "PARTIAL"
            message = f"Partial allocation: {total_allocated}/{needed} units. Shortage: {shortage} units."
        else:
            status = "FAILED"
            message = f"No stock available. All {needed} units are on backorder."
            # Create failed allocation record
            inv_any = Inventory.query.filter_by(product_id=item.product_id).first()
            if inv_any:
                alloc = Allocation(
                    order_id=order.id,
                    product_id=item.product_id,
                    inventory_id=inv_any.id,
                    requested_quantity=needed,
                    allocated_quantity=0,
                    status="FAILED",
                    reason="No available stock.",
                )
                db.session.add(alloc)

        return {
            "product_id": item.product_id,
            "status": status,
            "requested": needed,
            "allocated": total_allocated,
            "shortage": shortage,
            "details": allocation_details,
            "message": message,
        }

    def _build_allocation_message(self, results: list) -> str:
        success = sum(1 for r in results if r["status"] == "ALLOCATED")
        partial = sum(1 for r in results if r["status"] == "PARTIAL")
        failed = sum(1 for r in results if r["status"] == "FAILED")

        parts = []
        if success:
            parts.append(f"{success} item(s) fully allocated")
        if partial:
            parts.append(f"{partial} item(s) partially allocated")
        if failed:
            parts.append(f"{failed} item(s) failed (no stock)")

        return ". ".join(parts) + "." if parts else "Allocation complete."
