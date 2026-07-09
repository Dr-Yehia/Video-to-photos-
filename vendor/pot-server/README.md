# PO Token Provider Server (vendored)

Prebuilt server from [bgutil-ytdlp-pot-provider](https://github.com/Brainicism/bgutil-ytdlp-pot-provider)
v1.3.1 (GPL-3.0, see LICENSE). It generates YouTube **PO (proof-of-origin)
tokens** via BotGuard — the mechanism that unlocks qualities above 360p
and bypasses "confirm you're not a bot" checks on server IPs. The same
approach major downloader sites rely on.

Changes from upstream: transpiled `build/` output committed as-is; the
optional native `canvas` dependency removed from `package.json` so
`npm install` needs no compiler toolchain.

The app starts this automatically (see `slide_extractor/pot_server.py`):
on first boot it runs `npm install --omit=dev` here, then launches
`node build/main.js --port 4416`. The yt-dlp plugin
(`bgutil-ytdlp-pot-provider` in requirements.txt) auto-detects the
server at `127.0.0.1:4416`. Everything degrades gracefully when Node.js
is unavailable.
