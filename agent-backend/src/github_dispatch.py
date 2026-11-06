"""Trigger the GitHub Actions render farm from the hosted backend.

The web studio on Render can't render video itself (no Node/Chrome by design).
Instead, this module commits a validated payload to `render-jobs/` in the repo
via the GitHub Contents API, which fires the `Render video` workflow. That lets
a phone kick off a render with no git or CLI.

Security: the token is read from the environment, used ONLY to PUT the single
render-payload file, and is never logged or returned to the client. The
User-Agent is a generic client name (never the user's email)."""

from __future__ import annotations

import base64
from typing import Optional

import httpx

try:
    from . import config
except ImportError:  # pragma: no cover
    import config  # type: ignore

_API = "https://api.github.com"
_UA = "omni-video-studio"


def configured() -> bool:
    return config.has_github()


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": _UA,
    }


def commit_payload(payload_json: str, title: str) -> dict:
    """PUT the payload to render-jobs/ on the repo, triggering the workflow.

    Returns {committed, path, branch, actions_url, commit_url}. Raises
    RuntimeError with a friendly message on any failure.
    """
    if not configured():
        raise RuntimeError(
            "GitHub dispatch is not configured. Set GITHUB_TOKEN (a fine-grained "
            "PAT with Contents: write on the repo) in the backend environment."
        )

    repo = config.GITHUB_REPO
    path = config.GITHUB_RENDER_PATH
    branch = config.GITHUB_BRANCH
    url = f"{_API}/repos/{repo}/contents/{path}"

    try:
        with httpx.Client(timeout=30) as client:
            # Updating an existing file needs its current blob SHA; a first
            # create omits it. A 404 simply means "not there yet".
            sha: Optional[str] = None
            r = client.get(url, headers=_headers(), params={"ref": branch})
            if r.status_code == 200:
                sha = r.json().get("sha")
            elif r.status_code not in (404,):
                raise RuntimeError(f"GitHub read failed ({r.status_code}): {r.text[:200]}")

            body = {
                "message": f"Render: {title[:60]}".strip() or "Render payload",
                "content": base64.b64encode(payload_json.encode("utf-8")).decode("ascii"),
                "branch": branch,
            }
            if sha:
                body["sha"] = sha

            pr = client.put(url, headers=_headers(), json=body)
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Could not reach GitHub: {exc}") from exc

    if pr.status_code not in (200, 201):
        # Common cases: 401 bad token, 403 missing Contents:write, 404 wrong repo.
        raise RuntimeError(f"GitHub commit failed ({pr.status_code}): {pr.text[:200]}")

    commit_url = (pr.json().get("commit") or {}).get("html_url", "")
    return {
        "committed": True,
        "path": path,
        "branch": branch,
        "actions_url": f"https://github.com/{repo}/actions",
        "commit_url": commit_url,
    }
