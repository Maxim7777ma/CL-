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
  if (branchSelect) {
    branchSelect.addEventListener("change", function () {
      loadScheduleForSelected();
    });
  }

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

    const hours = data.hours || [];
    const doctors = data.doctors || [];

    // Верхняя строка с врачами
    doctorsContainer.innerHTML = "";
    doctors.forEach((doc) => {
      const div = document.createElement("div");
      div.className = "schedule-grid__doctors-item";
      div.textContent = doc.name;
      div.dataset.doctorId = doc.id;
      doctorsContainer.appendChild(div);
    });

    // Левая колонка времени
    timesContainer.innerHTML = "";
    hours.forEach((h) => {
      const div = document.createElement("div");
      div.className = "schedule-grid__time-cell";
      div.textContent = h;
      timesContainer.appendChild(div);
    });

    // Сетка ячеек
    cellsContainer.innerHTML = "";
    hours.forEach((h) => {
      const row = document.createElement("div");
      row.className = "schedule-grid__row";

      doctors.forEach((doc) => {
        const cell = document.createElement("div");
        cell.className = "schedule-slot";

        const busyInfo = (doc.busy_slots || {})[h + ":00".slice(2)]; // если у тебя формат "09:00" совпадает, можно doc.busy_slots[h]

        // наш data.busy_slots ключи: "HH:MM"
        const busy = (doc.busy_slots || {})[h];

        if (busy) {
          const label = document.createElement("div");
          label.className = "schedule-slot__label-busy";
          label.textContent = busy.service || "Зайнято";
          cell.appendChild(label);
        } else {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "schedule-slot__btn";
          btn.textContent = "Вільно";

          btn.addEventListener("click", () => {
            if (!isAuth) {
              alert("Щоб записатися онлайн, увійдіть або зареєструйтесь.");
              return;
            }
            const selectedBranchId = branchSelect && branchSelect.value ? branchSelect.value : "";
            openBookingModal({
              date: data.date,
              time: h,
              // якщо філію не вибрали — беремо ту, де працює лікар
              branchId: selectedBranchId || doc.branch_id || "",
              branchName: doc.branch || "",
              doctorId: doc.id,
              doctorName: doc.name,
            });
          });

          cell.appendChild(btn);

        }

        row.appendChild(cell);
      });

      cellsContainer.appendChild(row);
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
