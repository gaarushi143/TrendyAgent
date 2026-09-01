# Trend-Jacking Social Monitor

An AI agent that finds today's trending topics in your niche and automatically drafts brand-safe social media posts. Built with the Anthropic SDK (Claude) and Serper.dev for live web search.

## What It Does

Give it a niche like "Fitness" or "AI and Tech", and it will:

1. **Search** the live web for today's trending topics in that niche
2. **Filter** results using Claude — picks the best trend that's relevant, fresh, and safe for your brand
3. **Write** 3 social media posts (Twitter/X, LinkedIn, Instagram) tying the trend to your brand
4. **Save** everything to a markdown file you can copy from

## How It Works — Architecture

```
                         ┌─────────────────────┐
                         │    User runs CLI     │
                         │  --niche "Fitness"   │
                         └──────────┬──────────┘
                                    │
                                    v
┌──────────────────────────────────────────────────────────────┐
│                        agent.py                              │
│                    (Orchestrator)                             │
│  Reads brand guidelines, coordinates all steps,              │
│  assembles the final markdown output                         │
└──────┬──────────────────┬───────────────────┬────────────────┘
       │                  │                   │
       v                  v                   v
┌──────────────┐  ┌───────────────┐  ┌───────────────────┐
│ tools/       │  │ tools/        │  │ tools/            │
│ search.py    │  │ writer.py     │  │ writer.py         │
│              │  │ filter_trends │  │ write_posts       │
│ Serper.dev   │  │               │  │                   │
│ Web + News   │  │ Claude picks  │  │ Claude writes     │
│ search       │  │ best trend    │  │ 3 social posts    │
└──────┬───────┘  └───────┬───────┘  └────────┬──────────┘
       │                  │                    │
       v                  v                    v
  Live Google       Structured JSON       Markdown-formatted
  search results    with chosen trend     social media posts
```

## File Structure

```
AgentTrendhacker/
├── agent.py                # Main entry point — orchestrates the full pipeline
├── tools/
│   ├── __init__.py         # Makes tools/ a Python package
│   ├── search.py           # Web search tool (Serper.dev integration)
│   └── writer.py           # Claude-powered filtering and post writing
├── brand_guidelines.md     # Your brand's tone, audience, and topics to avoid
├── output/
│   └── posts_YYYY-MM-DD.md # Generated posts (created on each run)
├── requirements.txt        # Python dependencies
├── .env.example            # Template for API keys
├── .env                    # Your actual API keys (not committed to git)
└── .gitignore              # Keeps .env and output/ out of git
```

### How the files connect

**`agent.py`** is the orchestrator. It:
- Reads your `brand_guidelines.md` file
- Calls `search_trending()` from `tools/search.py` to get live web results
- Passes those results to `filter_trends()` in `tools/writer.py` — Claude picks the best trend
- Passes the chosen trend to `write_posts()` in `tools/writer.py` — Claude drafts 3 posts
- Saves everything to `output/posts_YYYY-MM-DD.md`

**`tools/search.py`** is the agent's "hands" — it reaches the live internet via Serper.dev. It makes two API calls (web search + news search), combines the results, and deduplicates them.

**`tools/writer.py`** is the agent's "brain" — it contains two functions that each call Claude:
- `filter_trends()` — evaluates search results for relevance, freshness, brand safety, and trend-jack potential. Returns a JSON object with the chosen trend.
- `write_posts()` — takes the chosen trend + brand guidelines and writes 3 platform-specific posts.

**`brand_guidelines.md`** tells Claude about your brand — name, tone of voice, target audience, and topics to avoid. Customize this file with your own brand's info.

## Setup

### 1. Clone and install dependencies

```bash
cd AgentTrendhacker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Get your API keys

You need two API keys:

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

### 4. Customize your brand (optional)

Edit `brand_guidelines.md` with your real brand's info. The default file has a sample brand ("Acme Tech Solutions") that works out of the box for testing.

## Usage

```bash
python agent.py --niche "AI and Tech"
```

### Options

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--niche` | Yes | — | The topic area to search for trends (e.g. "Fitness", "Marketing", "Startups") |
| `--brand` | No | `brand_guidelines.md` | Path to a custom brand guidelines file |

### Examples

```bash
# Search for fitness trends
python agent.py --niche "Fitness"

# Search for AI trends
python agent.py --niche "AI and Tech"

# Search for marketing trends with a custom brand file
python agent.py --niche "Marketing" --brand my_company_brand.md
```

### What you'll see

```
🔍 Searching for trending topics in: Fitness...
   Found 17 results. Top 10 trending topics:

   1. AI-Powered Fitness Coaching Leads 2026 Trends
      Source: techcrunch.com

   2. Wearable Tech Revolution in Personal Training
      Source: theverge.com
   ...

🧠 Filtering for the best brand-safe trend...
   Selected: AI-Powered Fitness Coaching Leads 2026 Trends

✍️  Drafting social media posts...

✅ Done! Posts saved to: output/posts_2026-09-01.md
```

### Output file

The generated `output/posts_YYYY-MM-DD.md` contains:

1. **Metadata** — niche, chosen trend, source link, and why it was picked
2. **3 drafted posts** — Twitter/X (280 chars), LinkedIn (professional), Instagram (casual + hashtags)
3. **All trending topics found** — the full top 10 list with sources and links for inspiration

## Concepts Learned

This project teaches three fundamental AI agent concepts:

| Concept | Where in the code | What it means |
|---------|-------------------|---------------|
| **Tool Integration** | `tools/search.py` | Giving an LLM "hands" to use external APIs (Serper.dev) to access live data it can't see on its own |
| **Dynamic Decision Making** | `tools/writer.py` → `filter_trends()` | The LLM reads messy, unstructured internet data and makes a judgment call about what's relevant and safe |
| **Information Routing** | `tools/writer.py` → `write_posts()` | Passing live web data into a secondary workflow — combining the trend with brand guidelines to produce tailored content |

## Cost Per Run

Each run makes:
- **2 Serper API calls** (1 web search + 1 news search) — free tier includes 2,500 searches
- **2 Claude API calls** (1 for filtering + 1 for writing) — uses Claude Sonnet 5, roughly $0.01-0.03 per run depending on result length
