# tests/core/test_di.py
from interpark_mcp.dependencies.requester import get_requester
from interpark_mcp.core.interfaces import FlightSearcher
from interpark_mcp.infra.requester import InterparkRequester


def test_get_requester_returns_flight_searcher():
    requester = get_requester()
    assert isinstance(requester, FlightSearcher)


def test_get_requester_returns_interpark_implementation():
    requester = get_requester()
    assert isinstance(requester, InterparkRequester)
