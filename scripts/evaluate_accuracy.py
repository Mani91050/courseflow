from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from backend.main import extract_deadlines

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "backend" / "tests" / "fixtures" / "accuracy_cases.json"
REPORT = ROOT / "docs" / "accuracy-report.md"


def evaluate() -> dict:
    cases = json.loads(FIXTURES.read_text(encoding="utf-8"))
    rows = []
    true_positives = false_positives = false_negatives = 0

    for case in cases:
        actual = [event.due_date.isoformat() for event in extract_deadlines(case["text"], case["default_year"])]
        expected = case["expected_dates"]
        actual_counts, expected_counts = Counter(actual), Counter(expected)
        matched = sum((actual_counts & expected_counts).values())
        extra = sum((actual_counts - expected_counts).values())
        missed = sum((expected_counts - actual_counts).values())
        true_positives += matched
        false_positives += extra
        false_negatives += missed
        rows.append({"name": case["name"], "expected": len(expected), "found": len(actual), "matched": matched, "extra": extra, "missed": missed, "passed": extra == 0 and missed == 0})

    precision = true_positives / (true_positives + false_positives) if true_positives + false_positives else 1
    recall = true_positives / (true_positives + false_negatives) if true_positives + false_negatives else 1
    return {"cases": rows, "true_positives": true_positives, "false_positives": false_positives, "false_negatives": false_negatives, "precision": precision, "recall": recall}


def write_report(result: dict) -> None:
    lines = [
        "# CourseFlow Extraction Accuracy Report",
        "",
        "This benchmark evaluates deterministic **date extraction**, not title quality or complete real-world syllabus understanding.",
        "",
        "## Summary",
        "",
        f"- Fixtures: **{len(result['cases'])}**",
        f"- Expected dated deadlines: **{result['true_positives'] + result['false_negatives']}**",
        f"- Correctly extracted dates: **{result['true_positives']}**",
        f"- Missed expected dates: **{result['false_negatives']}**",
        f"- False-positive dates: **{result['false_positives']}**",
        f"- Date precision: **{result['precision']:.1%}**",
        f"- Date recall: **{result['recall']:.1%}**",
        "",
        "## Results by fixture",
        "",
        "| Fixture | Expected | Found | Correct | Extra | Missed | Result |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["cases"]:
        lines.append(f"| {row['name']} | {row['expected']} | {row['found']} | {row['matched']} | {row['extra']} | {row['missed']} | {'Pass' if row['passed'] else 'Review'} |")
    lines += [
        "",
        "## Interpretation",
        "",
        "CourseFlow reliably handles the explicitly supported full-month, abbreviated-month, ordinal, numeric, ISO, and missing-year formats in this fixture set. Relative phrases such as `next Friday` are intentionally not converted because they lack a stable calendar date.",
        "",
        "The historical-date fixture exposes an important limitation: deterministic pattern matching cannot always know whether an exact date describes a future deadline or historical context. CourseFlow mitigates this by showing the original source sentence and requiring human review before export.",
        "",
        "## Reproduce",
        "",
        "```bash",
        "PYTHONPATH=. python scripts/evaluate_accuracy.py",
        "pytest backend/tests -q",
        "```",
        "",
        "This is a small, transparent hackathon benchmark—not a claim of universal syllabus accuracy.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    result = evaluate()
    write_report(result)
    print(json.dumps(result, indent=2))
