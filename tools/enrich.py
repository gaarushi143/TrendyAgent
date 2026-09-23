"""
tools/enrich.py — Deep trend research using Serper + Claude.

After the agent picks the best trend, this module researches it further:
runs 3 targeted searches to gather context, then has Claude synthesize
everything into a structured trend brief with hashtags, key phrases,
triggering events, and trajectory.
"""

import json

import requests

from tools.search import call_serper, clean_results, SERPER_SEARCH_URL, SERPER_NEWS_URL
from tools.trends import get_related_queries, get_interest_over_time
from tools.writer import get_client, get_text, MODEL


def _format_results(results: list[dict], label: str) -> str:
    if not results:
        return f"--- {label} ---\n(no results)\n"
    text = f"--- {label} ---\n"
    for i, r in enumerate(results, 1):
        text += f"  {i}. {r['title']}\n"
        text += f"     {r['snippet']}\n"
        text += f"     Source: {r['source']}\n\n"
    return text


def enrich_trend(trend: dict) -> dict:
    """
    Research a chosen trend in depth and return a structured brief.

    Runs 3 Serper searches focused on the trend, then has Claude
    synthesize the results into core essence, hashtags, key phrases,
    triggering events, and trajectory.
    """
    title = trend["trend_title"]

    # Search 1: Core context
    try:
        resp1 = call_serper(SERPER_SEARCH_URL, title)
    except requests.exceptions.RequestException:
        resp1 = {}
    core_results = clean_results(resp1.get("organic", []))

    # Search 2: Social conversation and hashtags
    try:
        resp2 = call_serper(SERPER_SEARCH_URL, f"{title} reactions OR opinions OR hashtag")
    except requests.exceptions.RequestException:
        resp2 = {}
    social_results = clean_results(resp2.get("organic", []))

    # Search 3: Triggering events (news endpoint)
    try:
        resp3 = call_serper(SERPER_NEWS_URL, f"{title} announced OR launched OR happened")
    except requests.exceptions.RequestException:
        resp3 = {}
    event_results = clean_results(resp3.get("news", []))

    # Google Trends: related queries and interest data
    related = get_related_queries(title)
    interest = get_interest_over_time(title)

    results_text = _format_results(core_results, "Core context")
    results_text += _format_results(social_results, "Social conversation")
    results_text += _format_results(event_results, "Background / triggering events")

    # Add Google Trends data
    results_text += "\n--- Google Trends Data ---\n"
    if related["rising"]:
        results_text += "Rising related queries:\n"
        for q in related["rising"]:
            results_text += f"  - {q['query']} (growth: {q['value']})\n"
    if related["top"]:
        results_text += "Top related queries:\n"
        for q in related["top"]:
            results_text += f"  - {q['query']} (score: {q['value']})\n"
    if interest["values"]:
        results_text += f"Interest trend (past 7 days): {interest['trend']}\n"
        results_text += f"  Peak interest: {interest['peak']}/100, Current: {interest['current']}/100\n"
    else:
        results_text += "No Google Trends interest data available for this topic.\n"

    system_prompt = """You are a trend researcher. Given raw search results about a trending topic,
synthesize them into a structured trend brief. Read every result carefully
and extract real information — don't make things up or guess.

Respond with ONLY a JSON object (no markdown, no code fences) in this exact format:
{
    "core_essence": "2-3 sentences explaining what this trend actually is at its core",
    "hashtags": ["#Hashtag1", "#Hashtag2"],
    "key_phrases": ["phrase one", "phrase two"],
    "triggering_events": "1-2 sentences about what specific event(s) sparked this trend",
    "trajectory": "rising | peaking | fading — pick one, then a 1-sentence explanation"
}

Rules:
- hashtags: 5-8 hashtags people are actually using. Mix broad and specific.
  Use the Google Trends rising queries to inform hashtag choices.
- key_phrases: 5-8 key terms most associated with this trend. Pull from
  both the search results AND the Google Trends related queries.
- trajectory: Use the Google Trends interest data (rising/stable/declining,
  peak vs current scores) as your primary signal. Supplement with language
  from the articles. This should be data-driven, not a guess.
- If the results don't give you enough info for a field, say so honestly."""

    user_message = f"""Trend: {title}
Summary: {trend.get('trend_summary', '')}

{results_text}

Synthesize these into a trend brief. Respond with JSON only."""

    response = get_client().messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    response_text = get_text(response)

    # Strip markdown code fences if Claude wraps the JSON
    stripped = response_text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        stripped = "\n".join(lines)

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return {
            "core_essence": "Could not enrich — raw response: " + response_text[:200],
            "hashtags": [],
            "key_phrases": [],
            "triggering_events": "Unknown",
            "trajectory": "Unknown",
        }
