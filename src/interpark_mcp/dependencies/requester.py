# src/interpark_mcp/dependencies/requester.py
from interpark_mcp.core.interfaces import FlightSearcher
from interpark_mcp.infra.requester import InterparkRequester


def get_requester() -> FlightSearcher:
    return InterparkRequester()
