"""
agent.py — Main entry point for the Trend-Jacking Social Monitor.

This is the orchestrator script that ties the entire pipeline together.
It takes a niche from the user, searches for trending topics, filters them
for brand safety, and generates social media posts.

Usage:
    python agent.py --niche "AI and Tech"
    python agent.py --niche "Fitness" --brand acme
    python agent.py                          # generic top 10 trends, default brand

The pipeline flows in 4 steps:
    1. Read brand guidelines from a markdown file
    2. Search the web for trending topics in the given niche (tools/search.py)
    3. Use Claude to filter results and pick the best brand-safe trend (tools/writer.py)
    4. Use Claude to draft 3 social media posts tying the trend to the brand (tools/writer.py)

Output is saved to: output/posts_YYYY-MM-DD.md
"""

import argparse
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from tools.enrich import enrich_trend
from tools.search import search_trending
from tools.writer import filter_trends, write_posts

# Load environment variables from .env file (API keys live here)
load_dotenv()


def load_brand_guidelines(name: str = "acme") -> str:
    """
    Load brand guidelines by brand name.

    Looks for brands/{name}.md first. Falls back to treating the argument
    as a direct file path for backwards compatibility.
    """
    brand_file = Path("brands") / f"{name}.md"
    if brand_file.exists():
        return brand_file.read_text()
    path = Path(name)
    if path.exists():
        return path.read_text()
    print(f"Error: Brand '{name}' not found.")
    print(f"  Looked for: {brand_file}  and  {path}")
    print(f"  Available brands: {', '.join(p.stem for p in Path('brands').glob('*.md'))}")
    sys.exit(1)


def save_output(content: str, niche: str) -> str:
    """
    Save the final markdown output (trend info + drafted posts) to a file.

    Creates the output/ directory if it doesn't exist. Files are named by
    today's date so you get one file per day.

    Args:
        content: The full markdown string to write.
        niche: The niche that was searched (unused for now, kept for future use).

    Returns:
        The file path where the output was saved.
    """
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    filename = f"posts_{date.today().isoformat()}.md"
    filepath = output_dir / filename
    filepath.write_text(content)
    return str(filepath)


def main():
    """
    Main function — runs the full trend-jacking pipeline.

    Steps:
        1. Parse CLI arguments (--niche is required, --brand is optional)
        2. Validate that API keys are set in the environment
        3. Load brand guidelines from the markdown file
        4. Search for trending topics using Serper.dev
        5. Filter trends using Claude (picks the best, brand-safe trend)
        6. Generate 3 social media posts using Claude
        7. Save everything to a markdown file in output/
    """

    # --- Step 1: Parse command-line arguments ---
    parser = argparse.ArgumentParser(description="Trend-Jacking Social Monitor")
    parser.add_argument("--niche", default=None, help='The niche to search trends for (e.g. "AI and Tech"). Omit for generic top trends.')
    parser.add_argument("--brand", default="acme", help='Brand name — loads brands/{name}.md (e.g. "acme")')
    args = parser.parse_args()

    # --- Step 2: Validate API keys ---
    # Both keys are required: Anthropic for Claude, Serper for web search
    api_key = os.getenv("ANTHROPIC_API_KEY")
    serper_key = os.getenv("SERPER_API_KEY")
    if not api_key or not serper_key:
        print("Error: Set ANTHROPIC_API_KEY and SERPER_API_KEY in your .env file.")
        print("Copy .env.example to .env and fill in your keys.")
        sys.exit(1)

    # --- Step 3: Load brand guidelines ---
    brand_guidelines = load_brand_guidelines(args.brand)

    # --- Step 4: Search for trending topics ---
    niche = args.niche
    if niche:
        print(f"\n🔍 Searching for trending topics in: {niche}...")
    else:
        print(f"\n🔍 Searching for today's top trending topics...")
    results = search_trending(niche)
    if not results:
        print("No trending topics found. Try a different niche.")
        sys.exit(1)
    top_results = results[:10]
    print(f"   Found {len(results)} results. Top 10 trending topics:\n")
    for i, r in enumerate(top_results, 1):
        print(f"   {i}. {r['title']}")
        print(f"      Source: {r['source']}")
        print()

    # --- Step 5: Filter trends with Claude ---
    niche_label = niche or "General"
    print(f"\n🧠 Filtering for the best brand-safe trend...")
    trend = filter_trends(results, niche_label, brand_guidelines)
    print(f'   Selected: {trend["trend_title"]}')

    # --- Step 6: Enrich the chosen trend ---
    print(f"\n🔬 Researching trend in depth...")
    brief = enrich_trend(trend)
    trend.update(brief)
    print(f'   Trajectory: {trend.get("trajectory", "N/A")}')
    if trend.get("hashtags"):
        print(f'   Hashtags: {" ".join(trend["hashtags"][:5])}')

    # --- Step 7: Generate social media posts with Claude ---
    # Claude writes 3 posts (Twitter, LinkedIn, Instagram) that tie the
    # trending topic to the brand naturally
    print(f"\n✍️  Drafting social media posts...")
    posts_markdown = write_posts(trend, brand_guidelines)

    # --- Step 7: Assemble and save the output ---
    # Combine the trend metadata and drafted posts into one markdown file
    output = f"# Trend-Jacking Posts — {date.today().isoformat()}\n\n"
    output += f"**Niche:** {niche_label}\n\n"
    output += f'**Trend:** {trend["trend_title"]}\n\n'
    output += f'**Source:** {trend["source_url"]}\n\n'
    output += f'**Why this trend:** {trend["reasoning"]}\n\n'
    output += "## Trend Brief\n\n"
    output += f'**Core Essence:** {trend.get("core_essence", "N/A")}\n\n'
    output += f'**Triggering Event(s):** {trend.get("triggering_events", "N/A")}\n\n'
    output += f'**Trajectory:** {trend.get("trajectory", "N/A")}\n\n'
    output += f'**Key Phrases:** {", ".join(trend.get("key_phrases", []))}\n\n'
    output += f'**Related Hashtags:** {" ".join(trend.get("hashtags", []))}\n\n'
    output += "---\n\n"
    output += posts_markdown

    # Append the full list of top 10 trending topics at the end
    # so the user can see what else was found and get inspiration
    output += "\n\n---\n\n"
    output += "## All Trending Topics Found\n\n"
    for i, r in enumerate(top_results, 1):
        output += f"{i}. **{r['title']}**\n"
        output += f"   - Source: {r['source']}\n"
        output += f"   - {r['snippet']}\n"
        output += f"   - [Read more]({r['link']})\n\n"

    filepath = save_output(output, niche_label)
    print(f"\n✅ Done! Posts saved to: {filepath}")


if __name__ == "__main__":
    main()
