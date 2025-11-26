document.addEventListener("DOMContentLoaded", function () {
  const block = document.querySelector("[data-treatments-list]");
  if (!block) return;

  block.addEventListener("click", function (e) {
    const link = e.target.closest("[data-treatments-page]");
    if (!link) return;

    e.preventDefault();
    const href = link.getAttribute("href");
    if (!href) return;

    const url = new URL(href, window.location.origin);

    fetch(url.toString(), {
      headers: {
        "X-Requested-With": "XMLHttpRequest"
      }
    })
      .then((r) => r.text())
      .then((html) => {
        // Мы не делаем отдельный partial, поэтому проще:
        // сервер всё равно отдаёт ту же страницу, но нам
        // нужно только кусок с блоком категорий.
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");
        const newBlock = doc.querySelector("#landing-treatments-block");
        if (!newBlock) return;

        block.innerHTML = newBlock.innerHTML;
        block.scrollIntoView({ behavior: "smooth", block: "start" });
      })
      .catch((err) => {
        console.error("Помилка завантаження категорій:", err);
      });
  });
});
