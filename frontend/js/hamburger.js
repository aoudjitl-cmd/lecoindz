document.addEventListener("DOMContentLoaded", function () {

  const navbar = document.querySelector(".navbar");
  const nav = document.querySelector(".navbar-nav");
  if (!navbar || !nav) return;

  // 1. Créer le bouton hamburger (toujours dans le DOM, caché sur desktop via CSS)
  const btn = document.createElement("button");
  btn.className = "hamburger-btn";
  btn.setAttribute("aria-label", "Ouvrir le menu");
  btn.innerHTML = "<span></span><span></span><span></span>";
  navbar.appendChild(btn);

  let drawerBuilt = false;

  function buildDrawer() {
    if (drawerBuilt) return;
    // Envelopper les liens dans un tiroir uniquement sur mobile
    const drawer = document.createElement("div");
    drawer.className = "nav-drawer";
    while (nav.firstChild) drawer.appendChild(nav.firstChild);
    nav.appendChild(drawer);
    drawerBuilt = true;
  }

  function destroyDrawer() {
    if (!drawerBuilt) return;
    const drawer = nav.querySelector(".nav-drawer");
    if (!drawer) return;
    // Remettre les liens directement dans nav (desktop)
    while (drawer.firstChild) nav.insertBefore(drawer.firstChild, drawer);
    drawer.remove();
    drawerBuilt = false;
    nav.classList.remove("open");
    btn.classList.remove("open");
    document.body.style.overflow = "";
  }

  function applyMode() {
    if (window.innerWidth <= 768) {
      buildDrawer();
    } else {
      destroyDrawer();
    }
  }

  // 2. Ouvrir / fermer
  btn.addEventListener("click", function (e) {
    e.stopPropagation();
    const isOpen = nav.classList.toggle("open");
    btn.classList.toggle("open", isOpen);
    btn.setAttribute("aria-label", isOpen ? "Fermer le menu" : "Ouvrir le menu");
    document.body.style.overflow = isOpen ? "hidden" : "";
  });

  // 3. Clic sur le fond sombre ferme le menu
  nav.addEventListener("click", function (e) {
    if (e.target === nav) {
      nav.classList.remove("open");
      btn.classList.remove("open");
      document.body.style.overflow = "";
    }
  });

  // 4. Adapter au resize
  window.addEventListener("resize", applyMode);

  // 5. Init au chargement
  applyMode();
});