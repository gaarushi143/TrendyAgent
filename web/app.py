"""
web/app.py — Flask frontend for TrendHacker.

Wraps the CLI agent pipeline into a web UI with Server-Sent Events
for real-time progress updates, a markdown output editor, and
a quality review dashboard.

Usage:
    cd AgentTrendhacker
    source .venv/bin/activate
    python web/app.py
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request, stream_with_context

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

from tools.enrich import enrich_trend
from tools.search import search_trending, search_trending_agentic
from tools.trend_filter import filter_trends_v2
from tools.writer import (
    replace_post,
    review_posts,
    rewrite_post,
    split_posts,
    write_posts,
)

app = Flask(__name__)


def _load_brand_guidelines(name, file_path=None):
    if file_path:
        fp = Path(file_path)
        if fp.exists():
            return fp.read_text()
        raise FileNotFoundError(f"Brand file not found: {file_path}")
    brand_file = PROJECT_ROOT / "brands" / f"{name}.md"
    if brand_file.exists():
        return brand_file.read_text()
    raise FileNotFoundError(f"Brand '{name}' not found in brands/")


def _sse(event_type, data):
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/healthz")
def healthz():
    # Cheap endpoint the portfolio pings to wake the server from Render's sleep
    return "ok"


@app.route("/api/brands")
def list_brands():
    brands_dir = PROJECT_ROOT / "brands"
    brands = sorted(p.stem for p in brands_dir.glob("*.md"))
    return jsonify(brands)


@app.route("/api/outputs")
def list_outputs():
    output_dir = PROJECT_ROOT / "output"
    if not output_dir.exists():
        return jsonify([])
    files = sorted((f.name for f in output_dir.glob("*.md")), reverse=True)
    return jsonify(list(files))


@app.route("/api/output/<filename>")
def get_output(filename):
    filepath = PROJECT_ROOT / "output" / filename
    if not filepath.exists():
        return jsonify({"error": "Not found"}), 404
    return jsonify({"content": filepath.read_text(), "filename": filename})


@app.route("/api/output/<filename>", methods=["POST"])
def save_output(filename):
    filepath = PROJECT_ROOT / "output" / filename
    data = request.get_json()
    filepath.parent.mkdir(exist_ok=True)
    filepath.write_text(data["content"])
    return jsonify({"ok": True})


@app.route("/api/feedback", methods=["POST"])
def save_feedback():
    data = request.get_json()
    feedback_dir = PROJECT_ROOT / "feedback"
    feedback_dir.mkdir(exist_ok=True)
    filename = f"feedback_{date.today().isoformat()}.md"
    filepath = feedback_dir / filename
    entry = f"\n---\n\n**Date:** {date.today().isoformat()}\n"
    if data.get("output_file"):
        entry += f"**Output:** {data['output_file']}\n"
    entry += f"\n{data.get('feedback', '')}\n"
    with open(filepath, "a") as f:
        f.write(entry)
    return jsonify({"ok": True})


@app.route("/api/run")
def run_agent():
    brand = request.args.get("brand", "").strip()
    niche = request.args.get("niche", "")
    brand_file = request.args.get("brand_file", "")
    brand_url = request.args.get("brand_url", "").strip()
    brand_context = request.args.get("brand_context", "").strip()

    @stream_with_context
    def generate():
        try:
            yield _sse("step", {"step": "loading", "message": "Loading brand guidelines..."})

            brand_guidelines = ""
            loaded_from_file = False

            if brand:
                try:
                    brand_guidelines = _load_brand_guidelines(brand, brand_file or None)
                    loaded_from_file = True
                    yield _sse("log", {"message": f"Loaded brand: {brand}", "type": "success"})
                except FileNotFoundError:
                    brand_guidelines += f"# {brand}\n\n"
                    yield _sse("log", {"message": f"Brand name: {brand} (no guidelines file)", "type": "info"})

            if brand_url and not loaded_from_file:
                brand_guidelines += f"**Website:** {brand_url}\n\n"
                yield _sse("log", {"message": f"Using URL: {brand_url}", "type": "success"})
            elif brand_url and loaded_from_file:
                brand_guidelines += f"\n**Website:** {brand_url}\n\n"

            if brand_context:
                brand_guidelines += f"\n## Brand Context\n\n{brand_context}\n\n"
                yield _sse("log", {"message": "Using provided brand context", "type": "success"})

            if not brand_guidelines.strip():
                brand_guidelines = (
                    "# Brand\n\n"
                    "No specific brand provided. "
                    "Keep posts professional, positive, and engaging. "
                    "Avoid controversial or divisive topics.\n"
                )
                yield _sse("log", {"message": "Running with generic brand defaults", "type": "info"})

            if not loaded_from_file and not brand_context:
                brand_guidelines += (
                    "Use the brand's name and website as context for tone and audience. "
                    "Keep posts professional, positive, and on-brand. "
                    "Avoid controversial or divisive topics.\n"
                )

            niche_val = niche if niche else None
            niche_label = niche or "General"

            yield _sse("step", {"step": "searching", "message": "Searching for trending topics..."})

            if niche_val:
                results, search_metadata = search_trending_agentic(niche_val, brand_guidelines)
                plan = search_metadata.get("search_plan", {})
                evaluation = search_metadata.get("evaluation", {})
                yield _sse("strategy", {
                    "audience": plan.get("audience_summary", ""),
                    "geography": plan.get("geography", {}).get("country_code", "us"),
                    "query_count": len(plan.get("queries", [])),
                })
                yield _sse("queries", [
                    {"query": q["query"], "source": q.get("source_hint", "general"), "endpoint": q.get("endpoint", "search")}
                    for q in plan.get("queries", [])
                ])
                verified = evaluation.get("verified_trends", [])
                if verified:
                    yield _sse("verified", [
                        {"name": v["trend_name"], "sources": v.get("source_count", 1)}
                        for v in verified
                    ])
            else:
                results = search_trending(niche_val)
                search_metadata = {}

            if not results:
                yield _sse("error", {"message": "No trending topics found. Try a different niche."})
                return
            top_results = results[:10]
            yield _sse("trends", [
                {"title": r["title"], "source": r["source"], "snippet": r["snippet"], "link": r["link"]}
                for r in top_results
            ])
            yield _sse("log", {"message": f"Found {len(results)} results", "type": "info"})

            yield _sse("step", {"step": "filtering", "message": "Claude is clustering and picking trends..."})
            trend = filter_trends_v2(results, niche_label, brand_guidelines)
            yield _sse("selected", {
                "trend_title": trend.get("trend_title", ""),
                "trend_summary": trend.get("trend_summary", ""),
                "source_url": trend.get("source_url", ""),
                "reasoning": trend.get("reasoning", ""),
                "top_trends": trend.get("top_trends", []),
            })
            yield _sse("log", {"message": f"Selected: {trend['trend_title']}", "type": "success"})

            yield _sse("step", {"step": "enriching", "message": "Researching trend in depth..."})
            brief = enrich_trend(trend)
            trend.update(brief)
            yield _sse("enrichment", {
                "core_essence": brief.get("core_essence", ""),
                "hashtags": brief.get("hashtags", []),
                "key_phrases": brief.get("key_phrases", []),
                "triggering_events": brief.get("triggering_events", ""),
                "trajectory": brief.get("trajectory", ""),
            })
            yield _sse("log", {"message": f"Trajectory: {trend.get('trajectory', 'N/A')}", "type": "info"})

            yield _sse("step", {"step": "writing", "message": "Drafting social media posts..."})
            posts_markdown = write_posts(trend, brand_guidelines)
            yield _sse("posts", {"markdown": posts_markdown})
            yield _sse("log", {"message": "3 posts drafted", "type": "success"})

            yield _sse("step", {"step": "reviewing", "message": "Quality review in progress..."})
            rewrites_done = 0
            final_review = None

            for attempt in range(3):
                review = review_posts(posts_markdown, brand_guidelines)
                final_review = review
                yield _sse("review", {"scores": review, "attempt": attempt + 1})

                failing = [
                    p for p in ["twitter", "linkedin", "instagram"]
                    if not review.get(p, {}).get("pass", True)
                ]

                if not failing:
                    yield _sse("log", {"message": "All posts passed quality review!", "type": "success"})
                    break

                if attempt >= 2:
                    yield _sse("log", {"message": "Max retries reached — keeping best versions", "type": "warning"})
                    break

                yield _sse("log", {"message": f"Rewriting {len(failing)} post(s)...", "type": "warning"})
                posts_by_platform = split_posts(posts_markdown)
                for platform in failing:
                    original = posts_by_platform.get(platform, "")
                    feedback = review[platform].get("feedback", "")
                    rewritten = rewrite_post(platform, original, feedback, trend, brand_guidelines)
                    posts_markdown = replace_post(posts_markdown, platform, rewritten)
                    rewrites_done += 1
                    yield _sse("rewrite", {"platform": platform, "attempt": attempt + 1})

            yield _sse("step", {"step": "saving", "message": "Assembling output..."})

            output = f"# TrendHacker Posts — {date.today().isoformat()}\n\n"
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

            if final_review:
                output += "## Quality Review\n\n"
                output += "| Platform | Brand Alignment | Platform Fit | Authenticity | Trend Connection | Overall | Status |\n"
                output += "|----------|----------------|--------------|--------------|------------------|---------|--------|\n"
                for platform in ["twitter", "linkedin", "instagram"]:
                    r = final_review.get(platform, {})
                    name = {"twitter": "Twitter/X", "linkedin": "LinkedIn", "instagram": "Instagram"}[platform]
                    ba = r.get("score_brand_alignment", "—")
                    pf = r.get("score_platform_fit", "—")
                    au = r.get("score_authenticity", "—")
                    tc = r.get("score_trend_connection", "—")
                    ov = r.get("overall", "—")
                    st = "Pass" if r.get("pass", True) else "Fail"
                    output += f"| {name} | {ba} | {pf} | {au} | {tc} | {ov} | {st} |\n"
                output += f"\nRewrites needed: {rewrites_done}\n\n"

            output += "---\n\n"
            output += posts_markdown
            output += "\n\n---\n\n"
            output += "## Top Trending Topics\n\n"
            top_trends = trend.get("top_trends", [])
            if top_trends:
                for i, t in enumerate(top_trends, 1):
                    marker = " — *Selected*" if i == 1 else ""
                    output += f"**{i}. {t['name']}**{marker}\n\n"
                    output += f"{t.get('context', '')}\n\n"
                    if i == 1:
                        if trend.get("hashtags"):
                            output += f"Hashtags: {' '.join(trend['hashtags'])}\n\n"
                        if trend.get("trajectory"):
                            output += f"Trajectory: {trend['trajectory']}\n\n"
            else:
                for i, r in enumerate(top_results, 1):
                    output += f"**{i}. {r['title']}**\n\n"
                    output += f"{r['snippet']}\n\n"
                    output += f"*Source: {r['source']}* — [Read more]({r['link']})\n\n"

            output_dir = PROJECT_ROOT / "output"
            output_dir.mkdir(exist_ok=True)
            filename = f"posts_{date.today().isoformat()}.md"
            (output_dir / filename).write_text(output)

            yield _sse("complete", {
                "filename": filename,
                "output": output,
                "review": final_review,
                "rewrites": rewrites_done,
            })

        except Exception as e:
            yield _sse("error", {"message": str(e)})

    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, port=port, threaded=True)
