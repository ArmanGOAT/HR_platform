# HR Platform — API contract (v1)

This is the contract between the **web app** (`services/ui`) and the **gateway** service.
The web app talks only to the gateway; the gateway talks to Postgres, MinIO, the ingest
queue and the search service. Any change here must be agreed by both sides.

- Base path: `/api`
- Format: JSON (`Content-Type: application/json`), except file upload (`multipart/form-data`)
- Time: ISO 8601 strings in UTC, e.g. `2026-11-12T10:15:00Z`
- IDs: a resume id is the **SHA-256 hex of the uploaded file**. The same file uploaded twice
  gets the same id, so duplicates are detected for free.
- Personal data: the API never returns original file names, names, phones, e-mails or links.
  `text` and chunk texts are **already anonymized** by the ingest service.

## Errors

Every non-2xx response has this body:

```json
{ "error": { "code": "unsupported_file_type", "message": "Only PDF, DOCX, PNG and JPG are accepted." } }
```

| HTTP | `code` examples |
|---|---|
| 400 | `bad_request`, `empty_query` |
| 404 | `not_found` |
| 413 | `file_too_large` |
| 415 | `unsupported_file_type` |
| 503 | `search_unavailable`, `storage_unavailable` |

## Types

```ts
type ResumeStatus = "queued" | "processing" | "ready" | "failed";
type Language = "en" | "ru" | "uz" | "unknown";
type Section = "summary" | "experience" | "project" | "education" | "skills" | "other";

interface Resume {
  id: string;                       // sha256 hex (64 chars)
  source: "upload" | "telegram" | "djinni";
  status: ResumeStatus;
  error: string | null;             // set when status = "failed"
  language: Language | null;        // null until processed
  supported: boolean;               // MVP: only "en" is searchable
  ocr_used: boolean | null;         // true if text came from OCR (scan / photo)
  pages: number | null;
  title: string | null;             // detected headline, e.g. "Junior Data Scientist"
  skills: string[];                 // normalized skills, e.g. ["Python", "SQL"]
  experience_years: number | null;
  created_at: string;
  updated_at: string;
}

interface Chunk {
  id: string;                       // "<resume_id>:<n>"
  section: Section;
  text: string;                     // anonymized
}

interface ResumeDetail extends Resume {
  text: string;                     // full anonymized text
  chunks: Chunk[];
}
```

## Endpoints

### `GET /api/health`

```json
{
  "status": "ok",
  "version": "0.1.0",
  "services": { "db": "ok", "storage": "ok", "queue": "ok", "search": "ok" }
}
```

`status` is `"degraded"` if any service is not `"ok"`.

### `GET /api/stats`

```json
{
  "resumes": {
    "total": 1240,
    "by_status": { "queued": 3, "processing": 1, "ready": 1220, "failed": 16 },
    "by_language": { "en": 610, "ru": 420, "uz": 190, "unknown": 20 }
  }
}
```

### `GET /api/rankers`

Lists the ranking models the search service can use. The MVP has only the keyword baseline;
later versions add `bm25`, `encoder-v1`, … without changing the web app.

```json
{
  "default": "keyword",
  "items": [
    { "id": "keyword", "name": "Keyword match (baseline)", "version": "0.1.0",
      "description": "Counts query terms in the resume text." }
  ]
}
```

### `POST /api/resumes` — upload

`multipart/form-data`, field `files` (one or more).
Accepted: `.pdf`, `.docx`, `.png`, `.jpg`, `.jpeg`. Max **10 MB per file**, max **20 files per request**.

Response `202 Accepted`, items in the **same order** as the uploaded files:

```json
{
  "items": [
    { "id": "9f2c…", "status": "queued", "duplicate": false },
    { "id": "41ab…", "status": "ready",  "duplicate": true }
  ]
}
```

The gateway stores the file in MinIO (`raw/<id>`), creates the Postgres row and puts an
ingest job in the queue. Processing is asynchronous: the client polls `GET /api/resumes/{id}`.

### `GET /api/resumes`

Query: `status`, `language`, `q` (substring in title/skills), `limit` (default 50, max 200), `offset`.

```json
{ "total": 1240, "items": [ /* Resume */ ] }
```

Sorted by `created_at` descending.

### `GET /api/resumes/{id}`

Returns `ResumeDetail`. While the resume is `queued`/`processing`, `text` is `""` and
`chunks` is `[]`. Recommended polling interval for the client: 2 s.

### `DELETE /api/resumes/{id}`

Removes the resume from Postgres, MinIO and the search index. `204 No Content`.

### `POST /api/search`

Request:

```json
{
  "query": "Python backend developer, 3+ years, Django, PostgreSQL, Docker",
  "top_k": 50,
  "ranker": "keyword",
  "filters": { "min_experience_years": 2 }
}
```

- `query` — free text or a whole job description (required, 1–20 000 chars)
- `top_k` — 1…200, default 50
- `ranker` — id from `GET /api/rankers`, default = its `default`
- `filters` — optional

Response:

```json
{
  "search_id": "s_01HF…",
  "ranker": { "id": "keyword", "version": "0.1.0" },
  "took_ms": 37,
  "total_candidates": 610,
  "query_terms": ["python", "django", "postgresql", "docker"],
  "results": [
    {
      "rank": 1,
      "resume_id": "9f2c…",
      "score": 7.42,
      "title": "Backend Developer",
      "skills": ["Python", "Django", "PostgreSQL", "Docker", "Redis"],
      "experience_years": 4,
      "matched_terms": ["python", "django", "postgresql", "docker"],
      "missing_terms": [],
      "highlights": [
        {
          "chunk_id": "9f2c…:2",
          "section": "experience",
          "text": "Built REST APIs in Python/Django, migrated the database to PostgreSQL …",
          "spans": [[17, 23], [24, 30], [62, 72]]
        }
      ],
      "evidence": null
    }
  ]
}
```

- `score` — higher is better; its scale depends on the ranker, so the client only compares
  scores **within one response**.
- `highlights[].spans` — `[start, end)` character offsets inside `highlights[].text` to highlight.
- `evidence` — `null` for the keyword baseline. Neural rankers fill it with one item per
  requirement of the job description:

```json
"evidence": [
  { "requirement": "3+ years of Python", "chunk_id": "9f2c…:2",
    "text": "Built REST APIs in Python/Django …", "similarity": 0.83 }
]
```

Only resumes with `status = "ready"` and `supported = true` are searched.

### `POST /api/feedback`

HR marks a search result. These labels feed the offline evaluation set.

```json
{ "search_id": "s_01HF…", "resume_id": "9f2c…", "label": "relevant" }
```

`label` is `"relevant"` or `"not_relevant"`. Sending again for the same
(`search_id`, `resume_id`) replaces the label. Response `201`: `{ "id": "fb_…" }`.
