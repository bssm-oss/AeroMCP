# src/aeromcp/dependencies/requester.py
from typing import Annotated

from uncalled_for import Depends

from aeromcp.core.interfaces import FlightSearcher as _FlightSearcher
from aeromcp.infra.requester import AirRequester


def get_requester() -> _FlightSearcher:
    return AirRequester()


FlightSearcher = Annotated[_FlightSearcher, Depends(get_requester)]
