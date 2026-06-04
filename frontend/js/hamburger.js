// Menu hamburger — à inclure dans chaque page via <script src="js/hamburger.js"></script>
document.addEventListener("DOMContentLoaded", function () {

  const navbar = document.querySelector(".navbar");
  if (!navbar) return;

  // 1. Créer le bouton hamburger
  const btn = document.createElement("button");
  btn.className = "hamburger-btn";
  btn.setAttribute("aria-label", "Ouvrir le menu");
  btn.innerHTML = "<span></span><span></span><span></span>";
  navbar.appendChild(btn);

  // 2. Envelopper les liens dans un tiroir
  const nav = document.querySelector(".navbar-nav");
  if (!nav) return;

  const drawer = document.createElement("div");
  drawer.className = "nav-drawer";
  while (nav.firstChild) drawer.appendChild(nav.firstChild);
  nav.appendChild(drawer);

  // 3. Ouvrir / fermer
  btn.addEventListener("click", function (e) {
    e.stopPropagation();
    const isOpen = nav.classList.toggle("open");
    btn.classList.toggle("open", isOpen);
    btn.setAttribute("aria-label", isOpen ? "Fermer le menu" : "Ouvrir le menu");
    document.body.style.overflow = isOpen ? "hidden" : "";
  });

  // 4. Clic sur le fond sombre ferme le menu
  nav.addEventListener("click", function (e) {
    if (e.target === nav) {
      nav.classList.remove("open");
      btn.classList.remove("open");
      document.body.style.overflow = "";
    }
  });

  // 5. Fermer sur resize vers desktop
  window.addEventListener("resize", function () {
    if (window.innerWidth > 768) {
      nav.classList.remove("open");
      btn.classList.remove("open");
      document.body.style.overflow = "";
    }
  });
});