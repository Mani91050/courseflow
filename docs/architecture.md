# CourseFlow Architecture

```mermaid
flowchart LR
    U[Student] --> UI[React review interface]
    UI -->|Text or PDF| API[FastAPI]
    API --> PDF[PyMuPDF extractor]
    PDF --> PARSE[Date and event parser]
    PARSE --> UI
    UI -->|Approved and edited events| RULES[Conflict rules]
    RULES --> UI
    UI -->|Approved events| ICS[ICS generator]
    ICS --> CAL[Calendar download]
```

## Trust boundary

CourseFlow never treats extracted dates as automatically correct. The student sees source text and can edit, approve, or reject each item before export.
