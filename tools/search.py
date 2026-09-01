"""
tools/search.py — Web search tool using Serper.dev.

This module is the agent's "hands" — it reaches out to the live internet
to find what's trending right now. This is the first core concept of
building an agent: TOOL INTEGRATION.

A plain LLM prompt can't see today's internet. By giving the agent a
search tool, it can pull in real-time data to work with.

How it works:
    1. Takes a niche (e.g. "AI and Tech") from the user
    2. Builds a search query focused on today's trends
    3. Calls Serper.dev's Google Search API (both web + news endpoints)
    4. Combines and deduplicates results
    5. Returns a clean list of results (title, snippet, link, source)

Serper.dev API docs: https://serper.dev/
Free tier: 2,500 searches included.
"""

import os
from datetime import date
from urllib.parse import urlparse

import requests

# Serper.dev API endpoints
SERPER_SEARCH_URL = "https://google.serper.dev/search"
SERPER_NEWS_URL = "https://google.serper.dev/news"


def _call_serper(endpoint: str, query: str) -> dict:
    """
    Make a single API call to Serper.dev.

    This is the low-level HTTP call. It sends a POST request with the
    search query and returns the raw JSON response.

    Args:
        endpoint: The Serper API URL to call (search or news).
        query: The search query string.

    Returns:
        The raw JSON response from Serper as a dict.

    Raises:
        requests.exceptions.HTTPError: If the API returns a non-200 status.
    """
    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",
    }
    payload = {
        "q": query,
        "num": 10,  # Request 10 results per query
    }

    response = requests.post(endpoint, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def _extract_domain(url: str) -> str:
    """
    Extract the domain name from a URL for display purposes.

    Example: "https://www.techcrunch.com/2026/09/01/..." -> "techcrunch.com"

    Args:
        url: The full URL string.

    Returns:
        The domain name (with www. stripped off).
    """
    domain = urlparse(url).netloc
    return domain.removeprefix("www.")


def _clean_results(raw_results: list[dict]) -> list[dict]:
    """
    Convert raw Serper API results into a clean, consistent format.

    Serper returns different fields depending on the endpoint (web search
    results have 'snippet', news results have 'snippet' too but sometimes
    use 'date' and 'source'). This function normalizes them all into the
    same shape.

    Args:
        raw_results: List of result dicts directly from the Serper API response.

    Returns:
        List of cleaned dicts, each with: title, snippet, link, source.
    """
    cleaned = []
    for item in raw_results:
        cleaned.append({
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "link": item.get("link", ""),
            "source": item.get("source", _extract_domain(item.get("link", ""))),
        })
    return cleaned


def _deduplicate(results: list[dict]) -> list[dict]:
    """
    Remove duplicate results based on URL.

    Since we search both web and news endpoints, the same article can
    appear in both. This keeps only the first occurrence.

    Args:
        results: List of cleaned result dicts.

    Returns:
        Deduplicated list (order preserved, first occurrence wins).
    """
    seen_links = set()
    unique = []
    for result in results:
        if result["link"] not in seen_links:
            seen_links.add(result["link"])
            unique.append(result)
    return unique


def search_trending(niche: str) -> list[dict]:
    """
    Search the web for today's trending topics in a given niche.

    Uses Serper.dev (a Google Search API wrapper) to find current trends.
    Makes TWO searches to get comprehensive results:
        1. A general web search: "trending {niche} today {date}"
        2. A news search: "{niche} trends" (news endpoint returns only recent articles)

    Results from both are combined, deduplicated, and returned in a
    simplified format. Uses 2 of your Serper API credits per run.

    Args:
        niche: The topic area to search for trends in (e.g. "AI and Tech",
               "Fitness", "Marketing").

    Returns:
        A list of dicts, each containing:
            - title (str): The headline of the search result
            - snippet (str): A brief description/summary
            - link (str): URL to the source article
            - source (str): The domain name of the source

        Returns an empty list if no results are found or the API call fails.
    """
    today = date.today().isoformat()

    # --- Search 1: General web search for trending topics ---
    # This catches blog posts, listicles, and trend roundups
    web_query = f"trending {niche} today {today}"
    try:
        web_response = _call_serper(SERPER_SEARCH_URL, web_query)
    except requests.exceptions.RequestException as e:
        print(f"   Warning: Web search failed: {e}")
        web_response = {}

    web_results = _clean_results(web_response.get("organic", []))

    # --- Search 2: News search for recent articles ---
    # The news endpoint only returns recent articles, so we get fresh results
    news_query = f"{niche} trends"
    try:
        news_response = _call_serper(SERPER_NEWS_URL, news_query)
    except requests.exceptions.RequestException as e:
        print(f"   Warning: News search failed: {e}")
        news_response = {}

    news_results = _clean_results(news_response.get("news", []))

    # --- Combine and deduplicate ---
    # News results go first (more likely to be fresh/trending)
    all_results = _deduplicate(news_results + web_results)

    return all_results
