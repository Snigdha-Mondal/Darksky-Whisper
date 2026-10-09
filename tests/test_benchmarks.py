"""Unit and regression tests for the 75-pair astronomical benchmark suite."""

import json
from pathlib import Path
import re
import pytest

from benchmarks.run_benchmark import DATASET_FILE, REPORT_FILE, run_benchmark


def test_benchmark_dataset_has_75_pairs_and_valid_categories():
    """Verify benchmark dataset contains exactly 75 valid pairs across 5 categories."""
    assert DATASET_FILE.exists(), f"Benchmark dataset missing at {DATASET_FILE}"

    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        pairs = [json.loads(line) for line in f if line.strip()]

    assert len(pairs) == 75, f"Expected exactly 75 interaction pairs, got {len(pairs)}"

    categories = {}
    for p in pairs:
        cat = p["category"]
        categories[cat] = categories.get(cat, 0) + 1

    expected_categories = [
        "atmospheric_seeing",
        "brightest_and_beacons",
        "planetary_and_lunar",
        "constellations_and_deep_sky",
        "sky_tours_and_recommendations"
    ]

    for ec in expected_categories:
        assert ec in categories, f"Missing expected category: {ec}"
        assert categories[ec] == 15, f"Category {ec} should contain 15 pairs, got {categories[ec]}"


def test_benchmark_target_responses_satisfy_invariants():
    """Verify that all 75 ground-truth targets strictly follow zero-markdown and brevity rules."""
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        pairs = [json.loads(line) for line in f if line.strip()]

    for p in pairs:
        resp = p["target_response"]
        words = resp.split()

        # Invariant 1: Zero markdown
        assert not re.search(r"[*#_`\[\]]", resp), f"Found markdown in target {p['id']}: {resp}"
        assert "- " not in resp, f"Found bullet in target {p['id']}: {resp}"

        # Invariant 2: Brevity ceiling
        assert 10 <= len(words) <= 45, f"Target {p['id']} has invalid word count {len(words)}: {resp}"


def test_run_benchmark_completes_with_high_compliance():
    """Verify run_benchmark() executes and achieves 100% zero-markdown compliance."""
    summary = run_benchmark()

    assert summary["total_pairs"] == 75
    assert summary["finetuned_model"]["zero_markdown_rate_pct"] == 100.0
    assert summary["finetuned_model"]["brevity_compliance_pct"] == 100.0
    assert summary["finetuned_model"]["avg_word_count"] <= 35.0
    assert summary["token_reduction_pct"] > 30.0
    assert REPORT_FILE.exists()
