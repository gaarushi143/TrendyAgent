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


def call_serper(endpoint: str, query: str, country_code: str = None) -> dict:
    """
    Make a single API call to Serper.dev.

    Args:
        endpoint: The Serper API URL to call (search or news).
        query: The search query string.
        country_code: Optional two-letter country code for geographic targeting (e.g. "us", "gb").

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
        "num": 10,
    }
    if country_code:
        payload["gl"] = country_code

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
        title = item.get("title", "").strip()
        snippet = item.get("snippet", "").strip()
        link = item.get("link", "").strip()
        if not title or not link:
            continue
        cleaned.append({
            "title": title,
            "snippet": snippet,
            "link": link,
            "source": item.get("source", extract_domain(link)),
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


def _execute_queries(queries: list[dict], country_code: str = None) -> list[dict]:
    """Run a list of planned search queries via Serper and return combined results."""
    all_results = []
    for q in queries:
        endpoint = SERPER_NEWS_URL if q.get("endpoint") == "news" else SERPER_SEARCH_URL
        try:
            resp = call_serper(endpoint, q["query"], country_code=country_code)
        except requests.exceptions.RequestException as e:
            print(f"   Warning: Query failed ({q.get('source_hint', '?')}): {e}")
            continue
        key = "news" if q.get("endpoint") == "news" else "organic"
        results = clean_results(resp.get(key, []))
        for r in results:
            r["found_by"] = q.get("source_hint", "general")
        all_results.extend(results)
    return deduplicate(all_results)


def search_trending_agentic(niche: str, brand_guidelines: str) -> tuple[list[dict], dict]:
    """
    Agentic search: plan → execute → evaluate → (maybe) search more.

    Uses Claude to generate niche-aware queries, runs them, then evaluates
    whether the results have enough coverage and quality. If not, runs
    follow-up queries (max 1 extra round to stay lightweight).

    Returns:
        (results, metadata) where metadata contains the search plan,
        evaluation, and all data needed for training logs.
    """
    from tools.search_planner import plan_searches, evaluate_results
    from tools.logger import log_stage

    # --- Step 1: Plan ---
    print("   Planning search strategy...")
    search_plan = plan_searches(niche, brand_guidelines)
    print(f"   Audience: {search_plan.get('audience_summary', '?')}")
    geo = search_plan.get("geography", {})
    country_code = geo.get("country_code", "us")
    print(f"   Geography: {country_code} ({geo.get('reasoning', '')})")
    queries = search_plan.get("queries", [])
    print(f"   Planned {len(queries)} queries:")
    for q in queries:
        print(f"     - [{q.get('source_hint', '?')}] {q['query']}")

    log_stage("search_plan", {"niche": niche, "brand_guidelines": brand_guidelines}, search_plan)

    # --- Step 2: Execute ---
    all_results = _execute_queries(queries, country_code)
    print(f"   Got {len(all_results)} results from initial search")

    # --- Step 3: Evaluate ---
    print("   Evaluating result quality...")
    evaluation = evaluate_results(all_results, search_plan, niche)
    print(f"   Sufficient: {evaluation.get('sufficient', '?')}")
    if evaluation.get("verified_trends"):
        print(f"   Verified trends (multi-source):")
        for t in evaluation["verified_trends"]:
            print(f"     - {t['trend_name']} ({t.get('source_count', '?')} sources)")

    log_stage("search_evaluate", {
        "niche": niche,
        "result_count": len(all_results),
        "search_plan_summary": search_plan.get("audience_summary", ""),
    }, evaluation)

    # --- Step 4: Follow-up if needed (max 1 round) ---
    if not evaluation.get("sufficient", True) and evaluation.get("follow_up_queries"):
        gaps = evaluation.get("coverage_gaps", [])
        print(f"   Coverage gaps: {', '.join(gaps)}")
        follow_ups = evaluation["follow_up_queries"]
        print(f"   Running {len(follow_ups)} follow-up queries:")
        for q in follow_ups:
            print(f"     - [{q.get('source_hint', '?')}] {q['query']}")
        follow_up_results = _execute_queries(follow_ups, country_code)
        all_results = deduplicate(all_results + follow_up_results)
        print(f"   Total after follow-up: {len(all_results)}")

    # --- Step 5: Add Google Trends for extra signal ---
    print("   Fetching Google Trends data...")
    trending_terms = get_trending_searches(country_code if country_code == "united_states" else "united_states")
    for term in trending_terms:
        all_results.append({
            "title": term,
            "snippet": f"Trending on Google: {term}",
            "link": f"https://trends.google.com/trends/explore?q={term.replace(' ', '+')}",
            "source": "Google Trends",
            "found_by": "Google Trends",
        })
    all_results = deduplicate(all_results)

    metadata = {
        "search_plan": search_plan,
        "evaluation": evaluation,
        "result_count": len(all_results),
        "country_code": country_code,
    }

    return all_results, metadata
