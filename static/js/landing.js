document.addEventListener("DOMContentLoaded", function () {
  const bookingBox = document.getElementById("booking-box");
  if (!bookingBox) return;

  const apiDayUrl = bookingBox.dataset.apiDayScheduleUrl;
  const apiCreateUrl = bookingBox.dataset.apiCreateAppointmentUrl;
  const isAuth = bookingBox.dataset.isAuthenticated === "1";

  const toggleBtn = bookingBox.querySelector("[data-booking-toggle]");
  const closeBtn = bookingBox.querySelector("[data-booking-close]");
  const calendarEl = bookingBox.querySelector("[data-calendar]");
  const openCalendarBtn = bookingBox.querySelector("[data-open-calendar]");
  const selectedDateLabel = bookingBox.querySelector("[data-selected-date-label]");
  const scheduleEl = bookingBox.querySelector("[data-schedule]");
  const scheduleDateLabel = bookingBox.querySelector("[data-schedule-date-label]");
  const doctorsContainer = bookingBox.querySelector("[data-schedule-doctors]");
  const timesContainer = bookingBox.querySelector("[data-schedule-times]");
  const cellsContainer = bookingBox.querySelector("[data-schedule-cells]");

  // Модалка
  const modalEl = bookingBox.querySelector("[data-booking-modal]");
  const modalCloseEls = bookingBox.querySelectorAll("[data-booking-modal-close]");
  const modalSummary = bookingBox.querySelector("[data-booking-summary]");
  const modalForm = bookingBox.querySelector("[data-booking-form]");
  const dateInput = bookingBox.querySelector("[data-booking-date-input]");
  const timeInput = bookingBox.querySelector("[data-booking-time-input]");
  const branchInput = bookingBox.querySelector("[data-booking-branch-input]");
  const doctorInput = bookingBox.querySelector("[data-booking-doctor-input]");
  const modalError = bookingBox.querySelector("[data-booking-error]");
  const modalSuccess = bookingBox.querySelector("[data-booking-success]");
  const serviceSelect = document.getElementById("booking-service-select");
  const noteTextarea = document.getElementById("booking-note");

  const branchSelect = document.getElementById("booking-branch-select");
  const branchDropdown = bookingBox.querySelector("[data-branch-dropdown]");
  const branchToggle = bookingBox.querySelector("[data-branch-toggle]");
  const branchMenu = bookingBox.querySelector("[data-branch-menu]");
  const branchCurrentLabel = bookingBox.querySelector("[data-branch-current-label]");


  const authModal = bookingBox.querySelector("[data-auth-modal]");
  const authModalBackdrop = bookingBox.querySelector("[data-auth-modal-backdrop]");
  const authModalCloseEls = bookingBox.querySelectorAll("[data-auth-modal-close]");
  const authRegisterBtn = bookingBox.querySelector("[data-auth-register]");
  const registerUrl = bookingBox.dataset.registerUrl || "/register/";

  // ====== Helpers ======
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

  function formatDateReadable(date) {
    return date.toLocaleDateString("uk-UA", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }

  // ====== LocalStorage для розгорнутого режиму ======
  const LS_KEY_EXPANDED = "bookingWidgetExpanded";
  function applyExpandedFromStorage() {
    const val = localStorage.getItem(LS_KEY_EXPANDED);
    if (val === "1") {
      document.body.classList.add("booking-expanded");
    }
  }
  applyExpandedFromStorage();

  function setExpanded(expanded) {
    if (expanded) {
      document.body.classList.add("booking-expanded");
      localStorage.setItem(LS_KEY_EXPANDED, "1");
    } else {
      document.body.classList.remove("booking-expanded");
      localStorage.setItem(LS_KEY_EXPANDED, "0");
    }
  }

  if (toggleBtn) {
    toggleBtn.addEventListener("click", function () {
      setExpanded(true);
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", function () {
      setExpanded(false);
    });
  }

  // ====== Логіка календаря ======
  const monthLabel = calendarEl.querySelector("[data-cal-month-label]");
  const gridEl = calendarEl.querySelector("[data-cal-grid]");
  const prevBtn = calendarEl.querySelector("[data-cal-prev]");
  const nextBtn = calendarEl.querySelector("[data-cal-next]");

  let currentMonth = new Date();
  currentMonth.setDate(1);

  let selectedDate = null;

  function renderCalendar() {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();

    monthLabel.textContent = currentMonth.toLocaleDateString("uk-UA", {
      year: "numeric",
      month: "long",
    });

    gridEl.innerHTML = "";

    // Пн = 1, ... Нд = 0 => приводимо до нашої сітки
    const firstDayWeek = (new Date(year, month, 1).getDay() + 6) % 7;
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    // Попередні дні для вирівнювання
    for (let i = 0; i < firstDayWeek; i++) {
      const span = document.createElement("button");
      span.className = "booking-calendar__day booking-calendar__day--outside";
      span.disabled = true;
      gridEl.appendChild(span);
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    for (let day = 1; day <= daysInMonth; day++) {
      const d = new Date(year, month, day);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "booking-calendar__day";
      btn.textContent = day;
      btn.dataset.date = d.toISOString().slice(0, 10);

      if (d.toDateString() === today.toDateString()) {
        btn.classList.add("booking-calendar__day--today");
      }

      if (selectedDate && d.toDateString() === selectedDate.toDateString()) {
        btn.classList.add("booking-calendar__day--selected");
      }

      btn.addEventListener("click", () => {
        selectedDate = d;
        selectedDateLabel.textContent = formatDateReadable(d);
        scheduleDateLabel.textContent = formatDateReadable(d);
        calendarEl.style.display = "none";
        renderCalendar();
        loadScheduleForSelected();
      });

      gridEl.appendChild(btn);
    }
  }

  if (openCalendarBtn) {
    openCalendarBtn.addEventListener("click", function () {
      if (calendarEl.style.display === "none" || !calendarEl.style.display) {
        calendarEl.style.display = "block";
        renderCalendar();
      } else {
        calendarEl.style.display = "none";
      }
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener("click", function () {
      currentMonth.setMonth(currentMonth.getMonth() - 1);
      renderCalendar();
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", function () {
      currentMonth.setMonth(currentMonth.getMonth() + 1);
      renderCalendar();
    });
  }

  // При завантаженні — відразу показуємо поточний місяць та обираємо сьогодні
  (function initCalendarDefault() {
    const today = new Date();
    selectedDate = today;
    selectedDateLabel.textContent = formatDateReadable(today);
    scheduleDateLabel.textContent = formatDateReadable(today);
    renderCalendar();
    loadScheduleForSelected();
  })();

  // Автооновлення при зміні філії
// ==== Дропдаун філій ====

// открыть/закрыть меню по клику на кнопку
if (branchToggle && branchDropdown) {
  branchToggle.addEventListener("click", function () {
    branchDropdown.classList.toggle("is-open");
  });
}

// выбор філії в меню
if (branchMenu && branchSelect) {
  branchMenu.addEventListener("click", function (e) {
    const btn = e.target.closest(".booking-branch-option");
    if (!btn) return;

    const branchId = btn.dataset.branchId || "";
    const branchName = btn.textContent.trim() || "Усі філії";

    // пишем выбранный id в hidden-инпут
    branchSelect.value = branchId;

    // меняем текст на основной кнопке
    if (branchCurrentLabel) {
      branchCurrentLabel.textContent = branchName;
    }

    // подсветка активного пункта
    branchMenu.querySelectorAll(".booking-branch-option").forEach((b) => {
      b.classList.remove("is-active");
    });
    btn.classList.add("is-active");

    // закрываем меню
    if (branchDropdown) {
      branchDropdown.classList.remove("is-open");
    }

    // обновляем расписание
    loadScheduleForSelected();
  });
}

// закрытие меню по клику вне
document.addEventListener("click", function (e) {
  if (!branchDropdown) return;
  if (!branchDropdown.contains(e.target)) {
    branchDropdown.classList.remove("is-open");
  }
});



  // ====== Завантаження розкладу ======
  function loadScheduleForSelected() {
    if (!selectedDate) return;
    if (!apiDayUrl) return;

    const dateStr = selectedDate.toISOString().slice(0, 10);
    const branchId = branchSelect ? branchSelect.value : "";

    const url = new URL(apiDayUrl, window.location.origin);
    url.searchParams.set("date", dateStr);
    if (branchId) url.searchParams.set("branch", branchId);

    fetch(url.toString())
      .then((r) => r.json())
      .then((data) => {
        if (data.error) {
          console.error(data.error);
          return;
        }
        renderSchedule(data);
      })
      .catch((err) => {
        console.error(err);
      });
  }

function renderSchedule(data) {
  scheduleEl.style.display = "block";

  // slots — массив "09:00", "09:30", ...
  const slots = data.slots || data.hours || [];
  const doctors = data.doctors || [];

  // шапка с врачами
  doctorsContainer.innerHTML = "";
  doctors.forEach((doc) => {
    const div = document.createElement("div");
    div.className = "schedule-grid__doctors-item";
    div.textContent = doc.name;
    div.dataset.doctorId = doc.id;
    doctorsContainer.appendChild(div);
  });

  // левая колонка времени
  timesContainer.innerHTML = "";
  slots.forEach((time) => {
    const div = document.createElement("div");
    div.className = "schedule-grid__time-cell";
    div.textContent = time;
    timesContainer.appendChild(div);
  });

  // подсветка ближайшего свободного слота
  const now = new Date();
  const todayStr = now.toISOString().slice(0, 10);
  const isToday = data.date === todayStr;
  let nextHighlighted = false;

  // карта: какие слоты нужно пропустить из-за span > 1
  const skipMap = {};
  doctors.forEach((doc) => {
    skipMap[doc.id] = {};
  });

  cellsContainer.innerHTML = "";

  slots.forEach((time, slotIndex) => {
    const row = document.createElement("div");
    row.className = "schedule-grid__row";

    doctors.forEach((doc) => {
      skipMap[doc.id] = skipMap[doc.id] || {};

      // если этот 30-минутный отрезок уже покрыт предыдущим длинным занятым слотом
      if (skipMap[doc.id][time]) {
        const dummy = document.createElement("div");
        dummy.className = "schedule-slot schedule-slot--hidden";
        row.appendChild(dummy);
        return;
      }

      const cell = document.createElement("div");
      cell.className = "schedule-slot";

      const workStart = doc.work_start || null;  // "09:00"
      const workEnd = doc.work_end || null;      // "18:00"

      const isWorkingHere =
        (!workStart || time >= workStart) &&
        (!workEnd || time < workEnd);

      const breakStart = doc.break_start || null;
      const breakEnd = doc.break_end || null;
      const isBreak =
        breakStart && breakEnd && time >= breakStart && time < breakEnd;

      // врач не работает в это время
      if (!isWorkingHere) {
        cell.classList.add("schedule-slot--off");
        row.appendChild(cell);
        return;
      }

      // перерыв / обед
      if (isBreak) {
        cell.classList.add("schedule-slot--break");
        const label = document.createElement("div");
        label.className = "schedule-slot__label-break";
        label.textContent = "Перерва";
        cell.appendChild(label);
        row.appendChild(cell);
        return;
      }

      const busy = (doc.busy_slots || {})[time];

      if (busy) {
        // сколько 30-минутных слотов занимает приём
        const span = busy.span && busy.span > 1 ? busy.span : 1;

        const label = document.createElement("div");
        label.className = "schedule-slot__label-busy";
        label.textContent = busy.service || "Зайнято";
        cell.appendChild(label);

        if (span > 1) {
          // растягиваем ячейку по вертикали
          cell.style.gridRow = "span " + span;

          // помечаем следующие слоты как покрытые этим приёмом
          for (let i = 1; i < span && slotIndex + i < slots.length; i++) {
            const nextTime = slots[slotIndex + i];
            skipMap[doc.id][nextTime] = true;
          }
        }

        row.appendChild(cell);
      } else {
        // свободный слот
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "schedule-slot__btn";
        btn.textContent = "Вільно";

        // подсветка ближайшего свободного слота (одного)
        if (isToday && !nextHighlighted) {
          const [h, m] = time.split(":").map(Number);
          const slotDate = new Date();
          slotDate.setHours(h, m, 0, 0);

          if (slotDate >= now) {
            btn.classList.add("schedule-slot__btn--next");
            nextHighlighted = true;
          }
        }

        btn.addEventListener("click", () => {
          if (!isAuth) {
            openAuthModal();
            return;
          }
          const selectedBranchId =
            branchSelect && branchSelect.value ? branchSelect.value : "";
          openBookingModal({
            date: data.date,
            time: time,
            branchId: selectedBranchId || doc.branch_id || "",
            branchName: doc.branch || "",
            doctorId: doc.id,
            doctorName: doc.name,
          });
        });

        cell.appendChild(btn);
        row.appendChild(cell);
      }
    });

    cellsContainer.appendChild(row);
  });
}

  // ====== Міні-модалка "увійдіть / зареєструйтесь" ======
  function openAuthModal() {
    if (!authModal) return;
    authModal.style.display = "flex";
  }

  function closeAuthModal() {
    if (!authModal) return;
    authModal.style.display = "none";
  }

  if (authModalBackdrop) {
    authModalBackdrop.addEventListener("click", closeAuthModal);
  }

  if (authModalCloseEls) {
    authModalCloseEls.forEach((el) => {
      el.addEventListener("click", closeAuthModal);
    });
  }

  if (authRegisterBtn) {
    authRegisterBtn.addEventListener("click", function () {
      window.location.href = registerUrl;
    });
  }


  // ====== Модалка ======

  function openBookingModal({ date, time, branchId, branchName, doctorId, doctorName }) {
    if (!modalEl) return;
    modalError.textContent = "";
    modalSuccess.textContent = "";
    if (serviceSelect) serviceSelect.value = "";
    if (noteTextarea) noteTextarea.value = "";

    dateInput.value = date;
    timeInput.value = time;
    branchInput.value = branchId || "";      // 👈 сюда кладём ID філії
    doctorInput.value = doctorId;

    const humanDate = new Date(date + "T00:00:00");
    const branchText = branchName ? ` (філія: ${branchName})` : "";

    modalSummary.textContent =
        `Ви записуєтесь до лікаря ${doctorName}${branchText} ` +
        `на ${formatDateReadable(humanDate)} о ${time}.`;

    modalEl.style.display = "flex";
  }

  function closeBookingModal() {
    if (!modalEl) return;
    modalEl.style.display = "none";
  }

  if (modalCloseEls) {
    modalCloseEls.forEach((el) => {
      el.addEventListener("click", closeBookingModal);
    });
  }

  if (modalForm) {
    modalForm.addEventListener("submit", function (e) {
      e.preventDefault();
      modalError.textContent = "";
      modalSuccess.textContent = "";

      if (!apiCreateUrl) return;

      const formData = new FormData(modalForm);

      fetch(apiCreateUrl, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: formData,
      })
        .then((r) => r.json().then((data) => ({ ok: r.ok, data })))
        .then(({ ok, data }) => {
          if (!ok || !data.success) {
            const errors = data.errors || {};
            const msg =
              errors.slot ||
              errors.date ||
              errors.time ||
              errors.branch ||
              errors.doctor ||
              "Сталася помилка. Спробуйте пізніше.";
            modalError.textContent = msg;
            return;
          }

          modalSuccess.textContent = "Запис успішно створено!";
          // Обновляем сетку
          loadScheduleForSelected();
          setTimeout(() => {
            closeBookingModal();
          }, 900);
        })
        .catch(() => {
          modalError.textContent = "Помилка мережі. Спробуйте пізніше.";
        });
    });
  }
});


document.addEventListener("DOMContentLoaded", function () {
  const doctorCards = document.querySelectorAll("[data-doctor-card]");
  if (!doctorCards.length) return;

  doctorCards.forEach((card) => {
    const toggles = card.querySelectorAll("[data-doctor-toggle]");
    toggles.forEach((btn) => {
      btn.addEventListener("click", function () {
        card.classList.toggle("is-flipped");
      });
    });
  });
});

document.addEventListener("DOMContentLoaded", function () {
  const servicesBlock = document.getElementById("services-block");
  if (!servicesBlock) return;

  // Слушаем клики ТОЛЬКО внутри блока с услугами
  servicesBlock.addEventListener("click", function (e) {
    const link = e.target.closest("[data-services-page]");
    if (!link) return;  // клик не по кнопке пагинации

    e.preventDefault();

    const href = link.getAttribute("href");
    if (!href) return;

    // Собираем абсолютный URL для fetch
    const url = new URL(href, window.location.origin);

    fetch(url.toString(), {
      headers: {
        "X-Requested-With": "XMLHttpRequest"  // просто маркер, на бэке не обязателен
      }
    })
      .then((r) => r.text())
      .then((html) => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");

        // Берём такой же блок с новой страницы
        const newBlock = doc.getElementById("services-block");
        if (!newBlock) return;

        // Заменяем только контент блока, без перезагрузки страницы
        servicesBlock.innerHTML = newBlock.innerHTML;

        // Опционально — прокрутить к началу блока плавно
        servicesBlock.scrollIntoView({ behavior: "smooth", block: "start" });
      })
      .catch((err) => {
        console.error("Помилка завантаження послуг:", err);
      });
  });
});
