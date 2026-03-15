#!/usr/bin/env python3

import os

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

# ------------------------------------------------------------
# File filtering rules
# ------------------------------------------------------------

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
    return any(path.startswith(p) for p in ALLOWED_PATH_PREFIXES)


# ------------------------------------------------------------
# Fetch PR files
# ------------------------------------------------------------

files_url = f"{API}/pulls/{PR_NUMBER}/files"
resp = requests.get(files_url, headers=HEADERS)
resp.raise_for_status()

files = resp.json()

diff_chunks = []

for f in files:
    path = f["filename"]

    if not allowed_file(path):
        continue

    patch = f.get("patch", "")

    if not patch:
        continue

    diff_chunks.append(f"### {path}\n{patch}")

if not diff_chunks:
    diff_chunks.append("No relevant files matched review filters.")

diff_text = "\n\n".join(diff_chunks)

# limit prompt size to avoid token explosions
MAX_CHARS = 12000
diff_text = diff_text[:MAX_CHARS]

# ------------------------------------------------------------
# Build prompt
# ------------------------------------------------------------

prompt = f"""
You are reviewing a pull request for a documentation and CI governance repository.

Focus on:
- GitHub Actions workflow correctness
- CI reliability and security
- documentation structure
- repository governance compliance
- Docusaurus documentation best practices

Only comment on real issues or improvements.

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

response = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers=OPENAI_HEADERS,
    json=payload,
)

response.raise_for_status()

review = response.json()["choices"][0]["message"]["content"]

# ------------------------------------------------------------
# Post PR comment
# ------------------------------------------------------------

comment_payload = {"body": f"### 🤖 ChatGPT CI Review\n\n{review}"}

comment_url = f"{API}/issues/{PR_NUMBER}/comments"

requests.post(comment_url, headers=HEADERS, json=comment_payload).raise_for_status()

print("Review posted successfully.")
