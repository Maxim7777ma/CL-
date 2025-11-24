document.addEventListener("DOMContentLoaded", function () {
  const userMenu = document.querySelector("[data-user-menu]");
  if (!userMenu) return;

  const toggleBtn = userMenu.querySelector(".user-menu__toggle");
  const panel = userMenu.querySelector(".user-menu__panel");

  const closeMenu = () => {
    userMenu.classList.remove("is-open");
    if (toggleBtn) {
      toggleBtn.setAttribute("aria-expanded", "false");
    }
  };

  const openMenu = () => {
    userMenu.classList.add("is-open");
    if (toggleBtn) {
      toggleBtn.setAttribute("aria-expanded", "true");
    }
  };

  const toggleMenu = () => {
    if (userMenu.classList.contains("is-open")) {
      closeMenu();
    } else {
      openMenu();
    }
  };

  if (toggleBtn) {
    toggleBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      toggleMenu();
    });
  }

  // клик вне меню — закрити
  document.addEventListener("click", function (e) {
    if (!userMenu.contains(e.target)) {
      closeMenu();
    }
  });

  // Escape — закрити
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      closeMenu();
    }
  });
});
