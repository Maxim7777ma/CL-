document.addEventListener("DOMContentLoaded", function () {
  const modal = document.querySelector("[data-doc-modal]");
  if (!modal) return;

  const titleEl = modal.querySelector("[data-doc-title]");
  const imgEl = modal.querySelector("[data-doc-image]");
  const pdfEl = modal.querySelector("[data-doc-pdf]");
  const fallbackEl = modal.querySelector("[data-doc-fallback]");
  const downloadLink = modal.querySelector("[data-doc-download-link]");

  function openDocPreview(url, name, filename) {
    if (!url) return;

    const lower = (filename || url).toLowerCase();

    // Скидаємо все
    imgEl.style.display = "none";
    pdfEl.style.display = "none";
    fallbackEl.style.display = "none";

    titleEl.textContent = name || "Документ";

    if (
      lower.endsWith(".jpg") ||
      lower.endsWith(".jpeg") ||
      lower.endsWith(".png") ||
      lower.endsWith(".webp") ||
      lower.endsWith(".gif")
    ) {
      imgEl.src = url;
      imgEl.style.display = "block";
    } else if (lower.endsWith(".pdf")) {
      pdfEl.src = url;
      pdfEl.style.display = "block";
    } else {
      downloadLink.href = url;
      fallbackEl.style.display = "block";
    }

    modal.classList.add("is-open");
  }

  function closeDocPreview() {
    imgEl.src = "";
    pdfEl.src = "";
    modal.classList.remove("is-open");
  }

  modal.querySelectorAll("[data-doc-close]").forEach((el) => {
    el.addEventListener("click", closeDocPreview);
  });

  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeDocPreview();
    }
  });

  document.querySelectorAll("[data-doc-preview]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const url = btn.dataset.docUrl;
      const name = btn.dataset.docName;
      const filename = btn.dataset.docFilename;
      openDocPreview(url, name, filename);
    });
  });
});
