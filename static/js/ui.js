
(function passwordToggle() {
  document.addEventListener("click", (event) => {
    const btn = event.target.closest(".toggle-password");
    if (!btn) return;
    const targetId = btn.getAttribute("data-target");
    const input = document.getElementById(targetId);
    if (!input) return;
    const isPassword = input.getAttribute("type") === "password";
    input.setAttribute("type", isPassword ? "text" : "password");
    btn.classList.toggle("active", isPassword);
    btn.setAttribute("aria-label", isPassword ? "Ocultar contrasena" : "Mostrar contrasena");
  });
})();

(function sessionForm() {
  const addBtn = document.getElementById("addSetRow");
  const container = document.getElementById("setRows");
  const template = document.getElementById("setRowTemplate");

  if (!addBtn || !container || !template) return;

  addBtn.addEventListener("click", () => {
    const clone = template.content.cloneNode(true);
    container.appendChild(clone);
    const exerciseInput = container.querySelector(".set-row:last-child input[name='exercise[]']");
    if (exerciseInput) exerciseInput.focus();
  });

  container.addEventListener("click", (event) => {
    const btn = event.target.closest(".remove-row");
    if (!btn) return;
    const row = btn.closest(".set-row");
    if (row && container.children.length > 1) row.remove();
  });
})();

// Suggestion chips for session form (by muscle group)
(function sessionSuggestions() {
  const dataEl = document.getElementById("sessionSuggestionsData");
  const chipsWrap = document.getElementById("sessionExerciseChips");
  const filterSelect = document.getElementById("sessionMuscleFilter");
  if (!dataEl || !chipsWrap) return;

  let suggestions = {};
  try {
    suggestions = JSON.parse(dataEl.dataset.suggestions || "{}");
  } catch (e) {
    suggestions = {};
  }
  let slugMap = {};
  try {
    slugMap = JSON.parse(dataEl.dataset.slugMap || "{}");
  } catch (e) {
    slugMap = {};
  }

  let lastFocused = null;
  document.addEventListener("focusin", (event) => {
    if (event.target && event.target.matches("input[name='exercise[]']")) {
      lastFocused = event.target;
    }
  });

  function renderChips(group) {
    chipsWrap.innerHTML = "";
    const list = suggestions[group] || [];
    list.forEach((ex) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip";
      btn.textContent = ex;
      btn.addEventListener("click", () => {
        if (!lastFocused) {
          lastFocused = document.querySelector("input[name='exercise[]']");
        }
        if (!lastFocused) return;
        lastFocused.value = ex;
        lastFocused.focus();
      });
      chipsWrap.appendChild(btn);
    });
  }

  let groups = Object.keys(suggestions).filter((k) => k !== k.toLowerCase());
  if (groups.includes("Todos")) {
    groups = ["Todos", ...groups.filter((g) => g !== "Todos")];
  }
  if (filterSelect && groups.length) {
    filterSelect.innerHTML = "";
    groups.forEach((g) => {
      const opt = document.createElement("option");
      opt.value = g;
      opt.textContent = g;
      filterSelect.appendChild(opt);
    });
    filterSelect.addEventListener("change", () => renderChips(filterSelect.value));
    const qsMuscle = new URLSearchParams(window.location.search).get("muscle");
    const mapped = qsMuscle ? (slugMap[qsMuscle] || qsMuscle) : "";
    if (mapped && suggestions[mapped]) {
      filterSelect.value = mapped;
      renderChips(mapped);
    } else {
      renderChips(filterSelect.value);
    }
  } else if (groups.length) {
    renderChips(groups[0]);
  }
})();

(function routineDays() {
  const addBtn = document.getElementById("addDayBtn");
  const container = document.getElementById("dayContainer");
  const template = document.getElementById("dayTemplate");
  if (!addBtn || !container || !template) return;

  addBtn.addEventListener("click", () => {
    const clone = template.content.cloneNode(true);
    container.appendChild(clone);
  });

  container.addEventListener("click", (event) => {
    const btn = event.target.closest(".remove-day");
    if (!btn) return;
    const row = btn.closest(".routine-row");
    if (row && container.children.length > 1) row.remove();
  });

  let lastFocused = null;
  container.addEventListener("focusin", (event) => {
    if (event.target.classList.contains("day-textarea")) {
      lastFocused = event.target;
    }
  });

  const chips = document.getElementById("exerciseChips");
  if (chips) {
    chips.addEventListener("click", (event) => {
      const btn = event.target.closest(".chip");
      if (!btn) return;
      const value = btn.getAttribute("data-ex");
      if (!value) return;
      if (!lastFocused) {
        const first = container.querySelector(".day-textarea");
        lastFocused = first || null;
      }
      if (!lastFocused) return;
      const current = lastFocused.value.trim();
      lastFocused.value = current ? `${current}\n${value}` : value;
      lastFocused.focus();
    });
  }
})();

// Prefill routine form from recommended templates
(function routineTemplates() {
  const container = document.getElementById("routineTemplates");
  const dayContainer = document.getElementById("dayContainer");
  const dayTemplate = document.getElementById("dayTemplate");
  const nameInput = document.querySelector("input[name='name']");
  const trainBoxes = document.querySelectorAll("input[name='train_days[]']");
  const restBoxes = document.querySelectorAll("input[name='rest_days[]']");
  if (!container || !dayContainer || !dayTemplate || !nameInput) return;

  let templates = [];
  try {
    templates = JSON.parse(container.dataset.templates || "[]");
  } catch (e) {
    templates = [];
  }

  function clearDays() {
    dayContainer.innerHTML = "";
  }

  function addDay(label, exercises) {
    const clone = dayTemplate.content.cloneNode(true);
    const row = clone.querySelector(".routine-row");
    if (!row) return;
    const labelInput = row.querySelector("input[name='day_label[]']");
    const exInput = row.querySelector("textarea[name='day_exercises[]']");
    if (labelInput) labelInput.value = label || "";
    if (exInput) exInput.value = (exercises || []).join("\n");
    dayContainer.appendChild(row);
  }

  function setChecks(nodes, values) {
    const set = new Set(values || []);
    nodes.forEach((box) => {
      box.checked = set.has(box.value);
    });
  }

  container.addEventListener("click", (event) => {
    const card = event.target.closest("[data-template-index]");
    if (!card) return;
    const idx = Number(card.dataset.templateIndex || 0);
    const tpl = templates[idx];
    if (!tpl) return;
    nameInput.value = tpl.name || "";
    clearDays();
    (tpl.days || []).forEach((d) => addDay(d.label, d.exercises));
    if (trainBoxes.length) setChecks(trainBoxes, tpl.train_days || []);
    if (restBoxes.length) setChecks(restBoxes, tpl.rest_days || []);
  });
})();
