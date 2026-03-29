# Content Taxonomy

This document defines the canonical taxonomy for all content in the Engineering Journal.

The taxonomy is **strictly enforced** and defined in:

.github/taxonomy.yml

---

## Structure

The taxonomy consists of:

- Domains (high-level classification)
- Tags (controlled vocabulary)

---

## Domains

Each document MUST have:

- one primary domain
- optional secondary domains

Example:

```yaml
primary_domain: networking
secondary_domains:
  - troubleshooting
```

Domains are defined in `.github/taxonomy.yml`.

---

## Tags

Tags MUST:

- come from the approved taxonomy
- be relevant to the content
- be consistent across documents

Example:

```yaml
tags:
  - smb
  - authentication
  - windows
```

---

## Enforcement

The following rules are enforced via CI:

- primary_domain MUST exist in taxonomy
- secondary_domains MUST exist in taxonomy
- tags MUST exist in taxonomy
- unknown values result in CI failure

---

## Design Principles

### Deterministic

All values are controlled and validated.

### Scalable

New domains/tags added via PR.

### Flexible

Domains provide structure, tags provide flexibility.

### Consistent

No free-form tagging allowed.

---

## Adding to Taxonomy

To add a new domain or tag:

1. Update `.github/taxonomy.yml`
2. Submit PR
3. Ensure naming consistency
4. Avoid duplicates or synonyms

---

## Anti-Patterns

Avoid:

- duplicate tags (e.g., network vs networking)
- overly broad tags (e.g., misc)
- redundant domains
- tagging everything

---

## Future Enhancements

- tag linting
- domain dashboards
- content grouping automation
