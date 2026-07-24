"""Auto-managed PO (proof-of-origin) token server.

YouTube locks qualities above 360p and shows bot checks unless requests
carry a BotGuard PO token — this is why every free download channel
kept collapsing to 360p. The vendored bgutil server (vendor/pot-server)
generates those tokens; the bgutil yt-dlp plugin picks them up
automatically once the server answers on 127.0.0.1:4416.

ensure_pot_server() is idempotent and safe to call on every app start:
  - no Node.js on the host  -> logged, app continues without tokens
  - first run              -> `npm install --omit=dev` (pure-JS deps,
                               no compiler needed), then launch
  - already running        -> ping succeeds, nothing to do
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading

import requests

PORT = int(os.environ.get("POT_SERVER_PORT", "4416"))
_VENDOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "vendor", "pot-server")
_lock = threading.Lock()
_started = False


def pot_server_alive(timeout: float = 1.5) -> bool:
    try:
        r = requests.get(f"http://127.0.0.1:{PORT}/ping", timeout=timeout)
        return r.ok
    except Exception:
        return False


def _launch() -> str:
    node = shutil.which("node") or shutil.which("nodejs")
    if not node:
        return "Node.js not found — PO token server disabled"
    vendor = os.path.abspath(_VENDOR_DIR)
    main_js = os.path.join(vendor, "build", "main.js")
    if not os.path.isfile(main_js):
        return f"pot server files missing at {vendor}"

    if not os.path.isdir(os.path.join(vendor, "node_modules")):
        npm = shutil.which("npm")
        if not npm:
            return "npm not found — cannot install pot server deps"
        try:
            subprocess.run(
                [npm, "install", "--omit=dev", "--no-audit", "--no-fund"],
                cwd=vendor, check=True, capture_output=True, timeout=600)
        except Exception as exc:
            return f"npm install failed: {exc}"

    try:
        subprocess.Popen(
            [node, main_js, "--port", str(PORT)],
            cwd=vendor,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True)
    except Exception as exc:
        return f"failed to launch pot server: {exc}"
    return "launched"


def ensure_pot_server(background: bool = True) -> None:
    """Start the PO token server if possible, and make sure a JS runtime
    exists. With background=True the potentially slow first-time work
    (npm install, Deno download) runs in a daemon thread so the app UI
    is never blocked."""
    global _started
    with _lock:
        if _started:
            return
        _started = True

    def work():
        # Warm the JS runtime first: without it yt-dlp cannot decode
        # YouTube's ciphered formats at all.
        try:
            from .jsruntime import js_runtimes
            js_runtimes()
        except Exception:
            pass
        if not pot_server_alive():
            _launch()

    if background:
        threading.Thread(target=work, daemon=True).start()
    else:
        work()
