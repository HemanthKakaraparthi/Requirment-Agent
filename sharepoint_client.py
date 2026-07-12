"""
SharePoint client for the Combined Agent.

Uses Microsoft Graph API with app-only auth (client_credentials flow) —
exactly the pattern from your buddy's working code, generalised to cover:
  • listing files in a folder
  • downloading a file (PDF, DOCX, XLSX, TXT) to a temp path
  • uploading a file (PRD markdown) back to SharePoint

Required env vars in SDLC/.env:
    SHAREPOINT_TENANT_ID     = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    SHAREPOINT_CLIENT_ID     = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    SHAREPOINT_CLIENT_SECRET = your-client-secret
    SHAREPOINT_SITE_URL      = https://anheuserbuschinbev.sharepoint.com/sites/TestOps2025364

Optional:
    SHAREPOINT_READ_FOLDER   = /Documents/Briefs    (default: root)
    SHAREPOINT_PRD_FOLDER    = /Documents/PRDs       (default: same as READ_FOLDER)

Azure AD app needs these Graph API *application* permissions (not delegated):
    Sites.ReadWrite.All   (or Sites.Read.All if you only want read access)
After granting, an admin must click "Grant admin consent" in the Portal.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional

import requests

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def is_configured() -> bool:
    """Return True if all required SharePoint env vars are set."""
    return all(
        os.getenv(k)
        for k in (
            "SHAREPOINT_TENANT_ID",
            "SHAREPOINT_CLIENT_ID",
            "SHAREPOINT_CLIENT_SECRET",
            "SHAREPOINT_SITE_URL",
        )
    )


# ── Auth ─────────────────────────────────────────────────────────────────────

def _get_token() -> str:
    """
    Acquire a fresh app-only access token via client_credentials.
    Tokens live ~1 hour; we fetch a new one per tool-call to avoid expiry.
    (Cheap — one HTTPS round-trip, ~200ms.)
    """
    tenant_id     = os.environ["SHAREPOINT_TENANT_ID"]
    client_id     = os.environ["SHAREPOINT_CLIENT_ID"]
    client_secret = os.environ["SHAREPOINT_CLIENT_SECRET"]

    res = requests.post(
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        data={
            "grant_type":    "client_credentials",
            "client_id":     client_id,
            "client_secret": client_secret,
            "scope":         "https://graph.microsoft.com/.default",
        },
        timeout=30,
    )
    res.raise_for_status()
    token = res.json().get("access_token")
    if not token:
        raise RuntimeError(f"Token response had no access_token: {res.text[:300]}")
    return token


def _headers() -> dict:
    return {"Authorization": f"Bearer {_get_token()}"}


# ── Site + Drive resolution ───────────────────────────────────────────────────

# Simple module-level cache (no lru_cache so we can clear it if needed).
_site_id_cache:  Optional[str] = None
_drive_id_cache: Optional[str] = None


def _get_site_id() -> str:
    global _site_id_cache
    if _site_id_cache:
        return _site_id_cache

    raw = os.environ["SHAREPOINT_SITE_URL"].strip().rstrip("/")
    # Strip scheme: https://anheuserbuschinbev.sharepoint.com/sites/TestOps2025364
    raw = raw.replace("https://", "").replace("http://", "")
    # Split into hostname + site-path
    parts    = raw.split("/", 1)
    hostname = parts[0]                        # anheuserbuschinbev.sharepoint.com
    sitepath = parts[1] if len(parts) > 1 else ""  # sites/TestOps2025364

    url = f"{GRAPH_BASE}/sites/{hostname}:/{sitepath}"
    res = requests.get(url, headers=_headers(), timeout=30)
    if not res.ok:
        raise RuntimeError(
            f"Could not resolve SharePoint site.\n"
            f"URL tried: {url}\n"
            f"Response {res.status_code}: {res.text[:400]}\n"
            f"Make sure SHAREPOINT_SITE_URL is correct and the app has Sites.ReadWrite.All."
        )
    _site_id_cache = res.json()["id"]
    return _site_id_cache


def _get_drive_id() -> str:
    global _drive_id_cache
    if _drive_id_cache:
        return _drive_id_cache

    site_id = _get_site_id()
    res = requests.get(
        f"{GRAPH_BASE}/sites/{site_id}/drive",
        headers=_headers(),
        timeout=30,
    )
    res.raise_for_status()
    _drive_id_cache = res.json()["id"]
    return _drive_id_cache


# ── Public API ────────────────────────────────────────────────────────────────

def list_folder(folder_path: str = "") -> list[dict]:
    """
    List the contents of a folder in the SharePoint document library.

    Args:
        folder_path: Site-relative path e.g. "Documents/Briefs".
                     Empty string or "/" lists the root.
    Returns:
        List of dicts with keys: id, name, type, extension, size_kb, modified,
        download_url (files only).
    """
    site_id  = _get_site_id()
    drive_id = _get_drive_id()
    hdr      = _headers()

    folder_path = folder_path.strip("/")
    if folder_path:
        url = f"{GRAPH_BASE}/sites/{site_id}/drives/{drive_id}/root:/{folder_path}:/children"
    else:
        url = f"{GRAPH_BASE}/sites/{site_id}/drives/{drive_id}/root/children"

    items = []
    # Graph paginates at 200 items — follow @odata.nextLink
    while url:
        res = requests.get(url, headers=hdr, timeout=30)
        if not res.ok:
            raise RuntimeError(
                f"list_folder failed for path '{folder_path}': "
                f"{res.status_code} {res.text[:300]}"
            )
        body = res.json()
        for item in body.get("value", []):
            is_folder = "folder" in item
            items.append({
                "id":           item["id"],
                "name":         item["name"],
                "type":         "folder" if is_folder else "file",
                "extension":    "" if is_folder else Path(item["name"]).suffix.lower(),
                "size_kb":      round(item.get("size", 0) / 1024, 1),
                "modified":     item.get("lastModifiedDateTime", ""),
                "download_url": item.get("@microsoft.graph.downloadUrl", ""),
            })
        url = body.get("@odata.nextLink")   # None when we've reached the last page

    return items


def download_file(item_id: str) -> tuple[bytes, str]:
    """
    Download a file from SharePoint by its Graph item ID.

    Returns:
        (content_bytes, filename)
    """
    site_id  = _get_site_id()
    drive_id = _get_drive_id()
    hdr      = _headers()

    # First get the item metadata to know the filename
    meta_res = requests.get(
        f"{GRAPH_BASE}/sites/{site_id}/drives/{drive_id}/items/{item_id}",
        headers=hdr,
        timeout=30,
    )
    meta_res.raise_for_status()
    filename = meta_res.json().get("name", "download")

    # Now download the content (Graph redirects to the CDN URL)
    content_res = requests.get(
        f"{GRAPH_BASE}/sites/{site_id}/drives/{drive_id}/items/{item_id}/content",
        headers=hdr,
        allow_redirects=True,
        timeout=120,
    )
    content_res.raise_for_status()
    return content_res.content, filename


def download_to_temp(item_id: str) -> tuple[Path, str]:
    """
    Download a SharePoint file to a system temp file.

    Returns:
        (temp_path, filename) — temp_path has the correct extension.
    """
    content, filename = download_file(item_id)
    suffix = Path(filename).suffix or ".tmp"

    tmp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
        prefix="sp_download_",
    )
    tmp.write(content)
    tmp.close()
    return Path(tmp.name), filename


def upload_file(folder_path: str, filename: str, content: bytes, content_type: str = "text/plain; charset=utf-8") -> dict:
    """
    Upload (or replace) a file in a SharePoint folder.

    Args:
        folder_path:  Site-relative folder e.g. "Documents/PRDs".
                      Empty string uploads to the root library.
        filename:     File name including extension e.g. "PRD_feature_x.md".
        content:      File bytes.
        content_type: MIME type (default text/plain for .md files).
    Returns:
        dict with id, name, web_url, size_kb of the created/updated item.
    """
    site_id  = _get_site_id()
    drive_id = _get_drive_id()
    hdr      = _headers()
    hdr["Content-Type"] = content_type

    folder_path = folder_path.strip("/")
    if folder_path:
        url = f"{GRAPH_BASE}/sites/{site_id}/drives/{drive_id}/root:/{folder_path}/{filename}:/content"
    else:
        url = f"{GRAPH_BASE}/sites/{site_id}/drives/{drive_id}/root:/{filename}:/content"

    res = requests.put(url, headers=hdr, data=content, timeout=120)
    if not res.ok:
        raise RuntimeError(
            f"upload_file failed for '{folder_path}/{filename}': "
            f"{res.status_code} {res.text[:400]}"
        )
    item = res.json()
    return {
        "id":      item["id"],
        "name":    item["name"],
        "web_url": item.get("webUrl", ""),
        "size_kb": round(item.get("size", 0) / 1024, 1),
    }
