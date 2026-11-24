// Videos de "Así trabajamos": se reproducen solos (silenciados) al entrar en
// pantalla y se pausan al salir. El usuario puede activar el sonido con los controles.
(function () {
  var videos = document.querySelectorAll(".video-card video");
  if (!videos.length) return;

  videos.forEach(function (v) {
    v.muted = true;
    v.defaultMuted = true;
  });

  function play(v) {
    var p = v.play();
    if (p && p.catch) p.catch(function () {});
  }

  if (!("IntersectionObserver" in window)) {
    videos.forEach(play);
    return;
  }

  var io = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) play(e.target);
        else e.target.pause();
      });
    },
    { threshold: 0.4 }
  );
  videos.forEach(function (v) { io.observe(v); });
})();
