(function () {
  document.querySelectorAll("[data-bg]").forEach(function (el) {
    var url = el.getAttribute("data-bg");
    if (url) el.style.backgroundImage = "url('" + url + "')";
  });

  var filters = document.querySelectorAll(".gallery-filter");
  var items = document.querySelectorAll(".gallery-item");

  filters.forEach(function (btn) {
    btn.addEventListener("click", function () {
      filters.forEach(function (b) { b.classList.remove("is-active"); });
      btn.classList.add("is-active");
      var filter = btn.getAttribute("data-filter");
      items.forEach(function (item) {
        var show = filter === "all" || item.getAttribute("data-category") === filter;
        item.hidden = !show;
      });
    });
  });

  var lightbox = document.getElementById("lightbox");
  var lightboxImg = document.getElementById("lightboxImg");
  var lightboxClose = document.getElementById("lightboxClose");

  items.forEach(function (item) {
    item.addEventListener("click", function () {
      lightboxImg.src = item.getAttribute("data-full");
      lightboxImg.alt = item.querySelector("img").alt;
      lightbox.hidden = false;
    });
  });

  function closeLightbox() { lightbox.hidden = true; lightboxImg.src = ""; }
  lightboxClose.addEventListener("click", closeLightbox);
  lightbox.addEventListener("click", function (e) {
    if (e.target === lightbox) closeLightbox();
  });

  var buildPromptBtn = document.getElementById("buildPromptBtn");
  var buildPanel = document.getElementById("buildPanel");
  var buildPanelClose = document.getElementById("buildPanelClose");

  function closeBuildPanel() { buildPanel.hidden = true; }
  buildPromptBtn.addEventListener("click", function () { buildPanel.hidden = false; });
  buildPanelClose.addEventListener("click", closeBuildPanel);
  buildPanel.addEventListener("click", function (e) {
    if (e.target === buildPanel) closeBuildPanel();
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    closeLightbox();
    closeBuildPanel();
  });

  var valueTabs = document.querySelectorAll(".values-tab");
  var valuePanels = document.querySelectorAll(".values-tab-panel-item");
  valueTabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      var value = tab.getAttribute("data-value");
      valueTabs.forEach(function (t) {
        t.classList.remove("is-active");
        t.setAttribute("aria-selected", "false");
      });
      tab.classList.add("is-active");
      tab.setAttribute("aria-selected", "true");
      valuePanels.forEach(function (p) {
        p.classList.toggle("is-active", p.getAttribute("data-value") === value);
      });
    });
  });
})();
