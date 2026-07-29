"""
Vercel Python serverless function.
Runs yt-dlp against a URL and returns direct, unproxied format links.
No media ever passes through this server — we only return metadata + links,
so the browser downloads straight from the source CDN.
"""

import json
from http.server import BaseHTTPRequestHandler

from yt_dlp import YoutubeDL


def _human_size(num_bytes):
    if not num_bytes:
        return None
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _pick_formats(info):
    formats = info.get("formats") or []
    picked = []

    for f in formats:
        vcodec = f.get("vcodec") or "none"
        acodec = f.get("acodec") or "none"
        has_video = vcodec != "none"
        has_audio = acodec != "none"

        # Skip formats with no direct URL (e.g. fragmented/DASH manifests
        # that need special handling) — keep this simple and downloadable.
        if not f.get("url"):
            continue

        if has_video and has_audio:
            kind = "video+audio"
        elif has_video:
            kind = "video only"
        elif has_audio:
            kind = "audio only"
        else:
            continue

        picked.append({
            "format_id": f.get("format_id"),
            "ext": f.get("ext"),
            "kind": kind,
            "resolution": f.get("format_note") or f.get("resolution") or (
                f"{f.get('height')}p" if f.get("height") else None
            ),
            "fps": f.get("fps"),
            "filesize": _human_size(f.get("filesize") or f.get("filesize_approx")),
            "abr": f.get("abr"),
            "url": f.get("url"),
        })

    # Progressive (video+audio) formats first, then video-only, then audio-only.
    order = {"video+audio": 0, "video only": 1, "audio only": 2}
    picked.sort(key=lambda x: order.get(x["kind"], 3))
    return picked


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            data = json.loads(raw or b"{}")
            url = (data.get("url") or "").strip()
        except Exception:
            self._send_json(400, {"error": "Invalid request body."})
            return

        if not url:
            self._send_json(400, {"error": "Please provide a 'url'."})
            return

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "skip_download": True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            self._send_json(502, {"error": f"Extraction failed: {str(e)}"})
            return

        if info is None:
            self._send_json(502, {"error": "No information could be extracted."})
            return

        formats = _pick_formats(info)

        # Fallback: some extractors only expose a single top-level url.
        if not formats and info.get("url"):
            formats = [{
                "format_id": info.get("format_id") or "direct",
                "ext": info.get("ext"),
                "kind": "video+audio",
                "resolution": info.get("resolution"),
                "fps": info.get("fps"),
                "filesize": _human_size(info.get("filesize") or info.get("filesize_approx")),
                "abr": info.get("abr"),
                "url": info.get("url"),
            }]

        self._send_json(200, {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "source": info.get("webpage_url") or url,
            "formats": formats,
        })
