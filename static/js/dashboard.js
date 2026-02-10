// dashboard.js

// Helpers
const $ = (id) => document.getElementById(id);

function toast(msg) {
  const t = $("toast");
  if (!t) return;
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 1200);
}

// Quick action cards -> modal
(function quickCards() {
  const modal = $("quickModal");
  const title = $("quickModalTitle");
  const body = $("quickModalBody");
  const go = $("quickModalGo");
  const close = $("quickModalClose");
  const cancel = $("quickModalCancel");
  const cards = document.querySelectorAll(".quick-card");

  if (!modal || !cards.length) return;

  function openModal(card) {
    title.textContent = card.dataset.title || "Accion";
    body.textContent = card.dataset.body || "";
    go.setAttribute("href", card.dataset.link || "#");
    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
  }

  function closeModal() {
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
  }

  cards.forEach((card) => card.addEventListener("click", () => openModal(card)));
  close?.addEventListener("click", closeModal);
  cancel?.addEventListener("click", closeModal);
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
  });
})();

// Modal Notes (arriba derecha)
(function modalNotes() {
  const btn = $("notesBtn");
  const modal = $("notesModal");
  const close = $("notesClose");

  if (!btn || !modal || !close) return;

  btn.addEventListener("click", () => {
    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
  });

  close.addEventListener("click", () => {
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
  });

  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.classList.remove("open");
      modal.setAttribute("aria-hidden", "true");
    }
  });
})();

// Notes Rotator (carrusel)
(function rotator() {
  const root = $("notesRotator");
  if (!root) return;

  let notes = [];
  try {
    notes = JSON.parse(root.dataset.notes || "[]");
  } catch {
    notes = [];
  }
  if (!notes.length) notes = ["Registra tu primera sesión y el sistema se vuelve inteligente."];

  let idx = 0;

  const noteText = $("noteText");
  const dots = $("noteDots");
  const prev = $("notePrev");
  const next = $("noteNext");
  const copy = $("noteCopy");
  const save = $("noteSave");

  function renderDots() {
    dots.innerHTML = "";
    notes.forEach((_, i) => {
      const d = document.createElement("div");
      d.className = "note-dot" + (i === idx ? " active" : "");
      d.addEventListener("click", () => { idx = i; render(); });
      dots.appendChild(d);
    });
  }

  function render() {
    if (noteText) noteText.textContent = notes[idx] || "";
    renderDots();
  }

  function step(delta) {
    idx = (idx + delta + notes.length) % notes.length;
    render();
  }

  prev?.addEventListener("click", () => step(-1));
  next?.addEventListener("click", () => step(1));

  copy?.addEventListener("click", async () => {
    const text = notes[idx] || "";
    try {
      await navigator.clipboard.writeText(text);
      toast("Copiado.");
    } catch {
      toast("No se pudo copiar.");
    }
  });

  save?.addEventListener("click", async () => {
    const text = notes[idx] || "";
    try {
      const res = await fetch("/api/save_note", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      const data = await res.json();
      if (data.ok) toast("Guardado.");
      else toast("Error al guardar.");
    } catch {
      toast("Error al guardar.");
    }
  });

  render();
})();
