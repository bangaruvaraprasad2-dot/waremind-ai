"""
Picking Engine — Optimizes pick tasks with zone sequencing.
"""
from database import db
from database.models import Order, OrderItem, Inventory, Allocation, PickTask

ZONE_SEQUENCE = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}
WORKERS = [
    "James Carter", "Sarah Mitchell", "David Park", "Emily Rodriguez",
    "Marcus Johnson", "Linda Chen", "Alex Thompson", "Priya Patel",
]


class PickingEngine:

    def generate_pick_tasks(self, order: Order) -> list:
        """Generate optimized pick tasks for an order."""
        import random

        # Clear existing tasks
        PickTask.query.filter_by(order_id=order.id).delete()

        # Build pick list from allocations
        pick_list = []
        for alloc in order.allocations:
            if alloc.status != "ALLOCATED" or alloc.allocated_quantity <= 0:
                continue
            inv = Inventory.query.get(alloc.inventory_id)
            if not inv:
                continue
            pick_list.append({
                "product_id": alloc.product_id,
                "inventory_id": inv.id,
                "zone": inv.zone,
                "bin_location": inv.bin_location,
                "quantity": alloc.allocated_quantity,
            })

        # Sort by zone then bin (minimize travel distance)
        pick_list.sort(
            key=lambda p: (
                ZONE_SEQUENCE.get(p["zone"], 99),
                p["bin_location"],
            )
        )

        worker = random.choice(WORKERS)
        tasks = []

        for seq, item in enumerate(pick_list, 1):
            task = PickTask(
                order_id=order.id,
                product_id=item["product_id"],
                worker_name=worker,
                zone=item["zone"],
                bin_location=item["bin_location"],
                quantity=item["quantity"],
                sequence=seq,
                status="PENDING",
            )
            db.session.add(task)
            tasks.append(task.to_dict() if hasattr(task, 'to_dict') else {
                "sequence": seq,
                "zone": item["zone"],
                "bin_location": item["bin_location"],
                "quantity": item["quantity"],
                "worker_name": worker,
            })

        db.session.flush()
        return tasks

    def get_optimized_route(self, order: Order) -> dict:
        """Return picking route analysis."""
        tasks = sorted(order.pick_tasks, key=lambda t: t.sequence)

        zones_visited = list(dict.fromkeys(t.zone for t in tasks))
        total_items = sum(t.quantity for t in tasks)
        estimated_time = len(tasks) * 3 + len(zones_visited) * 5  # minutes

        return {
            "route": [
                {"seq": t.sequence, "zone": t.zone, "bin": t.bin_location,
                 "qty": t.quantity, "worker": t.worker_name, "status": t.status}
                for t in tasks
            ],
            "zones_visited": zones_visited,
            "total_items": total_items,
            "total_bins": len(tasks),
            "estimated_time_minutes": estimated_time,
            "optimization": "Zone-sequenced picking (minimize travel distance)",
        }
