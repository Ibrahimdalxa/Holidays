const form = document.getElementById("grab-form");
const input = document.getElementById("url-input");
const btn = document.getElementById("grab-btn");
const status = document.getElementById("status");
const result = document.getElementById("result");
const thumb = document.getElementById("thumb");
const titleEl = document.getElementById("result-title");
const subEl = document.getElementById("result-sub");
const list = document.getElementById("format-list");

function setStatus(msg, isError) {
  status.textContent = msg || "";
  status.classList.toggle("error", Boolean(isError));
}

function formatDuration(seconds) {
  if (!seconds && seconds !== 0) return null;
  const s = Math.round(seconds);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const pad = (n) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${pad(m)}:${pad(sec)}` : `${m}:${pad(sec)}`;
}

function kindClass(kind) {
  if (kind === "video+audio") return "kind-video-audio";
  if (kind === "video only") return "kind-video-only";
  return "kind-audio-only";
}

function renderFormats(formats) {
  list.innerHTML = "";
  if (!formats.length) {
    list.innerHTML = `<li class="format-row"><span>No downloadable formats found for this link.</span></li>`;
    return;
  }
  for (const f of formats) {
    const li = document.createElement("li");
    li.className = "format-row";

    const resBits = [f.resolution, f.fps ? `${f.fps}fps` : null, f.abr ? `${Math.round(f.abr)}kbps` : null]
      .filter(Boolean)
      .join(" · ");

    li.innerHTML = `
      <span class="kind-tag ${kindClass(f.kind)}">${f.kind}</span>
      <span>${resBits || "—"}</span>
      <span>${(f.ext || "—").toUpperCase()}</span>
      <span>${f.filesize || "—"}</span>
      <a class="dl-link" href="${f.url}" target="_blank" rel="noopener" download>Download</a>
    `;
    list.appendChild(li);
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const url = input.value.trim();
  if (!url) return;

  btn.disabled = true;
  result.hidden = true;
  setStatus("Inspecting source…");

  try {
    const res = await fetch("/api/extract", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();

    if (!res.ok) {
      setStatus(data.error || "Something went wrong.", true);
      return;
    }

    titleEl.textContent = data.title || "Untitled";
    const durationTxt = formatDuration(data.duration);
    subEl.textContent = [data.uploader, durationTxt].filter(Boolean).join(" · ") || data.source;

    if (data.thumbnail) {
      thumb.src = data.thumbnail;
      thumb.alt = data.title || "";
    } else {
      thumb.removeAttribute("src");
    }

    renderFormats(data.formats || []);
    result.hidden = false;
    setStatus(`${(data.formats || []).length} format(s) found.`);
  } catch (err) {
    setStatus("Network error — the function may be cold-starting, try again.", true);
  } finally {
    btn.disabled = false;
  }
});
