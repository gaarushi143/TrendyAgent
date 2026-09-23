# Trend-Jacking Social Monitor — Implementation Plan

## Context

Build a Python CLI agent that takes a niche (e.g. "Tech", "Fitness"), searches the live web for today's trending topics in that niche, filters results for brand safety and relevance, then drafts 3 social media posts tying the trend to a brand. This is a learning project — first AI agent — focused on three concepts: tool integration, dynamic decision-making, and information routing.

## Architecture

```
User Input (niche + brand) → Serper + Google Trends Search → Claude Filters → Enrich (Serper + Google Trends + Claude) → Claude Writes → Markdown File
```

Single Python script (`agent.py`) with helper modules. No framework — raw Anthropic SDK + `requests` for Serper + `pytrends` for Google Trends.

## Phase 1: Project Scaffolding

**Files:**
- `agent.py` — main entry point (CLI via `argparse`)
- `tools/search.py` — Serper.dev web search wrapper
- `tools/writer.py` — Claude-powered filtering + writing
- `tools/enrich.py` — deep trend research (Serper + Google Trends + Claude synthesis)
- `tools/trends.py` — Google Trends integration via pytrends (no API key needed)
- `brands/` — directory of brand guideline files (e.g. `brands/acme.md`)
- `brand_guidelines.md` — legacy sample (kept for backwards compatibility)
- `requirements.txt` — `anthropic`, `requests`, `python-dotenv`, `pytrends`
- `.env.example` — template for `ANTHROPIC_API_KEY` and `SERPER_API_KEY`
- `.gitignore` — ignore `.env`, `output/`, `__pycache__`

**What happens:** User runs `python agent.py --niche "AI and Tech" --brand acme` and the script orchestrates the full pipeline. Both `--niche` and `--brand` are optional — omitting niche gives generic top trends, brand defaults to `acme`.

## Phase 2: Search Tools (Serper + Google Trends)

**Files:** `tools/search.py`, `tools/trends.py`

- Function `search_trending(niche: str = None) -> list[dict]` combines three data sources:
  1. Serper web search: `f"trending {niche} today {current_date}"`
  2. Serper news search: `f"{niche} trends"` (recent articles only)
  3. Google Trends: `get_trending_searches()` — today's actual trending queries on Google
- When niche is `None`, searches for generic "top trending topics today" across all categories
- Results are combined (news first, then Google Trends, then web), deduplicated, and returned
- `tools/trends.py` wraps pytrends with three functions:
  - `get_trending_searches()` — today's top trending Google searches (free, no API key)
  - `get_related_queries(keyword)` — top and rising related queries for a keyword
  - `get_interest_over_time(keyword)` — 7-day interest data with trend direction

**Key learning:** Tool integration — combining multiple data sources (Serper for articles, Google Trends for real search volume) gives the agent richer, more reliable input.

## Phase 3: Filtering Step (Claude Picks the Best Trend)

**File:** `tools/writer.py` — function `filter_trends(results, niche, brand_guidelines)`

- Sends the raw search results + brand guidelines to Claude with a system prompt that instructs it to:
  1. Evaluate each result for relevance to the niche
  2. Filter out anything negative, controversial, or brand-unsafe
  3. Pick the single best trend and explain why in one sentence
- Returns structured output: `{trend_title, trend_summary, source_url, reasoning}`
- Uses `claude-sonnet-5` (cheaper for this filtering step)

**Key learning:** Dynamic decision-making — the LLM reads messy internet data and decides what's relevant.

## Phase 4: Enrichment Step (Deep Trend Research)

**Files:** `tools/enrich.py`, `tools/trends.py`

- Takes the chosen trend from the filtering step
- Gathers data from two sources:
  - **Serper** — 3 targeted searches:
    1. Direct search for the trend title (core context)
    2. `"{title} reactions OR opinions OR hashtag"` (social conversation)
    3. `"{title} announced OR launched OR happened"` via news endpoint (triggering events)
  - **Google Trends** — real search data:
    1. `get_related_queries(title)` — top and rising queries people search alongside this trend
    2. `get_interest_over_time(title)` — 7-day interest curve with peak/current scores
- Sends all data (Serper results + Google Trends signals) to Claude with a synthesis prompt
- Trajectory is now data-driven (Google Trends interest curve) instead of guessed from article language
- Hashtags and key phrases are informed by actual rising Google queries
- Returns structured brief: `{core_essence, hashtags, key_phrases, triggering_events, trajectory}`
- Uses `claude-sonnet-5`

**Key learning:** Multi-step reasoning with multiple data sources — the agent combines article context with real search volume data before synthesizing.

## Phase 5: Writing Step (Claude Drafts Posts)

**File:** `tools/writer.py` — function `write_posts(trend, brand_guidelines)`

- Takes the chosen trend (now enriched with deep context) + brand guidelines
- System prompt instructs Claude to write 3 social media posts:
  - 1 Twitter/X post (≤280 chars)
  - 1 LinkedIn post (professional tone, 2-3 paragraphs)
  - 1 Instagram caption (casual, with hashtag suggestions)
- Each post ties the trending topic to the brand naturally
- Uses `claude-sonnet-5`

**Key learning:** Information routing — passing live web data into a secondary writing workflow.

## Phase 6: Output & Polish

**File:** `agent.py` — orchestration + markdown output

- Wire all steps together in `main()`
- Write results to `output/posts_YYYY-MM-DD.md` with:
  - Header with niche, date, chosen trend
  - Trend Brief section (core essence, triggering events, trajectory, key phrases, hashtags)
  - The 3 drafted posts clearly formatted
  - Source link for the trend
- Print a summary to terminal showing what was found and written
- Add basic error handling (missing API keys, no results found)

## Brand Guidelines

Brand files live in `brands/{name}.md` and are selected via `--brand {name}`. Each contains:
- Brand name, industry, tone of voice
- Target audience
- Topics to avoid
- Key messaging pillars

Ships with `brands/acme.md` as the default example.

## Verification

1. Set up `.env` with real API keys
2. Run `python3 agent.py --niche "AI and Tech" --brand acme`
3. Confirm it searches, filters, enriches, and writes to `output/posts_YYYY-MM-DD.md`
4. Run with a different niche (`--niche "Fitness"`) to verify it adapts
5. Run without a niche (`python3 agent.py`) to verify generic trends work
6. Run with a different brand (`--brand nike`) after creating `brands/nike.md`
7. Check the markdown file has the Trend Brief section + all 3 post formats
