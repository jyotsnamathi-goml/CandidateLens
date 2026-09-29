"""
LinkedIn Public Profile Scraper and Evidence Extraction Service.
Extracts structured candidate profile data (headline, experience, skills, summary)
from LinkedIn profile URLs safely with SSRF protection, caching, and graceful fallbacks.
"""

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import trafilatura

from app.config import settings
from app.services.web_fetch import validate_url_safety

logger = logging.getLogger("candidatelens")


def clean_linkedin_url(input_val: str) -> str:
    """Extract canonical LinkedIn URL or username."""
    val = input_val.strip().rstrip("/")
    # If already a full URL
    if "linkedin.com" in val:
        if not val.startswith("http://") and not val.startswith("https://"):
            val = "https://" + val
        return val

    # Clean username / handle (e.g., 'in/alexchen', '@alexchen', 'alexchen')
    val = val.lstrip("@")
    if val.startswith("in/"):
        val = val[3:]
    return f"https://www.linkedin.com/in/{val}"


def extract_linkedin_username(url_or_handle: str) -> str:
    """Extract the username/vanity name from LinkedIn URL or handle."""
    clean = clean_linkedin_url(url_or_handle)
    parsed = urlparse(clean)
    parts = [p for p in parsed.path.split("/") if p]
    if "in" in parts:
        idx = parts.index("in")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return parts[-1] if parts else "candidate"


def get_artifact_cache_path(candidate_id: str, key: str) -> Path:
    cand_dir = settings.artifacts_path / candidate_id
    cand_dir.mkdir(parents=True, exist_ok=True)
    hash_key = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return cand_dir / f"{hash_key}.json"


class LinkedInClient:
    """
    Client for extracting public evidence from LinkedIn candidate URLs.
    Performs SSRF validation, parses OpenGraph tags, JSON-LD structured schemas,
    and profile body text, and provides structured evidence to LLM Call 1.
    """

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def fetch_profile_evidence(
        self,
        url_or_username: str,
        candidate_id: str,
    ) -> dict[str, Any]:
        """
        Fetch public LinkedIn profile information.
        Returns structured dictionary with profile details, headline, summary, and experiences.
        """
        url = clean_linkedin_url(url_or_username)
        username = extract_linkedin_username(url)
        cache_file = get_artifact_cache_path(candidate_id, f"linkedin_{username}")

        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        profile_data: dict[str, Any] = {
            "url": url,
            "username": username,
            "headline": "",
            "summary": "",
            "experiences": [],
            "skills": [],
            "raw_excerpt": "",
            "status": "extracted",
        }

        try:
            validate_url_safety(url)
        except Exception as e:
            logger.warning(f"LinkedIn URL safety check failed for {url}: {e}")
            profile_data["status"] = "unsafe_url"
            return profile_data

        try:
            with httpx.Client(headers=self.headers, timeout=12.0, follow_redirects=True) as client:
                resp = client.get(url)

                if resp.status_code == 200:
                    html_text = resp.text

                    # 1. Extract OpenGraph and Title metadata
                    og_title_match = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
                    og_desc_match = re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
                    meta_desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
                    title_match = re.search(r'<title>([^<]+)</title>', html_text, re.IGNORECASE)

                    headline = ""
                    if og_title_match:
                        headline = og_title_match.group(1).strip()
                    elif title_match:
                        headline = title_match.group(1).strip()

                    # Clean headline
                    if " | LinkedIn" in headline:
                        headline = headline.replace(" | LinkedIn", "").strip()

                    profile_data["headline"] = headline

                    summary = ""
                    if og_desc_match:
                        summary = og_desc_match.group(1).strip()
                    elif meta_desc_match:
                        summary = meta_desc_match.group(1).strip()
                    profile_data["summary"] = summary

                    # 2. Extract JSON-LD schema if present
                    json_ld_matches = re.findall(r'<script\s+type=["\']application/ld\+json["\']\s*>(.*?)</script>', html_text, re.DOTALL | re.IGNORECASE)
                    for jld in json_ld_matches:
                        try:
                            data = json.loads(jld.strip())
                            if isinstance(data, dict):
                                if data.get("@type") == "Person":
                                    if not profile_data["headline"] and data.get("jobTitle"):
                                        profile_data["headline"] = data.get("jobTitle")
                                    if not profile_data["summary"] and data.get("description"):
                                        profile_data["summary"] = data.get("description")
                                    if data.get("worksFor"):
                                        wf = data.get("worksFor")
                                        if isinstance(wf, list):
                                            profile_data["experiences"].extend([c.get("name") for c in wf if isinstance(c, dict) and c.get("name")])
                                        elif isinstance(wf, dict) and wf.get("name"):
                                            profile_data["experiences"].append(wf.get("name"))
                        except Exception:
                            pass

                    # 3. Extract readable text using trafilatura
                    extracted_text = trafilatura.extract(html_text) or trafilatura.html2txt(html_text) or ""
                    clean_text = " ".join(extracted_text.split())
                    profile_data["raw_excerpt"] = clean_text[:3000]

                    # 4. Extract common skill keywords from text
                    common_tech_skills = [
                        "Python", "TypeScript", "JavaScript", "React", "Node.js", "Go", "Golang",
                        "Rust", "Java", "C++", "AWS", "GCP", "Kubernetes", "Docker", "PostgreSQL",
                        "MySQL", "Redis", "Kafka", "GraphQL", "FastAPI", "Django", "PyTorch", "TensorFlow",
                        "LLM", "Microservices", "CI/CD", "Next.js", "TailwindCSS", "Distributed Systems"
                    ]
                    combined_profile_text = f"{clean_text} {profile_data['headline']} {profile_data['summary']}"
                    detected_skills = [s for s in common_tech_skills if re.search(rf"\b{re.escape(s)}\b", combined_profile_text, re.IGNORECASE)]
                    profile_data["skills"] = detected_skills

                elif resp.status_code in [403, 999, 429]:
                    # LinkedIn authwall / rate limit fallback
                    logger.info(f"LinkedIn returned status {resp.status_code} for {url}. Using structured vanity profile fallback.")
                    profile_data["status"] = "authwall_fallback"
                    profile_data["headline"] = f"LinkedIn Member ({username})"
                    profile_data["raw_excerpt"] = f"Public LinkedIn Profile: {url}"
                else:
                    logger.warning(f"LinkedIn HTTP error {resp.status_code} for {url}")
                    profile_data["status"] = f"http_{resp.status_code}"

        except Exception as e:
            logger.warning(f"Failed to scrape LinkedIn URL {url}: {e}")
            profile_data["status"] = "error"
            profile_data["raw_excerpt"] = f"LinkedIn profile reference: {url}"

        # Cache locally
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(profile_data, f, indent=2)
        except Exception:
            pass

        return profile_data
