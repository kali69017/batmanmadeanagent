from datetime import date

# NYSE full-closure holidays. Update yearly, or replace with
# pandas_market_calendars if we want this to stop being manual.
MARKET_HOLIDAYS = {
    2026: {
        date(2026, 1, 1),   # New Year's Day
        date(2026, 1, 19),  # MLK Day
        date(2026, 2, 16),  # Presidents Day
        date(2026, 4, 3),   # Good Friday
        date(2026, 5, 25),  # Memorial Day
        date(2026, 6, 19),  # Juneteenth
        date(2026, 7, 3),   # Independence Day (observed)
        date(2026, 9, 7),   # Labor Day
        date(2026, 11, 26), # Thanksgiving
        date(2026, 12, 25), # Christmas
    },
}


def is_market_holiday(d: date) -> bool:
    return d in MARKET_HOLIDAYS.get(d.year, set())
