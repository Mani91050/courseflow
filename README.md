# CourseFlow

**Turn a messy syllabus into a reviewed, conflict-aware calendar.**

CourseFlow is a student planning application created for Beginner's Paradise — FirstCommit 2026. Students paste syllabus text or upload a text-based PDF; CourseFlow extracts dated assignments and exams, lets the student verify every item, detects workload collisions, suggests preparation start dates, and exports approved deadlines as a standard `.ics` calendar.

> Current milestone: text/PDF extraction, human review, conflict detection, and calendar export.

## Problem

Important course dates are often buried inside long syllabi. Manually copying them is slow and error-prone, and ordinary calendars do not warn students when several deadlines collide.

## Who it is for

Students managing several courses, especially students who receive deadlines in PDF syllabi and want a reliable calendar without silently trusting automated extraction.

## Workflow

`IMPORT → REVIEW → RESOLVE → EXPORT`

1. Paste syllabus text or upload a PDF.
2. Review the extracted title, date, effort estimate, and source text.
3. Approve, edit, or reject each deadline.
4. Resolve same-day and seven-day workload warnings.
5. Export approved events to an `.ics` calendar.

## Current features

- Text and text-based PDF input
- Multiple common date formats
- Assignment, exam, project, and presentation classification
- Source text and confidence shown for review
- Editable dates, titles, and effort estimates
- Approve/reject controls
- Same-day conflict detection
- Heavy seven-day workload detection
- Suggested preparation start dates
- `.ics` calendar export
- Responsive interface
- Backend unit tests

## Architecture

```text
React + TypeScript UI
        |
        | multipart form / JSON
        v
FastAPI backend
  ├── PyMuPDF text extraction
  ├── deterministic date parser
  ├── conflict rules
  └── ICS generator
        |
        v
Reviewed calendar download
```

CourseFlow deliberately keeps a human review step between extraction and export. Automation proposes; the student verifies.

## Project structure

```text
courseflow/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── samples/
│   └── sample-syllabus.txt
├── LICENSE
└── README.md
```

## Local setup

### Backend

```bash
cd courseflow
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Health check: `http://localhost:8000/api/health`

### Frontend

In another terminal:

```bash
cd courseflow/frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### Tests

From the project root with the Python environment active:

```bash
pytest backend/tests -q
```

### Production configuration

Copy `frontend/.env.example` to `frontend/.env` and set:

```env
VITE_API_URL=https://your-backend.example.com
```

Do not add a trailing slash.

## Known limitations

- The MVP accepts text-based PDFs; scanned-image OCR is not included yet.
- Date extraction is deterministic and supports common formats, not every possible phrase.
- Missing years use the selected/default year and must be reviewed.
- Effort estimates are initial defaults that the student should edit.
- CourseFlow does not write directly to a user's private calendar; it exports a portable `.ics` file.
- Data is processed for the current request and is not persisted by the backend.

## Privacy

The backend processes uploaded syllabus content in memory. The current version does not create user accounts or save syllabus files to a database.

## Technologies

- React
- TypeScript
- Vite
- FastAPI
- Python
- Pydantic
- PyMuPDF
- python-dateutil
- Pytest
- Lucide icons

## External resources and attribution

- [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF text extraction
- [python-dateutil](https://dateutil.readthedocs.io/) for date parsing
- [Lucide](https://lucide.dev/) for interface icons
- Google Fonts (`DM Sans`, `Manrope`) for typography

## AI usage disclosure

AI assistance was used for requirements analysis, brainstorming, code scaffolding, debugging suggestions, test planning, and documentation review. The participant is responsible for reviewing, running, understanding, modifying, and presenting the submitted project. Development decisions, testing results, external-resource disclosures, and final claims must be verified by the participant.

Significant AI chat history can be provided to organizers if requested.

## Development history

This project is being built during FirstCommit. The repository should contain multiple meaningful commits that accurately show progress. Do not upload the entire project as one final commit.

## License

MIT — see [LICENSE](LICENSE).
