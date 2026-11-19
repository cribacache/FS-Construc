(function () {
  "use strict";

  var drawer = document.getElementById("customizerDrawer");
  var siteMain = document.getElementById("siteMain");
  if (!drawer || !siteMain) return;

  siteMain.removeAttribute("data-style-preset");
  siteMain.removeAttribute("data-festive");

  var csrfMeta = document.querySelector('meta[name="csrf-token"]');
  var csrf = csrfMeta ? csrfMeta.getAttribute("content") : "";
  var statusEl = document.getElementById("editStatus");
  var urlSettingsSave = drawer.getAttribute("data-url-settings-save") || "/mis-fotos/api/settings/save/";
  var isDirty = false;

  function valOf(id, fallback) {
    var node = document.getElementById(id);
    return node ? node.value : fallback;
  }

  function checkedOf(id, fallback) {
    var node = document.getElementById(id);
    return node ? !!node.checked : fallback;
  }

  function setStatus(msg, isError) {
    if (!statusEl) return;
    statusEl.textContent = msg;
    statusEl.classList.toggle("is-error", !!isError);
  }

  function postJson(url, payload) {
    return fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf
      },
      body: JSON.stringify(payload || {})
    }).then(function (res) {
      return res.json().catch(function () {
        return { ok: false, error: "Respuesta inválida del servidor." };
      }).then(function (data) {
        if (!res.ok || !data.ok) throw new Error(data.error || "Error al guardar.");
        return data;
      });
    });
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  var dirtyIndicator = null;
  function markDirty() {
    isDirty = true;
    if (dirtyIndicator) {
      dirtyIndicator.textContent = "Cambios sin guardar";
      dirtyIndicator.classList.add("is-dirty");
    }
  }

  drawer.addEventListener("input", function (e) {
    if (e.target.id === "czGallerySearch" || e.target.type === "file") return;
    markDirty();
  });

  drawer.addEventListener("change", function (e) {
    if (e.target.id === "czGallerySearch" || e.target.type === "file") return;
    markDirty();
  });

  drawer.addEventListener("click", function (e) {
    if (e.target.closest(".cz-swatch, #czResetAccent, [data-sec-move]")) {
      markDirty();
    }
  });

  function collectFullSettingsPayload() {
    var order = [];
    var toggles = {};
    Array.prototype.forEach.call(drawer.querySelectorAll("#czSectionSorter .cz-sec-row"), function (row) {
      var key = row.getAttribute("data-sec-key");
      var chk = row.querySelector("[data-sec-toggle]");
      order.push(key);
      toggles[key] = chk ? chk.checked : true;
    });

    var customAccent = siteMain.style.getPropertyValue("--custom-accent");

    return {
      carousel_transition: valOf("czTransition", "fade"),
      carousel_interval: Math.max(3, parseInt(valOf("czInterval", "6"), 10) || 6),
      carousel_kenburns: checkedOf("czKenBurns", true),
      carousel_pause_hover: checkedOf("czPauseHover", false),
      phone_display: valOf("czPhoneDisplay", ""),
      phone_raw: valOf("czPhoneRaw", ""),
      whatsapp_number: valOf("czWhatsapp", ""),
      whatsapp_prefill: valOf("czWhatsappPrefill", ""),
      email_primary: valOf("czEmail1", "contacto@fsconstrucciones.cl"),
      email_sales: valOf("czEmail2", ""),
      office_location: valOf("czOfficeLocation", ""),
      instagram_handle: valOf("czIgHandle", ""),
      instagram_url: valOf("czIgUrl", ""),
      tiktok_handle: valOf("czTtHandle", ""),
      tiktok_url: valOf("czTtUrl", ""),
      theme_preset: siteMain.getAttribute("data-theme") || valOf("czThemePreset", "navy"),
      accent_color: customAccent ? customAccent.trim() : "",
      font_preset: siteMain.getAttribute("data-font") || valOf("czFontPreset", "editorial"),
      radius_preset: siteMain.getAttribute("data-radius") || valOf("czRadiusPreset", "pill"),
      section_spacing: siteMain.getAttribute("data-spacing") || valOf("czSectionSpacing", "normal"),
      hero_height: siteMain.getAttribute("data-hero-height") || valOf("czHeroHeight", "full"),
      hero_overlay: parseInt(valOf("czHeroOverlay", "48"), 10) || 48,
      cta_label: valOf("czCtaLabel", "Cotizar"),
      show_marquee: checkedOf("czShowMarquee", true),
      show_floating_wa: checkedOf("czShowFloatingWa", true),
      show_choose: toggles.choose !== false,
      show_portfolio: toggles.portfolio !== false,
      show_tech: toggles.tech !== false,
      show_services: toggles.services !== false,
      show_why: toggles.why !== false,
      section_order: order
    };
  }

  function saveAllEverything() {
    setStatus("Guardando todos los cambios…");
    var topSaveBtn = document.getElementById("editSave");
    if (topSaveBtn) topSaveBtn.click();

    return postJson(urlSettingsSave, collectFullSettingsPayload()).then(function () {
      isDirty = false;
      setStatus("Todo guardado. Actualizando vista…");
      window.location.reload();
    }).catch(function (err) {
      setStatus(err.message, true);
    });
  }

  Array.prototype.forEach.call(drawer.querySelectorAll(".czp-footer-bar"), function (oldBar) {
    oldBar.remove();
  });

  var footerBar = el("div", "czp-footer-bar");
  var footerTop = el("div", "czp-footer-top");
  dirtyIndicator = el("span", "czp-dirty-indicator", "Todo guardado");
  var footerActions = el("div", "czp-footer-actions");

  var discardAllBtn = el("button", "czp-btn-ghost", "Descartar");
  discardAllBtn.type = "button";
  discardAllBtn.addEventListener("click", function () {
    if (!isDirty || window.confirm("¿Descartar los cambios sin guardar y recargar?")) {
      isDirty = false;
      window.location.reload();
    }
  });

  var saveAllBtn = el("button", "czp-btn-save", "Guardar todo");
  saveAllBtn.type = "button";
  saveAllBtn.addEventListener("click", saveAllEverything);

  footerActions.appendChild(discardAllBtn);
  footerActions.appendChild(saveAllBtn);
  footerTop.appendChild(dirtyIndicator);
  footerTop.appendChild(footerActions);
  footerBar.appendChild(footerTop);
  footerBar.appendChild(el("p", "czp-footer-hint", "Los cambios se ven al instante en la página. Pulsa «Guardar todo» (Ctrl+S) para publicarlos."));

  drawer.appendChild(footerBar);

  document.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
      e.preventDefault();
      saveAllEverything();
    }
  });

  window.addEventListener("beforeunload", function (e) {
    if (isDirty) {
      e.preventDefault();
      e.returnValue = "";
    }
  });
})();