(function () {
  "use strict";

  function csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : "";
  }

  function showToast(msg) {
    let el = document.getElementById("studioToast");
    if (!el) {
      el = document.createElement("div");
      el.id = "studioToast";
      el.className = "studio-toast";
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.classList.add("is-visible");
    clearTimeout(el._timer);
    el._timer = setTimeout(() => el.classList.remove("is-visible"), 3200);
  }

  /* =========================================================
     1. CARRUSEL ÚNICO A 60FPS SIN DOBLE EXPOSICIÓN NI SALTOS
     ========================================================= */
  let carouselAutoTimer = null;
  let carouselCleanupTimer = null;

  function initStudioHeroCarousel() {
    const hero = document.getElementById("inicio");
    const track = document.getElementById("studioHeroCarousel");
    if (!hero || !track) return;

    clearInterval(carouselAutoTimer);
    clearTimeout(carouselCleanupTimer);

    const slides = Array.from(track.querySelectorAll(".studio-hero-slide"));
    if (!slides.length) return;

    slides.forEach((slide) => {
      const img = slide.querySelector("img");
      if (img && typeof img.decode === "function") {
        img.decode().catch(() => {});
      }
    });

    let current = slides.findIndex((s) => s.classList.contains("is-active"));
    if (current < 0) current = 0;

    function resetAllStates(activeIdx) {
      slides.forEach((slide, idx) => {
        slide.classList.remove("is-prev", "is-entering", "is-dir-next", "is-dir-prev");
        slide.classList.toggle("is-active", idx === activeIdx);
        const vid = slide.querySelector("video");
        if (vid) {
          if (idx === activeIdx) {
            vid.play().catch(() => {});
          } else {
            vid.pause();
          }
        }
      });
    }

    resetAllStates(current);
    if (slides.length <= 1) return;

    const currentEl = document.getElementById("studioHeroSlideCurrent");
    const captionEl = document.getElementById("studioHeroSlideCaption");
    const prevBtn = document.getElementById("studioHeroPrev");
    const nextBtn = document.getElementById("studioHeroNext");
    const dots = Array.from(document.querySelectorAll("#studioHeroDots [data-go-slide]"));

    function finishTransition(outgoing, incoming) {
      clearTimeout(carouselCleanupTimer);
      if (outgoing) {
        outgoing.classList.remove("is-prev");
        const outVid = outgoing.querySelector("video");
        if (outVid) outVid.pause();
      }
      if (incoming) {
        incoming.classList.remove("is-entering", "is-dir-next", "is-dir-prev");
      }
    }

    function goTo(targetIndex, dirHint) {
      const next = (targetIndex + slides.length) % slides.length;
      if (next === current) return;

      clearTimeout(carouselCleanupTimer);

      const outgoing = slides[current];
      const incoming = slides[next];
      const direction = dirHint || (next > current ? "next" : "prev");

      slides.forEach((s, idx) => {
        if (idx !== current && idx !== next) {
          s.classList.remove("is-active", "is-prev", "is-entering", "is-dir-next", "is-dir-prev");
          const v = s.querySelector("video");
          if (v) v.pause();
        }
      });

      outgoing.classList.remove("is-active", "is-entering", "is-dir-next", "is-dir-prev");
      outgoing.classList.add("is-prev");

      incoming.classList.remove("is-prev", "is-entering", "is-dir-next", "is-dir-prev");
      void incoming.offsetWidth;
      incoming.classList.add(
        "is-active",
        "is-entering",
        direction === "prev" ? "is-dir-prev" : "is-dir-next"
      );

      const inVid = incoming.querySelector("video");
      if (inVid) {
        inVid.currentTime = 0;
        inVid.play().catch(() => {});
      }

      current = next;

      if (currentEl) {
        currentEl.textContent = String(current + 1).padStart(2, "0");
      }
      if (captionEl) {
        captionEl.textContent = incoming.dataset.slideCaption || "";
      }
      dots.forEach((d, idx) => d.classList.toggle("is-active", idx === current));

      const onAnimDone = () => {
        incoming.removeEventListener("animationend", onAnimDone);
        finishTransition(outgoing, incoming);
      };
      incoming.addEventListener("animationend", onAnimDone, { once: true });
      carouselCleanupTimer = setTimeout(() => {
        incoming.removeEventListener("animationend", onAnimDone);
        finishTransition(outgoing, incoming);
      }, 680);
    }

    function getIntervalMs() {
      const sec = parseInt(hero.dataset.interval || "6", 10);
      return Math.max(3, isNaN(sec) ? 6 : sec) * 1000;
    }

    function startAutoplay() {
      clearInterval(carouselAutoTimer);
      carouselAutoTimer = setInterval(() => {
        goTo(current + 1, "next");
      }, getIntervalMs());
    }

    if (!track.dataset.bound) {
      track.dataset.bound = "1";

      if (prevBtn) {
        prevBtn.addEventListener("click", (e) => {
          e.preventDefault();
          e.stopPropagation();
          goTo(current - 1, "prev");
          startAutoplay();
        });
      }
      if (nextBtn) {
        nextBtn.addEventListener("click", (e) => {
          e.preventDefault();
          e.stopPropagation();
          goTo(current + 1, "next");
          startAutoplay();
        });
      }
      dots.forEach((dot) => {
        dot.addEventListener("click", (e) => {
          e.preventDefault();
          e.stopPropagation();
          const idx = parseInt(dot.dataset.goSlide || "0", 10);
          goTo(idx, idx >= current ? "next" : "prev");
          startAutoplay();
        });
      });

      hero.addEventListener("mouseenter", () => {
        if (hero.dataset.pauseHover === "1") {
          clearInterval(carouselAutoTimer);
        }
      });
      hero.addEventListener("mouseleave", () => {
        if (hero.dataset.pauseHover === "1") {
          startAutoplay();
        }
      });
    }

    startAutoplay();
  }

  /* =========================================================
     2. COLA DE ARCHIVOS CON VISTA PREVIA INSTANTÁNEA
     ========================================================= */
  function formatBytes(bytes) {
    if (!bytes) return "0 B";
    const units = ["B", "KB", "MB", "GB"];
    const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
  }

  function createFileQueueManager({ inputId, dropzoneId, queueId, submitBtnId }) {
    const input = document.getElementById(inputId);
    const dropzone = document.getElementById(dropzoneId);
    const queueEl = document.getElementById(queueId);
    const submitBtn = document.getElementById(submitBtnId);
    if (!input || !dropzone || !queueEl || !submitBtn) return null;

    let filesList = [];
    let objectUrls = [];

    function revokeAll() {
      objectUrls.forEach((u) => URL.revokeObjectURL(u));
      objectUrls = [];
    }

    function render() {
      revokeAll();
      if (!filesList.length) {
        queueEl.hidden = true;
        queueEl.innerHTML = "";
        submitBtn.disabled = true;
        return;
      }

      submitBtn.disabled = false;
      const totalBytes = filesList.reduce((acc, f) => acc + f.size, 0);
      queueEl.hidden = false;

      const cardsHtml = filesList
        .map((file, idx) => {
          const url = URL.createObjectURL(file);
          objectUrls.push(url);
          const isVideo = file.type.startsWith("video/");
          const mediaHtml = isVideo
            ? `<video class="cz-q-thumb" src="${url}" muted playsinline preload="metadata"></video>`
            : `<img class="cz-q-thumb" src="${url}" alt="">`;
          return `
            <div class="cz-q-item">
              ${mediaHtml}
              <button type="button" class="cz-q-remove" data-q-remove="${idx}" title="Quitar archivo">&times;</button>
              <div class="cz-q-meta" title="${file.name}">
                ${file.name}
                <small>${isVideo ? "VIDEO" : "FOTO"} &middot; ${formatBytes(file.size)}</small>
              </div>
            </div>
          `;
        })
        .join("");

      queueEl.innerHTML = `
        <div class="cz-queue-head">
          <span>${filesList.length} archivo${filesList.length > 1 ? "s" : ""} listo${filesList.length > 1 ? "s" : ""} (${formatBytes(totalBytes)})</span>
          <button type="button" class="cz-queue-clear" data-q-clear>Limpiar</button>
        </div>
        <div class="cz-queue-grid">${cardsHtml}</div>
      `;
    }

    function addFiles(newFiles) {
      const incoming = Array.from(newFiles || []);
      if (!incoming.length) return;
      filesList = filesList.concat(incoming);
      input.value = "";
      render();
    }

    input.addEventListener("change", (e) => {
      addFiles(e.target.files);
    });

    ["dragenter", "dragover"].forEach((evt) => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.add("is-dragover");
      });
    });
    ["dragleave", "drop"].forEach((evt) => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.remove("is-dragover");
      });
    });
    dropzone.addEventListener("drop", (e) => {
      if (e.dataTransfer && e.dataTransfer.files) {
        addFiles(e.dataTransfer.files);
      }
    });

    queueEl.addEventListener("click", (e) => {
      const remBtn = e.target.closest("[data-q-remove]");
      if (remBtn) {
        const idx = parseInt(remBtn.dataset.qRemove, 10);
        filesList.splice(idx, 1);
        render();
        return;
      }
      if (e.target.closest("[data-q-clear]")) {
        filesList = [];
        render();
      }
    });

    return {
      getFiles: () => filesList.slice(),
      clear: () => {
        filesList = [];
        render();
      },
    };
  }

  /* =========================================================
     3. ESTUDIO AVANZADO + VISOR REAL TABLET / MÓVIL
     ========================================================= */
  function initStudioDrawer() {
    const drawer = document.getElementById("customizerDrawer");
    const main = document.getElementById("siteMain");
    if (!drawer || !main) return;
    
    function syncDrawerLayout() {
      const isOpen = drawer.classList.contains("is-open");
      document.body.classList.toggle("is-drawer-open", isOpen);
      if (isOpen) {
        document.body.style.setProperty("--cz-drawer-w", `${drawer.offsetWidth || 390}px`);
      }
    }

    new MutationObserver(syncDrawerLayout).observe(drawer, {
      attributes: true,
      attributeFilter: ["class"],
    });
    syncDrawerLayout();

    const params = new URLSearchParams(window.location.search);
    const openTab = params.get("cz_tab");
    if (openTab) {
      drawer.classList.add("is-open");
      drawer.setAttribute("aria-hidden", "false");
      drawer.querySelectorAll("[data-cz-tab]").forEach((t) => {
        t.classList.toggle("is-active", t.dataset.czTab === openTab);
      });
      drawer.querySelectorAll("[data-cz-pane]").forEach((p) => {
        p.classList.toggle("is-active", p.dataset.czPane === openTab);
      });
      window.history.replaceState({}, "", window.location.pathname);
    }

    const stage = document.getElementById("devicePreviewStage");
    const bezel = document.getElementById("deviceBezel");
    const frame = document.getElementById("devicePreviewFrame");
    const specLabel = document.getElementById("deviceSpecLabel");
    const refreshBtn = document.getElementById("deviceRefreshBtn");

    function syncDeviceFrame() {
      if (!frame || !stage || stage.hidden) return;
      let doc;
      try {
        doc = frame.contentDocument;
      } catch (e) {
        return;
      }
      if (!doc) return;

      const frameMain = doc.getElementById("siteMain");
      if (frameMain && main) {
        frameMain.dataset.theme = main.dataset.theme || "navy";
        frameMain.dataset.font = main.dataset.font || "editorial";
        frameMain.dataset.radius = main.dataset.radius || "pill";
        frameMain.dataset.heroHeight = main.dataset.heroHeight || "full";
        frameMain.dataset.spacing = main.dataset.spacing || "normal";
        frameMain.style.cssText = main.style.cssText;
      }

      const sorterEl = document.getElementById("czSectionSorter");
      const frameHost = doc.getElementById("dynamicSectionsHost");
      if (sorterEl && frameHost) {
        let num = 1;
        sorterEl.querySelectorAll(".cz-sec-row").forEach((row) => {
          const key = row.dataset.secKey;
          const cb = row.querySelector("[data-sec-toggle]");
          const visible = cb ? cb.checked : true;
          const secEl = frameHost.querySelector(`[data-dyn-section="${key}"]`);
          if (secEl) {
            frameHost.appendChild(secEl);
            secEl.hidden = !visible;
          }
          const span = key === "tech" ? 2 : 1;
          if (visible) {
            if (secEl) {
              if (key === "tech") {
                secEl.querySelectorAll("[data-sec-num]").forEach((el, idx) => {
                  el.textContent = String(num + idx).padStart(2, "0");
                });
              } else {
                const numEl = secEl.querySelector("[data-sec-num]");
                if (numEl) numEl.textContent = String(num).padStart(2, "0");
              }
            }
            num += span;
          }
        });
        const frameContactNum = doc.getElementById("contactSecNum");
        if (frameContactNum) frameContactNum.textContent = String(num).padStart(2, "0");
      }

      const ctaInputEl = document.getElementById("czCtaLabel");
      const frameCta = doc.getElementById("headerCtaBtn");
      if (ctaInputEl && frameCta) {
        frameCta.textContent = ctaInputEl.value.trim() || "Cotizar";
      }

      const marqueeCheckEl = document.getElementById("czShowMarquee");
      const frameMarquee = doc.getElementById("siteMarquee");
      if (marqueeCheckEl && frameMarquee) {
        frameMarquee.hidden = !marqueeCheckEl.checked;
      }

      const waCheckEl = document.getElementById("czShowFloatingWa");
      const frameWa = doc.getElementById("floatingWaBtn");
      if (waCheckEl && frameWa) {
        frameWa.hidden = !waCheckEl.checked;
      }
    }

    function reloadDeviceFrame() {
      if (!frame || !stage || stage.hidden) return;
      frame.src = `/?_preview=${Date.now()}`;
    }

    if (frame) {
      frame.addEventListener("load", syncDeviceFrame);
    }

    document.querySelectorAll(".vp-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".vp-btn").forEach((b) => b.classList.remove("is-active"));
        btn.classList.add("is-active");

        const mode = btn.dataset.vp;
        if (mode === "desktop") {
          document.body.classList.remove("is-device-preview");
          if (stage) stage.hidden = true;
          if (frame) frame.removeAttribute("src");
          initStudioHeroCarousel();
          return;
        }

        clearInterval(carouselAutoTimer);
        clearTimeout(carouselCleanupTimer);
        document.querySelectorAll("#inicio video").forEach((v) => v.pause());
        document.body.classList.add("is-device-preview");
        if (stage) stage.hidden = false;
        if (bezel) bezel.classList.toggle("is-tablet", mode === "tablet");
        if (specLabel) {
          specLabel.textContent =
            mode === "tablet"
              ? "iPad / Tablet · 768 × 860 px"
              : "iPhone / Móvil · 390 × 780 px";
        }
        if (frame && !frame.getAttribute("src")) {
          frame.src = `/?_preview=${Date.now()}`;
        } else {
          syncDeviceFrame();
        }
      });
    });

    if (refreshBtn) {
      refreshBtn.addEventListener("click", reloadDeviceFrame);
    }

    const slideQueue = createFileQueueManager({
      inputId: "czSlideFiles",
      dropzoneId: "czSlideDropzone",
      queueId: "czSlideQueue",
      submitBtnId: "uploadSlidesBtn",
    });

    const galleryQueue = createFileQueueManager({
      inputId: "czGalleryFiles",
      dropzoneId: "czGalleryDropzone",
      queueId: "czGalleryQueue",
      submitBtnId: "uploadGalleryBtn",
    });

    const uploadSlidesBtn = document.getElementById("uploadSlidesBtn");
    if (uploadSlidesBtn && slideQueue) {
      const freshBtn = uploadSlidesBtn.cloneNode(true);
      uploadSlidesBtn.parentNode.replaceChild(freshBtn, uploadSlidesBtn);

      freshBtn.addEventListener("click", async () => {
        const files = slideQueue.getFiles();
        if (!files.length) return;
        const fd = new FormData();
        const titleInput = document.getElementById("czSlideTitle");
        fd.append("title", titleInput ? titleInput.value.trim() : "");
        files.forEach((f) => fd.append("media", f));

        freshBtn.disabled = true;
        freshBtn.textContent = `Subiendo ${files.length} archivo(s)...`;

        try {
          const res = await fetch(drawer.dataset.urlCarouselAdd, {
            method: "POST",
            headers: { "X-CSRFToken": csrfToken() },
            body: fd,
          });
          const data = await res.json();
          if (!data.ok) throw new Error(data.error || "Error al subir");
          window.location.href = `${window.location.pathname}?cz_tab=carousel`;
        } catch (err) {
          showToast(err.message);
          freshBtn.disabled = false;
          freshBtn.textContent = "Subir al carrusel";
        }
      });
    }

    const uploadGalleryBtn = document.getElementById("uploadGalleryBtn");
    if (uploadGalleryBtn && galleryQueue) {
      const freshGalBtn = uploadGalleryBtn.cloneNode(true);
      uploadGalleryBtn.parentNode.replaceChild(freshGalBtn, uploadGalleryBtn);

      freshGalBtn.addEventListener("click", async () => {
        const files = galleryQueue.getFiles();
        if (!files.length) return;
        const fd = new FormData();
        const catSel = document.getElementById("czGalleryCat");
        const titleIn = document.getElementById("czGalleryTitle");
        fd.append("category", catSel ? catSel.value : "fachadas");
        fd.append("title", titleIn ? titleIn.value.trim() : "");
        files.forEach((f) => fd.append("images", f));

        freshGalBtn.disabled = true;
        freshGalBtn.textContent = `Publicando ${files.length} archivo(s)...`;

        try {
          const res = await fetch(drawer.dataset.urlGalleryAdd, {
            method: "POST",
            headers: { "X-CSRFToken": csrfToken() },
            body: fd,
          });
          const data = await res.json();
          if (!data.ok) throw new Error(data.error || "Error al publicar");
          window.location.href = `${window.location.pathname}?cz_tab=gallery`;
        } catch (err) {
          showToast(err.message);
          freshGalBtn.disabled = false;
          freshGalBtn.textContent = "Publicar en portafolio";
        }
      });
    }

    const galSearch = document.getElementById("czGallerySearch");
    if (galSearch) {
      galSearch.addEventListener("input", () => {
        const q = galSearch.value.trim().toLowerCase();
        document.querySelectorAll("#czGalleryList .cz-item").forEach((li) => {
          const hay = li.dataset.search || "";
          li.hidden = Boolean(q && !hay.includes(q));
        });
      });
    }

    const sorter = document.getElementById("czSectionSorter");
    const host = document.getElementById("dynamicSectionsHost");

    function syncSectionsLive() {
      if (!sorter || !host) return;
      let num = 1;
      const rows = Array.from(sorter.querySelectorAll(".cz-sec-row"));

      rows.forEach((row) => {
        const key = row.dataset.secKey;
        const checkbox = row.querySelector("[data-sec-toggle]");
        const badge = row.querySelector(".cz-sec-badge");
        const visible = checkbox ? checkbox.checked : true;
        row.classList.toggle("is-hidden-sec", !visible);

        const domSection = host.querySelector(`[data-dyn-section="${key}"]`);
        if (domSection) {
          host.appendChild(domSection);
          domSection.hidden = !visible;
        }

        const span = key === "tech" ? 2 : 1;
        if (visible) {
          if (badge) {
            badge.textContent =
              span === 2
                ? `${String(num).padStart(2, "0")}–${String(num + 1).padStart(2, "0")}`
                : String(num).padStart(2, "0");
          }
          if (domSection) {
            if (key === "tech") {
              domSection.querySelectorAll("[data-sec-num]").forEach((el, idx) => {
                el.textContent = String(num + idx).padStart(2, "0");
              });
            } else {
              const numEl = domSection.querySelector("[data-sec-num]");
              if (numEl) numEl.textContent = String(num).padStart(2, "0");
            }
          }
          num += span;
        } else if (badge) {
          badge.textContent = "Oculta";
        }
      });

      const contactStr = String(num).padStart(2, "0");
      const contactBadge = document.getElementById("czContactNumBadge");
      const contactNumEl = document.getElementById("contactSecNum");
      if (contactBadge) contactBadge.textContent = contactStr;
      if (contactNumEl) contactNumEl.textContent = contactStr;

      syncDeviceFrame();
    }

    if (sorter) {
      let draggedRow = null;

      sorter.addEventListener("dragstart", (e) => {
        const row = e.target.closest(".cz-sec-row");
        if (!row) return;
        draggedRow = row;
        row.classList.add("is-dragging");
      });
      sorter.addEventListener("dragend", () => {
        if (draggedRow) draggedRow.classList.remove("is-dragging");
        draggedRow = null;
        syncSectionsLive();
      });
      sorter.addEventListener("dragover", (e) => {
        e.preventDefault();
        const target = e.target.closest(".cz-sec-row");
        if (!draggedRow || !target || draggedRow === target) return;
        const rect = target.getBoundingClientRect();
        const after = e.clientY - rect.top > rect.height / 2;
        sorter.insertBefore(draggedRow, after ? target.nextSibling : target);
      });

      sorter.addEventListener("click", (e) => {
        const moveBtn = e.target.closest("[data-sec-move]");
        if (!moveBtn) return;
        const row = moveBtn.closest(".cz-sec-row");
        const dir = parseInt(moveBtn.dataset.secMove, 10);
        if (dir < 0 && row.previousElementSibling) {
          sorter.insertBefore(row, row.previousElementSibling);
        } else if (dir > 0 && row.nextElementSibling) {
          sorter.insertBefore(row.nextElementSibling, row);
        }
        syncSectionsLive();
      });

      sorter.addEventListener("change", (e) => {
        if (e.target.matches("[data-sec-toggle]")) {
          syncSectionsLive();
        }
      });
    }

    const themeInput = document.getElementById("czThemePreset");
    document.querySelectorAll("#czPaletteGrid .cz-swatch").forEach((sw) => {
      sw.addEventListener("click", () => {
        document.querySelectorAll("#czPaletteGrid .cz-swatch").forEach((b) => b.classList.remove("is-active"));
        sw.classList.add("is-active");
        const val = sw.dataset.themeVal;
        if (themeInput) themeInput.value = val;
        main.dataset.theme = val;
        syncDeviceFrame();
      });
    });

    const accentPicker = document.getElementById("czAccentColor");
    const accentHex = document.getElementById("czAccentHex");
    const resetAccent = document.getElementById("czResetAccent");
    let customAccentActive = Boolean(main.style.getPropertyValue("--custom-accent"));

    if (accentPicker) {
      accentPicker.addEventListener("input", () => {
        customAccentActive = true;
        main.style.setProperty("--custom-accent", accentPicker.value);
        if (accentHex) accentHex.textContent = accentPicker.value;
        syncDeviceFrame();
      });
    }
    if (resetAccent) {
      resetAccent.addEventListener("click", () => {
        customAccentActive = false;
        main.style.removeProperty("--custom-accent");
        if (accentHex) accentHex.textContent = "Automático";
        syncDeviceFrame();
      });
    }

    const fontSel = document.getElementById("czFontPreset");
    if (fontSel) {
      fontSel.addEventListener("change", () => {
        main.dataset.font = fontSel.value;
        syncDeviceFrame();
      });
    }

    const radiusSel = document.getElementById("czRadiusPreset");
    if (radiusSel) {
      radiusSel.addEventListener("change", () => {
        main.dataset.radius = radiusSel.value;
        syncDeviceFrame();
      });
    }

    const spacingSel = document.getElementById("czSectionSpacing");
    if (spacingSel) {
      spacingSel.addEventListener("change", () => {
        main.dataset.spacing = spacingSel.value;
        syncDeviceFrame();
      });
    }

    const heroHeightSel = document.getElementById("czHeroHeight");
    if (heroHeightSel) {
      heroHeightSel.addEventListener("change", () => {
        main.dataset.heroHeight = heroHeightSel.value;
        syncDeviceFrame();
      });
    }

    const overlayRange = document.getElementById("czHeroOverlay");
    const overlayVal = document.getElementById("czOverlayVal");
    if (overlayRange) {
      overlayRange.addEventListener("input", () => {
        main.style.setProperty("--hero-shade-alpha", `${overlayRange.value}%`);
        if (overlayVal) overlayVal.textContent = `${overlayRange.value}%`;
        syncDeviceFrame();
      });
    }

    const ctaInput = document.getElementById("czCtaLabel");
    const ctaBtn = document.getElementById("headerCtaBtn");
    if (ctaInput && ctaBtn) {
      ctaInput.addEventListener("input", () => {
        ctaBtn.textContent = ctaInput.value.trim() || "Cotizar";
        syncDeviceFrame();
      });
    }

    const marqueeCheck = document.getElementById("czShowMarquee");
    const marqueeEl = document.getElementById("siteMarquee");
    if (marqueeCheck && marqueeEl) {
      marqueeCheck.addEventListener("change", () => {
        marqueeEl.hidden = !marqueeCheck.checked;
        syncDeviceFrame();
      });
    }

    const waFloatCheck = document.getElementById("czShowFloatingWa");
    const waFloatEl = document.getElementById("floatingWaBtn");
    if (waFloatCheck && waFloatEl) {
      waFloatCheck.addEventListener("change", () => {
        waFloatEl.hidden = !waFloatCheck.checked;
        syncDeviceFrame();
      });
    }

    async function postSettings(payload, btn, defaultLabel) {
      if (btn) {
        btn.disabled = true;
        btn.textContent = "Guardando...";
      }
      try {
        const res = await fetch(drawer.dataset.urlSettingsSave, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken(),
          },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!data.ok) throw new Error(data.error || "No se pudo guardar");
        showToast("Cambios guardados correctamente");
        reloadDeviceFrame();
      } catch (err) {
        showToast(err.message);
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.textContent = defaultLabel;
        }
      }
    }

    const saveCarouselBtn = document.getElementById("saveCarouselConfigBtn");
    if (saveCarouselBtn) {
      const cleanCarBtn = saveCarouselBtn.cloneNode(true);
      saveCarouselBtn.parentNode.replaceChild(cleanCarBtn, saveCarouselBtn);
      cleanCarBtn.addEventListener("click", () => {
        const hero = document.getElementById("inicio");
        const transition = document.getElementById("czTransition").value;
        const interval = parseInt(document.getElementById("czInterval").value || "6", 10);
        const kenburns = document.getElementById("czKenBurns").checked;
        const pauseHover = document.getElementById("czPauseHover").checked;

        if (hero) {
          hero.dataset.transition = transition;
          hero.dataset.interval = String(interval);
          hero.dataset.pauseHover = pauseHover ? "1" : "0";
          hero.classList.toggle("is-kenburns", kenburns);
          initStudioHeroCarousel();
        }

        postSettings(
          {
            carousel_transition: transition,
            carousel_interval: interval,
            carousel_kenburns: kenburns,
            carousel_pause_hover: pauseHover,
          },
          cleanCarBtn,
          "Aplicar configuración"
        );
      });
    }

    const saveContactBtn = document.getElementById("saveContactSettingsBtn");
    if (saveContactBtn) {
      const cleanConBtn = saveContactBtn.cloneNode(true);
      saveContactBtn.parentNode.replaceChild(cleanConBtn, saveContactBtn);
      cleanConBtn.addEventListener("click", () => {
        postSettings(
          {
            phone_display: document.getElementById("czPhoneDisplay").value,
            phone_raw: document.getElementById("czPhoneRaw").value,
            whatsapp_number: document.getElementById("czWhatsapp").value,
            whatsapp_prefill: document.getElementById("czWhatsappPrefill").value,
            email_primary: document.getElementById("czEmail1").value,
            email_sales: document.getElementById("czEmail2").value,
            office_location: document.getElementById("czOfficeLocation").value,
            instagram_handle: document.getElementById("czIgHandle").value,
            instagram_url: document.getElementById("czIgUrl").value,
            tiktok_handle: document.getElementById("czTtHandle").value,
            tiktok_url: document.getElementById("czTtUrl").value,
          },
          cleanConBtn,
          "Guardar contacto y redes"
        );
      });
    }

    const saveThemeBtn = document.getElementById("saveThemeSettingsBtn");
    if (saveThemeBtn) {
      const cleanThmBtn = saveThemeBtn.cloneNode(true);
      saveThemeBtn.parentNode.replaceChild(cleanThmBtn, saveThemeBtn);
      cleanThmBtn.addEventListener("click", () => {
        const sectionOrder = Array.from(
          document.querySelectorAll("#czSectionSorter .cz-sec-row")
        ).map((r) => r.dataset.secKey);

        const visibility = {};
        document.querySelectorAll("[data-sec-toggle]").forEach((cb) => {
          visibility[`show_${cb.dataset.secToggle}`] = cb.checked;
        });

        postSettings(
          {
            ...visibility,
            section_order: sectionOrder,
            theme_preset: themeInput ? themeInput.value : "navy",
            accent_color: customAccentActive && accentPicker ? accentPicker.value : "",
            font_preset: fontSel ? fontSel.value : "editorial",
            radius_preset: radiusSel ? radiusSel.value : "pill",
            section_spacing: spacingSel ? spacingSel.value : "normal",
            hero_height: heroHeightSel ? heroHeightSel.value : "full",
            hero_overlay: overlayRange ? parseInt(overlayRange.value, 10) : 48,
            cta_label: ctaInput ? ctaInput.value : "Cotizar",
            show_marquee: marqueeCheck ? marqueeCheck.checked : true,
            show_floating_wa: waFloatCheck ? waFloatCheck.checked : true,
          },
          cleanThmBtn,
          "Guardar estilo y secciones"
        );
      });
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    initStudioHeroCarousel();
    initStudioDrawer();
  });
})();