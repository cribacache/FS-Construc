/* Confirmaciones del panel. Antes se hacían con onsubmit="..." en el HTML, pero
   la política de seguridad (CSP) bloquea los atributos de evento en línea, así
   que el aviso nunca aparecía y la foto se borraba sin preguntar. */
document.addEventListener("submit", function (event) {
  var form = event.target;
  var message = form && form.getAttribute ? form.getAttribute("data-confirm") : null;
  if (message && !window.confirm(message)) event.preventDefault();
});
