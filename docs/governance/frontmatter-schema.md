# Frontmatter Schema

This document defines the canonical frontmatter schema for all content in the Engineering Journal.

This schema is **deterministic and enforced** via repository governance.

---

## Core Schema (Required for ALL content)

```yaml
title: string
description: string
content_type: string
status: draft | review | active | deprecated | archived
tags: [string]
owners: ["@github-username"]
created_at: YYYY-MM-DD
last_reviewed: YYYY-MM-DD
```

---

## Content Type Enforcement

All content MUST:

1. Declare `content_type` in frontmatter
2. Reside in the correct directory

| content_type | required path                  |
| ------------ | ------------------------------ |
| docs         | website/docs/\*\*              |
| lab          | website/docs/labs/\*\*         |
| case-study   | website/docs/case-studies/\*\* |
| journal      | website/docs/journal/\*\*      |
| adr          | website/docs/adr/\*\*          |

Mismatch between `content_type` and path is a **CI failure**.

---

## Content Type Extensions

### Lab

```yaml
difficulty: beginner | intermediate | advanced
environment: string
tools: [string]
```

---

### Case Study

```yaml
problem: string
impact: string
resolution: string
```

---

### Journal Entry

```yaml
date: YYYY-MM-DD
topics: [string]
```

---

### ADR

```yaml
adr_id: string
decision: string
context: string
consequences: string
```

---

## Field Definitions

### title

Human-readable title of the document.

### description

Short summary used for SEO and previews.

### content_type

Determines schema validation and taxonomy alignment.

### status

Lifecycle state of the content.

Allowed values:

- draft
- review
- active
- deprecated
- archived

### tags

Must match controlled vocabulary defined in taxonomy (#126).

### owners

GitHub usernames responsible for maintaining the content.

### created_at

Date the content was created.

### last_reviewed

Date the content was last reviewed for accuracy.

---

## Validation Rules

- All required fields MUST be present
- `status` MUST match allowed enum
- `tags` MUST match approved taxonomy
- `owners` MUST be valid GitHub usernames
- Dates MUST be ISO 8601 (`YYYY-MM-DD`)
- `content_type` MUST match directory

---

## Future Enforcement

This schema will be enforced via:

- CI validation scripts
- Pre-commit hooks
- Content linting
