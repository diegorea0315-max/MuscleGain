const tierList = document.getElementById("tierList");
const muscleName = document.getElementById("muscleName");
const muscleOverview = document.getElementById("muscleOverview");
const hotspots = Array.from(document.querySelectorAll(".muscle-hotspot"));
const tabs = Array.from(document.querySelectorAll(".map-tab"));
const views = Array.from(document.querySelectorAll(".muscle-view"));

function clearActive() {
  hotspots.forEach((b) => b.classList.remove("active"));
}

function setView(view) {
  if (!views.length) return;
  views.forEach((v) => v.classList.toggle("active", v.dataset.view === view));
  tabs.forEach((t) => {
    const active = t.dataset.view === view;
    t.classList.toggle("active", active);
    t.setAttribute("aria-selected", active ? "true" : "false");
  });
  clearActive();
}

tabs.forEach((btn) => {
  btn.addEventListener("click", () => setView(btn.dataset.view));
});

function normalizeVideo(url) {
  if (!url) return "";
  if (url.includes("youtube.com") || url.includes("youtu.be")) {
    try {
      const id = url.includes("youtu.be")
        ? url.split("youtu.be/")[1]?.split("?")[0]
        : new URL(url).searchParams.get("v");
      if (id) return `https://www.youtube.com/embed/${id}`;
    } catch (e) {
      return "";
    }
  }
  return "";
}

function renderTiers(tiers) {
  tierList.innerHTML = "";
  tiers.forEach((t) => {
    const card = document.createElement("div");
    card.className = "tier-card-view";
    const videoEmbed = normalizeVideo(t.video_url);
    card.innerHTML = `
      <div class="tier-badge">Tier ${t.tier}</div>
      ${t.title ? `<div class="tier-title">${t.title}</div>` : ""}
      ${t.body_html ? `<div class="tier-body">${t.body_html}</div>` : "<div class=\"tier-empty\">Sin contenido</div>"}
      ${
        t.video_url
          ? `<div class="tier-video-link"><a href="${t.video_url}" target="_blank" rel="noopener">Ver video</a></div>`
          : ""
      }
      ${
        videoEmbed
          ? `<div class="tier-video"><iframe src="${videoEmbed}" title="Video" loading="lazy" allowfullscreen></iframe></div>`
          : ""
      }
    `;
    tierList.appendChild(card);
  });
}

async function loadMuscle(slug) {
  muscleName.textContent = "Cargando...";
  muscleOverview.textContent = "";
  tierList.innerHTML = "";
  const res = await fetch(`/api/muscles/${slug}`);
  const data = await res.json();
  if (!data.ok) return;
  muscleName.textContent = data.info.name || slug;
  muscleOverview.innerHTML = data.info.overview_html || "Sin resumen por ahora.";
  renderTiers(data.tiers || []);
}

hotspots.forEach((btn) => {
  btn.addEventListener("click", () => {
    clearActive();
    btn.classList.add("active");
    loadMuscle(btn.dataset.muscle);
  });
});

if (tabs.length) setView("front");

if (window.MUSCLES && window.MUSCLES.length) {
  loadMuscle(window.MUSCLES[0].slug);
}
