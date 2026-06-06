# tests/core/test_interfaces.py
from datetime import date
from interpark_mcp.core.interfaces import FlightSearcher
from interpark_mcp.core.models import Flight


def test_flight_searcher_is_abstract():
    import inspect
    assert inspect.isabstract(FlightSearcher)


async def test_concrete_subclass_works():
    class MockSearcher(FlightSearcher):
        async def search_domestic(self, origin, destination, departure_date,
                                   return_date=None, adult=1, child=0, infant=0):
            return []

    searcher = MockSearcher()
    result = await searcher.search_domestic("GMP", "CJU", date(2026, 6, 20))
    assert result == []
