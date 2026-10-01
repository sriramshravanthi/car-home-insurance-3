(function () {
  "use strict";
  // Progressive enhancement only: every effect here is decorative or additive.
  // If this script fails to load or run, the page is still complete and readable —
  // .reveal elements are only hidden once .js is added to <html> below, and
  // .sx-nav-toggle stays display:none (see site.css) until .js is present, so the
  // full nav link list stays visible and usable at every width without JS.
  document.documentElement.classList.add("js");

  function onReady(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  onReady(function () {
    // Scroll reveal
    var revealEls = document.querySelectorAll(".reveal");
    if ("IntersectionObserver" in window && revealEls.length) {
      var io = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              entry.target.classList.add("in-view");
              io.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
      );
      revealEls.forEach(function (el) { io.observe(el); });
    } else {
      revealEls.forEach(function (el) { el.classList.add("in-view"); });
    }

    // Count-up numbers: HTML already holds the final text, so a JS failure
    // just means no animation, never missing/wrong data.
    var counters = document.querySelectorAll("[data-countup]");
    if ("IntersectionObserver" in window && counters.length) {
      var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      var cIo = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (!entry.isIntersecting) return;
            cIo.unobserve(entry.target);
            var el = entry.target;
            var finalText = el.textContent;
            var target = parseFloat(el.getAttribute("data-countup"));
            if (reduceMotion || isNaN(target)) return;
            var prefix = el.getAttribute("data-prefix") || "";
            var suffix = el.getAttribute("data-suffix") || "";
            var duration = 900;
            var start = null;
            function step(ts) {
              if (start === null) start = ts;
              var progress = Math.min((ts - start) / duration, 1);
              var eased = 1 - Math.pow(1 - progress, 3);
              var value = Math.round(target * eased);
              el.textContent = prefix + value.toLocaleString("en-US") + suffix;
              if (progress < 1) requestAnimationFrame(step);
              else el.textContent = finalText;
            }
            requestAnimationFrame(step);
          });
        },
        { threshold: 0.4 }
      );
      counters.forEach(function (el) { cIo.observe(el); });
    }

    // Mobile nav toggle: plain button + class, not <details>/<summary>. A real
    // Chromium bug drops a flex-row descendant's painted content entirely at
    // narrow widths when the row needs real free-space distribution — see
    // site.css for the full writeup. A plain button sidesteps it cleanly.
    document.querySelectorAll(".sx-nav-toggle").forEach(function (toggle) {
      var nav = toggle.closest(".sx-nav");
      if (!nav) return;
      var close = function () {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      };
      toggle.addEventListener("click", function () {
        var open = nav.classList.toggle("is-open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
      document.addEventListener("click", function (e) {
        if (nav.classList.contains("is-open") && !nav.contains(e.target)) close();
      });
      nav.addEventListener("keydown", function (e) {
        if (e.key === "Escape") { close(); toggle.focus(); }
      });
    });

    // Sticky header shadow
    var header = document.querySelector(".sx-header");
    if (header) {
      var lastState = false;
      window.addEventListener(
        "scroll",
        function () {
          var scrolled = window.scrollY > 12;
          if (scrolled !== lastState) {
            header.classList.toggle("cx-scrolled", scrolled);
            lastState = scrolled;
          }
        },
        { passive: true }
      );
    }
  });
})();
