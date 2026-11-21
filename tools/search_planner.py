"""
tools/search_planner.py — Agentic search planning and evaluation.

Two Claude-powered functions that make the search stage intelligent:

1. plan_searches() — Given a brand + niche, generates targeted search queries
   that hit niche-specific platforms (Billboard for Music, Hacker News for Tech, etc.)
   instead of firing generic "trending {niche} today" queries.

2. evaluate_results() — Looks at what the search found and decides:
   is this enough? are trends verified across sources? any gaps to fill?
   If not sufficient, returns follow-up queries for a second pass.

Together they form the agentic loop: plan → search → evaluate → (maybe search more).
Uses Haiku for cost efficiency — these calls accumulate training data for
future fine-tuning of an open-source model.
"""

import json
from datetime import date

from tools.niche_registry import format_sources_for_prompt
from tools.writer import get_client, get_text

PLANNER_MODEL = "claude-haiku-4-5"


def _strip_fences(text: str) -> str:
    """Strip markdown code fences from a JSON response."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        stripped = "\n".join(lines)
    return stripped


def plan_searches(niche: str, brand_guidelines: str) -> dict:
    """
    Generate a niche-aware search strategy using Claude.

    Reads the brand guidelines to understand the audience, then produces
    targeted search queries that hit niche-specific platforms using site:
    operators where valuable.

    Returns:
        {
            "audience_summary": str,
            "geography": {"country_code": str, "reasoning": str},
            "queries": [{"query": str, "source_hint": str, "rationale": str, "endpoint": str}]
        }
    """
    registry_block = format_sources_for_prompt(niche)

    system_prompt = """You are a trend research strategist. Given a brand's guidelines and a niche,
plan a smart search strategy that finds genuinely trending topics.

You must:
1. Read the brand guidelines to understand the target audience (age, interests, values, geography)
2. Use the NICHE SOURCE REGISTRY (provided below the brand guidelines) as your primary
   source list. It tells you exactly which sites to use site: queries for, which platforms
   need "coverage about" queries, and which aggregator sites proxy closed-platform data.
   You MUST use at least 3 sources from the registry in your queries.
   If no registry is provided, use your own knowledge of the niche.
3. Generate 4-8 targeted search queries, using site: operators for crawlable platforms
   and coverage queries for closed platforms — as the registry specifies.
4. Think about what the AUDIENCE cares about — a Gen Z audience finds trends on TikTok,
   a professional audience on LinkedIn/industry publications

Respond with ONLY a JSON object (no markdown, no code fences):
{
    "audience_summary": "One sentence: who we're finding trends for and what they care about",
    "geography": {
        "country_code": "two-letter country code (e.g. us, gb, in)",
        "reasoning": "Why this geography based on the brand's audience"
    },
    "queries": [
        {
            "query": "The exact search query to run via Google",
            "source_hint": "What platform/source this targets (e.g. 'Billboard', 'general news', 'Reddit')",
            "rationale": "Why this query matters for this brand's audience",
            "endpoint": "search or news"
        }
    ]
}

Rules:
- Use site: operators ONLY for platforms Google can actually crawl well:
  GOOD for site: → reddit.com, billboard.com, techcrunch.com, pitchfork.com, producthunt.com,
                   womenshealthmag.com, news.ycombinator.com, theverge.com
  BAD for site:  → tiktok.com, instagram.com, spotify.com, strava.com, threads.net
  These platforms block Google indexing. Instead, search for COVERAGE ABOUT them:
    - Instead of "site:tiktok.com trending sounds" → "trending on tiktok" sounds viral 2026
    - Instead of "site:spotify.com charts" → "spotify viral chart" OR "spotify top songs" this week
    - Instead of "site:instagram.com fitness" → "trending on instagram" fitness reels
  This finds articles, blogs, and news REPORTING on those platform trends — which Google indexes.
- Include at least 2 general queries and 2 platform-specific queries
- Include at least 1 news-endpoint query (endpoint: "news")
- Queries should find what's trending RIGHT NOW, not evergreen content
- Think about audience overlap: what does THIS brand's audience care about within this niche?
- Maximum 8 queries to keep the search lightweight"""

    user_message = f"""Plan a trend search strategy.

