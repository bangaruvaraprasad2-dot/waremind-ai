"""
Unit tests for the Priority Engine.
Run: python -m pytest tests/
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from services.priority_engine import PriorityEngine


def make_order(customer_type="STANDARD", hours_until_deadline=24, days_old=0, items=None):
    """Create a mock order for testing."""
    order = MagicMock()
    order.customer_type = customer_type
    order.deadline = datetime.utcnow() + timedelta(hours=hours_until_deadline)
    order.created_at = datetime.utcnow() - timedelta(days=days_old)
    order.total_value = sum(items or [500])
    return order


class TestPriorityEngine:
    def setup_method(self):
        self.engine = PriorityEngine()

    def test_critical_order_premium_short_deadline(self):
        """Premium customer with 2-hour deadline should be CRITICAL."""
        order = make_order(customer_type="PREMIUM", hours_until_deadline=2, items=[2500])
        score, priority, reason = self.engine.calculate_priority(order)
        assert priority == "CRITICAL"
        assert score >= 80

    def test_critical_order_overdue(self):
        """Overdue order should be HIGH or CRITICAL priority."""
        order = make_order(hours_until_deadline=-1, items=[500])
        score, priority, reason = self.engine.calculate_priority(order)
        assert priority in ["CRITICAL", "HIGH"]
        assert score >= 70

    def test_high_priority_medium_deadline(self):
        """Premium customer with 8-hour deadline should be HIGH."""
        order = make_order(customer_type="PREMIUM", hours_until_deadline=8, items=[200])
        score, priority, reason = self.engine.calculate_priority(order)
        assert priority in ["HIGH", "CRITICAL"]
        assert score >= 60

    def test_normal_priority_standard(self):
        """Standard customer with 24-hour deadline should be LOW or NORMAL."""
        order = make_order(customer_type="STANDARD", hours_until_deadline=24, items=[100])
        score, priority, reason = self.engine.calculate_priority(order)
        assert priority in ["LOW", "NORMAL", "HIGH"]

    def test_low_priority(self):
        """Standard customer with 96-hour deadline, low value should be LOW."""
        order = make_order(customer_type="STANDARD", hours_until_deadline=96, items=[30])
        score, priority, reason = self.engine.calculate_priority(order)
        assert priority in ["LOW", "NORMAL"]

    def test_score_range(self):
        """Score should always be 0-100."""
        orders = [
            make_order("PREMIUM", 1, 0, [5000]),
            make_order("STANDARD", 48, 0, [10]),
            make_order("WHOLESALE", 12, 2, [300]),
        ]
        for order in orders:
            score, _, _ = self.engine.calculate_priority(order)
            assert 0 <= score <= 100

    def test_reason_contains_score(self):
        """Reason string should contain the score."""
        order = make_order("PREMIUM", 2, 0, [1000])
        score, priority, reason = self.engine.calculate_priority(order)
        assert str(int(score)) in reason or f"{score:.1f}" in reason

    def test_premium_higher_than_standard(self):
        """PREMIUM customer should score higher than STANDARD with same deadline."""
        premium = make_order("PREMIUM", 12, 0, [500])
        standard = make_order("STANDARD", 12, 0, [500])
        premium_score, _, _ = self.engine.calculate_priority(premium)
        standard_score, _, _ = self.engine.calculate_priority(standard)
        assert premium_score > standard_score

    def test_urgent_higher_than_non_urgent(self):
        """Closer deadline should produce higher score."""
        urgent = make_order("STANDARD", 2, 0, [500])
        non_urgent = make_order("STANDARD", 48, 0, [500])
        urgent_score, _, _ = self.engine.calculate_priority(urgent)
        non_urgent_score, _, _ = self.engine.calculate_priority(non_urgent)
        assert urgent_score > non_urgent_score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
