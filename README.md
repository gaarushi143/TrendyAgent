# TrendHacker

An AI agent that finds today's trending topics in your niche and automatically drafts brand-safe social media posts — then reviews its own work and rewrites anything that doesn't meet quality standards. Built with the Anthropic SDK (Claude), Serper.dev for live web search, and Google Trends for real-time trend data.

## What It Does

Give it a brand name and optional niche like "Fitness" or "AI and Tech", and it will:

1. **Search** the live web + Google Trends for today's trending topics
2. **Filter** results using Claude — picks the best trend that's relevant, fresh, and safe for your brand
3. **Enrich** the chosen trend with deep research — core essence, hashtags, key phrases, triggering events, and trajectory
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
┌──────────────────────────────────────────────────────────────────┐
│                          agent.py                                │
│                      (Orchestrator)                              │
│  Loads brand guidelines, coordinates all steps,                  │
│  runs quality review loop, assembles final output                │
└──┬──────────┬──────────┬──────────┬──────────┬──────────┬───────┘
   │          │          │          │          │          │
   v          v          v          v          v          v
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│search  │ │trends  │ │writer  │ │enrich  │ │writer  │ │writer  │
│.py     │ │.py     │ │.py     │ │.py     │ │.py     │ │.py     │
│        │ │        │ │filter_ │ │enrich_ │ │write_  │ │review_ │
│Serper  │ │Google  │ │trends  │ │trend   │ │posts   │ │posts + │
│Web +   │ │Trends  │ │        │ │        │ │        │ │rewrite │
│News    │ │data    │ │Claude  │ │3 Serper│ │Claude  │ │_post   │
│search  │ │        │ │picks   │ │+Trends │ │writes  │ │        │
│        │ │        │ │best    │ │+Claude │ │3 posts │ │Feedback│
│        │ │        │ │trend   │ │        │ │        │ │Loop    │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
                                                         ↑    │
                                                         │    v
                                                    ┌──────────┐
                                                    │ Rewrite  │
                                                    │ failing  │
                                                    │ posts    │
                                                    │(max 2x)  │
                                                    └──────────┘
```

## File Structure

```
AgentTrendhacker/
├── agent.py                # Main entry point — orchestrates the full pipeline + feedback loop
├── tools/
│   ├── __init__.py         # Makes tools/ a Python package
│   ├── search.py           # Web search tool (Serper.dev + Google Trends)
│   ├── trends.py           # Google Trends integration via pytrends
│   ├── enrich.py           # Deep trend research (Serper + Trends + Claude)
│   └── writer.py           # Claude-powered filtering, writing, reviewing, and rewriting
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
- Calls `search_trending()` from `tools/search.py` to get live web results + Google Trends data
- Passes those results to `filter_trends()` in `tools/writer.py` — Claude picks the best trend
- Passes the chosen trend to `enrich_trend()` in `tools/enrich.py` — deep research with hashtags, key phrases, triggering events, and trajectory
- Passes the enriched trend to `write_posts()` in `tools/writer.py` — Claude drafts 3 posts
- Runs the **feedback loop**: `review_posts()` scores each post, and `rewrite_post()` fixes any that fail (up to 2 retries)
- Saves everything (including quality scores) to `output/posts_YYYY-MM-DD.md`

**`tools/search.py`** is the agent's "hands" — it reaches the live internet via Serper.dev and Google Trends. It makes two Serper API calls (web search + news search), fetches Google Trends trending searches, combines all results, and deduplicates them.

**`tools/trends.py`** wraps Google Trends via the pytrends library. Provides today's trending searches, related queries for a keyword, and interest-over-time data. Free, no API key needed.

**`tools/enrich.py`** is the research layer. After Claude picks a trend, this module runs 3 more Serper searches + Google Trends queries to build a deep trend brief: core essence, hashtags, key phrases, triggering events, and data-driven trajectory.

**`tools/writer.py`** is the agent's "brain" — it contains functions that call Claude:
- `filter_trends()` — evaluates search results for relevance, freshness, brand safety, and trend-jack potential
- `write_posts()` — takes the enriched trend + brand guidelines and writes 3 platform-specific posts
- `review_posts()` — scores each post on 4 criteria against brand guidelines (the observation step)
- `rewrite_post()` — rewrites a single failing post using the reviewer's specific feedback

**`brands/{name}.md`** tells Claude about your brand — name, tone of voice, target audience, and topics to avoid. Add your own brand by creating a new file in the `brands/` directory.

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
| **Dynamic Decision Making** | `tools/writer.py` → `filter_trends()` | The LLM reads messy, unstructured internet data and makes a judgment call about what's relevant and safe |
| **Multi-Step Research** | `tools/enrich.py` → `enrich_trend()` | The agent doesn't just pick a trend — it researches it in depth, combining multiple data sources before acting |
| **Information Routing** | `tools/writer.py` → `write_posts()` | Passing live web data + enriched research into a secondary workflow — combining the trend with brand guidelines to produce tailored content |
| **Observation & Reflection** | `tools/writer.py` → `review_posts()` + `rewrite_post()` | The agent evaluates its own output against quality criteria, identifies weaknesses, and rewrites to improve — completing the perception → reasoning → action → observation loop |

## Cost Per Run

Each run makes:
- **5 Serper API calls** (2 initial search + 3 enrichment) — free tier includes 2,500 searches
- **4-6 Claude API calls** (filtering + enrichment + writing + 1-3 review/rewrite cycles) — uses Claude Sonnet 5, roughly $0.03-0.08 per run
- **3 Google Trends requests** (trending searches + related queries + interest over time) — free, no API key needed
