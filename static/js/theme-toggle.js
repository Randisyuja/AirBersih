/**
 * Jogo Tirto - Dual-Theme Controller (Dark / Light Mode)
 * Synchronizes documentElement data-theme attribute, localStorage, and toggle button icon.
 */
(function () {
    'use strict';

    function getActiveTheme() {
        try {
            return document.documentElement.getAttribute('data-theme') || 
                   localStorage.getItem('theme') || 
                   'dark';
        } catch (e) {
            return document.documentElement.getAttribute('data-theme') || 'dark';
        }
    }

    function updateThemeUI(theme) {
        // 1. Sync data-theme attribute on <html>
        document.documentElement.setAttribute('data-theme', theme);

        // 2. Sync Toggle Button & Icon
        var btn = document.getElementById('themeToggleBtn');
        var icon = document.getElementById('themeToggleIcon');
        if (icon) {
            if (theme === 'dark') {
                icon.className = 'fas fa-sun';
                if (btn) {
                    btn.setAttribute('aria-label', 'Beralih ke Mode Terang');
                    btn.setAttribute('title', 'Beralih ke Mode Terang');
                }
            } else {
                icon.className = 'fas fa-moon';
                if (btn) {
                    btn.setAttribute('aria-label', 'Beralih ke Mode Gelap');
                    btn.setAttribute('title', 'Beralih ke Mode Gelap');
                }
            }
        }

        // 3. Dispatch custom event for reactive components (e.g. Chart.js)
        try {
            window.dispatchEvent(new CustomEvent('themeChanged', { 
                detail: { theme: theme } 
            }));
        } catch (e) {
            // Fallback for older browsers
        }
    }

    function setupThemeToggle() {
        var currentTheme = getActiveTheme();
        updateThemeUI(currentTheme);

        var toggleBtn = document.getElementById('themeToggleBtn');
        if (toggleBtn && !toggleBtn.dataset.themeBound) {
            toggleBtn.dataset.themeBound = 'true';
            toggleBtn.addEventListener('click', function (e) {
                e.preventDefault();
                var active = getActiveTheme();
                var targetTheme = (active === 'dark') ? 'light' : 'dark';
                try {
                    localStorage.setItem('theme', targetTheme);
                } catch (err) {
                    console.warn('Unable to persist theme to localStorage', err);
                }
                updateThemeUI(targetTheme);
            });
        }
    }

    // Run once DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupThemeToggle);
    } else {
        setupThemeToggle();
    }

    // Sync across browser tabs
    window.addEventListener('storage', function (e) {
        if (e.key === 'theme' && e.newValue) {
            updateThemeUI(e.newValue);
        }
    });
})();
