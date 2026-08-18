"""
Copilot Service — Rule-based AI warehouse assistant with optional LLM integration.
All responses are grounded in live database data.
"""
import re
from datetime import datetime, timedelta
from database import db
from database.models import (
    Order, Inventory, Product, WarehouseException, PickTask, PackTask
)


class CopilotService:

    def process_query(self, message: str) -> dict:
        """Process a natural language query and return a structured response."""
        message_lower = message.lower().strip()

        # Route to appropriate handler
        if any(kw in message_lower for kw in ["at risk", "risk", "danger", "critical order"]):
            return self._orders_at_risk()
        elif any(kw in message_lower for kw in ["replenish", "reorder", "restock", "low stock", "stock"]):
            return self._replenishment_status()
        elif any(kw in message_lower for kw in ["bottleneck", "slow", "delay", "performance"]):
            return self._bottleneck_status()
        elif any(kw in message_lower for kw in ["exception", "problem", "issue", "alert"]):
            return self._exception_summary()
        elif any(kw in message_lower for kw in ["today", "summary", "overview", "situation"]):
            return self._daily_summary()
        elif any(kw in message_lower for kw in ["dispatch", "ship", "ready"]):
            return self._dispatch_status()
        elif re.search(r"ord[-\s]?\d+|order\s+\d+", message_lower):
            # Specific order query
            match = re.search(r"(ord[-\s]?\d+|\d{4,})", message_lower)
            if match:
                return self._order_status(match.group(0))
        elif any(kw in message_lower for kw in ["inventory", "stock level", "warehouse"]):
            return self._inventory_overview()
        elif any(kw in message_lower for kw in ["help", "what can", "commands"]):
            return self._help_message()

        return self._general_response(message)

    def _orders_at_risk(self) -> dict:
        now = datetime.utcnow()
        at_risk_orders = Order.query.filter(
            Order.status.notin_(["DISPATCHED", "COMPLETED"]),
            Order.deadline <= now + timedelta(hours=6)
        ).order_by(Order.priority_score.desc()).limit(10).all()

        shortage_orders = (
            db.session.query(Order)
            .join(Order.exceptions)
            .filter(
                WarehouseException.exception_type.in_(["OUT_OF_STOCK", "ALLOCATION_CONFLICT"]),
                WarehouseException.status == "OPEN",
            )
            .distinct()
            .count()
        )

        picking_delay_orders = (
            db.session.query(Order)
            .join(Order.exceptions)
            .filter(
                WarehouseException.exception_type == "PICKING_DELAY",
                WarehouseException.status == "OPEN",
            )
            .distinct()
            .count()
        )

        quality_exceptions = WarehouseException.query.filter_by(
            exception_type="QUALITY_FAILURE", status="OPEN"
        ).count()

        total_at_risk = len(at_risk_orders)

        if total_at_risk == 0:
            return {
                "message": "✅ No orders are currently at high risk. All critical orders are on track.",
                "data": {},
                "type": "success"
            }

        lines = [
            f"⚠️ **{total_at_risk} order(s) currently at risk:**\n",
        ]

        if shortage_orders > 0:
            lines.append(f"• 📦 **{shortage_orders}** order(s) have inventory shortages")
        if picking_delay_orders > 0:
            lines.append(f"• 🔄 **{picking_delay_orders}** order(s) have picking delays")
        if quality_exceptions > 0:
            lines.append(f"• ❌ **{quality_exceptions}** order(s) have quality exceptions")

        lines.append("\n**Highest risk orders:**")
        for o in at_risk_orders[:5]:
            hours_left = (o.deadline - now).total_seconds() / 3600 if o.deadline else 0
            lines.append(
                f"• **{o.order_number}** — {o.priority} — {o.status} — "
                f"deadline in {hours_left:.1f}h — {o.customer_name}"
            )

        orders_data = []
        for o in at_risk_orders[:5]:
            hours_left = (o.deadline - now).total_seconds() / 3600 if o.deadline else 0
            items_info = []
            for item in o.items:
                if item.product:
                    items_info.append({
                        "name": item.product.name,
                        "sku": item.product.sku,
                        "image_url": item.product.image_url or "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=200&q=80",
                        "quantity": item.quantity,
                    })
            orders_data.append({
                "id": o.id,
                "order_number": o.order_number,
                "priority": o.priority,
                "priority_score": o.priority_score,
                "status": o.status,
                "customer_name": o.customer_name,
                "hours_left": round(hours_left, 1),
                "items": items_info,
            })

        return {
            "message": "\n".join(lines),
            "data": {
                "at_risk_count": total_at_risk,
                "shortage_orders": shortage_orders,
                "picking_delay_orders": picking_delay_orders,
                "quality_exceptions": quality_exceptions,
                "at_risk_orders": orders_data,
            },
            "type": "warning"
        }

    def _replenishment_status(self) -> dict:
        from services.replenishment_engine import ReplenishmentEngine
        engine = ReplenishmentEngine()
        recs = engine.get_all_recommendations()

        critical = [r for r in recs if r["risk"] == "CRITICAL"]
        high = [r for r in recs if r["risk"] == "HIGH"]
        medium = [r for r in recs if r["risk"] == "MEDIUM"]

        lines = [
            f"📦 **Replenishment Status:**\n",
            f"• 🔴 **{len(critical)}** product(s) critically low / out of stock",
            f"• 🟠 **{len(high)}** product(s) urgently need restocking",
            f"• 🟡 **{len(medium)}** product(s) approaching reorder level\n",
        ]

        if critical:
            lines.append("**Critical — order immediately:**")
            for r in critical[:4]:
                img_url = r.get("image_url") or "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=200&q=80"
                lines.append(
                    f"• ![{r['name']}]({img_url}) **{r['name']}** (SKU: {r['sku']}) — **{r['available_stock']}** units left"
                    f" — recommend ordering {r['recommended_quantity']} from {r['supplier']}"
                )

        if high:
            lines.append("\n**High urgency:**")
            for r in high[:4]:
                img_url = r.get("image_url") or "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=200&q=80"
                lines.append(
                    f"• ![{r['name']}]({img_url}) **{r['name']}** — **{r['available_stock']}** units "
                    f"(reorder level: {r['reorder_level']})"
                )

        return {
            "message": "\n".join(lines),
            "data": {
                "total_needing_reorder": len(recs),
                "critical": len(critical),
                "high": len(high),
                "recommendations": recs[:6],
            },
            "type": "info"
        }

    def _bottleneck_status(self) -> dict:
        from services.bottleneck_engine import BottleneckEngine
        analysis = BottleneckEngine().analyze()

        lines = [
            f"🔍 **Warehouse Bottleneck Analysis:**\n",
            f"🚧 **Bottleneck:** {analysis['bottleneck_label']}",
            f"⏱️ **Average time:** {analysis['avg_minutes']:.1f} minutes per task",
            f"📊 **Impact:** {analysis['impact']}\n",
            f"**All stages:**",
        ]

        for stage, info in analysis["stages"].items():
            indicator = "🔴" if stage == analysis["bottleneck_stage"] else "🟢"
            lines.append(
                f"• {indicator} **{info['label']}**: {info['avg_minutes']:.1f} min avg "
                f"({info['active_tasks']} active)"
            )

        lines.append(f"\n**Recommendation:** {analysis['recommendation']}")

        return {
            "message": "\n".join(lines),
            "data": analysis,
            "type": "info"
        }

    def _exception_summary(self) -> dict:
        open_exc = WarehouseException.query.filter(
            WarehouseException.status.in_(["OPEN", "IN_PROGRESS"])
        ).all()

        critical = [e for e in open_exc if e.severity == "CRITICAL"]
        high = [e for e in open_exc if e.severity == "HIGH"]
        medium = [e for e in open_exc if e.severity == "MEDIUM"]

        from datetime import date
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
        resolved_today = WarehouseException.query.filter(
            WarehouseException.status == "RESOLVED",
            WarehouseException.resolved_at >= today_start
        ).count()

        lines = [
            f"⚠️ **Exception Center Summary:**\n",
            f"• 🔴 **{len(critical)}** Critical exceptions requiring immediate action",
            f"• 🟠 **{len(high)}** High severity exceptions",
            f"• 🟡 **{len(medium)}** Medium severity exceptions",
            f"• ✅ **{resolved_today}** exceptions resolved today\n",
        ]

        if critical:
            lines.append("**Critical exceptions:**")
            for e in critical[:3]:
                order_ref = f" | Order: {e.order.order_number}" if e.order else ""
                lines.append(f"• [{e.exception_type}]{order_ref} — {e.description[:80]}...")

        return {
            "message": "\n".join(lines),
            "data": {
                "total_open": len(open_exc),
                "critical": len(critical),
                "high": len(high),
                "medium": len(medium),
                "resolved_today": resolved_today,
            },
            "type": "warning" if critical else "info"
        }

    def _daily_summary(self) -> dict:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        total_orders = Order.query.count()
        pending = Order.query.filter(
            Order.status.in_(["CREATED", "PRIORITIZED", "ALLOCATED", "PICKING", "PACKING", "QUALITY_CHECK"])
        ).count()
        dispatched_today = Order.query.filter(
            Order.status.in_(["DISPATCHED", "COMPLETED"]),
            Order.updated_at >= today_start
        ).count()
        critical = Order.query.filter_by(priority="CRITICAL").filter(
            Order.status.notin_(["DISPATCHED", "COMPLETED"])
        ).count()
        open_exc = WarehouseException.query.filter_by(status="OPEN").count()

        lines = [
            f"📊 **Today's Warehouse Summary:**\n",
            f"• 📋 **{total_orders}** total orders in system",
            f"• ⏳ **{pending}** orders pending fulfillment",
            f"• 🚚 **{dispatched_today}** orders dispatched today",
            f"• 🚨 **{critical}** critical orders in queue",
            f"• ⚠️ **{open_exc}** open exceptions requiring attention\n",
        ]

        fulfillment_rate = round((dispatched_today / max(total_orders, 1)) * 100, 1)
        lines.append(f"**Fulfillment rate today:** {fulfillment_rate}%")

        if critical > 0:
            lines.append(f"\n⚠️ Action required: {critical} critical order(s) need immediate attention.")

        return {
            "message": "\n".join(lines),
            "data": {
                "total_orders": total_orders,
                "pending": pending,
                "dispatched_today": dispatched_today,
                "critical_orders": critical,
                "open_exceptions": open_exc,
                "fulfillment_rate": fulfillment_rate,
            },
            "type": "info"
        }

    def _dispatch_status(self) -> dict:
        ready = Order.query.filter_by(status="READY_TO_DISPATCH").count()
        dispatched = Order.query.filter_by(status="DISPATCHED").count()
        completed = Order.query.filter_by(status="COMPLETED").count()

        ready_orders = Order.query.filter_by(status="READY_TO_DISPATCH").all()

        lines = [
            f"🚚 **Dispatch Status:**\n",
            f"• ✅ **{ready}** order(s) ready to dispatch",
            f"• 📦 **{dispatched}** order(s) currently in transit",
            f"• 🎉 **{completed}** order(s) completed today\n",
        ]

        if ready_orders:
            lines.append("**Ready to dispatch now:**")
            for o in ready_orders[:5]:
                lines.append(f"• **{o.order_number}** — {o.priority} — {o.customer_name}")

        return {
            "message": "\n".join(lines),
            "data": {"ready": ready, "dispatched": dispatched, "completed": completed},
            "type": "success" if ready > 0 else "info"
        }

    def _order_status(self, order_ref: str) -> dict:
        order_ref_clean = order_ref.upper().replace(" ", "-")
        if not order_ref_clean.startswith("ORD"):
            order_ref_clean = "ORD-" + order_ref_clean.lstrip("-")

        order = Order.query.filter(
            Order.order_number.ilike(f"%{order_ref_clean.replace('ORD-', '')}%")
        ).first()

        if not order:
            return {
                "message": f"❌ Could not find order matching '{order_ref}'. Please check the order number.",
                "data": {},
                "type": "error"
            }

        now = datetime.utcnow()
        hours_left = (order.deadline - now).total_seconds() / 3600 if order.deadline else None

        lines = [
            f"📋 **Order {order.order_number}:**\n",
            f"• **Status:** {order.status}",
            f"• **Priority:** {order.priority} (Score: {order.priority_score})",
            f"• **Customer:** {order.customer_name} ({order.customer_type})",
        ]

        if hours_left is not None:
            status_emoji = "🚨" if hours_left < 3 else "⏰"
            lines.append(f"• **Deadline:** {status_emoji} {hours_left:.1f} hours remaining")

        lines.append(f"• **Items:** {len(order.items)} product(s)")
        for item in order.items[:4]:
            if item.product:
                img_url = item.product.image_url or "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=200&q=80"
                lines.append(f"  — ![{item.product.name}]({img_url}) **{item.product.name}** (Qty: {item.quantity}, Allocated: {item.allocated_quantity})")

        open_exc = [e for e in order.exceptions if e.status in ["OPEN", "IN_PROGRESS"]]
        if open_exc:
            lines.append(f"• **⚠️ Open exceptions:** {len(open_exc)}")
            for e in open_exc[:2]:
                lines.append(f"  — {e.exception_type}: {e.description[:60]}...")

        return {
            "message": "\n".join(lines),
            "data": order.to_dict(),
            "type": "warning" if open_exc else "info"
        }

    def _inventory_overview(self) -> dict:
        from database.models import Inventory, Product
        total_units = db.session.query(db.func.sum(Inventory.quantity)).scalar() or 0
        damaged = db.session.query(db.func.sum(Inventory.damaged_quantity)).scalar() or 0
        reserved = db.session.query(db.func.sum(Inventory.reserved_quantity)).scalar() or 0
        available = max(0, total_units - damaged - reserved)

        total_products = Product.query.count()
        out_of_stock = db.session.query(Product).join(Inventory).filter(
            (Inventory.quantity - Inventory.reserved_quantity - Inventory.damaged_quantity) <= 0
        ).distinct().count()

        lines = [
            f"📦 **Inventory Overview:**\n",
            f"• **Total units:** {int(total_units):,}",
            f"• **Available:** {int(available):,}",
            f"• **Reserved:** {int(reserved):,}",
            f"• **Damaged:** {int(damaged):,}",
            f"• **Total products:** {total_products}",
            f"• **Out of stock:** {out_of_stock} products",
        ]

        return {
            "message": "\n".join(lines),
            "data": {
                "total_units": int(total_units),
                "available": int(available),
                "reserved": int(reserved),
                "damaged": int(damaged),
            },
            "type": "info"
        }

    def _help_message(self) -> dict:
        return {
            "message": (
                "👋 **WareMind AI Copilot — I can help with:**\n\n"
                "• **\"Which orders are at risk?\"** — Show orders with deadline or stock issues\n"
                "• **\"What needs replenishment?\"** — List products needing restocking\n"
                "• **\"Show me the bottleneck\"** — Identify slow operational stages\n"
                "• **\"Summarize today's situation\"** — Daily warehouse overview\n"
                "• **\"Show exceptions\"** — List all open warehouse exceptions\n"
                "• **\"Dispatch status\"** — Orders ready to ship\n"
                "• **\"Status of ORD-5001\"** — Details on a specific order\n"
                "• **\"Inventory overview\"** — Stock levels summary\n\n"
                "_All responses are based on live warehouse data. No hallucination._"
            ),
            "data": {},
            "type": "info"
        }

    def _general_response(self, message: str) -> dict:
        return {
            "message": (
                f"🤔 I'm not sure how to answer: *\"{message}\"*\n\n"
                "Try asking me:\n"
                "• Which orders are at risk?\n"
                "• What products need replenishment?\n"
                "• What is the warehouse bottleneck?\n"
                "• Show me today's summary\n\n"
                "Type **\"help\"** to see all available commands."
            ),
            "data": {},
            "type": "info"
        }
