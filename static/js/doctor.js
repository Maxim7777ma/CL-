document.addEventListener("DOMContentLoaded", function () {
  // хелпер для CSRF
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const csrftoken = getCookie("csrftoken");

  const cards = document.querySelectorAll("[data-appointment-card]");
  if (!cards.length) return;

  cards.forEach(card => {
    const toggleBtn = card.querySelector("[data-comment-toggle]");
    const summary = card.querySelector("[data-comment-summary]");
    const body = card.querySelector("[data-comment-body]");
    const textarea = card.querySelector("[data-comment-input]");
    const saveBtn = card.querySelector("[data-comment-save]");
    const cancelBtn = card.querySelector("[data-comment-cancel]");
    const statusEl = card.querySelector("[data-comment-status]");
    const serviceSelect = card.querySelector("[data-service-select]");
    const updateUrl = card.dataset.updateUrl;

    if (!updateUrl) return;

    const originalNote = textarea?.dataset.originalNote || "";

    // Развернуть / свернуть комментарий
    toggleBtn?.addEventListener("click", () => {
      card.classList.toggle("appointment-card--comments-open");
    });

    cancelBtn?.addEventListener("click", (e) => {
      e.preventDefault();
      if (textarea) {
        textarea.value = originalNote;
      }
      statusEl.textContent = "";
      card.classList.remove("appointment-card--comments-open");
    });

    function sendUpdate(showMessage) {
      if (!textarea || !serviceSelect) return;

      const formData = new FormData();
      formData.append("note", textarea.value);
      formData.append("service_id", serviceSelect.value);

      fetch(updateUrl, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrftoken,
        },
        body: formData,
      })
        .then(r => r.json().then(data => ({ ok: r.ok, data })))
        .then(({ ok, data }) => {
          if (!ok || !data.success) {
            console.error(data);
            statusEl.textContent = data.error || "Помилка збереження.";
            statusEl.style.color = "#b91c1c";
            return;
          }

          // оновлюємо summary
          if (summary) {
            if (data.note) {
              summary.textContent =
                data.note.length > 80
                  ? data.note.slice(0, 77) + "..."
                  : data.note;
            } else {
              summary.innerHTML =
                '<span class="appointment-card__comment-empty">Коментар ще не додано.</span>';
            }
          }

          if (showMessage) {
            statusEl.textContent = "Зміни збережено.";
            statusEl.style.color = "#16a34a";
            setTimeout(() => {
              statusEl.textContent = "";
              card.classList.remove("appointment-card--comments-open");
            }, 900);
          } else {
            statusEl.textContent = "";
          }
        })
        .catch(() => {
          statusEl.textContent = "Помилка мережі.";
          statusEl.style.color = "#b91c1c";
        });
    }

    // Зберегти коментар + послугу
    saveBtn?.addEventListener("click", (e) => {
      e.preventDefault();
      sendUpdate(true);
    });

    // Зміна послуги — можна відразу зберігати без відкриття коментаря
    serviceSelect?.addEventListener("change", () => {
      sendUpdate(false);
    });
  });
});
