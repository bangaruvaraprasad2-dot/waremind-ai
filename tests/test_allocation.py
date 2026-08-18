"""
Unit tests for Allocation Engine.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class TestAllocationEngine:
    """
    These tests require a Flask app context.
    Run with: python -m pytest tests/test_allocation.py -v
    """

    def test_allocation_import(self):
        """Test that allocation engine can be imported."""
        from services.allocation_engine import AllocationEngine
        engine = AllocationEngine()
        assert engine is not None

    def test_priority_engine_import(self):
        from services.priority_engine import PriorityEngine
        assert PriorityEngine() is not None

    def test_exception_engine_import(self):
        from services.exception_engine import ExceptionEngine
        assert ExceptionEngine() is not None

    def test_replenishment_engine_import(self):
        from services.replenishment_engine import ReplenishmentEngine
        assert ReplenishmentEngine() is not None

    def test_bottleneck_engine_import(self):
        from services.bottleneck_engine import BottleneckEngine
        assert BottleneckEngine() is not None

    def test_copilot_service_import(self):
        from services.copilot_service import CopilotService
        assert CopilotService() is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
