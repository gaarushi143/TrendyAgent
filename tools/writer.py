"""
tools/writer.py — Claude-powered trend filtering and post writing.

This module contains the agent's "brain" — it uses Claude to make decisions
and generate content. It demonstrates two core agent concepts:

1. DYNAMIC DECISION MAKING (filter_trends):
   The LLM reads messy, unstructured internet data and decides what's
   relevant and safe for the brand. This is something you can't do with
   a static prompt or simple rules — the agent needs to reason about
   each result in context.

2. INFORMATION ROUTING (write_posts):
   Live web data (the chosen trend) gets passed into a secondary "writing"
   workflow along with the brand guidelines. The agent combines these two
   sources to produce tailored social media posts.

Both functions call Claude's Messages API via the Anthropic Python SDK.
"""

import json
import os

import anthropic


def _get_text(response) -> str:
    """
    Extract the text content from a Claude API response.

    Claude's response.content is a list of content blocks. Newer models
    (like Sonnet 5) may include ThinkingBlocks before the TextBlock.
    This helper skips any non-text blocks and returns the first text block.

    Args:
        response: The response object from client.messages.create().

    Returns:
        The text string from the first TextBlock in the response.
    """
    for block in response.content:
        if block.type == "text":
            return block.text
    return ""

# We store the client in a variable so it's created only once,
# but we don't create it at import time — we wait until the first
# function call, so that load_dotenv() in agent.py has already run.
_client = None


def _get_client() -> anthropic.Anthropic:
    """
    Get (or create) the Anthropic client.

    We use lazy initialization here because this module gets imported
    before load_dotenv() runs in agent.py. If we created the client
    at import time, the ANTHROPIC_API_KEY wouldn't be loaded yet.
    """
    global _client
    if _client is None:
        # If the user has an identity-linked API key, they also need to
        # pass a workspace ID. We read it from the environment if set.
        workspace_id = os.getenv("ANTHROPIC_WORKSPACE_ID")
        if workspace_id:
            _client = anthropic.Anthropic(
                default_headers={"anthropic-workspace-id": workspace_id}
            )
        else:
            _client = anthropic.Anthropic()
    return _client

# We use Sonnet for both steps — it's fast, cheap, and more than capable
# for filtering and writing tasks. Swap to "claude-opus-5" if you want
# higher quality and don't mind the extra cost.
MODEL = "claude-sonnet-5"


def filter_trends(results: list[dict], niche: str, brand_guidelines: str) -> dict:
    """
    Use Claude to pick the single best trend from the search results.

    This is the FILTERING STEP — Claude reads all the search results and
    evaluates them against three criteria:
        1. Relevance: Is it actually about the niche?
        2. Freshness: Is it trending right now (not old news)?
        3. Brand safety: Does it avoid the topics listed in brand guidelines?

    Claude returns its pick along with a reason for choosing it.

    Args:
        results: List of search result dicts from search_trending().
                 Each has: title, snippet, link, source.
        niche: The niche the user searched for (provides context).
        brand_guidelines: Full text of the brand guidelines markdown file.

    Returns:
        A dict containing:
            - trend_title (str): The name/headline of the chosen trend
            - trend_summary (str): A 1-2 sentence summary of the trend
            - source_url (str): Link to the source article
            - reasoning (str): Why Claude picked this trend
    """

    # Format the search results into a numbered list for Claude to read.
    # This is the "messy internet data" that Claude needs to reason about.
    results_text = ""
    for i, r in enumerate(results, 1):
        results_text += f"""
Result {i}:
  Title: {r['title']}
  Snippet: {r['snippet']}
  Source: {r['source']}
  Link: {r['link']}
"""

    # The system prompt tells Claude its role and exactly what we need back.
    # We ask for JSON so we can parse the response programmatically.
    system_prompt = """You are a trend analyst for a brand's social media team.
Your job is to evaluate search results and pick the ONE best trending topic
that the brand can safely and naturally tie into a social media post.

You must evaluate each result against these criteria:
1. RELEVANCE — Is it actually about the given niche? Skip generic or off-topic results.
2. FRESHNESS — Is it trending right now? Prefer breaking news and hot takes over evergreen content.
3. BRAND SAFETY — Read the brand guidelines carefully. Skip anything touching the brand's "Topics to Avoid" list. Skip anything negative, controversial, or divisive.
4. TREND-JACK POTENTIAL — Could a brand naturally join this conversation without seeming forced?

Respond with ONLY a JSON object (no markdown, no code fences) in this exact format:
{
    "trend_title": "Short headline of the trend",
    "trend_summary": "1-2 sentence summary of what's trending and why",
    "source_url": "The link from the search result you chose",
    "reasoning": "One sentence explaining why this trend is the best pick for this brand"
}"""

    # The user message gives Claude the niche, the brand guidelines, and
    # the raw search results — everything it needs to make a decision.
    user_message = f"""Niche: {niche}

--- BRAND GUIDELINES ---
{brand_guidelines}

--- SEARCH RESULTS ---
{results_text}

Pick the single best trend for this brand to post about. Respond with JSON only."""

    # Call Claude's Messages API
    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    # Extract the text from Claude's response.
    # We use _get_text() because newer Claude models may return ThinkingBlocks
    # before the actual TextBlock in response.content.
    response_text = _get_text(response)

    # Parse the JSON response into a Python dict
    trend = json.loads(response_text)

    return trend


