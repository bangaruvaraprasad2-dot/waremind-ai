"""
Unit tests for the Bottleneck Engine.
Run: python -m pytest tests/test_bottleneck.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import create_app
from services.bottleneck_engine import BottleneckEngine


@pytest.fixture
def app_context():
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        yield


class TestBottleneckEngine:
    def setup_method(self):
        self.engine = BottleneckEngine()

    def test_analyze_bottleneck(self, app_context):
        """analyze should return current bottleneck stage, avg_minutes, and recommendation."""
        res = self.engine.analyze()
        assert isinstance(res, dict)
        assert "bottleneck_stage" in res
        assert "bottleneck_label" in res
        assert "avg_minutes" in res
        assert "stages" in res
        assert "recommendation" in res
        assert res["bottleneck_stage"] in ["PICKING", "PACKING", "QUALITY_CHECK"]
        assert len(res["recommendation"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
