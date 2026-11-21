# TrendHacker

An AI agent that finds today's trending topics in your niche and automatically drafts brand-safe social media posts — then reviews its own work and rewrites anything that doesn't meet quality standards. Built with the Anthropic SDK (Claude), Serper.dev for live web search, and Google Trends for real-time trend data.

## What It Does

Give it a brand name and optional niche like "Fitness" or "AI and Tech", and it will:

1. **Search** using an agentic loop — plans niche-aware queries, executes them, evaluates coverage, and runs follow-ups if needed
2. **Filter** results using Claude — picks the best trend that's relevant, fresh, and safe for your brand
3. **Enrich** the chosen trend with deep research — core essence, hashtags, key phrases, triggering events, trajectory, key voices, and competitor angle
4. **Write** 3 social media posts (Twitter/X, LinkedIn, Instagram) tying the trend to your brand
5. **Review** each post against brand guidelines — scores on brand alignment, platform fit, authenticity, and trend connection
6. **Rewrite** any posts that fail quality checks (up to 2 retries per run)
7. **Save** everything to a markdown file with quality scores included

## How It Works — Architecture

```
                          ┌─────────────────────────┐
                          │      User runs CLI       │
                          │ --brand acme             │
                          │ --niche "Fitness"        │
                          └───────────┬─────────────┘
                                      │
                                      v
┌──────────────────────────────────────────────────────────────────────┐
│                           agent.py (Orchestrator)                    │
│  Loads brand guidelines, coordinates all steps,                      │
│  runs quality review loop, logs training data, assembles output      │
└──┬──────────────┬──────────┬──────────┬──────────┬──────────┬───────┘
   │              │          │          │          │          │
   v              v          v          v          v          v
┌──────────┐  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ AGENTIC  │  │trends  │ │writer  │ │enrich  │ │writer  │ │writer  │
│ SEARCH   │  │.py     │ │.py     │ │.py     │ │.py     │ │.py     │
│          │  │        │ │filter_ │ │4 Serper│ │write_  │ │review_ │
│ planner  │  │Google  │ │trends  │ │+Trends │ │posts   │ │posts + │
│ ↓        │  │Trends  │ │        │ │+Claude │ │        │ │rewrite │
│ executor │  │data    │ │Claude  │ │+voices │ │Claude  │ │_post   │
│ ↓        │  │        │ │picks   │ │+compe- │ │writes  │ │        │
│ evaluator│  │        │ │best    │ │titors  │ │3 posts │ │Feedback│
│ ↓        │  │        │ │trend   │ │        │ │        │ │Loop    │
│ follow-up│  │        │ │        │ │        │ │        │ │        │
│ (if gaps)│  │        │ │        │ │        │ │        │ │        │
└──────────┘  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
   ↑                                                        ↑    │
   │ niche_registry.py                                      │    v
   │ 24 niches × sources                               ┌──────────┐
   │ + logger.py (JSONL)                                │ Rewrite  │
                                                        │ failing  │
                                                        │ posts    │
                                                        │(max 2x)  │
                                                        └──────────┘
```

## File Structure

```
AgentTrendhacker/
├── agent.py                # CLI entry point — orchestrates the full pipeline + feedback loop
├── web/
│   ├── app.py              # Flask web server with SSE streaming
│   └── templates/
│       └── index.html      # Dashboard UI (dark theme, brand colors)
├── tools/
│   ├── __init__.py         # Makes tools/ a Python package
│   ├── search.py           # Web search tool (Serper.dev + Google Trends) + agentic search loop
│   ├── search_planner.py   # Claude-powered query planning and result evaluation
│   ├── niche_registry.py   # Source registry — 24 niches with crawlable, closed, and aggregator sources
│   ├── trends.py           # Google Trends integration via pytrends
│   ├── enrich.py           # Deep trend research (Serper + Trends + Claude) + influencer discovery
│   ├── logger.py           # Training data logger — JSONL output for future fine-tuning
│   └── writer.py           # Claude-powered filtering, writing, reviewing, and rewriting
├── evals/
│   ├── __init__.py
│   ├── fixtures.py         # 13 test fixtures across 7 niches for eval
│   └── search_eval.py      # Heuristic + LLM-as-judge evals for search quality
├── brands/
│   ├── acme.md             # Sample brand guidelines
│   └── aerie.md            # Example second brand
├── output/
│   └── posts_YYYY-MM-DD.md # Generated posts with quality scores (created on each run)
├── requirements.txt        # Python dependencies
├── .env.example            # Template for API keys
├── .env                    # Your actual API keys (not committed to git)
└── .gitignore              # Keeps .env and output/ out of git
```

