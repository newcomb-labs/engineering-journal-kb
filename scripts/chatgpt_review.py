#!/usr/bin/env python3

import os
import time

import requests

OPENAI_TOKEN = os.environ["OPENAI_TOKEN"]
PR_NUMBER = os.environ["PR_NUMBER"]
REPO = os.environ["REPO"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

API = f"https://api.github.com/repos/{REPO}"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

OPENAI_HEADERS = {
    "Authorization": f"Bearer {OPENAI_TOKEN}",
    "Content-Type": "application/json",
}

MAX_RETRIES = 5
BACKOFF = 10
MAX_CHARS = 12000

ALLOWED_PATH_PREFIXES = [
    ".github/workflows/",
    "scripts/",
    "docs/",
    "website/",
]

ALLOWED_ROOT_FILES = [
    ".pre-commit-config.yaml",
    "cspell.config.yaml",
    ".lychee.toml",
    "package.json",
    "README.md",
]


def allowed_file(path: str) -> bool:
    if path in ALLOWED_ROOT_FILES:
        return True
    return any(path.startswith(prefix) for prefix in ALLOWED_PATH_PREFIXES)


def post_pr_comment(body: str) -> None:
    comment_url = f"{API}/issues/{PR_NUMBER}/comments"
    comment_payload = {"body": body}
    requests.post(comment_url, headers=HEADERS, json=comment_payload).raise_for_status()


files_url = f"{API}/pulls/{PR_NUMBER}/files"
resp = requests.get(files_url, headers=HEADERS)
resp.raise_for_status()

files = resp.json()
diff_chunks = []

for file_obj in files:
    path = file_obj["filename"]

    if not allowed_file(path):
        continue

    patch = file_obj.get("patch", "")
    if not patch:
        continue

    diff_chunks.append(f"### {path}\n{patch}")

if not diff_chunks:
    diff_chunks.append("No relevant files matched review filters.")

diff_text = "\n\n".join(diff_chunks)[:MAX_CHARS]

prompt = f"""
You are reviewing a pull request for a documentation and CI governance repository.

Focus on:
- GitHub Actions workflow correctness
- CI reliability and security
- documentation structure
- repository governance compliance
- Docusaurus documentation best practices

Only comment on real issues or improvements.
Be concise and practical.
If there are no significant issues, say that clearly.

Pull request changes:

{diff_text}
"""

payload = {
    "model": "gpt-4o-mini",
    "messages": [
        {"role": "system", "content": "You are a senior DevOps reviewer."},
        {"role": "user", "content": prompt},
    ],
}

review = None

for attempt in range(MAX_RETRIES):
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=OPENAI_HEADERS,
        json=payload,
        timeout=120,
    )

    if response.status_code == 200:
        review = response.json()["choices"][0]["message"]["content"]
        break

    if response.status_code == 429:
        wait = BACKOFF * (attempt + 1)
        print(f"Rate limited. Waiting {wait}s before retry...")
        time.sleep(wait)
        continue

    response.raise_for_status()

if review is None:
    fallback = """### 🤖 ChatGPT CI Review

ChatGPT review could not complete because the OpenAI API returned repeated rate-limit responses (HTTP 429).

Please retry by commenting `chatgpt` again on this pull request.
"""
    post_pr_comment(fallback)
    print("Posted fallback comment after repeated rate limits.")
    raise SystemExit(0)

comment_body = f"### 🤖 ChatGPT CI Review\n\n{review}"
post_pr_comment(comment_body)

print("Review posted successfully.")
