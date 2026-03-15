import os

import requests

OPENAI_TOKEN = os.environ["OPENAI_TOKEN"]
PR_NUMBER = os.environ["PR_NUMBER"]
REPO = os.environ["REPO"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

headers = {
    "Authorization": f"Bearer {OPENAI_TOKEN}",
    "Content-Type": "application/json",
}

prompt = """
You are reviewing a pull request for a documentation and CI governance repository.

Focus on:
- CI workflow correctness
- documentation structure
- governance compliance
- GitHub Actions best practices
"""

payload = {
    "model": "gpt-4.1-mini",
    "messages": [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": "Review this pull request for CI and docs improvements.",
        },
    ],
}

response = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers=headers,
    json=payload,
)

review = response.json()["choices"][0]["message"]["content"]

gh_headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

comment_payload = {"body": f"### ChatGPT Review\n\n{review}"}

requests.post(
    f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments",
    headers=gh_headers,
    json=comment_payload,
)
