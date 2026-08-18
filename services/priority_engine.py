"""
Priority Engine — Deterministic order priority scoring.

Scoring factors:
  Urgency:          30%
  Deadline:         30%
  Customer Type:    20%
  Order Age:        10%
  Business Value:   10%

Score mapping:
  80-100 → CRITICAL
  60-79  → HIGH
  40-59  → NORMAL
  0-39   → LOW
"""
from datetime import datetime


class PriorityEngine:

    CUSTOMER_TYPE_SCORES = {
        "PREMIUM": 100,
        "WHOLESALE": 70,
        "STANDARD": 40,
    }

    def calculate_priority(self, order) -> tuple:
        """
        Calculate priority score for an order.
        Returns: (score: float, priority: str, reason: str)
        """
        now = datetime.utcnow()

        # ── 1. Urgency Score (30%) ─────────────────────────────────────────────
        urgency_score = self._calc_urgency(order, now)

        # ── 2. Deadline Score (30%) ───────────────────────────────────────────
        deadline_score = self._calc_deadline(order, now)

        # ── 3. Customer Priority Score (20%) ─────────────────────────────────
        customer_score = self.CUSTOMER_TYPE_SCORES.get(
            order.customer_type, 40
        )

        # ── 4. Order Age Score (10%) ─────────────────────────────────────────
        age_score = self._calc_age(order, now)

        # ── 5. Business Value Score (10%) ─────────────────────────────────────
        value_score = self._calc_value(order)

        # ── Weighted Total ────────────────────────────────────────────────────
        total_score = (
            urgency_score * 0.30
            + deadline_score * 0.30
            + customer_score * 0.20
            + age_score * 0.10
            + value_score * 0.10
        )

        # ── Map to Priority Level ─────────────────────────────────────────────
        priority = self._score_to_priority(total_score)

        # ── Build Explanation ─────────────────────────────────────────────────
        reason = self._build_reason(
            total_score, priority, order, now,
            urgency_score, deadline_score, customer_score, age_score, value_score,
        )

        return round(total_score, 1), priority, reason

    def _calc_urgency(self, order, now) -> float:
        """Score urgency based on deadline proximity."""
        if not order.deadline:
            return 30.0  # No deadline = moderate urgency

        hours_left = (order.deadline - now).total_seconds() / 3600

        if hours_left <= 0:
            return 100.0  # Overdue
        elif hours_left <= 2:
            return 95.0
        elif hours_left <= 4:
            return 85.0
        elif hours_left <= 8:
            return 70.0
        elif hours_left <= 12:
            return 55.0
        elif hours_left <= 24:
            return 40.0
        elif hours_left <= 48:
            return 25.0
        else:
            return 10.0

    def _calc_deadline(self, order, now) -> float:
        """Score based on how tight the deadline is."""
        if not order.deadline:
            return 40.0

        hours_left = (order.deadline - now).total_seconds() / 3600

        if hours_left <= 0:
            return 100.0
        elif hours_left <= 1:
            return 100.0
        elif hours_left <= 3:
            return 90.0
        elif hours_left <= 6:
            return 75.0
        elif hours_left <= 12:
            return 60.0
        elif hours_left <= 24:
            return 45.0
        elif hours_left <= 72:
            return 25.0
        else:
            return 10.0

    def _calc_age(self, order, now) -> float:
        """Older orders should get higher priority to prevent starvation."""
        if not order.created_at:
            return 20.0

        age_hours = (now - order.created_at).total_seconds() / 3600

        if age_hours >= 48:
            return 100.0
        elif age_hours >= 24:
            return 80.0
        elif age_hours >= 12:
            return 60.0
        elif age_hours >= 6:
            return 40.0
        elif age_hours >= 2:
            return 25.0
        else:
            return 10.0

    def _calc_value(self, order) -> float:
        """Score based on order value."""
        try:
            value = order.total_value
        except Exception:
            value = 0

        if value >= 2000:
            return 100.0
        elif value >= 1000:
            return 80.0
        elif value >= 500:
            return 60.0
        elif value >= 200:
            return 40.0
        elif value >= 50:
            return 25.0
        else:
            return 10.0

    def _score_to_priority(self, score: float) -> str:
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "NORMAL"
        else:
            return "LOW"

    def _build_reason(
        self, score, priority, order, now,
        urgency, deadline, customer, age, value
    ) -> str:
        hours_left = ""
        if order.deadline:
            h = (order.deadline - now).total_seconds() / 3600
            hours_left = f" (deadline in {h:.1f}h)"

        lines = [
            f"Priority Score: {score:.1f} — {priority}",
            f"",
            f"Scoring breakdown:",
            f"  • Urgency (30%):       {urgency:.0f}/100 pts → {urgency * 0.30:.1f} pts",
            f"  • Deadline (30%):      {deadline:.0f}/100 pts → {deadline * 0.30:.1f} pts",
            f"  • Customer type (20%): {customer:.0f}/100 pts → {customer * 0.20:.1f} pts",
            f"  • Order age (10%):     {age:.0f}/100 pts → {age * 0.10:.1f} pts",
            f"  • Business value (10%): {value:.0f}/100 pts → {value * 0.10:.1f} pts",
            f"",
            f"Customer: {order.customer_type}{hours_left}",
        ]

        if priority == "CRITICAL":
            lines.append(
                f"⚠️  Critical because deadline proximity and/or customer priority demands immediate action."
            )
        elif priority == "HIGH":
            lines.append(f"High priority — process before normal orders.")
        elif priority == "NORMAL":
            lines.append(f"Normal priority — standard processing queue.")
        else:
            lines.append(f"Low priority — process when capacity allows.")

        return "\n".join(lines)
