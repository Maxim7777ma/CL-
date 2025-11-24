document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("patient-register-form");
  if (!form) return;

  const getErrorBlock = (fieldName) =>
    document.querySelector(`.register-form__error[data-error-for="${fieldName}"]`);

  const clearErrors = () => {
    document
      .querySelectorAll(".register-form__error")
      .forEach((el) => (el.textContent = ""));
  };

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    clearErrors();

    const formData = new FormData(form);

    fetch(form.action, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
      body: formData,
    })
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) {
          // Помилки валідації
          if (data.errors) {
            Object.entries(data.errors).forEach(([field, message]) => {
              const block = getErrorBlock(field);
              if (block) {
                block.textContent = message;
              } else {
                const globalBlock = getErrorBlock("__all__");
                if (globalBlock) {
                  globalBlock.textContent = message;
                }
              }
            });
          } else {
            const globalBlock = getErrorBlock("__all__");
            if (globalBlock) {
              globalBlock.textContent = "Сталася помилка. Спробуйте ще раз.";
            }
          }
          return;
        }

        // Успіх: редірект в кабінет пацієнта
        if (data.success && data.redirect_url) {
          window.location.href = data.redirect_url;
        }
      })
      .catch(() => {
        const globalBlock = getErrorBlock("__all__");
        if (globalBlock) {
          globalBlock.textContent = "Помилка мережі. Спробуйте ще раз пізніше.";
        }
      });
  });
});