--- BRAND GUIDELINES ---
{brand_guidelines}

--- NICHE ---
{niche}

--- TODAY'S DATE ---
{date.today().isoformat()}

{registry_block}

Generate the search plan. Respond with JSON only."""

    response = get_client().messages.create(
        model=PLANNER_MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    text = get_text(response)
    try:
        return json.loads(_strip_fences(text))
    except json.JSONDecodeError:
        return {
            "audience_summary": "Could not parse search plan",
            "geography": {"country_code": "us", "reasoning": "default"},
            "queries": [
                {"query": f"trending {niche} today {date.today().isoformat()}",
                 "source_hint": "general web", "rationale": "fallback", "endpoint": "search"},
                {"query": f"{niche} trends",
                 "source_hint": "general news", "rationale": "fallback", "endpoint": "news"},
            ],
        }


def evaluate_results(results: list[dict], search_plan: dict, niche: str) -> dict:
    """
    Evaluate search results: enough coverage? verified across sources? any gaps?

    Returns:
        {
            "sufficient": bool,
            "reasoning": str,
            "coverage_gaps": [str],
            "follow_up_queries": [{query, source_hint, rationale, endpoint}],
            "verified_trends": [{trend_name, source_count, sources}]
        }
    """
    results_text = ""
    for i, r in enumerate(results, 1):
        results_text += f"{i}. [{r.get('source', '?')}] {r['title']}\n   {r['snippet']}\n\n"

    targeted_sources = ", ".join(
        q.get("source_hint", "") for q in search_plan.get("queries", [])
    )

    system_prompt = """You are a trend research evaluator. Assess whether search results
provide enough high-quality, verified trending topics.

Evaluate on:
1. FRESHNESS — Are these from the last 48 hours, or recycled/evergreen content?
2. SOURCE DIVERSITY — Do any trends appear across multiple independent sources?
   A trend from one blog post is weak signal. The same story on 3+ sites is strong.
3. RELEVANCE — Are results actually about the niche, or generic/off-topic?
4. COVERAGE — Did we get results from the niche-specific platforms we targeted?
5. ORGANIC — Do any results look like sponsored content or SEO farms?

Respond with ONLY a JSON object (no markdown, no code fences):
{
    "sufficient": true or false,
    "reasoning": "2-3 sentences on the overall quality",
    "coverage_gaps": ["What's missing — e.g. 'no results from Billboard', 'no TikTok trend data'"],
    "follow_up_queries": [
        {
            "query": "A targeted follow-up search",
            "source_hint": "What source this targets",
            "rationale": "Why we need this",
            "endpoint": "search or news"
        }
    ],
    "verified_trends": [
        {
            "trend_name": "Short name of a trend appearing in 2+ independent sources",
            "source_count": 3,
            "sources": ["source1.com", "source2.com", "source3.com"]
        }
    ]
}

Rules:
- follow_up_queries: Only if sufficient is false. Maximum 3 queries.
- verified_trends: Only trends genuinely appearing in multiple INDEPENDENT sources.
  Same article republished on syndication sites doesn't count.
- Be honest about coverage — missing niche platforms is a real gap.
- A search is sufficient if we have at least 3 distinct, relevant, fresh trending topics."""

    user_message = f"""Evaluate these search results for the niche: {niche}

--- WHAT WE WERE LOOKING FOR ---
Audience: {search_plan.get('audience_summary', 'Unknown')}
Targeted sources: {targeted_sources}

--- SEARCH RESULTS ({len(results)} total) ---
{results_text}

Evaluate. Respond with JSON only."""

    response = get_client().messages.create(
        model=PLANNER_MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    text = get_text(response)
    try:
        return json.loads(_strip_fences(text))
    except json.JSONDecodeError:
        return {
            "sufficient": True,
            "reasoning": "Could not parse evaluation — proceeding with available results",
            "coverage_gaps": [],
            "follow_up_queries": [],
            "verified_trends": [],
        }
