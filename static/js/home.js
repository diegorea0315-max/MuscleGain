const modal = document.getElementById("infoModal");
const modalTitle = document.getElementById("modalTitle");
const modalText = document.getElementById("modalText");
const closeBtn = document.querySelector(".close");

const content = {
  disciplina: {
    title: "Disciplina",
    text: "La disciplina es hacer lo correcto incluso cuando nadie mira. El gimnasio ensena constancia, respeto por el proceso y control personal."
  },
  ciencia: {
    title: "Entrenar con ciencia",
    text: "No se trata de hacer mas, sino de hacer mejor. Basamos el progreso en principios reales de hipertrofia y recuperacion."
  },
  proceso: {
    title: "El proceso importa",
    text: "Nada grande ocurre de la noche a la manana. El progreso fisico refleja paciencia, compromiso y mentalidad a largo plazo."
  }
};

document.querySelectorAll(".info-card").forEach(card => {
  card.addEventListener("click", () => {
    const key = card.dataset.info;
    modalTitle.textContent = content[key].title;
    modalText.textContent = content[key].text;
    modal.style.display = "flex";
  });
});

closeBtn.onclick = () => modal.style.display = "none";
window.onclick = e => { if (e.target === modal) modal.style.display = "none"; };

