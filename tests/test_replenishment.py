"""
Unit tests for the Replenishment Engine.
Run: python -m pytest tests/test_replenishment.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import create_app
from services.replenishment_engine import ReplenishmentEngine


@pytest.fixture
def app_context():
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        yield


class TestReplenishmentEngine:
    def setup_method(self):
        self.engine = ReplenishmentEngine()

    def test_get_all_recommendations(self, app_context):
        """get_all_recommendations should return a list of recommendations with risk levels."""
        recs = self.engine.get_all_recommendations()
        assert isinstance(recs, list)
        for r in recs:
            assert "product_id" in r
            assert "sku" in r
            assert "name" in r
            assert "risk" in r
            assert "recommended_quantity" in r
            assert r["risk"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

    def test_get_single_recommendation(self, app_context):
        """get_recommendation for product_id=1 should return detailed stock info."""
        rec = self.engine.get_recommendation(1)
        assert isinstance(rec, dict)
        assert "available_stock" in rec
        assert "reorder_level" in rec
        assert "reason" in rec


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
