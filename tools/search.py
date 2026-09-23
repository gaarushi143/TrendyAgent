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

from tools.trends import get_trending_searches

# Serper.dev API endpoints
SERPER_SEARCH_URL = "https://google.serper.dev/search"
SERPER_NEWS_URL = "https://google.serper.dev/news"


def call_serper(endpoint: str, query: str) -> dict:
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


def extract_domain(url: str) -> str:
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


def clean_results(raw_results: list[dict]) -> list[dict]:
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
            "source": item.get("source", extract_domain(item.get("link", ""))),
        })
    return cleaned


def deduplicate(results: list[dict]) -> list[dict]:
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


def search_trending(niche: str = None) -> list[dict]:
    """
    Search the web for today's trending topics, optionally filtered by niche.

    When niche is provided, searches for trends in that specific area.
    When niche is None, searches for today's top trending topics across all categories.
    """
    today = date.today().isoformat()

    if niche:
        web_query = f"trending {niche} today {today}"
        news_query = f"{niche} trends"
    else:
        web_query = f"top trending topics today {today}"
        news_query = "trending today"

    try:
        web_response = call_serper(SERPER_SEARCH_URL, web_query)
    except requests.exceptions.RequestException as e:
        print(f"   Warning: Web search failed: {e}")
        web_response = {}

    web_results = clean_results(web_response.get("organic", []))

    try:
        news_response = call_serper(SERPER_NEWS_URL, news_query)
    except requests.exceptions.RequestException as e:
        print(f"   Warning: News search failed: {e}")
        news_response = {}

    news_results = clean_results(news_response.get("news", []))

    # --- Google Trends: today's actual trending searches ---
    print("   Fetching Google Trends data...")
    trending_terms = get_trending_searches()
    trends_results = []
    for term in trending_terms:
        trends_results.append({
            "title": term,
            "snippet": f"Trending on Google: {term}",
            "link": f"https://trends.google.com/trends/explore?q={term.replace(' ', '+')}",
            "source": "Google Trends",
        })

    # News first (freshest), then Google Trends (real signal), then web results
    all_results = deduplicate(news_results + trends_results + web_results)

    return all_results
