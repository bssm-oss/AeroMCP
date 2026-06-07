# src/aeromcp/core/interfaces.py
from abc import ABC, abstractmethod
from datetime import date
from aeromcp.core.models import Flight


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
        cabin: str | None = None,
        airlines: list[str] | None = None,
    ) -> list[Flight]:
        ...
