---
title: Migrating the Docs Site to Docusaurus
description: Notes on migrating the engineering knowledge base from MkDocs to Docusaurus classic, including the decision rationale, structural changes, and open work.
content_type: journal
type: journal
status: active
lifecycle: active
created_at: "2026-03-12"
last_reviewed: "2026-03-12"
owners:
  - "@newcomb-labs"
tags:
  - automation
  - ci-cd
primary_domain: devops
category: journal
---

## Summary

Migrated the engineering knowledge base from MkDocs to Docusaurus classic.
The goal was to unify docs and journal under a single governed platform with
better long-term fit for GitHub Pages and the content structure being built.

## Notes

### Why Docusaurus over MkDocs

MkDocs was the original platform. It was removed because it has no native
separation between evergreen docs and dated journal entries, the plugin
ecosystem requires more maintenance overhead, and the governance automation
being built targets the Docusaurus content model.

Docusaurus classic was chosen because it supports:

- `docs/` for evergreen reference content
- Sidebar auto-generation from directory structure
- MDX for interactive content
- GitHub Pages deployment via the standard deploy workflow

### Structural decisions made during migration

The repo separates content into two roots:

- `website/docs/` — governed evergreen content (labs, case studies, governance, engineering, operations)
- `website/docs/journal/` — governed dated entries (this directory)

The Docusaurus `blog/` feature was initially used for journal entries but
was removed in favour of `website/docs/journal/`. The `blog/` feature provides
RSS, author pages, and reading time — none of which are goals for this knowledge
base. Keeping journal entries in `docs/` means they go through the same
frontmatter governance, validation, and lifecycle enforcement as every other
content type.

### Governance automation introduced alongside migration

- Pre-commit hooks: heading fixer, frontmatter defaults, content validation
- CI workflows: content validation on PR and push to main
- Generated artifacts: indexes, glossary, content manifest — all derived
  deterministically from frontmatter at commit time
- Legacy docs drift guard: blocks any reintroduction of the previous platform

## Insights

Docusaurus sidebar auto-generation from `_category_.json` files is clean but
requires every directory to have one. The `generate_content_artifacts.py`
script writes these files deterministically so they never need to be authored
manually.

The `blog/` → `docs/journal/` decision should have been made at the start.
Running both in parallel for even a short period created schema drift that
required a dedicated reconciliation pass (Track 1). When in doubt, keep all
governed content in one system.
