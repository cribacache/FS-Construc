(function () {
  "use strict";

  var root = document.documentElement;
  var EDIT = root.hasAttribute("data-edit");
  var ANIM = root.classList.contains("anim");
  var FINE = !!(window.matchMedia && window.matchMedia("(pointer: fine)").matches);
  var REDUCED = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  root.classList.add("anim-ready");

  function $(selector, context) { return (context || document).querySelector(selector); }
  function $$(selector, context) { return Array.prototype.slice.call((context || document).querySelectorAll(selector)); }
  function clamp(value, min, max) { return Math.min(max, Math.max(min, value)); }
  function make(tag, className) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    return node;
  }

  // Un módulo que falla no debe dejar la página oculta ni romper a los demás.
  function safe(fn, animated) {
    try {
      fn();
    } catch (error) {
      if (window.console) window.console.error(error);
      if (animated) { root.classList.remove("anim"); root.classList.remove("is-intro"); }
    }
  }

  /* ------------------------------------------------------------------ */
  /* Scroll suave (inercia). Solo con mouse/trackpad; en táctil es nativo */
  /* ------------------------------------------------------------------ */
  var smooth = null;

  safe(function () {
    if (!ANIM || !FINE) return;
    var target = window.pageYOffset;
    var current = target;
    var running = false;
    var LERP = 0.09;

    function maxScroll() { return Math.max(0, root.scrollHeight - window.innerHeight); }

    function tick() {
      var diff = target - current;
      if (Math.abs(diff) < 0.4) {
        current = target;
        window.scrollTo(0, current);
        running = false;
        return;
      }
      current += diff * LERP;
      window.scrollTo(0, current);
      window.requestAnimationFrame(tick);
    }

    function start() {
      if (running) return;
      current = window.pageYOffset;
      running = true;
      window.requestAnimationFrame(tick);
    }

    function blocked(node) {
      if (root.classList.contains("no-scroll") || root.classList.contains("is-intro")) return true;
      return !!(node && node.closest && node.closest("textarea, select, [data-no-smooth]"));
    }

    window.addEventListener("wheel", function (event) {
      if (event.ctrlKey || event.defaultPrevented || blocked(event.target)) return;
      if (Math.abs(event.deltaX) > Math.abs(event.deltaY)) return;
      event.preventDefault();
      var delta = event.deltaY;
      if (event.deltaMode === 1) delta *= 32;
      else if (event.deltaMode === 2) delta *= window.innerHeight;
      if (!running) target = window.pageYOffset;
      target = clamp(target + delta, 0, maxScroll());
      start();
    }, { passive: false });

    window.addEventListener("scroll", function () {
      if (!running) { target = current = window.pageYOffset; }
    }, { passive: true });

    window.addEventListener("resize", function () { target = clamp(target, 0, maxScroll()); });

    smooth = { to: function (y) { target = clamp(y, 0, maxScroll()); start(); } };
  }, true);

  function scrollToElement(node) {
    var margin = parseFloat(window.getComputedStyle(node).scrollMarginTop) || 0;
    var y = node.getBoundingClientRect().top + window.pageYOffset - margin;
    if (smooth) smooth.to(y);
    else window.scrollTo({ top: y, behavior: REDUCED ? "auto" : "smooth" });
  }

  /* ------------------------------------------------------------------ */
  /* Intro y portada                                                      */
  /* ------------------------------------------------------------------ */
  var intro = $("#intro");

  function heroIn() { root.classList.add("hero-in"); }

  safe(function () {
    if (!ANIM) return;
    if (root.classList.contains("is-intro") && intro) {
      window.setTimeout(heroIn, 2200);
      window.setTimeout(function () { intro.classList.add("is-out"); }, 2600);
      window.setTimeout(function () { root.classList.remove("is-intro"); }, 3800);
    } else {
      window.setTimeout(heroIn, 120);
    }
  }, true);

  /* ------------------------------------------------------------------ */
  /* Titulares por línea (máscara) y portada letra por letra              */
  /* ------------------------------------------------------------------ */
  function readLines(node) {
    var lines = [""];
    Array.prototype.forEach.call(node.childNodes, function (child) {
      if (child.nodeName === "BR") lines.push("");
      else lines[lines.length - 1] += child.textContent;
    });
    return lines
      .map(function (line) { return line.replace(/\s+/g, " ").trim(); })
      .filter(Boolean);
  }

  function buildLines(node, lines, letters) {
    var full = lines.join(" ");
    node.textContent = "";
    node.setAttribute("aria-label", full);
    return lines.map(function (text) {
      var mask = make("span", "ln");
      var inner = make("span", "ln-in");
      mask.setAttribute("aria-hidden", "true");
      if (letters) {
        text.split("").forEach(function (character) {
          var letter = make("span", "ch");
          letter.textContent = character === " " ? "\u00a0" : character;
          inner.appendChild(letter);
        });
      } else {
        inner.textContent = text;
      }
      mask.appendChild(inner);
      node.appendChild(mask);
      return inner;
    });
  }

  // Última línea del titular en acento azul; si el titular es de una sola línea,
  // solo su última palabra.
  function accentLastLine(inners, lines) {
    if (!inners.length) return;
    if (inners.length > 1) {
      inners[inners.length - 1].classList.add("ln-accent");
      return;
    }
    var words = lines[0].split(" ");
    if (words.length < 2) return;
    var last = words.pop();
    inners[0].textContent = words.join(" ") + " ";
    var emphasis = document.createElement("em");
    emphasis.className = "ln-accent";
    emphasis.textContent = last;
    inners[0].appendChild(emphasis);
  }

  safe(function () {
    if (EDIT) return;

    var title = $("#heroTitle");
    if (title) {
      var lines = readLines(title);
      var words = lines.join(" ").split(" ");
      if (words.length <= 4) lines = words;
      var inners = buildLines(title, lines, ANIM);
      if (inners.length === 3) inners[1].classList.add("is-accent");
      if (ANIM) {
        inners.forEach(function (inner, index) {
          $$(".ch", inner).forEach(function (letter, position) {
            letter.style.transitionDelay = (index * 0.12 + position * 0.03) + "s";
          });
        });
      }
    }

    $$("[data-lines]").forEach(function (heading) {
      var lines = readLines(heading);
      var inners = buildLines(heading, lines, false);
      accentLastLine(inners, lines);
      inners.forEach(function (inner, index) { inner.style.transitionDelay = (index * 0.12) + "s"; });
    });

    var studio = $("#studioTitle");
    if (studio) {
      var text = studio.textContent.replace(/\s+/g, " ").trim();
      studio.textContent = "";
      studio.setAttribute("aria-label", text);
      text.split(" ").forEach(function (word, index) {
        var span = make("span", "w");
        span.setAttribute("aria-hidden", "true");
        if (index >= 4) {
          var emphasis = document.createElement("em");
          emphasis.textContent = word;
          span.appendChild(emphasis);
        } else {
          span.textContent = word;
        }
        span.style.transitionDelay = (index * 0.08) + "s";
        studio.appendChild(span);
        studio.appendChild(document.createTextNode(" "));
      });
    }
  }, true);

  /* ------------------------------------------------------------------ */
  /* Revelado al hacer scroll                                             */
  /* ------------------------------------------------------------------ */
  function runCounter(node) {
    var to = parseInt(node.getAttribute("data-count"), 10) || 0;
    var begin = window.performance.now();
    function frame(now) {
      var k = Math.min(1, (now - begin) / 1800);
      node.textContent = String(Math.round(to * (1 - Math.pow(1 - k, 4))));
      if (k < 1) window.requestAnimationFrame(frame);
    }
    window.requestAnimationFrame(frame);
  }

  safe(function () {
    if (!ANIM) return;
    var counters = $$("[data-count]");
    counters.forEach(function (node) { node.textContent = "0"; });

    $$("[data-reveal]").forEach(function (node) {
      var stagger = parseFloat(node.getAttribute("data-stagger"));
      if (!isNaN(stagger)) node.style.transitionDelay = (stagger * 0.1) + "s";
    });

    var once = $$("[data-reveal], [data-lines], .imgrev, [data-count]");
    var words = $$("#studioTitle .w");

    if (!("IntersectionObserver" in window)) {
      once.forEach(function (node) { node.classList.add("is-in"); });
      words.forEach(function (node) { node.classList.add("is-in"); });
      counters.forEach(runCounter);
      return;
    }

    var observer = new window.IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var node = entry.target;
        observer.unobserve(node);
        if (node.hasAttribute("data-count")) runCounter(node);
        else node.classList.add("is-in");
      });
    }, { rootMargin: "0px 0px -10% 0px" });
    once.forEach(function (node) { observer.observe(node); });

    var wordObserver = new window.IntersectionObserver(function (entries) {
      entries.forEach(function (entry) { entry.target.classList.toggle("is-in", entry.isIntersecting); });
    }, { rootMargin: "-30% 0px -30% 0px" });
    words.forEach(function (node) { wordObserver.observe(node); });
  }, true);

  /* ------------------------------------------------------------------ */
  /* Cabecera, menú móvil y efectos ligados al scroll                     */
  /* ------------------------------------------------------------------ */
  var header = $("#siteHeader");
  var menu = $("#mobileMenu");
  var menuButton = $("#menuBtn");
  var mobileProjectsToggle = $("#mobileProjectsToggle");
  var mobileProjectsGroup = $("#mobileProjectsGroup");

  function openMenu() {
    if (!menu) return;
    menu.classList.add("is-open");
    menu.setAttribute("aria-hidden", "false");
    menuButton.setAttribute("aria-expanded", "true");
    root.classList.add("no-scroll");
  }

  function closeMenu() {
    if (mobileProjectsGroup && mobileProjectsGroup.classList.contains("is-open")) {
      mobileProjectsGroup.classList.remove("is-open");
      if (mobileProjectsToggle) mobileProjectsToggle.setAttribute("aria-expanded", "false");
    }
    if (!menu || !menu.classList.contains("is-open")) return;
    menu.classList.remove("is-open");
    menu.setAttribute("aria-hidden", "true");
    menuButton.setAttribute("aria-expanded", "false");
    root.classList.remove("no-scroll");
  }

  if (menuButton) menuButton.addEventListener("click", openMenu);
  if (menu) {
    var menuClose = $("#menuClose");
    if (menuClose) menuClose.addEventListener("click", closeMenu);
  }
  if (mobileProjectsToggle && mobileProjectsGroup) {
    mobileProjectsToggle.addEventListener("click", function () {
      var isOpen = mobileProjectsGroup.classList.toggle("is-open");
      mobileProjectsToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });
  }

  var hero = $("#inicio");
  var heroMedia = $(".hero-media");
  var heroContent = $(".hero-content");
  var studioSection = $("#estudio");
  var studioMark = $(".studio-mark");
  var studioMedia = $("#studioMedia");
  var processSection = $("#proceso");
  var processFill = $("#processFill");
  var ticking = false;

  function update() {
    ticking = false;
    var vh = window.innerHeight;
    var y = window.pageYOffset;

    if (header) header.classList.toggle("is-solid", y > 60);
    if (!ANIM) return;

    if (hero && heroMedia && heroContent && y <= hero.offsetHeight) {
      var p = clamp(y / hero.offsetHeight, 0, 1);
      heroMedia.style.transform = "translate3d(0," + (p * 30) + "%,0)";
      heroContent.style.opacity = String(clamp(1 - p / 0.6, 0, 1));
    }

    if (studioSection) {
      var rect = studioSection.getBoundingClientRect();
      if (rect.bottom > 0 && rect.top < vh) {
        var q = clamp((vh - rect.top) / (vh + rect.height), 0, 1);
        if (studioMark) studioMark.style.transform = "translate3d(0," + (-15 + 30 * q) + "%,0)";
        if (studioMedia) {
          var image = studioMedia.firstElementChild;
          if (image) image.style.transform = "scale(" + (0.7 + 0.3 * clamp(q / 0.5, 0, 1)) + ")";
        }
      }
    }

    if (processSection && processFill) {
      var box = processSection.getBoundingClientRect();
      var r = clamp((vh * 0.75 - box.top) / (box.height + vh * 0.15), 0, 1);
      processFill.style.transform = "scaleX(" + r + ")";
    }
  }

  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(update);
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);
  update();

  /* ------------------------------------------------------------------ */
  /* Servicios: lista + foto/video fijo                                   */
  /* ------------------------------------------------------------------ */
  safe(function () {
    var items = $$(".svc-item");
    if (!items.length) return;
    var images = $$(".svc-img");
    var captions = $$(".svc-cap-title");
    var count = $("#svcCount");
    var active = 0;

    function activate(index) {
      if (index === active) return;
      active = index;
      items.forEach(function (item, i) { item.classList.toggle("is-active", i === index); });
      images.forEach(function (media, i) {
        var isCurrent = i === index;
        media.classList.toggle("is-active", isCurrent);
        if (isCurrent && media.tagName === "VIDEO" && media.paused) {
          media.play().catch(function () {});
        }
      });
      captions.forEach(function (caption, i) { caption.classList.toggle("is-active", i === index); });
      if (count) count.textContent = (index < 9 ? "0" : "") + (index + 1);
    }

    items.forEach(function (item, index) {
      item.addEventListener("mouseenter", function () { activate(index); });
      item.addEventListener("focusin", function () { activate(index); });
      item.addEventListener("click", function () { activate(index); });
    });
  });

  /* ------------------------------------------------------------------ */
  /* Portafolio: filtros, "ver más" y visor (fotos y videos en loop)      */
  /* ------------------------------------------------------------------ */
  var galleryGrid = $(".gallery-grid");
  var applyFilter = function () {};

  safe(function () {
    if (!galleryGrid) return;

    var filters = $$(".gallery-filter");
    var moreButton = $("#galleryMore");
    var PREVIEW = EDIT ? Infinity : 9;
    var RATIOS = ["tall", "square", "tall", "wide"];
    var startButton = $(".gallery-filter.is-active");
    var currentFilter = startButton ? startButton.getAttribute("data-filter") : "all";
    var expanded = false;

    function columnCount() {
      var template = window.getComputedStyle(galleryGrid).gridTemplateColumns || "";
      return Math.max(1, template.split(" ").filter(Boolean).length);
    }

    function render(animate) {
      var items = $$(".gallery-item", galleryGrid);
      var columns = columnCount();
      var shown = 0;
      var matching = 0;

      items.forEach(function (item) {
        var match = currentFilter === "all" || item.getAttribute("data-category") === currentFilter;
        if (match) matching++;
        var show = match && (expanded || shown < PREVIEW);
        item.hidden = !show;
        if (!show) return;
        var video = item.querySelector("video");
        if (video && video.paused) video.play().catch(function () {});
        item.setAttribute("data-ratio", RATIOS[Math.floor(shown / columns) % RATIOS.length]);
        if (animate && ANIM) {
          item.classList.remove("is-pop");
          void item.offsetWidth;
          item.style.animationDelay = (shown * 0.04) + "s";
          item.classList.add("is-pop");
        }
        shown++;
      });

      if (!moreButton) return;
      var extra = matching - PREVIEW;
      moreButton.hidden = !(extra > 0);
      moreButton.querySelector(".gallery-more-icon").innerHTML = expanded ? "&uarr;" : "&rarr;";
      moreButton.querySelector(".gallery-more-title").textContent = expanded ? "Ver menos" : "Ver más";
      moreButton.querySelector(".gallery-more-count").textContent =
        !expanded && extra > 0 ? "+ " + extra + (extra === 1 ? " proyecto" : " proyectos") : "";
    }

    applyFilter = function (filter) {
      currentFilter = filter;
      expanded = false;
      filters.forEach(function (button) {
        button.classList.toggle("is-active", button.getAttribute("data-filter") === filter);
      });
      render(true);
    };

    filters.forEach(function (button) {
      button.addEventListener("click", function () { applyFilter(button.getAttribute("data-filter")); });
    });

    if (moreButton) {
      moreButton.addEventListener("click", function () {
        expanded = !expanded;
        render(true);
        if (!expanded) {
          var section = $("#portafolio");
          if (section) scrollToElement(section);
        }
      });
    }

    galleryGrid.addEventListener("animationend", function (event) {
      if (event.target.classList && event.target.classList.contains("gallery-item")) {
        event.target.classList.remove("is-pop");
      }
    });

    var resizeTimer = 0;
    window.addEventListener("resize", function () {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(function () { render(false); }, 150);
    });

    render(false);

    /* Visor a pantalla completa */
    var box = $("#lightbox");
    var image = $("#lightboxImg");
    var video = $("#lightboxVideo");
    var titleNode = $("#lightboxTitle");
    var categoryNode = $("#lightboxCat");
    var currentItem = null;
    var closeTimer = 0;

    function visibleItems() {
      return $$(".gallery-item", galleryGrid).filter(function (item) { return !item.hidden; });
    }

    function resetVideo() {
      if (!video) return;
      video.pause();
      video.hidden = true;
      video.removeAttribute("src");
      video.load();
    }

    function show(item) {
      currentItem = item;
      var src = item.getAttribute("data-full");
      var isVideo = item.getAttribute("data-kind") === "video";
      if (isVideo && video) {
        image.hidden = true;
        image.src = "";
        video.hidden = false;
        video.src = src;
        video.play().catch(function () {});
      } else {
        resetVideo();
        image.hidden = false;
        image.src = src;
        image.alt = item.getAttribute("data-title") || "";
      }
      titleNode.textContent = item.getAttribute("data-title") || "";
      categoryNode.textContent = item.getAttribute("data-label") || "";
    }

    function triggerOpen() {
      window.requestAnimationFrame(function () {
        window.requestAnimationFrame(function () {
          if (!box.hidden) box.classList.add("is-open");
        });
      });
    }

    function open(item) {
      window.clearTimeout(closeTimer);
      $$("video", galleryGrid).forEach(function (v) { v.pause(); });
      show(item);
      box.hidden = false;
      root.classList.add("no-scroll");
      if (item.getAttribute("data-kind") !== "video" && image.decode) {
        image.decode().then(triggerOpen, triggerOpen);
      } else {
        triggerOpen();
      }
    }

    function close() {
      if (box.hidden) return;
      box.classList.remove("is-open");
      root.classList.remove("no-scroll");
      closeTimer = window.setTimeout(function () {
        box.hidden = true;
        image.src = "";
        resetVideo();
        $$(".gallery-item:not([hidden]) video", galleryGrid).forEach(function (v) {
          v.play().catch(function () {});
        });
      }, 320);
    }

    function step(direction) {
      var list = visibleItems();
      if (!list.length || !currentItem) return;
      var index = list.indexOf(currentItem);
      show(list[(index + direction + list.length) % list.length]);
    }

    $$(".gallery-item", galleryGrid).forEach(function (item) {
      item.addEventListener("click", function () { open(item); });
    });
    $("#lightboxClose").addEventListener("click", close);
    $("#lightboxPrev").addEventListener("click", function (event) { event.stopPropagation(); step(-1); });
    $("#lightboxNext").addEventListener("click", function (event) { event.stopPropagation(); step(1); });
    box.addEventListener("click", function (event) {
      if (event.target === box) close();
    });

    document.addEventListener("keydown", function (event) {
      if (box.hidden) return;
      if (event.key === "ArrowLeft") step(-1);
      else if (event.key === "ArrowRight") step(1);
    });
    box._close = close;
  });

  /* ------------------------------------------------------------------ */
  /* Contacto: cotizar / consultas y trabajo, CV y envío por WhatsApp     */
  /* ------------------------------------------------------------------ */
  var setContactMode = function () {};

  safe(function () {
    var form = $("#contactForm");
    if (!form) return;
    var tabs = $$(".contact-tab");
    var select = form.querySelector("select");
    var message = form.querySelector("textarea");
    var label = $("#serviceLabel");
    var cvRow = $("#cvRow");
    var cvPicker = $("#cvPicker");
    var cvInput = form.querySelector("input[type='file']");
    var cvFileName = $("#cvFileName");
    var cvClear = $("#cvClear");
    var defaultCvText = cvFileName ? cvFileName.textContent : "Adjuntar CV (PDF o Word)";
    var JOB = ["consulta", "trabajo"];
    var quotePlaceholder = message ? message.getAttribute("placeholder") || "" : "";
    var contactPlaceholder = "Escribe tu consulta o cuéntanos cómo te gustaría sumarte al equipo…";

    function updateCvLabel() {
      if (!cvInput || !cvFileName) return;
      var hasFile = !!(cvInput.files && cvInput.files.length);
      cvFileName.textContent = hasFile ? cvInput.files[0].name : defaultCvText;
      if (cvPicker) cvPicker.classList.toggle("has-file", hasFile);
      if (cvClear) cvClear.hidden = !hasFile;
    }

    function clearCv() {
      if (!cvInput) return;
      cvInput.value = "";
      updateCvLabel();
    }

    if (cvInput) cvInput.addEventListener("change", updateCvLabel);
    if (cvClear) {
      cvClear.addEventListener("click", function (event) {
        event.preventDefault();
        clearCv();
      });
    }

    setContactMode = function (mode) {
      var isContact = mode === "contacto";
      tabs.forEach(function (tab) {
        var on = tab.getAttribute("data-mode") === mode;
        tab.classList.toggle("is-active", on);
        tab.setAttribute("aria-selected", on ? "true" : "false");
      });
      if (label) label.textContent = isContact ? "Motivo del mensaje" : "Servicio de interés";
      if (message) message.setAttribute("placeholder", isContact ? contactPlaceholder : quotePlaceholder);
      if (cvRow) cvRow.hidden = !isContact;
      if (!isContact) clearCv();
      if (!select) return;
      Array.prototype.forEach.call(select.options, function (option) {
        var isJob = JOB.indexOf(option.value) !== -1;
        var allowed = option.value === "" || option.value === "otro" || (isContact ? isJob : !isJob);
        option.disabled = !allowed;
        option.hidden = !allowed;
      });
      if (select.selectedOptions.length && select.selectedOptions[0].disabled) select.value = "";
      if (isContact && !select.value) select.value = "consulta";
    };

    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () { setContactMode(tab.getAttribute("data-mode")); });
    });

    setContactMode(select && JOB.indexOf(select.value) !== -1 ? "contacto" : "cotizar");

    var whatsapp = $("#waSend");
    if (whatsapp) {
      whatsapp.addEventListener("click", function () {
        function value(name) {
          var field = form.elements[name];
          return field && field.value ? field.value.trim() : "";
        }
        var service = select && select.selectedOptions.length && select.value
          ? select.selectedOptions[0].textContent.trim() : "";
        var text = "Hola FS Construcciones, soy " + (value("name") || "un visitante del sitio") + ".";
        if (service) text += "\nInterés: " + service;
        if (value("message")) text += "\n" + value("message");
        if (cvInput && cvInput.files && cvInput.files.length) {
          text += "\nAdjunto mi CV: " + cvInput.files[0].name;
        }
        var contact = [value("phone"), value("email")].filter(Boolean).join(" / ");
        if (contact) text += "\nContacto: " + contact;
        window.open("https://wa.me/" + whatsapp.getAttribute("data-wa") + "?text=" + encodeURIComponent(text), "_blank", "noopener");
      });
    }
  });

  /* ------------------------------------------------------------------ */
  /* Enlaces internos (scroll suave, filtro y modo de contacto)           */
  /* ------------------------------------------------------------------ */
  document.addEventListener("click", function (event) {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    var link = event.target.closest ? event.target.closest("a[href^='#']") : null;
    if (!link) return;
    var hash = link.getAttribute("href");
    if (!hash || hash.length < 2) return;
    var node = document.getElementById(hash.slice(1));
    if (!node) return;

    event.preventDefault();
    var mode = link.getAttribute("data-contact-mode");
    if (mode) setContactMode(mode);
    var filter = link.getAttribute("data-gallery-filter") || link.getAttribute("data-nav-filter");
    if (filter) applyFilter(filter);
    if (link.blur) link.blur();
    closeMenu();
    scrollToElement(node);
    if (window.history && window.history.replaceState) window.history.replaceState(null, "", hash);
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    closeMenu();
    var box = $("#lightbox");
    if (box && box._close) box._close();
  });
})();