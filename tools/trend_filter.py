"""
tools/trend_filter.py — Two-step trend filtering.

Takes raw search results and produces a structured set of trends through
two Claude calls:

1. cluster_trends() — Reads all search results and extracts the top 10
   DISTINCT trends hidden inside the articles. Each trend gets: what it is,
   why it's trending, hashtags, and surrounding conversation.

2. pick_brand_trend() — Takes those 10 trends + brand guidelines and picks
   the single best one for the brand to trend-jack.

Uses Haiku for cost efficiency. Both calls are logged as training data
for future fine-tuning.
"""

import json
import time

from tools.writer import get_client, get_text
from tools.logger import log_stage

FILTER_MODEL = "claude-haiku-4-5"


def _strip_fences(text: str) -> str:
    """Strip markdown code fences wrapping a JSON response."""
    stripped = text.strip()
    if stripped.startswith("```"):
        first_newline = stripped.index("\n")
        stripped = stripped[first_newline + 1:]
    if stripped.endswith("```"):
        stripped = stripped[: stripped.rfind("```")]
    return stripped.strip()


def _format_results(results):
    """Format search results into a numbered list for the prompt."""
    text = ""
    for i, r in enumerate(results, 1):
        score_info = ""
        if r.get("trend_score"):
            score_info = f"\n  TrendScore: {r['trend_score']}"
        if r.get("query_hit_count", 1) > 1:
            score_info += f" | Cross-query hits: {r['query_hit_count']}"
        if r.get("hours_old") and r["hours_old"] < 72:
            score_info += f" | Age: {r['hours_old']}h"
        text += f"""
Result {i}:
  Title: {r.get('title', '')}
  Snippet: {r.get('snippet', '')}
  Source: {r.get('source', '')}
  Link: {r.get('link', '')}{score_info}
"""
    return text


