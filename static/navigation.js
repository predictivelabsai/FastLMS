(function () {
    "use strict";

    const mobileViewport = window.matchMedia("(max-width: 768px)");
    const sectionStorageKey = "fastlearn.nav.sections";
    const sidebarStorageKey = "fastlearn.nav.sidebar-expanded";

    function readStoredSections() {
        try {
            return JSON.parse(window.localStorage.getItem(sectionStorageKey) || "{}");
        } catch (_error) {
            return {};
        }
    }

    function storeSection(key, open) {
        try {
            const state = readStoredSections();
            state[key] = open;
            window.localStorage.setItem(sectionStorageKey, JSON.stringify(state));
        } catch (_error) {
            // Navigation remains usable when storage is unavailable.
        }
    }

    function setNavSection(section, open, persist) {
        if (!section) return;
        const button = section.querySelector(":scope > .nav-section-toggle");
        const body = section.querySelector(":scope > .nav-section-body");
        section.classList.toggle("open", open);
        if (button) button.setAttribute("aria-expanded", String(open));
        if (body) body.hidden = !open;
        if (persist) storeSection(section.dataset.navKey, open);
    }

    window.toggleNavSection = function (key) {
        const section = Array.from(document.querySelectorAll(".nav-section[data-nav-key]")).find(
            (item) => item.dataset.navKey === key
        );
        if (!section) return;
        setNavSection(section, !section.classList.contains("open"), true);
    };

    function restoreNavSections() {
        const stored = readStoredSections();
        document.querySelectorAll(".nav-section[data-nav-key]").forEach(function (section) {
            const key = section.dataset.navKey;
            const hasStoredState = Object.prototype.hasOwnProperty.call(stored, key);
            const defaultOpen = section.dataset.defaultOpen === "true";
            const containsCurrentPage = Boolean(section.querySelector('[aria-current="page"]'));
            setNavSection(section, containsCurrentPage || (hasStoredState ? Boolean(stored[key]) : defaultOpen), false);
        });
    }

    function sidebarIsExpanded() {
        const shell = document.querySelector(".app-grid");
        return !(shell && shell.classList.contains("sidebar-collapsed"));
    }

    function updatePaneAccessibility() {
        const pane = document.getElementById("left-pane");
        if (!pane) return;
        const hidden = mobileViewport.matches ? !pane.classList.contains("open") : !sidebarIsExpanded();
        pane.setAttribute("aria-hidden", String(hidden));
    }

    function setSidebarExpanded(expanded, persist) {
        const shell = document.querySelector(".app-grid");
        const collapseButton = document.querySelector(".desktop-sidebar-collapse");
        const expandButton = document.getElementById("desktop-sidebar-expand");
        if (shell) shell.classList.toggle("sidebar-collapsed", !expanded);
        if (collapseButton) collapseButton.setAttribute("aria-expanded", String(expanded));
        if (expandButton) expandButton.setAttribute("aria-expanded", String(expanded));
        updatePaneAccessibility();
        if (persist) {
            try {
                window.localStorage.setItem(sidebarStorageKey, String(expanded));
            } catch (_error) {
                // Sidebar still works when storage is unavailable.
            }
        }
    }

    window.toggleSidebar = function (force) {
        const next = typeof force === "boolean" ? force : !sidebarIsExpanded();
        setSidebarExpanded(next, true);
        if (next && !mobileViewport.matches) {
            window.setTimeout(function () {
                const collapseButton = document.querySelector(".desktop-sidebar-collapse");
                if (collapseButton) collapseButton.focus();
            }, 210);
        }
    };

    function restoreSidebar() {
        let expanded = true;
        try {
            expanded = window.localStorage.getItem(sidebarStorageKey) !== "false";
        } catch (_error) {
            expanded = true;
        }
        setSidebarExpanded(expanded, false);
    }

    function setLeftPane(open, moveFocus) {
        const pane = document.getElementById("left-pane");
        const overlay = document.getElementById("left-overlay");
        const button = document.getElementById("mobile-menu-button");
        const shouldOpen = Boolean(open && mobileViewport.matches);

        if (pane) pane.classList.toggle("open", shouldOpen);
        if (overlay) {
            overlay.classList.toggle("visible", shouldOpen);
            overlay.setAttribute("aria-hidden", String(!shouldOpen));
        }
        if (button) {
            button.setAttribute("aria-expanded", String(shouldOpen));
            button.setAttribute("aria-label", shouldOpen ? button.dataset.closeLabel : button.dataset.openLabel);
        }
        document.body.classList.toggle("nav-open", shouldOpen);
        updatePaneAccessibility();

        if (moveFocus) {
            window.setTimeout(function () {
                if (shouldOpen && pane) {
                    const closeButton = pane.querySelector(".mobile-drawer-close");
                    if (closeButton) closeButton.focus();
                } else if (button) {
                    button.focus();
                }
            }, 230);
        }
    }

    window.toggleLeftPane = function (force) {
        const pane = document.getElementById("left-pane");
        const next = typeof force === "boolean" ? force : !(pane && pane.classList.contains("open"));
        setLeftPane(next, true);
    };

    document.addEventListener("DOMContentLoaded", function () {
        restoreNavSections();
        restoreSidebar();
        setLeftPane(false, false);
        document.addEventListener("keydown", function (event) {
            const pane = document.getElementById("left-pane");
            if (event.key === "Escape" && pane && pane.classList.contains("open")) {
                setLeftPane(false, true);
            }
        });
    });

    const handleViewportChange = function () {
        setLeftPane(false, false);
        restoreSidebar();
    };
    if (mobileViewport.addEventListener) mobileViewport.addEventListener("change", handleViewportChange);
    else mobileViewport.addListener(handleViewportChange);
})();
