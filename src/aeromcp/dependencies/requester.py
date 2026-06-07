# src/aeromcp/dependencies/requester.py
from aeromcp.core.interfaces import FlightSearcher
from aeromcp.infra.requester import AirRequester


def get_requester() -> FlightSearcher:
    return AirRequester()