### How the files connect

**`agent.py`** is the orchestrator. It:
- Loads your brand guidelines from `brands/{name}.md` or a custom file path via `--brand-file`
- When a niche is provided, calls `search_trending_agentic()` — the full plan → execute → evaluate → follow-up loop. Without a niche, falls back to `search_trending()` for generic trends
- Passes results to `filter_trends()` in `tools/writer.py` — Claude picks the best trend
- Passes the chosen trend to `enrich_trend()` in `tools/enrich.py` — deep research with hashtags, key phrases, triggering events, trajectory, key voices, and competitor angle
- Passes the enriched trend to `write_posts()` in `tools/writer.py` — Claude drafts 3 posts
- Runs the **feedback loop**: `review_posts()` scores each post, and `rewrite_post()` fixes any that fail (up to 2 retries)
- Logs all LLM calls to `logs/` as JSONL training data
- Saves everything (including quality scores) to `output/posts_YYYY-MM-DD.md`

**`tools/search.py`** is the agent's "hands" — it reaches the live internet via Serper.dev and Google Trends. When a niche is provided, it runs the **agentic search loop** via `search_trending_agentic()`:

1. **Plan** — `search_planner.py` uses Claude Haiku to generate 4-8 niche-aware queries with `site:` operators for crawlable platforms and coverage queries for closed platforms
2. **Execute** — runs all planned queries via Serper, tagging each result with the source that found it
3. **Evaluate** — Claude judges whether results have enough coverage, freshness, and source diversity
4. **Follow-up** — if the evaluator finds gaps, runs up to 3 additional targeted queries
5. **Enrich with Trends** — adds Google Trends data for extra signal

Without a niche, it falls back to the simpler `search_trending()` with generic queries.

**`tools/search_planner.py`** contains two Claude-powered functions that make the search intelligent:
- `plan_searches()` reads the brand guidelines and niche source registry to generate targeted queries. It understands which platforms are Google-crawlable (use `site:` queries) vs closed (use "coverage about" queries).
- `evaluate_results()` judges coverage quality and returns follow-up queries if results are insufficient.

**`tools/niche_registry.py`** maps 24 niches to their best trend sources, categorized by access method:
- **Crawlable** — Google-indexed publications that work with `site:` queries (e.g. Billboard, TechCrunch, Allure)
- **Closed** — platforms that block Google crawling, with pre-written coverage query templates (e.g. TikTok, Spotify, Steam, Strava)
- **Aggregators** — proxy sites that surface data from closed platforms (e.g. SteamDB, Chartmetric, CoinGecko)
- **Subreddits** — niche-specific Reddit communities

Supported niches: Music, AI and Tech, Fitness, Food and Dining, Gaming, Beauty and Skincare, Travel and Outdoors, Finance and Investing, Fashion, Education, Health and Wellness, Parenting, Pets, Real Estate, Automotive, Sports, Entertainment, Sustainability, Home and Interior Design, Photography, Podcasting, E-commerce, Mental Health, Crypto and Web3. The alias map (82 entries) means you can pass casual names like "crypto", "ev", or "home decor".

**`tools/logger.py`** logs every LLM input/output pair as JSONL to `logs/training_data_YYYY-MM-DD.jsonl`. Each agent run appends to the day's file, building up training data for future fine-tuning of an open-source model.

**`tools/trends.py`** wraps Google Trends via the pytrends library. Provides today's trending searches, related queries for a keyword, and interest-over-time data. Free, no API key needed.

**`tools/enrich.py`** is the research layer. After Claude picks a trend, this module runs 4 Serper searches (core context, social conversation, triggering events, and influencer/creator discovery) + Google Trends queries to build a deep trend brief: core essence, hashtags, key phrases, triggering events, trajectory, key voices, and competitor angle.

