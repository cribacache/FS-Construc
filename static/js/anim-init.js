/* Se ejecuta en el <head>, antes de pintar: decide si la página usa animaciones
   de entrada. Sin JS, en el editor visual o con "movimiento reducido" todo el
   contenido se muestra de inmediato. */
(function () {
  var root = document.documentElement;
  if (root.hasAttribute("data-edit")) return;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  root.classList.add("anim");
  try {
    if (!window.sessionStorage.getItem("fsIntro")) {
      root.classList.add("is-intro");
      window.sessionStorage.setItem("fsIntro", "1");
    }
  } catch (e) {
    root.classList.add("is-intro");
  }

  // Red de seguridad: si home.js no llega a cargar, no dejamos el sitio oculto.
  window.setTimeout(function () {
    if (!root.classList.contains("anim-ready")) {
      root.classList.remove("anim");
      root.classList.remove("is-intro");
    }
  }, 6000);
})();
