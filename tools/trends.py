"""
tools/trends.py — Google Trends data via pytrends.

Provides real trend signals that Serper can't: what's actually trending
on Google right now, related rising queries, and interest-over-time data
for trajectory analysis. Free, no API key needed.
"""

from pytrends.request import TrendReq


def _get_pytrends() -> TrendReq:
    return TrendReq(hl="en-US", tz=360)


def get_trending_searches(country: str = "united_states") -> list[str]:
    """
    Get today's trending searches from Google Trends.

    Returns a list of trending search terms (strings), up to 20.
    These are the actual top trending queries on Google right now.
    """
    try:
        pt = _get_pytrends()
        df = pt.trending_searches(pn=country)
        return df[0].tolist()[:20]
    except Exception:
        return []


def get_related_queries(keyword: str) -> dict:
    """
    Get related queries for a keyword from Google Trends.

    Returns a dict with two lists:
        - top: most searched related queries (established associations)
        - rising: queries with biggest increase in search frequency (emerging)

    Each item is a dict with 'query' and 'value' keys.
    """
    try:
        pt = _get_pytrends()
        pt.build_payload([keyword], timeframe="now 7-d")
        related = pt.related_queries()
        result = {"top": [], "rising": []}

        data = related.get(keyword, {})
        if data.get("top") is not None and not data["top"].empty:
            top_df = data["top"].head(10)
            result["top"] = top_df.to_dict("records")
        if data.get("rising") is not None and not data["rising"].empty:
            rising_df = data["rising"].head(10)
            result["rising"] = rising_df.to_dict("records")

        return result
    except Exception:
        return {"top": [], "rising": []}


def get_interest_over_time(keyword: str) -> dict:
    """
    Get interest-over-time data for a keyword from the past 7 days.

    Returns a dict with:
        - values: list of interest scores (0-100) over the period
        - trend: "rising", "stable", or "declining" based on the data
        - peak: the highest interest score
        - current: the most recent interest score
    """
    try:
        pt = _get_pytrends()
        pt.build_payload([keyword], timeframe="now 7-d")
        df = pt.interest_over_time()

        if df.empty or keyword not in df.columns:
            return {"values": [], "trend": "unknown", "peak": 0, "current": 0}

        values = df[keyword].tolist()
        peak = max(values)
        current = values[-1]

        first_half_avg = sum(values[:len(values)//2]) / max(len(values[:len(values)//2]), 1)
        second_half_avg = sum(values[len(values)//2:]) / max(len(values[len(values)//2:]), 1)

        if second_half_avg > first_half_avg * 1.15:
            trend = "rising"
        elif second_half_avg < first_half_avg * 0.85:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "values": values,
            "trend": trend,
            "peak": peak,
            "current": current,
        }
    except Exception:
        return {"values": [], "trend": "unknown", "peak": 0, "current": 0}
