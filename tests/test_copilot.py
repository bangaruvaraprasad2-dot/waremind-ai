"""
Unit tests for AI Copilot Service.
Run: python -m pytest tests/test_copilot.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import create_app
from services.copilot_service import CopilotService


@pytest.fixture
def app_context():
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        yield


class TestCopilotService:
    def setup_method(self):
        self.copilot = CopilotService()

    def test_help_message_routing(self, app_context):
        """Query containing 'help' should return help overview message."""
        resp = self.copilot.process_query("help")
        assert "message" in resp
        assert "WareMind AI Copilot" in resp["message"]

    def test_replenishment_query_routing(self, app_context):
        """Replenishment query should return message and recommendations payload."""
        resp = self.copilot.process_query("What products need replenishment?")
        assert "message" in resp
        assert "data" in resp
        assert "recommendations" in resp["data"]

    def test_unknown_query_fallback(self, app_context):
        """Unrecognized query should return polite guidance response."""
        resp = self.copilot.process_query("xyz123 random prompt test")
        assert "message" in resp
        assert "I'm not sure" in resp["message"] or "help" in resp["message"].lower()

    def test_response_structure(self, app_context):
        """All responses should be dictionaries containing message, data, and type keys."""
        queries = ["help", "inventory overview", "bottleneck", "unknown command"]
        for q in queries:
            resp = self.copilot.process_query(q)
            assert isinstance(resp, dict)
            assert "message" in resp
            assert "data" in resp
            assert "type" in resp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
