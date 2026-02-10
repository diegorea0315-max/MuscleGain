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
