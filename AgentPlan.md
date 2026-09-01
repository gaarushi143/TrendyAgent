# Trend-Jacking Social Monitor — Implementation Plan

## Context

Build a Python CLI agent that takes a niche (e.g. "Tech", "Fitness"), searches the live web for today's trending topics in that niche, filters results for brand safety and relevance, then drafts 3 social media posts tying the trend to a brand. This is a learning project — first AI agent — focused on three concepts: tool integration, dynamic decision-making, and information routing.

## Architecture

```
User Input (niche) → Serper Search → Claude Filters → Claude Writes → Markdown File
```

Single Python script (`agent.py`) with helper modules. No framework — raw Anthropic SDK + `requests` for Serper.

## Phase 1: Project Scaffolding

**Files to create:**
- `agent.py` — main entry point (CLI via `argparse`)
- `tools/search.py` — Serper.dev web search wrapper
- `tools/writer.py` — Claude-powered filtering + writing
- `brand_guidelines.md` — sample brand guidelines file the agent reads
- `requirements.txt` — `anthropic`, `requests`, `python-dotenv`
- `.env.example` — template for `ANTHROPIC_API_KEY` and `SERPER_API_KEY`
- `.gitignore` — ignore `.env`, `output/`, `__pycache__`

**What happens:** User runs `python agent.py --niche "AI and Tech"` and the script orchestrates the full pipeline.

## Phase 2: Search Tool (Serper Integration)

**File:** `tools/search.py`

- Function `search_trending(niche: str) -> list[dict]` that calls Serper's `/search` endpoint
- Query: `f"trending {niche} today {current_date}"` + a news-focused query
- Returns a clean list of `{title, snippet, link, source}` dicts (top 10 results)
- Uses `requests.post` to `https://google.serper.dev/search` with the API key in headers

**Key learning:** Tool integration — giving the agent hands to reach the live web.

## Phase 3: Filtering Step (Claude Picks the Best Trend)

**File:** `tools/writer.py` — function `filter_trends(results, niche, brand_guidelines)`

- Sends the raw search results + brand guidelines to Claude with a system prompt that instructs it to:
  1. Evaluate each result for relevance to the niche
  2. Filter out anything negative, controversial, or brand-unsafe
  3. Pick the single best trend and explain why in one sentence
- Returns structured output: `{trend_title, trend_summary, source_url, reasoning}`
- Uses `claude-sonnet-5` (cheaper for this filtering step)

**Key learning:** Dynamic decision-making — the LLM reads messy internet data and decides what's relevant.

## Phase 4: Writing Step (Claude Drafts Posts)

**File:** `tools/writer.py` — function `write_posts(trend, brand_guidelines)`

- Takes the chosen trend + brand guidelines
- System prompt instructs Claude to write 3 social media posts:
  - 1 Twitter/X post (≤280 chars)
  - 1 LinkedIn post (professional tone, 2-3 paragraphs)
  - 1 Instagram caption (casual, with hashtag suggestions)
- Each post ties the trending topic to the brand naturally
- Uses `claude-sonnet-5`

**Key learning:** Information routing — passing live web data into a secondary writing workflow.

## Phase 5: Output & Polish

**File:** `agent.py` — orchestration + markdown output

- Wire all steps together in `main()`
- Write results to `output/posts_YYYY-MM-DD.md` with:
  - Header with niche, date, chosen trend
  - The 3 drafted posts clearly formatted
  - Source link for the trend
- Print a summary to terminal showing what was found and written
- Add basic error handling (missing API keys, no results found)

## Sample Brand Guidelines File

`brand_guidelines.md` will ship with example content the user can customize:
- Brand name, industry, tone of voice
- Target audience
- Topics to avoid
- Key messaging pillars

## Verification

1. Set up `.env` with real API keys
2. Run `python agent.py --niche "AI and Tech"`
3. Confirm it searches, filters, and writes to `output/posts_YYYY-MM-DD.md`
4. Run with a different niche (`--niche "Fitness"`) to verify it adapts
5. Check the markdown file has all 3 post formats with the trend clearly tied in
