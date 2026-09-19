from __future__ import annotations

import io
import re
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Literal

import fitz
from dateutil import parser as date_parser
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

app = FastAPI(title="CourseFlow API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

EventType = Literal["assignment", "exam", "project", "presentation", "other"]


class Deadline(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    course: str = "Course"
    due_date: date
    event_type: EventType = "other"
    effort_hours: int = Field(default=3, ge=1, le=100)
    source_text: str = ""
    confidence: float = Field(default=0.75, ge=0, le=1)
    approved: bool = True
    suggested_start: date | None = None


class Conflict(BaseModel):
    severity: Literal["low", "medium", "high"]
    title: str
    description: str
    event_ids: list[str]


class ParseResponse(BaseModel):
    events: list[Deadline]
    conflicts: list[Conflict]
    source_characters: int


class AnalyzeRequest(BaseModel):
    events: list[Deadline]


DATE_PATTERNS = [
    re.compile(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?\b", re.I),
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
]


def infer_type(text: str) -> EventType:
    value = text.lower()
    if any(word in value for word in ("exam", "midterm", "quiz", "test")):
        return "exam"
    if "presentation" in value or "demo" in value:
        return "presentation"
    if any(word in value for word in ("project", "prototype", "capstone")):
        return "project"
    if any(word in value for word in ("assignment", "homework", "essay", "report", "paper", "proposal")):
        return "assignment"
    return "other"


def default_effort(event_type: EventType) -> int:
    return {"exam": 10, "project": 12, "presentation": 7, "assignment": 5, "other": 3}[event_type]


def extract_course(text: str) -> str:
    first_lines = [line.strip() for line in text.splitlines() if line.strip()][:4]
    for line in first_lines:
        if re.search(r"\b[A-Z]{2,5}\s*[- ]?\d{2,4}\b", line):
            return line[:80]
    return first_lines[0][:80] if first_lines else "Course"


def parse_date(raw: str, default_year: int) -> date | None:
    cleaned = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", raw, flags=re.I)
    try:
        parsed = date_parser.parse(cleaned, fuzzy=False, default=datetime(default_year, 1, 1))
        return parsed.date()
    except (ValueError, OverflowError):
        return None


def clean_title(line: str, raw_date: str) -> str:
    title = line.replace(raw_date, " ")
    title = re.sub(r"\b(due|deadline|on|at|by|date)\b\s*[:\-]?", " ", title, flags=re.I)
    title = re.sub(r"\s+", " ", title).strip(" —–-:;,.\t")
    return title[:120] or "Untitled deadline"


def extract_deadlines(text: str, default_year: int | None = None) -> list[Deadline]:
    year = default_year or datetime.now().year
    course = extract_course(text)
    events: list[Deadline] = []
    seen: set[tuple[str, date]] = set()

    for original_line in text.splitlines():
        line = original_line.strip()
        if len(line) < 5:
            continue
        matches = []
        for pattern in DATE_PATTERNS:
            matches.extend(pattern.finditer(line))
        matches.sort(key=lambda match: match.start())

        for match in matches:
            raw_date = match.group(0)
            parsed = parse_date(raw_date, year)
            if not parsed:
                continue
            title = clean_title(line, raw_date)
            key = (title.lower(), parsed)
            if key in seen:
                continue
            seen.add(key)
            event_type = infer_type(line)
            confidence = 0.94 if re.search(r"\b(due|exam|midterm|deadline|presentation)\b", line, re.I) else 0.72
            effort = default_effort(event_type)
            start = parsed - timedelta(days=max(1, round(effort / 2)))
            events.append(
                Deadline(
                    title=title,
                    course=course,
                    due_date=parsed,
                    event_type=event_type,
                    effort_hours=effort,
                    source_text=line[:240],
                    confidence=confidence,
                    suggested_start=start,
                )
            )
    return sorted(events, key=lambda event: event.due_date)


def detect_conflicts(events: list[Deadline]) -> list[Conflict]:
    approved = sorted((event for event in events if event.approved), key=lambda event: event.due_date)
    conflicts: list[Conflict] = []

    by_date: dict[date, list[Deadline]] = {}
    for event in approved:
        by_date.setdefault(event.due_date, []).append(event)
    for due, same_day in by_date.items():
        if len(same_day) >= 2:
            conflicts.append(
                Conflict(
                    severity="high" if len(same_day) >= 3 else "medium",
                    title=f"{len(same_day)} deadlines on {due.strftime('%b %d')}",
                    description="Consider moving preparation earlier to avoid a same-day workload spike.",
                    event_ids=[event.id for event in same_day],
                )
            )

    for index, event in enumerate(approved):
        window = [candidate for candidate in approved[index:] if 0 <= (candidate.due_date - event.due_date).days <= 7]
        if len(window) >= 3:
            ids = [candidate.id for candidate in window]
            if not any(set(conflict.event_ids) == set(ids) for conflict in conflicts):
                conflicts.append(
                    Conflict(
                        severity="high",
                        title="Heavy seven-day workload",
                        description=f"{len(window)} deadlines fall within one week. Start the largest task first.",
                        event_ids=ids,
                    )
                )

    for event in approved:
        if event.confidence < 0.8:
            conflicts.append(
                Conflict(
                    severity="low",
                    title="Date needs review",
                    description=f"Check the source text for “{event.title}” before exporting.",
                    event_ids=[event.id],
                )
            )
    return conflicts


def pdf_to_text(content: bytes) -> str:
    try:
        document = fitz.open(stream=io.BytesIO(content), filetype="pdf")
        return "\n".join(page.get_text("text") for page in document)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Could not read this PDF.") from exc


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/api/parse", response_model=ParseResponse)
async def parse_syllabus(
    text: str = Form(default=""),
    default_year: int | None = Form(default=None),
    file: UploadFile | None = File(default=None),
) -> ParseResponse:
    source = text.strip()
    if file:
        if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=415, detail="CourseFlow MVP accepts PDF files only.")
        content = await file.read()
        if len(content) > 8 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="PDF must be smaller than 8 MB.")
        source = f"{source}\n{pdf_to_text(content)}".strip()
    if not source:
        raise HTTPException(status_code=400, detail="Paste syllabus text or upload a PDF.")

    events = extract_deadlines(source, default_year)
    return ParseResponse(events=events, conflicts=detect_conflicts(events), source_characters=len(source))


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest) -> dict[str, list[Conflict]]:
    return {"conflicts": detect_conflicts(request.events)}


def escape_ics(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


@app.post("/api/export/ics")
def export_ics(request: AnalyzeRequest) -> Response:
    events = [event for event in request.events if event.approved]
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//CourseFlow//Deadline Calendar//EN", "CALSCALE:GREGORIAN"]
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    for event in events:
        end = event.due_date + timedelta(days=1)
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{event.id}@courseflow",
                f"DTSTAMP:{stamp}",
                f"DTSTART;VALUE=DATE:{event.due_date.strftime('%Y%m%d')}",
                f"DTEND;VALUE=DATE:{end.strftime('%Y%m%d')}",
                f"SUMMARY:{escape_ics(event.title)}",
                f"DESCRIPTION:{escape_ics('Course: ' + event.course + ' | Suggested start: ' + str(event.suggested_start or ''))}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    body = "\r\n".join(lines) + "\r\n"
    return Response(
        body,
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="courseflow-calendar.ics"'},
    )
