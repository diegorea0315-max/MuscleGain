const list = document.getElementById("muscleList");
const nameInput = document.getElementById("muscleNameInput");
const overviewEditor = document.getElementById("overviewEditor");
const saveBtn = document.getElementById("saveMuscle");
const tierCards = Array.from(document.querySelectorAll(".tier-card"));
let activeSlug = "";

function applyCommand(cmd, targetId) {
  const target = document.getElementById(targetId);
  if (!target) return;
  target.focus();
  if (cmd === "createLink") {
    const url = prompt("URL del enlace:");
    if (url) document.execCommand("createLink", false, url);
    return;
  }
  document.execCommand(cmd, false, null);
}

document.querySelectorAll(".editor-toolbar").forEach((bar) => {
  const targetId = bar.dataset.target;
  bar.querySelectorAll(".tool-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      applyCommand(btn.dataset.cmd, targetId);
    });
  });
});

function setActiveItem(slug) {
  activeSlug = slug;
  document.querySelectorAll(".editor-item").forEach((el) => {
    el.classList.toggle("active", el.dataset.slug === slug);
  });
}

function fillTiers(tiers) {
  tierCards.forEach((card) => {
    const tier = card.dataset.tier;
    const data = tiers.find((t) => t.tier === tier) || {};
    card.querySelector(".tier-title").value = data.title || "";
    card.querySelector(".tier-body").innerHTML = data.body_html || "";
    card.querySelector(".tier-video").value = data.video_url || "";
  });
}

async function loadMuscle(slug) {
  setActiveItem(slug);
  nameInput.value = "";
  overviewEditor.innerHTML = "";
  tierCards.forEach((card) => {
    card.querySelector(".tier-title").value = "";
    card.querySelector(".tier-body").innerHTML = "";
    card.querySelector(".tier-video").value = "";
  });

  const res = await fetch(`/api/muscles/${slug}`);
  const data = await res.json();
  if (!data.ok) return;
  nameInput.value = data.info.name || "";
  overviewEditor.innerHTML = data.info.overview_html || "";
  fillTiers(data.tiers || []);
}

function collectPayload() {
  const tiers = tierCards.map((card) => ({
    tier: card.dataset.tier,
    title: card.querySelector(".tier-title").value,
    body_html: card.querySelector(".tier-body").innerHTML,
    video_url: card.querySelector(".tier-video").value,
  }));
  return {
    name: nameInput.value,
    overview_html: overviewEditor.innerHTML,
    tiers,
  };
}

saveBtn.addEventListener("click", async () => {
  if (!activeSlug) return;
  const res = await fetch(`/admin/muscle-map/save/${activeSlug}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(collectPayload()),
  });
  const data = await res.json();
  if (data.ok) {
    saveBtn.textContent = "Guardado";
    setTimeout(() => (saveBtn.textContent = "Guardar cambios"), 1200);
  }
});

if (window.MUSCLES) {
  window.MUSCLES.forEach((m) => {
    const item = document.createElement("button");
    item.className = "editor-item";
    item.dataset.slug = m.slug;
    item.textContent = m.name;
    item.addEventListener("click", () => loadMuscle(m.slug));
    list.appendChild(item);
  });
  if (window.MUSCLES.length) loadMuscle(window.MUSCLES[0].slug);
}
