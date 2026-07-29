# PULL — direct media link grabber

A minimal personal-use site: paste a URL, it runs `yt-dlp` server-side to find
the direct file URLs, and your browser downloads straight from the source.
No video ever passes through or gets stored on the server — the Python
function only returns metadata + links.

## How it works

- `index.html` / `style.css` / `app.js` — static frontend, no build step.
- `api/extract.py` — a Vercel **Python** serverless function. It calls
  `yt-dlp` (the real pip package) and returns the list of available formats
  with their direct URLs.
- `requirements.txt` — tells Vercel to `pip install yt-dlp` for that function.
- `vercel.json` — raises the function's timeout to 60s and gives it 1GB of
  memory (extraction can be slow on some sites; the default 10s is too tight).

This avoids the common failure mode of Node wrappers like `yt-dlp-exec` on
Vercel, which need a Python runtime under the hood and don't work out of the
box on serverless. Using Vercel's native Python function support sidesteps
that entirely.

## Deploy (free Vercel plan)

1. Push this folder to a GitHub repo (can be private, since it's for
   personal use).
2. On [vercel.com](https://vercel.com), **Add New → Project**, import the
   repo.
3. Framework preset: leave as **Other** / no framework — no build command
   needed.
4. Deploy. That's it — Vercel auto-detects `api/extract.py` as a Python
   function from `requirements.txt`.

No environment variables or extra config required.

## Local testing

```bash
npm i -g vercel
vercel dev
```

This runs both the static site and the Python function locally the same way
Vercel runs them in production.

## Limitations (by design, and by the free plan)

- **No server-side downloading.** The function only extracts and returns
  links — it never proxies the file. That's what keeps it inside Vercel
  Hobby's execution-time and bandwidth limits.
- **No merging of separate video+audio streams.** Many sites (YouTube in
  particular) split high-resolution video and audio into separate files.
  Where a combined "video+audio" format exists, it's listed first and is
  the simplest option. Video-only and audio-only formats are listed too,
  but combining them (e.g. with `ffmpeg`) is a manual step on your end —
  doing that server-side would need a persistent process, not a stateless
  function.
- **Cold starts.** The first request after idle time will be slower while
  the function spins up and imports yt-dlp.
- **Respect the source site's terms of service.** This tool doesn't get you
  around any platform's restrictions — it's just a thinner UI over `yt-dlp`
  for content you already have the right to download.
