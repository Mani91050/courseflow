from datetime import date

from fastapi.testclient import TestClient

from backend.main import Deadline, detect_conflicts, extract_deadlines

client = TestClient(__import__("backend.main", fromlist=["app"]).app)


def test_health():
    assert client.get("/api/health").json() == {"status": "healthy"}


def test_extracts_named_and_numeric_dates():
    text = """CS 301 Software Engineering
Assignment 1 due September 23, 2026
Midterm Exam: 09/25/2026
Final demo — 2026-10-05
"""
    events = extract_deadlines(text)
    assert len(events) == 3
    assert [event.due_date for event in events] == [date(2026, 9, 23), date(2026, 9, 25), date(2026, 10, 5)]
    assert events[1].event_type == "exam"


def test_detects_same_day_and_week_conflicts():
    events = [
        Deadline(title="Assignment", due_date=date(2026, 9, 25)),
        Deadline(title="Exam", due_date=date(2026, 9, 25), event_type="exam"),
        Deadline(title="Project", due_date=date(2026, 9, 29), event_type="project"),
    ]
    conflicts = detect_conflicts(events)
    titles = {conflict.title for conflict in conflicts}
    assert "2 deadlines on Sep 25" in titles
    assert "Heavy seven-day workload" in titles


def test_rejected_events_are_not_analyzed():
    events = [
        Deadline(title="A", due_date=date(2026, 9, 25), approved=False, confidence=1),
        Deadline(title="B", due_date=date(2026, 9, 25), approved=True, confidence=1),
    ]
    assert detect_conflicts(events) == []


def test_ics_contains_only_approved_events():
    payload = {
        "events": [
            {"id": "one", "title": "Approved", "due_date": "2026-09-25", "approved": True},
            {"id": "two", "title": "Rejected", "due_date": "2026-09-26", "approved": False},
        ]
    }
    response = client.post("/api/export/ics", json=payload)
    assert response.status_code == 200
    assert "SUMMARY:Approved" in response.text
    assert "Rejected" not in response.text
