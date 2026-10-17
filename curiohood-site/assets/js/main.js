/* CurioHood Travel Media — site interactions */
(function () {
  "use strict";

  // Mobile navigation
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
      var bars = toggle.querySelectorAll("span");
      if (bars.length === 3) {
        bars[0].style.transform = open ? "translateY(6.5px) rotate(45deg)" : "";
        bars[1].style.opacity = open ? "0" : "";
        bars[2].style.transform = open ? "translateY(-6.5px) rotate(-45deg)" : "";
      }
    });
    nav.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.querySelectorAll("span").forEach(function (s) { s.style.transform = ""; s.style.opacity = ""; });
      });
    });
  }

  // Highlight current page in nav
  var here = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".nav a").forEach(function (a) {
    var target = a.getAttribute("href");
    if (target === here || (here === "" && target === "index.html")) {
      a.classList.add("is-active");
      a.setAttribute("aria-current", "page");
    }
  });

  // Reveal on scroll
  var items = document.querySelectorAll(".reveal");
  if (items.length && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.06 });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add("is-in"); });
  }

  // Newsletter (demo: no backend wired yet)
  var form = document.querySelector(".nl-form");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var input = form.querySelector("input[type=email]");
      var note = form.querySelector(".nl-note");
      if (!input || !input.value || input.value.indexOf("@") < 0) {
        if (note) { note.textContent = "请填写有效的邮箱地址。"; note.style.color = "#E8B4A0"; }
        return;
      }
      if (note) { note.textContent = "已记录，我们会把下一期寄给你。"; note.style.color = "#C9973F"; }
      input.value = "";
    });
  }
})();
