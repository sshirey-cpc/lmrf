/**
 * Mobile nav fix for static Squarespace site.
 * Handles hamburger menu toggle and folder (dropdown) toggles.
 */
(function() {
  document.addEventListener('DOMContentLoaded', function() {
    var overlay = document.querySelector('.Mobile-overlay');
    var menuBtn = document.querySelector('.Mobile-bar-menu');
    var closeBtn = document.querySelector('.Mobile-overlay-close');
    var body = document.body;

    if (!overlay || !menuBtn) return;

    // Toggle mobile menu open/close
    function openMenu() {
      body.classList.add('is-mobile-overlay-active');
      overlay.style.display = 'block';
      overlay.style.visibility = 'visible';
      overlay.style.opacity = '1';
      overlay.style.zIndex = '9999';
    }

    function closeMenu() {
      body.classList.remove('is-mobile-overlay-active');
      overlay.style.display = '';
      overlay.style.visibility = '';
      overlay.style.opacity = '';
    }

    menuBtn.addEventListener('click', function(e) {
      e.preventDefault();
      if (body.classList.contains('is-mobile-overlay-active')) {
        closeMenu();
      } else {
        openMenu();
      }
    });

    if (closeBtn) {
      closeBtn.addEventListener('click', function(e) {
        e.preventDefault();
        closeMenu();
      });
    }

    // Handle folder toggles (e.g., "Youth Programs" dropdown)
    var folderBtns = document.querySelectorAll('.Mobile-overlay-nav-item--folder');
    folderBtns.forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        var folderId = btn.getAttribute('data-controller-folder-toggle');
        var folder = document.querySelector('.Mobile-overlay-folder[data-controller-folder="' + folderId + '"]');
        if (folder) {
          var isOpen = folder.style.display === 'block';
          folder.style.display = isOpen ? 'none' : 'block';
          folder.style.position = isOpen ? '' : 'relative';
          folder.style.transform = 'none';
        }
      });
    });

    // Back buttons in folders
    var backBtns = document.querySelectorAll('.Mobile-overlay-folder-item--toggle');
    backBtns.forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        var folder = btn.closest('.Mobile-overlay-folder');
        if (folder) {
          folder.style.display = 'none';
        }
      });
    });

    // Close menu when a nav link is clicked
    var navLinks = overlay.querySelectorAll('a.Mobile-overlay-nav-item, a.Mobile-overlay-folder-item');
    navLinks.forEach(function(link) {
      link.addEventListener('click', function() {
        closeMenu();
      });
    });
  });
})();
