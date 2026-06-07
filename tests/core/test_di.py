# tests/core/test_di.py
from aeromcp.dependencies.requester import get_requester
from aeromcp.core.interfaces import FlightSearcher
from aeromcp.infra.requester import AirRequester


def test_get_requester_returns_flight_searcher():
    requester = get_requester()
    assert isinstance(requester, FlightSearcher)


def test_get_requester_returns_air_implementation():
    requester = get_requester()
    assert isinstance(requester, AirRequester)
