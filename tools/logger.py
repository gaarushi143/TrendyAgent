"""
tools/logger.py — Training data logger.

Saves every LLM input/output pair as JSONL so it can later be used to
fine-tune an open-source model. Each line in the log file is one complete
(stage, input, output) record.

Log files go to logs/ and are named by date. Each agent run appends to
the day's file, building up training data over time.
"""

import json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("logs")


def log_stage(stage: str, inputs: dict, outputs: dict, metadata: dict = None):
    """
    Log one stage's input/output pair for future model training.

    Args:
        stage: Which pipeline stage produced this (e.g. "search_plan", "search_evaluate")
        inputs: What went into the LLM call (niche, brand_guidelines, etc.)
        outputs: What came back (the parsed JSON response)
        metadata: Optional extra context (latency, model used, etc.)
    """
    LOG_DIR.mkdir(exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "stage": stage,
        "inputs": inputs,
        "outputs": outputs,
        "metadata": metadata or {},
    }

    filename = f"training_data_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    filepath = LOG_DIR / filename
    with open(filepath, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")

    return entry


def load_logs(date_str: str = None) -> list[dict]:
    """
    Load logged training data, optionally filtered by date.

    Args:
        date_str: Date string like "2026-11-21". If None, loads all logs.

    Returns:
        List of log entry dicts.
    """
    entries = []
    if date_str:
        files = [LOG_DIR / f"training_data_{date_str}.jsonl"]
    else:
        files = sorted(LOG_DIR.glob("training_data_*.jsonl"))

    for filepath in files:
        if not filepath.exists():
            continue
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))

    return entries


def load_logs_by_stage(stage: str) -> list[dict]:
    """Load all logged entries for a specific stage (e.g. 'search_plan')."""
    return [e for e in load_logs() if e.get("stage") == stage]
