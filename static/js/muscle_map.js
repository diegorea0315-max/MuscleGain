const tierList = document.getElementById("tierList");
const muscleName = document.getElementById("muscleName");
const muscleOverview = document.getElementById("muscleOverview");
const addToWorkout = document.getElementById("addToWorkout");
const addToRoutine = document.getElementById("addToRoutine");
const tabs = Array.from(document.querySelectorAll(".map-tab"));
const views = Array.from(document.querySelectorAll(".muscle-view"));
const muscleGroups = Array.from(document.querySelectorAll(".musculo-group"));

function clearActive() {
  muscleGroups.forEach((g) => g.classList.remove("active"));
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
  if (addToWorkout) addToWorkout.href = `/session/new?muscle=${encodeURIComponent(slug)}`;
  if (addToRoutine) addToRoutine.href = `/routines?muscle=${encodeURIComponent(slug)}`;
  renderTiers(data.tiers || []);
}

function normalizeName(value) {
  return (value || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z]/g, "");
}

const nameToSlug = {
  pecho: "pectorales",
  pectorales: "pectorales",
  biceps: "biceps",
  bicepsizquierdo: "biceps",
  hombro: "hombros",
  triceps: "triceps",
  antebrazo: "antebrazos",
  cuadriceps: "cuadriceps",
  abdomen: "abdomen",
  dorsal: "espalda",
  espalda: "espalda",
  gluteo: "gluteos",
  isquios: "isquios",
  pantorrilla: "pantorrillas",
  lumbar: "espalda",
  espaldaalta: "trapecios",
  deltoideposterior: "hombros",
  trapecio: "trapecios",
};

function selectMuscleByName(name, el) {
  const key = normalizeName(name);
  const slug = nameToSlug[key];
  if (!slug) return;
  clearActive();
  if (el) el.classList.add("active");
  loadMuscle(slug);
}

muscleGroups.forEach((group) => {
  const raw = group.getAttribute("onclick") || "";
  const match = raw.match(/seleccionarMusculo\\('(.+?)'\\)/);
  if (match) {
    group.dataset.muscleName = match[1];
  }
  group.removeAttribute("onclick");
  group.addEventListener("click", (event) => {
    event.stopPropagation();
    const name = group.dataset.muscleName || "";
    selectMuscleByName(name, group);
  });
});

window.seleccionarMusculo = function seleccionarMusculo(name) {
  selectMuscleByName(name);
};

if (tabs.length) setView("front");

if (window.MUSCLES && window.MUSCLES.length) {
  loadMuscle(window.MUSCLES[0].slug);
}