def write_posts(trend: dict, brand_guidelines: str) -> str:
    """
    Use Claude to draft 3 social media posts about the chosen trend.

    This is the WRITING STEP — Claude takes the selected trend and the
    brand guidelines, then writes posts that tie the trend to the brand
    naturally. Each post is tailored to a different platform:

        1. Twitter/X: Short and punchy, 280 characters max
        2. LinkedIn: Professional tone, 2-3 paragraphs
        3. Instagram: Casual and engaging, with hashtag suggestions

    Args:
        trend: The chosen trend dict from filter_trends().
               Has: trend_title, trend_summary, source_url, reasoning.
        brand_guidelines: Full text of the brand guidelines markdown file.

    Returns:
        A markdown-formatted string containing all 3 drafted posts,
        ready to be included in the output file.
    """
    # The system prompt defines Claude's role as a social media copywriter
    # and gives it clear formatting instructions for each platform.
    system_prompt = """You are a social media copywriter for a brand.
You write engaging posts that tie trending topics to the brand naturally —
never forced, never salesy. You match the brand's tone of voice exactly.

Write exactly 3 posts in markdown format:

## Twitter/X Post
- Must be 280 characters or fewer (this is a hard limit)
- Punchy, attention-grabbing, conversational
- Include 1-2 relevant hashtags inline

## LinkedIn Post
- Professional but approachable tone
- 2-3 short paragraphs
- Open with a hook that references the trend
- End with a thought-provoking question or call to action
- No hashtags in the body, add 3-5 hashtags at the very end

## Instagram Caption
- Casual, friendly, human tone
- 2-3 short paragraphs
- Use line breaks for readability
- End with 5-10 relevant hashtags on a separate line

IMPORTANT RULES:
- Tie the trend to the brand naturally — don't just mention the trend and then pivot to a sales pitch
- Never use generic filler like "In today's fast-paced world..."
- Never use the word "leverage"
- Keep it authentic — write like a real person, not a marketing bot"""

    # The user message gives Claude the specific trend to write about
    # and the brand guidelines to follow. This is INFORMATION ROUTING —
    # we're passing live web data (the trend) into a writing workflow.
    user_message = f"""Write 3 social media posts about this trending topic for our brand.

--- TRENDING TOPIC ---
Title: {trend['trend_title']}
Summary: {trend['trend_summary']}
Source: {trend['source_url']}

--- BRAND GUIDELINES ---
{brand_guidelines}

Write the 3 posts now (Twitter/X, LinkedIn, Instagram). Follow the format exactly."""

    # Call Claude's Messages API
    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    # Return the raw markdown text — it's already formatted with
    # ## headers for each platform, ready to go into the output file.
    # We use _get_text() to skip any ThinkingBlocks in the response.
    return _get_text(response)
