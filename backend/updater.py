"""
Check GitHub Releases for available updates.
"""

import urllib.request
import json
import logging
from .version import __version__

GITHUB_REPO = "Adityak102006/Neptune"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

logger = logging.getLogger(__name__)

_cached_update = None


def check_for_update() -> dict | None:
    """
    Check GitHub for a newer release.
    Returns dict with version, url, body if update available, else None.
    Caches the result so we only hit GitHub once per session.
    """
    global _cached_update

    if _cached_update is not None:
        return _cached_update if _cached_update else None

    try:
        req = urllib.request.Request(
            RELEASES_URL,
            headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "Neptune"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        latest_tag = data.get("tag_name", "").lstrip("v")
        if not latest_tag:
            _cached_update = {}
            return None

        # Simple version comparison (major.minor.patch)
        def version_tuple(v: str):
            return tuple(int(x) for x in v.split(".")[:3])

        if version_tuple(latest_tag) > version_tuple(__version__):
            _cached_update = {
                "current_version": __version__,
                "latest_version": latest_tag,
                "download_url": data.get("html_url", ""),
                "release_notes": data.get("body", ""),
            }
            return _cached_update

        _cached_update = {}
        return None

    except Exception as e:
        logger.debug(f"Update check failed: {e}")
        _cached_update = {}
        return None
