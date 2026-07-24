"""JavaScript runtime for yt-dlp — the piece that unlocks YouTube formats.

YouTube ships most formats with an encrypted `signatureCipher` instead
of a plain URL. yt-dlp must run YouTube's own JavaScript to solve that
challenge, and for this it needs a JS runtime. By default it looks for
**deno only**; when no runtime is available it silently SKIPS every
ciphered format, so the format list comes back empty and the download
fails with the misleading "Requested format is not available" — even
for a fully authenticated session with valid cookies.

This module finds a usable runtime (deno / bun / node >= 22 / quickjs),
and if none exists it downloads the standalone Deno binary once into a
cache directory. Everything degrades gracefully: if no runtime can be
obtained, callers simply get {} and behave as before.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import threading
import zipfile
from typing import Optional, Tuple

# yt-dlp rejects older Node builds ("unsupported"); 22 is the first
# release line it accepts.
_MIN_NODE_MAJOR = 22

_DENO_URLS = {
    "x86_64": "https://github.com/denoland/deno/releases/latest/download/"
              "deno-x86_64-unknown-linux-gnu.zip",
    "aarch64": "https://github.com/denoland/deno/releases/latest/download/"
               "deno-aarch64-unknown-linux-gnu.zip",
}

_lock = threading.Lock()
_cached: Optional[Tuple[dict, str]] = None


def _cache_dir() -> str:
    base = os.environ.get("V2S_CACHE_DIR") or os.path.expanduser("~/.cache")
    path = os.path.join(base, "video-to-slides")
    os.makedirs(path, exist_ok=True)
    return path


def _version_of(path: str) -> str:
    try:
        r = subprocess.run([path, "--version"], capture_output=True,
                           text=True, timeout=20)
        return (r.stdout or r.stderr).strip().splitlines()[0]
    except Exception:
        return ""


def _node_major(path: str) -> int:
    v = _version_of(path).lstrip("v")
    try:
        return int(v.split(".")[0])
    except Exception:
        return 0


def _find_existing() -> Optional[Tuple[str, str]]:
    """(runtime_name, executable_path) for the first usable runtime."""
    for name in ("deno", "bun", "quickjs"):
        exe = shutil.which(name)
        if exe:
            return name, exe

    # Node must be recent enough, and a modern build often sits outside
    # PATH next to an older default one (common on hosting images).
    candidates = [shutil.which("node"), shutil.which("nodejs")]
    candidates += [f"/opt/node{v}/bin/node" for v in (24, 23, 22)]
    candidates.append(os.path.join(_cache_dir(), "node", "bin", "node"))
    best = None
    for exe in candidates:
        if exe and os.path.isfile(exe) and _node_major(exe) >= _MIN_NODE_MAJOR:
            best = exe
            break
    if best:
        return "node", best

    cached_deno = os.path.join(_cache_dir(), "deno")
    if os.path.isfile(cached_deno) and os.access(cached_deno, os.X_OK):
        return "deno", cached_deno
    return None


def _download_deno() -> Optional[str]:
    """Fetch the standalone Deno binary (single file, no dependencies)."""
    import platform

    import requests

    url = _DENO_URLS.get(platform.machine())
    if not url:
        return None
    dest_zip = os.path.join(_cache_dir(), "deno.zip")
    dest = os.path.join(_cache_dir(), "deno")
    try:
        with requests.get(url, stream=True, timeout=(15, 120)) as r:
            r.raise_for_status()
            with open(dest_zip, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
        with zipfile.ZipFile(dest_zip) as z:
            member = next((n for n in z.namelist()
                           if os.path.basename(n) == "deno"), None)
            if not member:
                return None
            with z.open(member) as src, open(dest, "wb") as out:
                shutil.copyfileobj(src, out)
        os.chmod(dest, os.stat(dest).st_mode | stat.S_IEXEC | stat.S_IXGRP
                 | stat.S_IXOTH)
        return dest if _version_of(dest) else None
    except Exception:
        return None
    finally:
        try:
            os.remove(dest_zip)
        except OSError:
            pass


def js_runtimes(allow_download: bool = True) -> Tuple[dict, str]:
    """Return (js_runtimes option for yt-dlp, human-readable status).

    Cached: detection and any download happen once per process.
    """
    global _cached
    with _lock:
        if _cached is not None:
            return _cached

        found = _find_existing()
        if not found and allow_download and \
                os.environ.get("V2S_DENO_DOWNLOAD", "1") != "0":
            path = _download_deno()
            if path:
                found = ("deno", path)

        if not found:
            _cached = ({}, "none — YouTube's ciphered formats cannot be "
                           "decoded (this is what makes the format list "
                           "empty)")
        else:
            name, exe = found
            _cached = ({name: {"path": exe}},
                       f"{name} ({_version_of(exe) or exe}) ✓")
        return _cached
