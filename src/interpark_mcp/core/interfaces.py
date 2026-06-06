# src/interpark_mcp/core/interfaces.py
from abc import ABC, abstractmethod
from datetime import date
from interpark_mcp.core.models import Flight


class FlightSearcher(ABC):
    @abstractmethod
    async def search_domestic(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date | None = None,
        adult: int = 1,
        child: int = 0,
        infant: int = 0,
    ) -> list[Flight]:
        ...