**`tools/writer.py`** is the agent's "brain" — it contains functions that call Claude:
- `filter_trends()` — evaluates search results for relevance, freshness, brand safety, and trend-jack potential
- `write_posts()` — takes the enriched trend + brand guidelines and writes 3 platform-specific posts
- `review_posts()` — scores each post on 4 criteria against brand guidelines (the observation step)
- `rewrite_post()` — rewrites a single failing post using the reviewer's specific feedback

**`brands/{name}.md`** tells Claude about your brand — name, tone of voice, target audience, and topics to avoid. Add your own brand by creating a new file in the `brands/` directory.

**`web/app.py`** is the Flask web server. It wraps the same pipeline as `agent.py` but streams progress via Server-Sent Events (SSE) so the dashboard can show each step in real time.

**`web/templates/index.html`** is the dashboard UI — a single-page app with the TrendHacker brand design (dark theme, Bricolage Grotesque typography, violet/yellow accent colors). Features:
- **Pipeline tracker** — animated step indicators (Search → Filter → Enrich → Write → Review → Done)
- **Agent console** — terminal-style log of every action the agent takes
- **Agent intelligence panel** — shows the Perceive → Reason → Act → Observe loop diagram and quality review scores with per-criteria bar charts
- **Markdown editor/viewer** — toggle between rendered preview and raw markdown editing, with save back to file
- **Past runs browser** — click any previous output file to view or edit it

## Web Dashboard

The web dashboard lets you run TrendHacker from a browser with real-time visualization of the agent pipeline.

```bash
source .venv/bin/activate
python3 web/app.py
```

