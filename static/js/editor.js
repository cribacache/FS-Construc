(function () {
  if (!document.documentElement.hasAttribute("data-edit")) return;

  var csrf = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
  var statusEl = document.getElementById("editStatus");
  var chipEl = document.getElementById("editChip");
  var saveBtn = document.getElementById("editSave");
  var discardBtn = document.getElementById("editDiscard");
  var drag = null; // { type: "slot" | "tile", id, slot }
  var root = document.documentElement;
  var DRAG_TYPE = "application/x-fs-photo";
  var MEDIA_ACCEPT = "image/*,video/mp4,video/webm,video/quicktime,video/ogg";

  function setStatus(message, isError) {
    if (!statusEl) return;
    statusEl.textContent = message;
    statusEl.classList.toggle("is-error", !!isError);
  }

  function post(url, body) {
    var options = { method: "POST", credentials: "same-origin", headers: { "X-CSRFToken": csrf } };
    if (body instanceof FormData) {
      options.body = body;
    } else {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body || {});
    }
    return fetch(url, options).then(function (response) {
      return response.json().catch(function () { return { ok: false, error: "Respuesta inválida del servidor." }; })
        .then(function (data) {
          if (!response.ok || !data.ok) throw new Error(data.error || "No se pudo guardar.");
          return data;
        });
    });
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function stop(handler) {
    return function (event) {
      event.preventDefault();
      event.stopPropagation();
      handler(event);
    };
  }

  // ---------- Texts ----------

  var texts = Array.prototype.slice.call(document.querySelectorAll(".ed-text"));
  var plainOnly = (function () {
    var probe = document.createElement("div");
    probe.setAttribute("contenteditable", "plaintext-only");
    return probe.contentEditable === "plaintext-only";
  })();

  function readText(node) {
    var raw = (node.innerText || node.textContent || "").replace(/\r/g, "");
    var lines = raw.split("\n").map(function (line) { return line.replace(/\s+/g, " ").trim(); });
    if (node.hasAttribute("data-multiline")) return lines.filter(Boolean).join("\n");
    return lines.join(" ").replace(/\s+/g, " ").trim();
  }

  function writeText(node, value) {
    node.textContent = "";
    value.split("\n").forEach(function (line, index) {
      if (index) node.appendChild(document.createElement("br"));
      node.appendChild(document.createTextNode(line));
    });
  }

  function syncCopies(node) {
    var key = node.getAttribute("data-text-key");
    var value = readText(node).replace(/\n/g, " ");
    document.querySelectorAll('[data-text-sync="' + key + '"]').forEach(function (copy) {
      copy.textContent = value;
    });
  }

  function collectChanges() {
    var changes = {};
    texts.forEach(function (node) {
      var value = readText(node);
      if (value !== node._saved) {
        changes[node.getAttribute("data-text-key")] = value === node.getAttribute("data-default") ? "" : value;
      }
    });
    return changes;
  }

  function updateChip() {
    if (!chipEl) return 0;
    var count = Object.keys(collectChanges()).length;
    chipEl.textContent = count === 0 ? "Sin cambios" : count + (count === 1 ? " cambio sin guardar" : " cambios sin guardar");
    chipEl.classList.toggle("is-dirty", count > 0);
    return count;
  }

  function saveTexts() {
    var changes = collectChanges();
    if (!Object.keys(changes).length) return Promise.resolve(false);
    return post("/mis-fotos/api/texts/", { changes: changes }).then(function () {
      texts.forEach(function (node) { node._saved = readText(node); });
      updateChip();
      return true;
    });
  }

  texts.forEach(function (node) {
    node._saved = readText(node);
    node.setAttribute("contenteditable", plainOnly ? "plaintext-only" : "true");
    node.setAttribute("spellcheck", "true");
    node.setAttribute("title", "Haz clic para editar este texto");
    // A link would navigate instead of letting you place the cursor.
    var link = node.closest("a[href]");
    if (link) link.removeAttribute("href");

    node.addEventListener("input", function () {
      syncCopies(node);
      updateChip();
    });
    node.addEventListener("keydown", function (event) {
      if (event.key === "Enter" && !node.hasAttribute("data-multiline")) {
        event.preventDefault();
        node.blur();
      } else if (event.key === "Escape") {
        node.blur();
      }
    });
    node.addEventListener("paste", function (event) {
      event.preventDefault();
      var pasted = (event.clipboardData || window.clipboardData).getData("text/plain");
      if (!node.hasAttribute("data-multiline")) pasted = pasted.replace(/\s*\n\s*/g, " ");
      document.execCommand("insertText", false, pasted);
    });
    // Never let a dragged photo/video (or file) be dropped into the text.
    node.addEventListener("dragover", function (event) { if (drag) event.preventDefault(); });
    node.addEventListener("drop", function (event) {
      if (drag || (event.dataTransfer && event.dataTransfer.files.length)) {
        event.preventDefault();
        event.stopPropagation();
      }
    });
    node.addEventListener("blur", function () {
      if (!readText(node)) {
        writeText(node, node.getAttribute("data-default"));
        syncCopies(node);
        updateChip();
      }
    });
  });

  if (saveBtn) {
    saveBtn.addEventListener("click", function () {
      setStatus("Guardando textos…");
      saveTexts().then(function (saved) {
        setStatus(saved ? "Textos guardados." : "No hay textos por guardar.");
      }).catch(function (error) { setStatus(error.message, true); });
    });
  }

  if (discardBtn) {
    discardBtn.addEventListener("click", function () {
      var count = updateChip();
      if (!count) { setStatus("No hay cambios por descartar."); return; }
      if (!window.confirm("¿Descartar los cambios de texto sin guardar?")) return;
      texts.forEach(function (node) {
        writeText(node, node._saved);
        syncCopies(node);
      });
      updateChip();
      setStatus("Cambios descartados.");
    });
  }

  window.addEventListener("beforeunload", function (event) {
    if (Object.keys(collectChanges()).length) {
      event.preventDefault();
      event.returnValue = "";
    }
  });

  // Anything that reloads the page saves the pending texts first.
  function run(label, task, reload) {
    setStatus(label + "…");
    return (reload ? saveTexts() : Promise.resolve()).then(task).then(function () {
      if (reload) {
        setStatus("Guardado. Actualizando…");
        window.location.reload();
      } else {
        setStatus("Guardado.");
      }
    }).catch(function (error) {
      setStatus(error.message, true);
    });
  }

  // ---------- Fixed (not editable inline) parts ----------

  [
    [".site-header", "Menú: no editable", true],
    [".contact-list", "Se edita en «Personalizar sitio»", true],
    [".contact-form-wrap", "Formulario: no editable", true],
    [".gallery-footnote", "Se edita en «Personalizar sitio»", false],
    [".contact-info .social-buttons", "Se edita en «Personalizar sitio»", false],
    [".service-icon", "", false],
    [".value-icon", "", false],
    [".process-number", "", false],
    [".values-tab-num", "", false],
    [".build-option-cta", "", false],
    [".service-link", "", false]
  ].forEach(function (entry) {
    document.querySelectorAll(entry[0]).forEach(function (node) {
      node.classList.add("ed-fixed");
      node.setAttribute("title", entry[1] || "Esta parte no se edita directamente");
      if (entry[2]) {
        node.classList.add("ed-fixed-block");
        node.setAttribute("data-ed-note", entry[1]);
      }
    });
  });
  document.querySelectorAll("[data-text-sync]").forEach(function (node) {
    node.setAttribute("title", "Este texto se edita en su sección");
  });

  var highlightToggle = document.getElementById("editHighlight");
  if (highlightToggle) {
    highlightToggle.addEventListener("change", function (event) {
      root.classList.toggle("ed-hl-off", !event.target.checked);
    });
  }

  // ---------- Photo / Video drag & drop ----------

  function startDrag(event, payload, source) {
    drag = payload;
    root.classList.add("ed-dragging");
    source.classList.add("ed-source");
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData(DRAG_TYPE, String(payload.id));
    event.dataTransfer.setDragImage(source, 20, 20);
  }

  function endDrag() {
    drag = null;
    root.classList.remove("ed-dragging");
    document.querySelectorAll(".ed-source, .ed-over").forEach(function (node) {
      node.classList.remove("ed-source", "ed-over");
    });
  }

  function makeGrip(payloadFn, source) {
    var grip = el("span", "ed-pill ed-grip", "⠿ Mover");
    grip.setAttribute("draggable", "true");
    grip.setAttribute("title", "Arrastra para mover este archivo");
    grip.addEventListener("dragstart", function (event) { startDrag(event, payloadFn(), source); });
    grip.addEventListener("dragend", endDrag);
    grip.addEventListener("click", function (event) { event.stopPropagation(); });
    return grip;
  }

  function dropTarget(node, onDrop) {
    node.addEventListener("dragover", function (event) {
      if (!drag) return;
      event.preventDefault();
      node.classList.add("ed-over");
    });
    node.addEventListener("dragleave", function () { node.classList.remove("ed-over"); });
    node.addEventListener("drop", function (event) {
      if (!drag) return;
      event.preventDefault();
      event.stopPropagation();
      var payload = drag;
      endDrag();
      onDrop(payload);
    });
  }

  // ---------- Fixed media slots (panel, banners) ----------

  var slotFile = el("input");
  slotFile.type = "file";
  slotFile.accept = MEDIA_ACCEPT;
  slotFile.hidden = true;
  document.body.appendChild(slotFile);
  var pendingSlot = null;

  slotFile.addEventListener("change", function () {
    var file = slotFile.files[0];
    if (!file || !pendingSlot) return;
    var slot = pendingSlot;
    var data = new FormData();
    data.append("image", file);
    run("Subiendo archivo", function () { return post("/mis-fotos/api/slot/" + slot + "/upload/", data); }, true);
    slotFile.value = "";
  });

  document.querySelectorAll("[data-slot]").forEach(function (slotEl) {
    var slot = slotEl.getAttribute("data-slot");
    // Si es la portada con carrusel, su gestión se hace desde el panel lateral
    if (slot === "hero_bg" && document.getElementById("heroCarousel")) return;

    var photoId = parseInt(slotEl.getAttribute("data-photo-id"), 10);
    var controls = el("div", "ed-ctl");
    if (photoId) controls.appendChild(makeGrip(function () { return { type: "slot", id: photoId, slot: slot }; }, slotEl));
    var change = el("span", "ed-pill", photoId ? "📷 Cambiar foto/video" : "📷 Subir foto/video");
    change.setAttribute("role", "button");
    change.addEventListener("click", stop(function () {
      pendingSlot = slot;
      slotFile.click();
    }));
    controls.appendChild(change);
    slotEl.appendChild(controls);

    dropTarget(slotEl, function (payload) {
      if (payload.type === "slot" && payload.slot === slot) return;
      run("Moviendo archivo", function () {
        return post("/mis-fotos/api/move/", { photo: payload.id, to_slot: slot });
      }, true);
    });
  });

  // ---------- Gallery ----------

  var grid = document.querySelector(".gallery-grid");

  if (grid) {
    // Clicking a tile must not open the lightbox while editing.
    grid.addEventListener("click", function (event) {
      if (event.target.closest(".gallery-item") && !event.target.closest(".ed-ctl")) {
        event.stopPropagation();
      }
    }, true);

    function galleryIds() {
      return Array.prototype.map.call(grid.querySelectorAll(".gallery-item"), function (tile) {
        return parseInt(tile.getAttribute("data-id"), 10);
      });
    }

    grid.querySelectorAll(".gallery-item").forEach(function (tile) {
      var id = parseInt(tile.getAttribute("data-id"), 10);
      var controls = el("div", "ed-ctl");
      controls.appendChild(makeGrip(function () { return { type: "tile", id: id }; }, tile));
      var del = el("span", "ed-pill ed-del", "×");
      del.setAttribute("role", "button");
      del.setAttribute("title", "Eliminar archivo");
      del.setAttribute("aria-label", "Eliminar archivo");
      del.addEventListener("click", stop(function () {
        if (!window.confirm("¿Eliminar este archivo? No se puede deshacer.")) return;
        var video = tile.querySelector("video");
        if (video) {
          video.pause();
          video.removeAttribute("src");
          video.load();
        }
        run("Eliminando archivo", function () {
          return post("/mis-fotos/api/photo/" + id + "/delete/");
        }, false).then(function () {
          if (!statusEl || !statusEl.classList.contains("is-error")) tile.remove();
        });
      }));
      controls.appendChild(del);
      tile.appendChild(controls);

      dropTarget(tile, function (payload) {
        if (payload.id === id) return;
        if (payload.type === "slot") {
          run("Moviendo archivo", function () {
            return post("/mis-fotos/api/move/", { photo: payload.id, with: id });
          }, true);
          return;
        }
        var dragged = grid.querySelector('.gallery-item[data-id="' + payload.id + '"]');
        if (!dragged) return;
        var tiles = Array.prototype.slice.call(grid.querySelectorAll(".gallery-item"));
        if (tiles.indexOf(dragged) < tiles.indexOf(tile)) {
          tile.after(dragged);
        } else {
          tile.before(dragged);
        }
        run("Guardando orden", function () {
          return post("/mis-fotos/api/gallery/reorder/", { ids: galleryIds() });
        }, false);
      });
    });

    // ---------- Add photo / video (modal rápido en galería) ----------

    var dialog = el("dialog", "ed-dialog");
    var form = el("form", "ed-form");
    form.appendChild(el("h3", "", "Agregar foto o video a Proyectos"));

    function field(labelText, control) {
      var label = el("label", "ed-field");
      label.appendChild(el("span", "", labelText));
      label.appendChild(control);
      return label;
    }

    var fileInput = el("input");
    fileInput.type = "file";
    fileInput.accept = MEDIA_ACCEPT;
    fileInput.required = true;
    var categorySelect = el("select");
    document.querySelectorAll(".gallery-filter").forEach(function (btn) {
      if (btn.getAttribute("data-filter") === "all") return;
      var option = el("option", "", btn.textContent.trim());
      option.value = btn.getAttribute("data-filter");
      categorySelect.appendChild(option);
    });
    var titleInput = el("input");
    titleInput.type = "text";
    titleInput.maxLength = 120;
    titleInput.placeholder = "Ej: Fachada casa Vitacura";

    form.appendChild(field("Foto o video (MP4 / WebM / MOV)", fileInput));
    form.appendChild(field("Categoría", categorySelect));
    form.appendChild(field("Título (opcional)", titleInput));
    var actions = el("div", "ed-form-actions");
    var cancel = el("button", "edit-btn ed-cancel", "Cancelar");
    cancel.type = "button";
    var submit = el("button", "edit-btn edit-btn-pri", "Subir archivo");
    submit.type = "submit";
    actions.appendChild(cancel);
    actions.appendChild(submit);
    form.appendChild(actions);
    dialog.appendChild(form);
    document.body.appendChild(dialog);

    cancel.addEventListener("click", function () { dialog.close(); });
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var data = new FormData();
      data.append("image", fileInput.files[0]);
      data.append("category", categorySelect.value);
      data.append("title", titleInput.value);
      dialog.close();
      run("Subiendo archivo", function () { return post("/mis-fotos/api/gallery/upload/", data); }, true);
    });

    var addTile = el("button", "gallery-add");
    addTile.type = "button";
    addTile.appendChild(el("span", "gallery-add-icon", "+"));
    addTile.appendChild(el("span", "gallery-add-title", "Agregar foto o video"));
    addTile.addEventListener("click", function () {
      var active = document.querySelector(".gallery-filter.is-active");
      var current = active ? active.getAttribute("data-filter") : "all";
      form.reset();
      if (current !== "all") categorySelect.value = current;
      dialog.showModal();
    });
    grid.insertBefore(addTile, document.getElementById("galleryMore"));
  }

  // ---------- Panel Lateral de Personalización Total ----------

  var drawer = document.getElementById("customizerDrawer");
  if (!drawer) return;

  var urlCarouselAdd = drawer.getAttribute("data-url-carousel-add") || "/mis-fotos/api/carousel/add/";
  var urlCarouselReorder = drawer.getAttribute("data-url-carousel-reorder") || "/mis-fotos/api/carousel/reorder/";
  var urlSettingsSave = drawer.getAttribute("data-url-settings-save") || "/mis-fotos/api/settings/save/";

  function openDrawer() {
    drawer.classList.add("is-open");
    drawer.setAttribute("aria-hidden", "false");
  }

  function closeDrawer() {
    drawer.classList.remove("is-open");
    drawer.setAttribute("aria-hidden", "true");
  }

  var openBtn = document.getElementById("openCustomizerBtn");
  var closeBtn = document.getElementById("closeCustomizerBtn");
  if (openBtn) openBtn.addEventListener("click", openDrawer);
  if (closeBtn) closeBtn.addEventListener("click", closeDrawer);

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && drawer.classList.contains("is-open")) {
      closeDrawer();
    }
  });

  // Pestañas del panel
  Array.prototype.forEach.call(drawer.querySelectorAll(".cz-tab"), function (tab) {
    tab.addEventListener("click", function () {
      var target = tab.getAttribute("data-cz-tab");
      Array.prototype.forEach.call(drawer.querySelectorAll(".cz-tab"), function (t) {
        t.classList.toggle("is-active", t === tab);
      });
      Array.prototype.forEach.call(drawer.querySelectorAll(".cz-pane"), function (p) {
        p.classList.toggle("is-active", p.getAttribute("data-cz-pane") === target);
      });
    });
  });

  // 1. Subir imágenes o videos ilimitados al carrusel
  var uploadSlidesBtn = document.getElementById("uploadSlidesBtn");
  if (uploadSlidesBtn) {
    uploadSlidesBtn.addEventListener("click", function () {
      var filesInput = document.getElementById("czSlideFiles");
      if (!filesInput || !filesInput.files.length) {
        setStatus("Selecciona al menos una imagen o video para el carrusel.", true);
        return;
      }
      var fd = new FormData();
      Array.prototype.forEach.call(filesInput.files, function (file) {
        fd.append("media", file);
      });
      var titleInput = document.getElementById("czSlideTitle");
      fd.append("title", titleInput ? titleInput.value : "");
      run("Subiendo diapositivas al carrusel", function () {
        return post(urlCarouselAdd, fd);
      }, true);
    });
  }

  // Reordenar / mostrar-ocultar / eliminar diapositivas del carrusel
  var slideList = document.getElementById("czSlideList");
  if (slideList) {
    slideList.addEventListener("click", function (event) {
      var moveBtn = event.target.closest("[data-move]");
      if (moveBtn) {
        var li = moveBtn.closest(".cz-item");
        var dir = parseInt(moveBtn.getAttribute("data-move"), 10);
        if (dir < 0 && li.previousElementSibling) slideList.insertBefore(li, li.previousElementSibling);
        if (dir > 0 && li.nextElementSibling) slideList.insertBefore(li.nextElementSibling, li);
        var ids = Array.prototype.map.call(slideList.querySelectorAll(".cz-item"), function (item) {
          return parseInt(item.getAttribute("data-id"), 10);
        });
        run("Guardando orden del carrusel", function () {
          return post(urlCarouselReorder, { ids: ids });
        }, false);
        return;
      }

      var toggleBtn = event.target.closest("[data-toggle-url]");
      if (toggleBtn) {
        var toggleUrl = toggleBtn.getAttribute("data-toggle-url");
        run("Cambiando visibilidad de diapositiva", function () {
          return post(toggleUrl);
        }, true);
        return;
      }

      var delBtn = event.target.closest("[data-delete-url]");
      if (delBtn && window.confirm("¿Eliminar esta diapositiva del carrusel?")) {
        var deleteUrl = delBtn.getAttribute("data-delete-url");
        var vid = delBtn.closest(".cz-item").querySelector("video");
        if (vid) {
          vid.pause();
          vid.removeAttribute("src");
          vid.load();
        }
        run("Eliminando diapositiva", function () {
          return post(deleteUrl);
        }, true);
      }
    });
  }

  // Guardar transición y velocidad del carrusel (vista previa inmediata)
  var saveCarouselConfigBtn = document.getElementById("saveCarouselConfigBtn");
  if (saveCarouselConfigBtn) {
    saveCarouselConfigBtn.addEventListener("click", function () {
      var transition = document.getElementById("czTransition").value;
      var interval = Math.max(3, parseInt(document.getElementById("czInterval").value, 10) || 6);
      var hero = document.getElementById("inicio");
      if (hero) {
        hero.setAttribute("data-transition", transition);
        hero.setAttribute("data-interval", String(interval));
      }
      run("Guardando transición del carrusel", function () {
        return post(urlSettingsSave, {
          carousel_transition: transition,
          carousel_interval: interval
        });
      }, false);
    });
  }

  // 2. Subir y eliminar proyectos desde el panel lateral (usa las APIs existentes)
  var uploadGalleryBtn = document.getElementById("uploadGalleryBtn");
  if (uploadGalleryBtn) {
    uploadGalleryBtn.addEventListener("click", function () {
      var filesInput = document.getElementById("czGalleryFiles");
      if (!filesInput || !filesInput.files.length) {
        setStatus("Elige al menos una foto o video del proyecto.", true);
        return;
      }
      var category = document.getElementById("czGalleryCat").value;
      var title = document.getElementById("czGalleryTitle").value;
      var uploads = Array.prototype.map.call(filesInput.files, function (file) {
        var fd = new FormData();
        fd.append("image", file);
        fd.append("category", category);
        fd.append("title", title);
        return post("/mis-fotos/api/gallery/upload/", fd);
      });
      run("Publicando proyectos", function () {
        return Promise.all(uploads);
      }, true);
    });
  }

  var galleryList = document.getElementById("czGalleryList");
  if (galleryList) {
    galleryList.addEventListener("click", function (event) {
      var delBtn = event.target.closest("[data-del-gallery]");
      if (!delBtn) return;
      if (!window.confirm("¿Eliminar este proyecto del portafolio?")) return;
      var li = delBtn.closest(".cz-item");
      var id = li ? li.getAttribute("data-id") : null;
      var delUrl = id ? "/mis-fotos/api/photo/" + id + "/delete/" : delBtn.getAttribute("data-del-gallery");
      run("Eliminando proyecto", function () {
        return post(delUrl);
      }, true);
    });
  }

  // 3. Guardar datos de contacto y redes sociales
  var saveContactSettingsBtn = document.getElementById("saveContactSettingsBtn");
  if (saveContactSettingsBtn) {
    saveContactSettingsBtn.addEventListener("click", function () {
      run("Guardando contacto y redes", function () {
        return post(urlSettingsSave, {
          phone_display: document.getElementById("czPhoneDisplay").value,
          phone_raw: document.getElementById("czPhoneRaw").value,
          whatsapp_number: document.getElementById("czWhatsapp").value,
          email_primary: document.getElementById("czEmail1").value,
          email_sales: document.getElementById("czEmail2").value,
          instagram_handle: document.getElementById("czIgHandle").value,
          instagram_url: document.getElementById("czIgUrl").value,
          tiktok_handle: document.getElementById("czTtHandle").value,
          tiktok_url: document.getElementById("czTtUrl").value
        });
      }, true);
    });
  }

})();