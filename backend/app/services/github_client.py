"""
GitHub REST API client for candidate evidence extraction.
Picks top repositories based on competency overlap, recency, and non-fork status.
Caches artifacts locally and handles rate limits and 404s gracefully.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger("candidatelens")


def clean_github_username(input_val: str) -> str:
    """Extract username from string or URL."""
    val = input_val.strip().rstrip("/")
    if "github.com/" in val:
        val = val.split("github.com/")[-1].split("/")[0]
    # Remove @ prefix if present
    val = val.lstrip("@")
    return val


def get_artifact_cache_path(candidate_id: str, key: str) -> Path:
    cand_dir = settings.artifacts_path / candidate_id
    cand_dir.mkdir(parents=True, exist_ok=True)
    hash_key = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return cand_dir / f"{hash_key}.json"


def score_repo(repo: dict[str, Any], competencies: list[str]) -> float:
    """Deterministic score for ranking repos: overlap with competencies + recency + non-fork bonus."""
    name = (repo.get("name") or "").lower()
    desc = (repo.get("description") or "").lower()
    topics = [t.lower() for t in repo.get("topics", [])]
    combined_text = f"{name} {desc} {' '.join(topics)}"

    overlap_score = 0.0
    for comp in competencies:
        for word in comp.lower().split():
            if len(word) > 3 and word in combined_text:
                overlap_score += 1.0

    # Non-fork bonus
    fork_bonus = 0.0 if repo.get("fork") else 1.5

    # Recency bonus based on pushed_at
    recency_bonus = 0.0
    pushed_at = repo.get("pushed_at")
    if pushed_at:
        try:
            dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            years_old = (datetime.now(timezone.utc) - dt).days / 365.25
            recency_bonus = max(0.0, 2.0 - years_old * 0.5)
        except Exception:
            pass

    stars_bonus = min(float(repo.get("stargazers_count", 0)) * 0.1, 1.0)
    return overlap_score + fork_bonus + recency_bonus + stars_bonus


class GitHubClient:
    def __init__(self, token: str | None = None):
        self.token = token or settings.GITHUB_TOKEN
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CandidateLens-Engine",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def fetch_user_evidence(
        self,
        username: str,
        competencies: list[str],
        candidate_id: str,
    ) -> dict[str, Any]:
        """
        Fetch candidate's top repositories and compute activity metrics.
        Returns a structured dictionary of public evidence and metrics.
        """
        user = clean_github_username(username)
        cache_file = get_artifact_cache_path(candidate_id, f"gh_user_{user}")

        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        metrics: dict[str, Any] = {
            "username": user,
            "repos_examined": 0,
            "top_repos": [],
            "total_commits_scanned": 0,
            "user_commit_share": 1.0,
            "last_commit_date": None,
            "original_repos_count": 0,
            "fork_count": 0,
        }

        with httpx.Client(headers=self.headers, timeout=12.0) as client:
            # 1. Fetch public repos
            repos_url = f"https://api.github.com/users/{user}/repos?per_page=30&sort=pushed"
            try:
                resp = client.get(repos_url)
                if resp.status_code == 404:
                    logger.warning(f"GitHub user {user} not found (404).")
                    return metrics
                elif resp.status_code in [403, 429]:
                    logger.warning(f"GitHub API rate limit exceeded ({resp.status_code}).")
                    return metrics
                resp.raise_for_status()
                all_repos = resp.json()
            except Exception as e:
                logger.warning(f"Failed to fetch GitHub repos for {user}: {e}")
                return metrics

            metrics["repos_examined"] = len(all_repos)
            for r in all_repos:
                if r.get("fork"):
                    metrics["fork_count"] += 1
                else:
                    metrics["original_repos_count"] += 1

            # 2. Score and pick top N
            scored_repos = sorted(
                all_repos,
                key=lambda r: score_repo(r, competencies),
                reverse=True
            )[: settings.GITHUB_MAX_REPOS]

            # 3. For each top repo, fetch details
            total_user_commits = 0
            total_all_commits = 0
            latest_commit_dt: datetime | None = None

            for repo in scored_repos:
                repo_name = repo.get("name")
                owner = repo.get("owner", {}).get("login", user)

                # Fetch README
                readme_text = ""
                try:
                    r_readme = client.get(f"https://api.github.com/repos/{owner}/{repo_name}/readme")
                    if r_readme.status_code == 200:
                        import base64
                        content_b64 = r_readme.json().get("content", "")
                        raw_bytes = base64.b64decode(content_b64)
                        readme_text = raw_bytes.decode("utf-8", errors="replace")[:4000]
                except Exception:
                    pass

                # Scan commits
                repo_commits_scanned = 0
                repo_user_commits = 0
                try:
                    commits_url = f"https://api.github.com/repos/{owner}/{repo_name}/commits?per_page={min(settings.GITHUB_MAX_COMMITS_SCANNED, 50)}"
                    r_commits = client.get(commits_url)
                    if r_commits.status_code == 200:
                        commits = r_commits.json()
                        repo_commits_scanned = len(commits)
                        total_all_commits += repo_commits_scanned
                        for c in commits:
                            author_login = c.get("author", {}).get("login", "") if c.get("author") else ""
                            commit_date = c.get("commit", {}).get("author", {}).get("date")
                            if author_login.lower() == user.lower() or not author_login:
                                repo_user_commits += 1
                                total_user_commits += 1

                            if commit_date:
                                try:
                                    dt = datetime.fromisoformat(commit_date.replace("Z", "+00:00"))
                                    if latest_commit_dt is None or dt > latest_commit_dt:
                                        latest_commit_dt = dt
                                except Exception:
                                    pass
                except Exception:
                    pass

                metrics["top_repos"].append({
                    "name": repo_name,
                    "html_url": repo.get("html_url"),
                    "description": repo.get("description"),
                    "language": repo.get("language"),
                    "topics": repo.get("topics", []),
                    "stars": repo.get("stargazers_count", 0),
                    "fork": repo.get("fork", False),
                    "created_at": repo.get("created_at"),
                    "pushed_at": repo.get("pushed_at"),
                    "readme_excerpt": readme_text,
                    "commits_scanned": repo_commits_scanned,
                    "user_commits": repo_user_commits,
                })

            metrics["total_commits_scanned"] = total_all_commits
            if total_all_commits > 0:
                metrics["user_commit_share"] = round(total_user_commits / total_all_commits, 2)
            else:
                metrics["user_commit_share"] = 1.0

            if latest_commit_dt:
                metrics["last_commit_date"] = latest_commit_dt.strftime("%Y-%m-%d")

        # Cache artifact
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)
        except Exception:
            pass

        return metrics