Then open [http://localhost:5001](http://localhost:5001). Select a brand, optionally enter a niche, and click **Run Agent**.

The dashboard streams every step as it happens — you'll see the pipeline progress bar light up, the agent console log each decision, and the quality scores appear after the review step. When a post fails review and gets rewritten, the feedback loop indicator activates.

## Setup

### 1. Clone and install dependencies

```bash
cd AgentTrendhacker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Get your API keys

You need two API keys (Google Trends requires no key):

| Service | What it does | Where to get it |
|---------|-------------|-----------------|
| **Anthropic** | Powers Claude (the AI brain) | [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) |
| **Serper.dev** | Google Search API (live web search) | [serper.dev](https://serper.dev) — free tier includes 2,500 searches |

### 3. Configure your `.env` file

```bash
cp .env.example .env
nano .env
```

Fill in your keys:

```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
SERPER_API_KEY=xxxxx
```

If you have an identity-linked Anthropic API key, you also need your workspace ID (find it at [console.anthropic.com/settings/workspaces](https://console.anthropic.com/settings/workspaces)):

```
ANTHROPIC_WORKSPACE_ID=wrkspc_xxxxx
```

### 4. Add your brand

Create a markdown file in `brands/` with your brand's info. The default `brands/acme.md` works out of the box for testing.

```bash
# Use the sample brand
python3 agent.py --brand acme --niche "AI and Tech"

# Or create your own
cp brands/acme.md brands/mybrand.md
# Edit brands/mybrand.md with your brand's info
python3 agent.py --brand mybrand --niche "Fitness"
```

## Usage

```bash
source .venv/bin/activate
python3 agent.py --brand acme --niche "AI and Tech"
```

### Options

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--brand` | **Yes** | — | Brand name — loads `brands/{name}.md` |
| `--brand-file` | No | — | Direct path to a brand guidelines `.md` file (overrides the `brands/` directory lookup) |
| `--niche` | No | Generic top trends | The topic area to search for trends (e.g. "Fitness", "Marketing", "Startups") |

### Examples

```bash
# Search for AI trends with acme brand (brand is required)
python3 agent.py --brand acme --niche "AI and Tech"

# Get today's top generic trends for a brand
python3 agent.py --brand acme

# Music trends for a different brand
python3 agent.py --brand aerie --niche "Music"

# Use a custom brand guidelines file from anywhere
python3 agent.py --brand myco --brand-file ~/Documents/myco_guidelines.md
```

### What you'll see

```
🔍 Searching for trending topics in: Fitness...
   Fetching Google Trends data...
   Found 25 results. Top 10 trending topics:

   1. AI-Powered Fitness Coaching Leads 2026 Trends
      Source: techcrunch.com

   2. Wearable Tech Revolution in Personal Training
      Source: theverge.com
   ...

🧠 Filtering for the best brand-safe trend...
   Selected: AI-Powered Fitness Coaching Leads 2026 Trends

🔬 Researching trend in depth...
   Trajectory: rising — search interest up 40% in the past week
   Hashtags: #FitTech #AIFitness #WearableTech #FitnessCoach #HealthTech

✍️  Drafting social media posts...

🔍 Reviewing post quality...
   Twitter     : 8.5/10 PASS
   Linkedin    : 5.5/10 FAIL
   Instagram   : 7.2/10 PASS
   Rewriting 1 post(s)...
   Twitter     : 8.5/10 PASS
   Linkedin    : 7.8/10 PASS
   Instagram   : 7.2/10 PASS
   All posts passed quality review!

✅ Done! Posts saved to: output/posts_2026-10-21.md
```

### Output file

The generated `output/posts_YYYY-MM-DD.md` contains:

1. **Metadata** — niche, chosen trend, source link, and why it was picked
2. **Trend Brief** — core essence, triggering events, trajectory, key phrases, and related hashtags
3. **Quality Review** — scores table for each post on 4 criteria, plus how many rewrites were needed
4. **3 drafted posts** — Twitter/X (280 chars), LinkedIn (professional), Instagram (casual + hashtags)
5. **All trending topics found** — the full top 10 list with sources and links for inspiration

## Concepts Learned

This project teaches five fundamental AI agent concepts:

| Concept | Where in the code | What it means |
|---------|-------------------|---------------|
| **Tool Integration** | `tools/search.py`, `tools/trends.py` | Giving an LLM "hands" to use external APIs (Serper.dev, Google Trends) to access live data it can't see on its own |
| **Agentic Loop** | `tools/search_planner.py`, `tools/search.py` | The agent plans its own queries, evaluates results, and decides whether to search more — a plan → execute → evaluate → (maybe) act again loop |
| **Dynamic Decision Making** | `tools/writer.py` → `filter_trends()` | The LLM reads messy, unstructured internet data and makes a judgment call about what's relevant and safe |
| **Multi-Step Research** | `tools/enrich.py` → `enrich_trend()` | The agent doesn't just pick a trend — it researches it in depth, combining multiple data sources before acting |
| **Information Routing** | `tools/writer.py` → `write_posts()` | Passing live web data + enriched research into a secondary workflow — combining the trend with brand guidelines to produce tailored content |
| **Observation & Reflection** | `tools/writer.py` → `review_posts()` + `rewrite_post()` | The agent evaluates its own output against quality criteria, identifies weaknesses, and rewrites to improve |
| **Evals** | `evals/search_eval.py`, `evals/fixtures.py` | Heuristic checks (structural correctness) + LLM-as-judge scoring (quality judgment) to measure and improve agent behavior |
| **Training Data Logging** | `tools/logger.py` | Every LLM call is logged as JSONL for future fine-tuning of an open-source model |

## Cost Per Run

Each run makes:
- **8-15 Serper API calls** (4-8 planned queries + up to 3 follow-ups + 4 enrichment) — free tier includes 2,500 searches
- **6-8 Claude API calls** (search planning with Haiku + evaluation + filtering + enrichment + writing + 1-3 review/rewrite cycles with Sonnet) — roughly $0.05-0.12 per run
- **3 Google Trends requests** (trending searches + related queries + interest over time) — free, no API key needed

## Evals

The eval suite measures search quality across brands and niches:

```bash
# Heuristic checks only (no API calls besides Haiku for planning)
python3 -m evals.search_eval

# Add LLM-as-judge scoring
python3 -m evals.search_eval --llm-judge

# Full eval with live Serper calls
python3 -m evals.search_eval --llm-judge --live
```

**Heuristic checks** (8 structural checks): query count, site: queries, news queries, geography, audience demographics, niche source coverage, query rationale, general queries. Plus 4 result-quality checks when running live.

**LLM-as-judge** scores on: niche awareness, audience fit, freshness focus, diversity, and practicality (1-10 each).

Results are saved to `evals/results/` (gitignored). Training data accumulates in `logs/` (also gitignored).
