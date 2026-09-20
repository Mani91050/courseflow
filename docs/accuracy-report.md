# CourseFlow Extraction Accuracy Report

This benchmark evaluates deterministic **date extraction**, not title quality or complete real-world syllabus understanding.

## Summary

- Fixtures: **9**
- Expected dated deadlines: **12**
- Correctly extracted dates: **12**
- Missed expected dates: **0**
- False-positive dates: **1**
- Date precision: **92.3%**
- Date recall: **100.0%**

## Results by fixture

| Fixture | Expected | Found | Correct | Extra | Missed | Result |
|---|---:|---:|---:|---:|---:|---|
| full month names | 3 | 3 | 3 | 0 | 0 | Pass |
| abbreviations and ordinal suffixes | 2 | 2 | 2 | 0 | 0 | Pass |
| numeric dates | 2 | 2 | 2 | 0 | 0 | Pass |
| ISO dates | 2 | 2 | 2 | 0 | 0 | Pass |
| missing years | 2 | 2 | 2 | 0 | 0 | Pass |
| duplicate line removal | 1 | 1 | 1 | 0 | 0 | Pass |
| no dated deadlines | 0 | 0 | 0 | 0 | 0 | Pass |
| unsupported relative dates | 0 | 0 | 0 | 0 | 0 | Pass |
| historical date false positive | 0 | 1 | 0 | 1 | 0 | Review |

## Interpretation

CourseFlow reliably handles the explicitly supported full-month, abbreviated-month, ordinal, numeric, ISO, and missing-year formats in this fixture set. Relative phrases such as `next Friday` are intentionally not converted because they lack a stable calendar date.

The historical-date fixture exposes an important limitation: deterministic pattern matching cannot always know whether an exact date describes a future deadline or historical context. CourseFlow mitigates this by showing the original source sentence and requiring human review before export.

## Reproduce

```bash
PYTHONPATH=. python scripts/evaluate_accuracy.py
pytest backend/tests -q
```

This is a small, transparent hackathon benchmark—not a claim of universal syllabus accuracy.
