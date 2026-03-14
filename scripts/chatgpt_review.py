#!/usr/bin/env python3
"""ChatGPT PR review helper for GitHub Actions.

Behavior:
- Fetches PR metadata and unified diff from GitHub API
- Sends a bounded diff to OpenAI Responses API
- Posts the review as a PR comment
- Writes the review to:
  - .github/chatgpt-review-output.md
  - GitHub Actions step summary (if available)

Environment variables required:
- GITHUB_TOKEN
- OPENAI_API_KEY
- GITHUB_REPOSITORY
- PR_NUMBER
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
import urllib.error
import urllib.request
from typing import Any

GITHUB_API = "https://api.github.com"
OPENAI_API = "https://api.openai.com/v1/responses"
OUTPUT_PATH = ".github/chatgpt-review-output.md"
MAX_DIFF_CHARS = 120_000
MAX_PROMPT_CHARS = 140_000


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"ERROR: missing required environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def github_request(
    method: str,
    url: str,
    token: str,
    data: dict[str, Any] | None = None,
    accept: str = "application/vnd.github+json",
) -> Any:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": accept,
        "User-Agent": "engineering-journal-kb-chatgpt-review",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read()
            if accept == "application/vnd.github.v3.diff":
                return raw.decode("utf-8", errors="replace")
            if not raw:
                return {}
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        print(f"GitHub API error {exc.code} for {url}\n{details}", file=sys.stderr)
        sys.exit(1)


def openai_request(api_key: str, prompt: str) -> str:
    payload = {
        "model": "gpt-5",
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "You are a senior code reviewer for a documentation-focused "
                            "GitHub repository. Review the pull request diff with an emphasis on:\n"
                            "- correctness\n"
                            "- CI / GitHub Actions robustness\n"
                            "- Docusaurus documentation integrity\n"
                            "- governance and maintainability\n"
                            "- security or permissions mistakes\n\n"
                            "Rules:\n"
                            "- Be concise and practical.\n"
                            "- Prioritize actionable findings.\n"
                            "- If there are no significant issues, say so clearly.\n"
                            "- Use markdown.\n"
                            "- Organize findings under: Summary, Findings, Suggestions.\n"
                            "- Only mention issues supported by the diff.\n"
                            "- Do not invent repository facts beyond what is provided."
                        ),
                    }
                ],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}],
            },
        ],
    }

    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(
        OPENAI_API,
        data=data,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw)
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        print(f"OpenAI API error {exc.code}\n{details}", file=sys.stderr)
        sys.exit(1)

    if isinstance(parsed.get("output_text"), str) and parsed["output_text"].strip():
        return parsed["output_text"].strip()

    output = parsed.get("output", [])
    chunks: list[str] = []
    for item in output:
        for content in item.get("content", []):
            text = content.get("text")
            if text:
                chunks.append(text)

    if chunks:
        return "\n".join(chunks).strip()

    print("ERROR: OpenAI response did not contain review text", file=sys.stderr)
    print(json.dumps(parsed, indent=2), file=sys.stderr)
    sys.exit(1)


def write_output(markdown: str) -> None:
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        handle.write(markdown)
        handle.write("\n")

    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(markdown)
            handle.write("\n")


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n[diff truncated for review size limits]\n"


def build_prompt(repo: str, pr: dict[str, Any], diff_text: str) -> str:
    title = pr.get("title", "")
    body = pr.get("body") or ""
    author = (pr.get("user") or {}).get("login", "unknown")
    base_ref = (pr.get("base") or {}).get("ref", "")
    head_ref = (pr.get("head") or {}).get("ref", "")

    prompt = f"""
Repository: {repo}
PR Number: #{pr.get("number")}
Title: {title}
Author: {author}
Base: {base_ref}
Head: {head_ref}

PR Description:
{body}

Unified Diff:
{diff_text}
"""
    return truncate(textwrap.dedent(prompt).strip(), MAX_PROMPT_CHARS)


def post_pr_comment(repo: str, pr_number: str, token: str, markdown: str) -> None:
    url = f"{GITHUB_API}/repos/{repo}/issues/{pr_number}/comments"
    github_request("POST", url, token, data={"body": markdown})


def main() -> None:
    github_token = require_env("GITHUB_TOKEN")
    openai_api_key = require_env("OPENAI_API_KEY")
    repo = require_env("GITHUB_REPOSITORY")
    pr_number = require_env("PR_NUMBER")

    pr_url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}"
    pr_data = github_request("GET", pr_url, github_token)
    diff_text = github_request(
        "GET",
        pr_url,
        github_token,
        accept="application/vnd.github.v3.diff",
    )

    trimmed_diff = truncate(diff_text, MAX_DIFF_CHARS)
    prompt = build_prompt(repo, pr_data, trimmed_diff)
    review_body = openai_request(openai_api_key, prompt)

    final_markdown = (
        f"## ChatGPT Review for PR #{pr_number}\n\n"
        f"{review_body}\n\n"
        "---\n"
        "_Triggered by PR comment containing `chatgpt`._"
    )

    write_output(final_markdown)
    post_pr_comment(repo, pr_number, github_token, final_markdown)
    print("ChatGPT review completed successfully.")


if __name__ == "__main__":
    main()
