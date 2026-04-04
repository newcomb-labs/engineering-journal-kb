# Content Lifecycle Model

This document defines the canonical lifecycle model for all content in the Engineering Journal.

The lifecycle is **strictly enforced** and applies to all content types.

---

## Lifecycle States

Content MUST use one of the following states:

- draft
- review
- active
- deprecated
- archived

---

## Lifecycle Flow

draft → review → active → deprecated → archived

---

## Transition Rules (STRICT)

Only the following transitions are allowed:

| From       | To         |
| ---------- | ---------- |
| draft      | review     |
| review     | draft      |
| review     | active     |
| active     | deprecated |
| deprecated | archived   |

---

## Disallowed Transitions

The following transitions are NOT allowed:

- draft → active
- active → review
- archived → any state
- deprecated → active

Violations MUST fail CI validation.

---

## Review Requirement

Content MUST pass through `review` before becoming `active`.

This ensures:

- quality control
- accuracy validation
- governance consistency

---

## Staleness Handling

Staleness is NOT a lifecycle state.

Instead, it is derived from:

- `last_reviewed` field
- future automation (e.g., stale detection scripts)

Example:

- Content not reviewed in X days → flagged as stale
- Does NOT change lifecycle automatically

---

## Ownership Responsibility

Content owners are responsible for:

- moving content through lifecycle states
- ensuring timely reviews
- deprecating outdated content
- archiving obsolete content

---

## Enforcement

The lifecycle model is enforced via:

- CI validation scripts
- frontmatter validation
- PR governance rules

Any invalid transition MUST result in a CI failure.

---

## Future Enhancements

Planned automation:

- stale content detection
- review reminders
- lifecycle dashboards
- automated reporting
