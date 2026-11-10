(function () {
  if (!document.documentElement.hasAttribute("data-edit")) return;

  var csrf = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
  var statusEl = document.getElementById("editStatus");
  var drag = null; // { type: "slot" | "tile", id, slot }
  var root = document.documentElement;

  function setStatus(message, isError) {
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

  function run(label, promise, reload) {
    setStatus(label + "…");
    return promise.then(function () {
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

  function startDrag(event, payload, source) {
    drag = payload;
    root.classList.add("ed-dragging");
    source.classList.add("ed-source");
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", String(payload.id));
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
    grip.setAttribute("title", "Arrastra para mover esta foto");
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

  // ---------- Fixed photo slots (portada, panel "¿Qué quieres construir?") ----------

  var slotFile = el("input");
  slotFile.type = "file";
  slotFile.accept = "image/*";
  slotFile.hidden = true;
  document.body.appendChild(slotFile);
  var pendingSlot = null;

  slotFile.addEventListener("change", function () {
    var file = slotFile.files[0];
    if (!file || !pendingSlot) return;
    var data = new FormData();
    data.append("image", file);
    run("Subiendo foto", post("/mis-fotos/api/slot/" + pendingSlot + "/upload/", data), true);
    slotFile.value = "";
  });

  document.querySelectorAll("[data-slot]").forEach(function (slotEl) {
    var slot = slotEl.getAttribute("data-slot");
    var photoId = parseInt(slotEl.getAttribute("data-photo-id"), 10);
    var controls = el("div", "ed-ctl");
    if (photoId) controls.appendChild(makeGrip(function () { return { type: "slot", id: photoId, slot: slot }; }, slotEl));
    var change = el("span", "ed-pill", photoId ? "Cambiar foto" : "Subir foto");
    change.setAttribute("role", "button");
    change.addEventListener("click", stop(function () {
      pendingSlot = slot;
      slotFile.click();
    }));
    controls.appendChild(change);
    slotEl.appendChild(controls);

    dropTarget(slotEl, function (payload) {
      if (payload.type === "slot" && payload.slot === slot) return;
      run("Moviendo foto", post("/mis-fotos/api/move/", { photo: payload.id, to_slot: slot }), true);
    });
  });

  // ---------- Gallery ----------

  var grid = document.querySelector(".gallery-grid");

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
    del.setAttribute("title", "Eliminar foto");
    del.setAttribute("aria-label", "Eliminar foto");
    del.addEventListener("click", stop(function () {
      if (!window.confirm("¿Eliminar esta foto? No se puede deshacer.")) return;
      run("Eliminando foto", post("/mis-fotos/api/photo/" + id + "/delete/"), false).then(function () {
        if (!statusEl.classList.contains("is-error")) tile.remove();
      });
    }));
    controls.appendChild(del);
    tile.appendChild(controls);

    dropTarget(tile, function (payload) {
      if (payload.id === id) return;
      if (payload.type === "slot") {
        run("Moviendo foto", post("/mis-fotos/api/move/", { photo: payload.id, with: id }), true);
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
      run("Guardando orden", post("/mis-fotos/api/gallery/reorder/", { ids: galleryIds() }), false);
    });
  });

  // ---------- Add photo ----------

  var dialog = el("dialog", "ed-dialog");
  var form = el("form", "ed-form");
  form.appendChild(el("h3", "", "Agregar foto a Proyectos"));

  function field(labelText, control) {
    var label = el("label", "ed-field");
    label.appendChild(el("span", "", labelText));
    label.appendChild(control);
    return label;
  }

  var fileInput = el("input");
  fileInput.type = "file";
  fileInput.accept = "image/*";
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

  form.appendChild(field("Foto", fileInput));
  form.appendChild(field("Categoría", categorySelect));
  form.appendChild(field("Título (opcional)", titleInput));
  var actions = el("div", "ed-form-actions");
  var cancel = el("button", "edit-btn ed-cancel", "Cancelar");
  cancel.type = "button";
  var submit = el("button", "edit-btn edit-btn-pri", "Subir foto");
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
    run("Subiendo foto", post("/mis-fotos/api/gallery/upload/", data), true);
  });

  var addTile = el("button", "gallery-add");
  addTile.type = "button";
  addTile.appendChild(el("span", "gallery-add-icon", "+"));
  addTile.appendChild(el("span", "gallery-add-title", "Agregar foto"));
  addTile.addEventListener("click", function () {
    var active = document.querySelector(".gallery-filter.is-active");
    var current = active ? active.getAttribute("data-filter") : "all";
    if (current !== "all") categorySelect.value = current;
    form.reset();
    if (current !== "all") categorySelect.value = current;
    dialog.showModal();
  });
  var more = document.getElementById("galleryMore");
  grid.insertBefore(addTile, more);
})();
