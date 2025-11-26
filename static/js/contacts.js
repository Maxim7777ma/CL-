// static/js/contacts.js
document.addEventListener('DOMContentLoaded', function () {
  const tabs = document.querySelectorAll('.contacts-branch-tab');
  if (!tabs.length) return;

  const nameEl = document.getElementById('contacts-branch-name');
  const cityEl = document.getElementById('contacts-branch-city');
  const addressEl = document.getElementById('contacts-branch-address');
  const phoneMainEl = document.getElementById('contacts-branch-phone-main');
  const phoneAddWrapper = document.getElementById('contacts-branch-phone-additional-wrapper');
  const phoneAddEl = document.getElementById('contacts-branch-phone-additional');
  const mapFrame = document.getElementById('contacts-map-frame');
  const mapLinkEl = document.getElementById('contacts-map-link');

  function setActiveBranch(btn) {
    // активная кнопка
    tabs.forEach(t => t.classList.remove('is-active'));
    btn.classList.add('is-active');

    const name = btn.dataset.branchName || '';
    const city = btn.dataset.branchCity || '';
    const address = btn.dataset.branchAddress || '';
    const phoneMain = btn.dataset.branchPhoneMain || '';
    const phoneAdd = btn.dataset.branchPhoneAdditional || '';
    const lat = btn.dataset.branchLat || '';
    const lng = btn.dataset.branchLng || '';
    const mapLink = btn.dataset.branchMapLink || '';

    // текстовая информация
    if (nameEl) nameEl.textContent = name;
    if (cityEl) cityEl.textContent = city;
    if (addressEl) addressEl.textContent = address;

    // основной телефон
    if (phoneMainEl) {
      if (phoneMain) {
        phoneMainEl.textContent = phoneMain;
        phoneMainEl.href = 'tel:' + phoneMain.replace(/\s/g, '');
      } else {
        phoneMainEl.textContent = '';
        phoneMainEl.removeAttribute('href');
      }
    }

    // дополнительный телефон (если есть)
    if (phoneAddWrapper && phoneAddEl) {
      if (phoneAdd) {
        phoneAddWrapper.style.display = 'inline';
        phoneAddEl.textContent = phoneAdd;
        phoneAddEl.href = 'tel:' + phoneAdd.replace(/\s/g, '');
      } else {
        phoneAddWrapper.style.display = 'none';
      }
    }

    // карта (кастомная обёртка, но iframe обычный и бесплатный)
// карта (кастомная обёртка, но iframe обычный и бесплатный)
if (mapFrame) {
  let src = '';

  // собираем человеческий адрес из города + адреса
  const fullAddress =
    (city && address) ? (city + ', ' + address) :
    (address || city || '');

  if (mapLink) {
    // если в БД сохранена готовая ссылка из Google Maps — просто используем её
    src = mapLink;
  } else if (lat && lng && fullAddress) {
    // и адрес, и координаты: в q кладём адрес (его увидит юзер),
    // а в ll — координаты для точного центра карты
    src =
      'https://www.google.com/maps?q=' +
      encodeURIComponent(fullAddress) +
      '&ll=' + lat + ',' + lng +
      '&z=16&output=embed';
  } else if (fullAddress) {
    // только адрес — тоже ок
    src =
      'https://www.google.com/maps?q=' +
      encodeURIComponent(fullAddress) +
      '&z=16&output=embed';
  } else if (lat && lng) {
    // крайний случай — только координаты, как у тебя было
    src =
      'https://www.google.com/maps?q=' +
      lat + ',' + lng +
      '&z=16&output=embed';
  }

  if (src) {
    mapFrame.src = src;
  }
}


    // ссылка "відкрити в Google Maps"
// ссылка "відкрити в Google Maps"
if (mapLinkEl) {
  const fullAddress =
    (city && address) ? (city + ', ' + address) :
    (address || city || '');

  if (mapLink) {
    mapLinkEl.href = mapLink;
  } else if (fullAddress) {
    mapLinkEl.href =
      'https://www.google.com/maps?q=' + encodeURIComponent(fullAddress);
  } else if (lat && lng) {
    mapLinkEl.href =
      'https://www.google.com/maps?q=' + lat + ',' + lng + '&z=16';
  } else {
    mapLinkEl.href = '#';
  }
}

  }

  // Инициализация — активируем первую вкладку
  setActiveBranch(tabs[0]);

  // Обработчики кликов по табам
  tabs.forEach(btn => {
    btn.addEventListener('click', function () {
      setActiveBranch(this);
    });
  });
});
