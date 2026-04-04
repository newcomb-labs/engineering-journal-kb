# Content Contract

This document defines the content contract for the Engineering Journal.

It serves as both:

- a validation specification (for CI enforcement)
- an authoring guide (for contributors)

All content MUST comply with this contract.

---

## Core Requirements

Every document MUST:

- include valid frontmatter
- use approved taxonomy values
- follow lifecycle rules
- include required structural sections

---

## Structural Requirements

Each content type has required minimum sections.

### Lab

- Overview
- Environment
- Steps
- Validation
- Lessons Learned

### Case Study

- Summary
- Problem
- Impact
- Root Cause
- Resolution
- Lessons Learned

### Journal Entry

- Summary
- Notes
- Insights

### ADR

- Title
- Status
- Context
- Decision
- Consequences

---

## Enforcement

The contract is enforced via:

- CI validation scripts
- frontmatter validation
- taxonomy validation
- lifecycle validation
- structural linting

Violations MUST result in CI failure.
