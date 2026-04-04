# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly.

Include:

- description of the vulnerability
- reproduction steps
- potential impact

Please avoid public disclosure until the issue is resolved.

## Response Expectations

Reports will be reviewed and triaged as quickly as possible.

## Known Dependency Vulnerabilities

### Docusaurus transitive dependencies (April 2026)

**Affected packages:** `serialize-javascript`, `lodash-es`, `copy-webpack-plugin`, `css-minimizer-webpack-plugin`, `@chevrotain/*`, `mermaid`, `langium`

**Dependabot alerts:** #1–#24

**Status:** Accepted risk. Will resolve when Docusaurus publishes a patch release.

**Reason:** These are transitive build-time dependencies of `@docusaurus/core` and
`@docusaurus/theme-mermaid` at the current latest stable version (3.9.2). They are
not present in the deployed site — the build output is static HTML, CSS, and JS with
no server runtime, no user input, and no execution of these packages after build time.
The documented attack vectors (code injection via template input, prototype pollution,
RCE via serialized objects) require an attacker to control input at build time on a
trusted developer machine, which is outside the threat model for this repository.

`npm audit fix --force` would resolve the alerts by downgrading Docusaurus core to
3.5.2, which is an older version with its own issues. This is not an acceptable trade.

**Resolution path:** Update `website/package.json` to the Docusaurus release that
patches these deps and re-run `npm install` in `website/`.
