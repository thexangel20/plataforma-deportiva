(() => {
  const form = document.querySelector("[data-comparison-form]");
  if (!form) return;

  const checkboxes = Array.from(form.querySelectorAll("input[name='ids']"));
  const count = form.querySelector("[data-comparison-count]");
  const submit = form.querySelector("[data-comparison-submit]");

  const syncState = () => {
    const selected = checkboxes.filter((checkbox) => checkbox.checked).length;
    if (count) {
      count.textContent = `${selected} seleccionado${selected === 1 ? "" : "s"}`;
    }
    if (submit) {
      submit.disabled = selected < 2;
    }
  };

  checkboxes.forEach((checkbox) => checkbox.addEventListener("change", syncState));
  form.addEventListener("submit", (event) => {
    const selected = checkboxes.filter((checkbox) => checkbox.checked).length;
    if (selected < 2) {
      event.preventDefault();
      window.alert("Selecciona al menos dos deportes para compararlos.");
    }
  });

  syncState();
})();
