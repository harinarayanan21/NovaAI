import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

TIMEZONE_ALIASES = {
    "US/Eastern": "America/New_York",
    "US/Central": "America/Chicago",
    "US/Mountain": "America/Denver",
    "US/Pacific": "America/Los_Angeles",
    "US/Alaska": "America/Anchorage",
    "US/Hawaii": "Pacific/Honolulu",
    "EST": "America/New_York",
    "CST": "America/Chicago",
    "MST": "America/Denver",
    "PST": "America/Los_Angeles",
    "GMT": "Europe/London",
    "CET": "Europe/Berlin",
    "IST": "Asia/Kolkata",
    "JST": "Asia/Tokyo",
    "CST_CN": "Asia/Shanghai",
    "AEST": "Australia/Sydney",
    "NZST": "Pacific/Auckland",
}


def _resolve_timezone(name: str) -> ZoneInfo:
    """Resolve timezone name with alias fallback."""
    if name in TIMEZONE_ALIASES:
        name = TIMEZONE_ALIASES[name]
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, KeyError):
        for alias, full in TIMEZONE_ALIASES.items():
            if full == name:
                return ZoneInfo(full)
        raise ZoneInfoNotFoundError(f"No time zone found with key {name}")


@tool
def datetime_tool(timezone_name: str = "UTC") -> str:
    """Get the current date, time, weekday, and timezone. You MUST use the returned values to answer the user - do NOT call this tool again.

    Args:
        timezone_name: Timezone like "UTC", "America/New_York", "America/Los_Angeles", "Europe/London", "Europe/Paris", "Asia/Tokyo", "Asia/Kolkata", "Australia/Sydney". Also accepts short forms like "EST", "PST", "IST", "GMT".

    Returns:
        JSON with current date, time, weekday, timezone, and ISO timestamp.
    """
    try:
        tz = _resolve_timezone(timezone_name)
        now = datetime.now(tz)

        result = {
            "success": True,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": now.strftime("%A"),
            "timezone": timezone_name,
            "iso_timestamp": now.isoformat(),
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
        }

        logger.info("Datetime: %s %s (%s)", result["date"], result["time"], timezone_name)
        return json.dumps(result)
    except ZoneInfoNotFoundError:
        return json.dumps({
            "success": False,
            "error": f"Unknown timezone: {timezone_name}. Use IANA names like 'America/New_York', 'Europe/London', 'Asia/Tokyo'."
        })
    except Exception as e:
        logger.error("Datetime error: %s", str(e))
        return json.dumps({"success": False, "error": str(e)})
