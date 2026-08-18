"""
Unit tests for the Picking & Route Optimization Engine.
Run: python -m pytest tests/test_picking.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import MagicMock
from services.picking_engine import PickingEngine


class TestPickingEngine:
    def setup_method(self):
        self.engine = PickingEngine()

    def test_optimized_route_structure(self):
        """get_optimized_route should return route, zones_visited, and estimated_time_minutes."""
        order = MagicMock()
        t1 = MagicMock(sequence=1, zone="A", bin_location="A-01", quantity=2, worker_name="James", status="PENDING")
        t2 = MagicMock(sequence=2, zone="C", bin_location="C-05", quantity=1, worker_name="James", status="PENDING")
        order.pick_tasks = [t2, t1]  # unsorted

        result = self.engine.get_optimized_route(order)
        assert "route" in result
        assert "zones_visited" in result
        assert "total_items" in result
        assert "estimated_time_minutes" in result
        assert result["total_items"] == 3
        assert result["zones_visited"] == ["A", "C"]
        assert result["estimated_time_minutes"] == 2 * 3 + 2 * 5  # 16 minutes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
