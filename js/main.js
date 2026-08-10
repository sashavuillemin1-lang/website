(function () {
  "use strict";

  var header = document.getElementById("site-header");
  var navToggle = document.getElementById("nav-toggle");
  var mainNav = document.getElementById("main-nav");

  window.addEventListener("scroll", function () {
    header.classList.toggle("is-scrolled", window.scrollY > 30);
  });

  navToggle.addEventListener("click", function () {
    var isOpen = header.classList.toggle("nav-open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
  });
  mainNav.querySelectorAll(".nav-link").forEach(function (link) {
    link.addEventListener("click", function () {
      header.classList.remove("nav-open");
      navToggle.setAttribute("aria-expanded", "false");
    });
  });

  var sections = document.querySelectorAll("main section[id]");
  var navLinks = document.querySelectorAll(".nav-link");
  var sectionObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        navLinks.forEach(function (link) {
          link.classList.toggle("is-active", link.getAttribute("href") === "#" + entry.target.id);
        });
      }
    });
  }, { rootMargin: "-45% 0px -45% 0px" });
  sections.forEach(function (section) { sectionObserver.observe(section); });

  var revealItems = document.querySelectorAll(".reveal");
  var revealObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });
  revealItems.forEach(function (item) { revealObserver.observe(item); });

  var menuTabs = document.querySelectorAll(".menu-tab");
  var menuCards = document.querySelectorAll(".menu-card");
  menuTabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      menuTabs.forEach(function (t) { t.classList.remove("is-active"); t.setAttribute("aria-selected", "false"); });
      tab.classList.add("is-active");
      tab.setAttribute("aria-selected", "true");
      var cat = tab.dataset.cat;
      menuCards.forEach(function (card) {
        card.hidden = card.dataset.cat !== cat;
      });
    });
  });

  var reserveForm = document.getElementById("reserve-form");
  var reserveSuccess = document.getElementById("reserve-success");
  var reserveSuccessDetail = document.getElementById("reserve-success-detail");
  var reserveAgain = document.getElementById("reserve-again");
  var dateInput = document.getElementById("r-date");

  if (dateInput) {
    var today = new Date();
    today.setHours(0, 0, 0, 0);
    dateInput.min = today.toISOString().slice(0, 10);
  }

  function setFieldError(field, hasError) {
    field.classList.toggle("has-error", hasError);
  }

  function isValidEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  }

  function isFutureOrTodayDate(value) {
    if (!value) return false;
    var chosen = new Date(value + "T00:00:00");
    var today0 = new Date();
    today0.setHours(0, 0, 0, 0);
    return chosen.getTime() >= today0.getTime();
  }

  if (reserveForm) {
    reserveForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var valid = true;

      var nameField = document.getElementById("r-name").closest(".field");
      var nameOk = document.getElementById("r-name").value.trim().length > 1;
      setFieldError(nameField, !nameOk);
      if (!nameOk) valid = false;

      var dateField = document.getElementById("r-date").closest(".field");
      var dateOk = isFutureOrTodayDate(document.getElementById("r-date").value);
      setFieldError(dateField, !dateOk);
      if (!dateOk) valid = false;

      var timeField = document.getElementById("r-time").closest(".field");
      var timeOk = document.getElementById("r-time").value !== "";
      setFieldError(timeField, !timeOk);
      if (!timeOk) valid = false;

      var emailField = document.getElementById("r-email").closest(".field");
      var emailOk = isValidEmail(document.getElementById("r-email").value.trim());
      setFieldError(emailField, !emailOk);
      if (!emailOk) valid = false;

      var phoneField = document.getElementById("r-phone").closest(".field");
      var phoneOk = document.getElementById("r-phone").value.trim().length > 5;
      setFieldError(phoneField, !phoneOk);
      if (!phoneOk) valid = false;

      if (!valid) {
        var firstError = reserveForm.querySelector(".has-error input, .has-error select");
        if (firstError) firstError.focus();
        return;
      }

      var name = document.getElementById("r-name").value.trim();
      var guests = document.getElementById("r-guests").value;
      var date = document.getElementById("r-date").value;
      var time = document.getElementById("r-time").value;
      var formattedDate = new Date(date + "T00:00:00").toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" });

      reserveSuccessDetail.textContent = "Merci " + name.split(" ")[0] + ", votre table pour " + guests + " est demandée le " + formattedDate + " à " + time + ".";
      reserveForm.hidden = true;
      reserveSuccess.hidden = false;
    });
  }

  if (reserveAgain) {
    reserveAgain.addEventListener("click", function () {
      reserveSuccess.hidden = true;
      reserveForm.hidden = false;
    });
  }

  var newsletterForm = document.getElementById("newsletter-form");
  var newsletterNote = document.getElementById("newsletter-note");
  if (newsletterForm) {
    newsletterForm.addEventListener("submit", function (e) {
      e.preventDefault();
      newsletterForm.hidden = true;
      newsletterNote.hidden = false;
    });
  }

  var yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  var locationIframe = document.getElementById("location-iframe");
  if (locationIframe) {
    locationIframe.addEventListener("load", function () {
      locationIframe.classList.add("is-loaded");
    });
  }
})();
