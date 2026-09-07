(function () {
    "use strict";

    const mobileViewport = window.matchMedia("(max-width: 768px)");

    function setLeftPane(open) {
        const pane = document.getElementById("left-pane");
        const overlay = document.getElementById("left-overlay");
        const button = document.getElementById("mobile-menu-button");
        const shouldOpen = Boolean(open && mobileViewport.matches);

        if (pane) {
            pane.classList.toggle("open", shouldOpen);
            pane.setAttribute("aria-hidden", String(mobileViewport.matches && !shouldOpen));
        }
        if (overlay) overlay.classList.toggle("visible", shouldOpen);
        if (button) button.setAttribute("aria-expanded", String(shouldOpen));
        document.body.classList.toggle("nav-open", shouldOpen);
    }

    window.toggleLeftPane = function (force) {
        const pane = document.getElementById("left-pane");
        const next = typeof force === "boolean" ? force : !(pane && pane.classList.contains("open"));
        setLeftPane(next);
    };

    document.addEventListener("DOMContentLoaded", function () {
        setLeftPane(false);
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") setLeftPane(false);
        });
    });

    const closeOnDesktop = function (event) {
        if (!event.matches) setLeftPane(false);
    };
    if (mobileViewport.addEventListener) mobileViewport.addEventListener("change", closeOnDesktop);
    else mobileViewport.addListener(closeOnDesktop);
})();
