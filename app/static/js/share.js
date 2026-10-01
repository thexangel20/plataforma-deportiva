(() => {
  const button = document.querySelector("[data-share-button]");
  const message = document.querySelector("[data-share-message]");
  if (!button) return;

  const shareUrl = button.dataset.shareUrl;

  const showMessage = (text, isError = false) => {
    if (!message) return;
    message.textContent = text;
    message.classList.toggle("mensaje-compartir-error", isError);
    window.setTimeout(() => {
      message.textContent = "";
      message.classList.remove("mensaje-compartir-error");
    }, 3000);
  };

  const copyUrl = async () => {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(shareUrl);
      return;
    }

    const input = document.createElement("input");
    input.value = shareUrl;
    input.setAttribute("readonly", "");
    input.style.position = "fixed";
    input.style.opacity = "0";
    document.body.appendChild(input);
    input.select();
    const copied = document.execCommand("copy");
    input.remove();
    if (!copied) throw new Error("No se pudo copiar el enlace");
  };

  button.addEventListener("click", async () => {
    try {
      if (navigator.share) {
        await navigator.share({ title: document.title, url: shareUrl });
        showMessage("Enlace compartido correctamente.");
      } else {
        await copyUrl();
        showMessage("Enlace copiado al portapapeles.");
      }
    } catch (error) {
      if (error.name !== "AbortError") {
        showMessage("No se pudo compartir el enlace.", true);
      }
    }
  });
})();
