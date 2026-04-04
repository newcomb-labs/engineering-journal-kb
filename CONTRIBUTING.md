# Contributing Guide

This repository is a governed engineering knowledge base. All changes follow
the same rigor as production code — structure, automation, and CI enforcement
are non-negotiable.

---

## Workflow

1. Open or select an issue
2. Create a branch following the naming convention
3. Implement changes
4. Ensure pre-commit hooks pass locally
5. Submit a pull request linked to the issue
6. Ensure all CI checks pass before requesting review

---

## Branch Naming

```text
feat/<name>      — new content or capability
fix/<name>       — correction or repair
chore/<name>     — maintenance, deps, config
```

---

## Commit Style

This repository follows [Conventional Commits](https://www.conventionalcommits.org/).

```text
feat(scope): description
fix(scope): description
chore(scope): description
docs(scope): description
ci(scope): description
```

Scopes map to area labels: `ci`, `repo`, `journal`, `labs`, `case-studies`,
`governance`, `theme`, `security`.

Commits that do not follow this format will be rejected by CI.

---

## Pull Requests

Every PR must:

- be linked to an issue (`Closes #N`)
- carry a `type:` label and an `area:` label
- pass all CI checks before merge
- include documentation updates if behaviour changes

---

## Markdown Authoring Rules

All markdown files are linted by `markdownlint` and `prettier`. Follow these
rules to avoid CI failures.

### Headings

- Use ATX headings (`#`, `##`, `###`) — not Setext underlines
- One H1 per file
- Do not skip heading levels (H1 → H3 is invalid)
- Do not use bold emphasis as a heading substitute — `**Title**` on its own
  line will fail MD036

### Frontmatter

Every governed document must include all 12 required fields. Run
`apply_frontmatter_defaults.py` to scaffold missing fields:

```bash
python3 scripts/apply_frontmatter_defaults.py website/docs/path/to/file.md
```

Required fields: `title`, `description`, `content_type`, `type`, `status`,
`lifecycle`, `created_at`, `last_reviewed`, `owners`, `tags`, `primary_domain`,
`category`.

### Lists

- Use `-` for unordered lists
- Use `1.` with ordered lists
- Indent nested lists by 2 spaces

### Code blocks

- Always specify the language on fenced code blocks:

  ````text
  ```bash
  echo "example"
  ```
  ````

- Use backtick fences — not tildes

### Line length

MD013 is disabled — no hard line length limit. Keep lines readable.

### Links

Use relative links for internal cross-references:

```markdown
[VM Cloning Lab](/docs/labs/vm-cloning-auth-failure-lab)
```

Do not use bare URLs in prose.

---

## Fast-Path Workflows

### Adding a journal entry

```bash
# 1. Create the file
cp website/docs/journal/2026-03-12-docusaurus-migration.md \
   website/docs/journal/YYYY-MM-DD-your-title.md

# 2. Update frontmatter
#    - title, description, created_at, last_reviewed, tags

# 3. Apply any missing defaults
python3 scripts/apply_frontmatter_defaults.py \
  website/docs/journal/YYYY-MM-DD-your-title.md

# 4. Commit
git add website/docs/journal/YYYY-MM-DD-your-title.md
git commit -m "docs(journal): add entry - your title"
```

### Adding a lab

```bash
# 1. Create the file under website/docs/labs/
# 2. Required sections: Overview, Environment, Steps, Validation, Lessons Learned
# 3. Apply defaults
python3 scripts/apply_frontmatter_defaults.py website/docs/labs/your-lab.md
# 4. Commit
git commit -m "docs(labs): add lab - your title"
```

### Adding a case study

```bash
# 1. Create the file under website/docs/case-studies/
# 2. Required sections: Summary, Problem, Impact, Root Cause, Resolution, Lessons Learned
# 3. Apply defaults
python3 scripts/apply_frontmatter_defaults.py website/docs/case-studies/your-study.md
# 4. Commit
git commit -m "docs(case-studies): add case study - your title"
```

### Fixing a CI failure

```text
Validation failed: missing required fields
→ Run: python3 scripts/apply_frontmatter_defaults.py <file>

Unknown content_type
→ Check content_type matches: doc | lab | case-study | journal

Missing section '## Summary'
→ Add the required H2 section to the file body

Unknown word (cspell)
→ Add the word to config/cspell-dictionary.txt if it is legitimate IT terminology
```

---

## Content Types and Required Sections

| Type         | Directory                    | Required sections                                                 |
| ------------ | ---------------------------- | ----------------------------------------------------------------- |
| `doc`        | `website/docs/**`            | none                                                              |
| `lab`        | `website/docs/labs/`         | Overview, Environment, Steps, Validation, Lessons Learned         |
| `case-study` | `website/docs/case-studies/` | Summary, Problem, Impact, Root Cause, Resolution, Lessons Learned |
| `journal`    | `website/docs/journal/`      | Summary, Notes, Insights                                          |

---

## Taxonomy

Tags and domains must come from the approved taxonomy in `.github/taxonomy.yml`.
To add a new tag or domain, update that file in a separate PR.

See `docs/governance/taxonomy.md` for full reference.

---

## Governance Reference

| Document              | Location                                   |
| --------------------- | ------------------------------------------ |
| Frontmatter schema    | `docs/governance/frontmatter-schema.md`    |
| Content lifecycle     | `docs/governance/content-lifecycle.md`     |
| Taxonomy              | `docs/governance/taxonomy.md`              |
| Content contract      | `docs/governance/content-contract.md`      |
| Repo standards        | `docs/governance/repo-standards.md`        |
| Repository governance | `docs/governance/REPOSITORY_GOVERNANCE.md` |