def cluster_trends(results, niche):
    """
    Extract the top 10 distinct trends from raw search results.

    Many search results are articles ABOUT trends. This function reads
    through all of them and clusters the actual underlying trends —
    deduplicating, grouping related articles, and surfacing what's
    really happening.

    Returns:
        {
            "trends": [
                {
                    "name": "Short trend name (2-5 words)",
                    "core": "What this trend actually is, in 2-3 sentences",
                    "why_trending": "Why it's trending right now",
                    "hashtags": ["#tag1", "#tag2", "#tag3"],
                    "conversation": "What people are saying — the debate, excitement, or controversy",
                    "source_articles": [1, 3, 7]
                }
            ]
        }
    """
    capped = results[:30]
    results_text = _format_results(capped)

    system_prompt = """You are a trend analyst. Your job is to read raw search results and extract
the ACTUAL trending topics hidden inside them.

Many results are articles ABOUT trends (e.g. "Top 10 Fitness Trends for 2026").
Your job is to extract the real underlying trends (e.g. "AI-Powered Fitness Coaching",
"Cold Plunge Recovery") — not repeat article headlines.

Group related articles together. If 3 articles all mention "AI agents" from different
angles, that's ONE trend with 3 source articles.

For each trend, provide:
- name: The actual trend topic in 2-5 words (NOT an article headline)
- core: What this trend actually IS, explained in 2-3 plain sentences. Someone who has
  never heard of this should understand it after reading this.
- why_trending: Why is this blowing up RIGHT NOW? What triggered it? A product launch?
  A viral moment? A cultural shift? Be specific.
- hashtags: 3-5 hashtags people are actually using around this trend
- conversation: What's the surrounding talk? What are people debating, excited about,
  or worried about? What takes are flying around?
- source_articles: Which result numbers (from the search results) relate to this trend

Respond with ONLY a JSON object (no markdown, no code fences):
{
    "trends": [
        {
            "name": "Short Trend Name",
            "core": "What this trend actually is...",
            "why_trending": "Why it's trending right now...",
            "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
            "conversation": "What people are saying about it...",
            "source_articles": [1, 3, 7]
        }
    ]
}

Rules:
- Extract up to 10 DISTINCT trends. Fewer is fine if there aren't 10 real trends.
- Rank by how strongly they're trending (most momentum first)
- Results include a TrendScore (higher = more trending), cross-query hit counts,
  and age in hours. Use these as signals — a high TrendScore or many cross-query
  hits means the topic appeared in multiple independent searches.
- Merge duplicate/overlapping trends into one entry
- Skip generic evergreen content that isn't actually trending
- Skip sponsored content and SEO filler
- Be specific in "why_trending" — vague answers like "it's popular" are useless"""

    user_message = f"""Niche: {niche}

--- SEARCH RESULTS ({len(capped)} total) ---
{results_text}

Extract the distinct trending topics. Respond with JSON only."""

    start = time.time()
    response = get_client().messages.create(
        model=FILTER_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    latency = time.time() - start

    text = get_text(response)
    try:
        parsed = json.loads(_strip_fences(text))
    except json.JSONDecodeError:
        parsed = {"trends": []}

    if not parsed.get("trends"):
        if response.stop_reason == "max_tokens":
            try:
                truncated = _strip_fences(text)
                if not truncated.endswith("}"):
                    last_complete = truncated.rfind("},")
                    if last_complete > 0:
                        truncated = truncated[:last_complete + 1] + "]}"
                        parsed = json.loads(truncated)
            except (json.JSONDecodeError, ValueError):
                pass

    log_stage(
        stage="filter_cluster",
        inputs={"niche": niche, "result_count": len(results)},
        outputs=parsed,
        metadata={"model": FILTER_MODEL, "latency_s": round(latency, 2)},
    )

    return parsed


def pick_brand_trend(clustered_trends, brand_guidelines, niche):
    """
    From the clustered trends, pick the ONE best for the brand.

    Evaluates each trend against:
    - Brand safety (avoids topics in the brand's "Topics to Avoid")
    - Audience fit (matches the brand's target demographic)
    - Trend-jack potential (the brand can join naturally, not forced)
    - Timeliness (trending NOW, not fading)

    Returns:
        {
            "picked_index": 0,
            "trend_title": "The trend name",
            "trend_summary": "1-2 sentence summary",
            "source_url": "Best source link",
            "reasoning": "Why this trend is the best pick",
            "hashtags": ["#tag1", "#tag2"],
            "conversation_hook": "The specific angle the brand should use"
        }
    """
    trends = clustered_trends.get("trends", [])
    if not trends:
        return {
            "trend_title": "No trends found",
            "trend_summary": "Could not extract trends from search results",
            "source_url": "",
            "reasoning": "No valid trends were identified",
            "top_trends": [],
        }

    trends_text = ""
    for i, t in enumerate(trends, 1):
        trends_text += f"""
Trend {i}: {t.get('name', 'Unknown')}
  What it is: {t.get('core', '')}
  Why trending: {t.get('why_trending', '')}
  Hashtags: {', '.join(t.get('hashtags', []))}
  Conversation: {t.get('conversation', '')}
"""

    system_prompt = """You are a brand strategist choosing which trending topic a brand should post about.

You'll receive a list of trending topics (already extracted and analyzed) and the brand's
guidelines. Pick the ONE trend that's the best fit.

Evaluate each trend against:
1. BRAND SAFETY — Read the brand guidelines carefully. Skip anything touching the brand's
   "Topics to Avoid" list. Skip anything negative, controversial, or divisive.
2. AUDIENCE FIT — Does this trend resonate with the brand's target audience?
3. TREND-JACK POTENTIAL — Could the brand join this conversation naturally? The best trends
   are ones where the brand has a genuine connection, not a forced tie-in.
4. TIMELINESS — Is this at peak momentum or already fading?

Respond with ONLY a JSON object (no markdown, no code fences):
{
    "picked_index": 0,
    "trend_title": "The trend name",
    "trend_summary": "1-2 sentence summary combining what it is and why it matters",
    "reasoning": "Why this trend is the best pick for THIS specific brand",
    "conversation_hook": "The specific angle or take the brand should use to join this conversation"
}

picked_index is 0-based (0 = first trend in the list)."""

    user_message = f"""Niche: {niche}

--- BRAND GUIDELINES ---
{brand_guidelines}

--- TRENDING TOPICS ({len(trends)} total) ---
{trends_text}

Pick the best trend for this brand. Respond with JSON only."""

    start = time.time()
    response = get_client().messages.create(
        model=FILTER_MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    latency = time.time() - start

    text = get_text(response)
    try:
        pick = json.loads(_strip_fences(text))
    except json.JSONDecodeError:
        pick = {"picked_index": 0, "trend_title": trends[0].get("name", "Unknown"),
                "trend_summary": trends[0].get("core", ""), "reasoning": "Fallback to top trend"}

    log_stage(
        stage="filter_pick",
        inputs={"niche": niche, "trend_count": len(trends)},
        outputs=pick,
        metadata={"model": FILTER_MODEL, "latency_s": round(latency, 2)},
    )

    return pick


def filter_trends_v2(results, niche, brand_guidelines):
    """
    Two-step trend filter: cluster, then pick.

    This replaces the old single-step filter_trends(). It produces richer
    output — the full list of 10 trends with context, plus the brand pick.

    Returns a dict matching the old filter_trends() signature (trend_title,
    trend_summary, source_url, reasoning, top_trends) plus new fields
    (hashtags, conversation_hook) so the rest of the pipeline works unchanged.
    """
    # Step 1: Cluster search results into distinct trends
    clustered = cluster_trends(results, niche)
    trends = clustered.get("trends", [])

    # Step 2: Pick the best trend for the brand
    pick = pick_brand_trend(clustered, brand_guidelines, niche)

    # Merge the pick with the full trend data for downstream use
    picked_idx = pick.get("picked_index", 0)
    if 0 <= picked_idx < len(trends):
        picked_trend = trends[picked_idx]
    elif trends:
        picked_trend = trends[0]
    else:
        picked_trend = {}

    # Find the best source URL from the original results
    source_articles = picked_trend.get("source_articles", [])
    source_url = ""
    if source_articles and len(results) > 0:
        idx = source_articles[0] - 1
        if 0 <= idx < len(results):
            source_url = results[idx].get("link", "")

    # Build the output dict — compatible with the old format so agent.py
    # and enrich.py work without changes
    result = {
        "trend_title": pick.get("trend_title", picked_trend.get("name", "")),
        "trend_summary": pick.get("trend_summary", picked_trend.get("core", "")),
        "source_url": source_url,
        "reasoning": pick.get("reasoning", ""),
        "conversation_hook": pick.get("conversation_hook", ""),
        "hashtags": picked_trend.get("hashtags", []),
        "top_trends": [
            {
                "name": t.get("name", ""),
                "core": t.get("core", ""),
                "why_trending": t.get("why_trending", ""),
                "hashtags": t.get("hashtags", []),
                "conversation": t.get("conversation", ""),
                "context": t.get("core", ""),
            }
            for t in trends
        ],
    }

    return result
