# Engineering Knowledge Copilot
## Stage 5 Frontend API Contract

Contract version: Stage 5A.2 v1

This document freezes the minimum backend contract used by the Stage 5 frontend.

The frontend is a presentation layer only.

Authorization, program access, document classification, retrieval filtering,
relevance gating, source authority handling, and grounded generation remain
backend responsibilities.

---

## 1. Users

### GET /api/users

Returns the synthetic personas available to the demo frontend.

User object:

- user_id: string
- name: string
- role: string
- assigned_programs: string[]
- clearance: string

The frontend may display these fields.

The frontend MUST NOT use role, clearance, or assigned_programs to make
authorization decisions.

---

## 2. Repositories

### GET /api/repositories

Repository object:

- repository_id: string
- name: string
- provider: string
- status: string
- document_count: integer
- last_sync: string | null

Current repositories:

1. demo-engineering-repository
   - provider: local_demo
   - documents: 48

2. google-drive-engineering-repository
   - provider: google_drive
   - documents: 48

Repository metadata is provided by the backend and should not be hard-coded
into the frontend.

---

## 3. Knowledge Query

### POST /api/query

Request body:

```json
{
  "user_id": "sarah",
  "repository_id": "google-drive-engineering-repository",
  "query": "What caused the Gen-3 wireless charger thermal failure?"
}
