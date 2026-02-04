
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
    const dayInput = container.querySelector(".routine-row:last-child .table-input");
    if (dayInput) dayInput.focus();
  });

  container.addEventListener("click", (event) => {
    const btn = event.target.closest(".remove-row");
    if (!btn) return;
    const row = btn.closest(".set-row");
    if (row && container.children.length > 1) row.remove();
  });
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

(function muscleMap() {
  const map = document.querySelector(".muscle-map");
  const nameEl = document.getElementById("muscleName");
  const tierEl = document.getElementById("muscleTier");
  const notesEl = document.getElementById("muscleNotes");
  if (!map || !nameEl || !tierEl || !notesEl) return;

  const tierData = {
    Pectoral: { tier: "A", note: "Prioriza presses y aperturas con control." },
    Dorsal: { tier: "A", note: "Remo y dominadas para densidad real." },
    Biceps: { tier: "B", note: "Curl estricto y tempo controlado." },
    Triceps: { tier: "B", note: "Fondos y extensiones para volumen." },
    Cuadriceps: { tier: "A", note: "Sentadilla profunda y prensa." },
    Isquios: { tier: "A", note: "Peso muerto rumano + curl femoral." },
    Pantorrilla: { tier: "C", note: "Frecuencia alta, rango completo." },
  };

  map.addEventListener("click", (event) => {
    const target = event.target.closest(".muscle");
    if (!target) return;
    const name = target.getAttribute("data-muscle") || "Musculo";
    const data = tierData[name] || { tier: "B", note: "Trabajo constante y tecnico." };

    map.querySelectorAll(".muscle").forEach((m) => m.classList.remove("active"));
    target.classList.add("active");

    nameEl.textContent = name;
    tierEl.textContent = `Tier: ${data.tier}`;
    notesEl.textContent = data.note;
  });
})();
