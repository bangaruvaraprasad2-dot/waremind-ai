"""
Unit tests for Exception Engine.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import MagicMock, patch
from services.exception_engine import ExceptionEngine


class TestExceptionEngine:
    def setup_method(self):
        self.engine = ExceptionEngine()

    def test_import(self):
        assert self.engine is not None

    def test_resolve_low_stock(self):
        exc = MagicMock()
        exc.exception_type = "LOW_STOCK"
        exc.order_id = None
        exc.product_id = 1

        with patch('services.exception_engine.db'):
            result = self.engine._resolve_low_stock(exc)

        assert result["success"] is True
        assert "replenishment" in result["message"].lower()

    def test_resolve_damaged(self):
        exc = MagicMock()
        exc.exception_type = "DAMAGED_ITEM"
        exc.order_id = None

        with patch('services.exception_engine.db'):
            result = self.engine._resolve_damaged(exc)

        assert result["success"] is True
        assert result["action_taken"] == "QUARANTINE_AND_CLAIM"

    def test_resolve_delay(self):
        exc = MagicMock()
        exc.exception_type = "PICKING_DELAY"
        exc.order_id = None

        with patch('services.exception_engine.Order') as MockOrder:
            MockOrder.query.get.return_value = None
            result = self.engine._resolve_delay(exc)

        assert result["success"] is True

    def test_resolve_quality_failure(self):
        exc = MagicMock()
        exc.exception_type = "QUALITY_FAILURE"
        exc.order_id = None

        with patch('services.exception_engine.Order') as MockOrder:
            MockOrder.query.get.return_value = None
            result = self.engine._resolve_quality_failure(exc)

        assert result["success"] is True

    def test_apply_recommendation_routing(self):
        """Test that apply_recommendation routes to correct handler."""
        for exc_type, expected_action in [
            ("LOW_STOCK", "REPLENISHMENT_ORDERED"),
            ("DAMAGED_ITEM", "QUARANTINE_AND_CLAIM"),
            ("MISSING_ITEM", "ITEM_LOCATED"),
        ]:
            exc = MagicMock()
            exc.exception_type = exc_type
            exc.order_id = None

            with patch('services.exception_engine.db'), \
                 patch('services.exception_engine.Order') as MockOrder:
                MockOrder.query.get.return_value = None
                result = self.engine.apply_recommendation(exc)

            assert result["success"] is True
            assert result["action_taken"] == expected_action


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
