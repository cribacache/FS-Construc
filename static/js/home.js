(function () {
  document.querySelectorAll("[data-bg]").forEach(function (el) {
    var url = el.getAttribute("data-bg");
    if (url) el.style.backgroundImage = "url('" + url + "')";
  });

  var filters = document.querySelectorAll(".gallery-filter");
  var items = document.querySelectorAll(".gallery-item");

  var EDIT_MODE = document.documentElement.hasAttribute("data-edit");
  var GALLERY_PREVIEW = EDIT_MODE ? Infinity : 5;
  var moreBtn = document.getElementById("galleryMore");
  var currentFilter = "all";
  var expanded = false;

  function renderGallery() {
    var shown = 0;
    var matching = 0;
    items.forEach(function (item) {
      var match = currentFilter === "all" || item.getAttribute("data-category") === currentFilter;
      if (match) matching++;
      var show = match && (expanded || shown < GALLERY_PREVIEW);
      if (show) shown++;
      item.hidden = !show;
    });
    if (!moreBtn) return;
    var extra = matching - GALLERY_PREVIEW;
    moreBtn.hidden = extra <= 0;
    moreBtn.querySelector(".gallery-more-icon").innerHTML = expanded ? "&uarr;" : "&rarr;";
    moreBtn.querySelector(".gallery-more-title").textContent = expanded ? "Ver menos" : "Ver más";
    moreBtn.querySelector(".gallery-more-count").textContent =
      !expanded && extra > 0 ? "+ " + extra + (extra === 1 ? " proyecto" : " proyectos") : "";
  }

  function applyFilter(filter) {
    currentFilter = filter;
    expanded = false;
    filters.forEach(function (b) {
      b.classList.toggle("is-active", b.getAttribute("data-filter") === filter);
    });
    renderGallery();
  }

  if (moreBtn) {
    moreBtn.addEventListener("click", function () {
      expanded = !expanded;
      renderGallery();
      if (!expanded) {
        var section = document.getElementById("portafolio");
        if (section) section.scrollIntoView({ block: "start" });
      }
    });
  }
  renderGallery();

  filters.forEach(function (btn) {
    btn.addEventListener("click", function () {
      applyFilter(btn.getAttribute("data-filter"));
    });
  });

  // Navbar: los items del menu desplegable aplican el filtro / pestaña y luego
  // el ancla (#portafolio, #nosotros...) hace el scroll.
  document.querySelectorAll("[data-gallery-filter]").forEach(function (link) {
    link.addEventListener("click", function () {
      applyFilter(link.getAttribute("data-gallery-filter"));
    });
  });
  document.querySelectorAll("[data-values-tab]").forEach(function (link) {
    link.addEventListener("click", function () {
      var tab = document.querySelector('.values-tab[data-value="' + link.getAttribute("data-values-tab") + '"]');
      if (tab) tab.click();
    });
  });
  // Cierra el menu tras elegir (el hover lo mantendria abierto bajo el cursor).
  document.querySelectorAll(".nav-dropdown a").forEach(function (link) {
    link.addEventListener("click", function () {
      var item = link.closest(".nav-item");
      item.classList.add("is-closed");
      if (document.activeElement) document.activeElement.blur();
      item.addEventListener("mouseleave", function () { item.classList.remove("is-closed"); }, { once: true });
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

  function closeBuildPanel() { if (!EDIT_MODE) buildPanel.hidden = true; }
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
