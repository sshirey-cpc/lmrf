/**
 * Mobile nav for static Squarespace site.
 * - Hamburger toggle
 * - Close button (injected)
 * - Youth Programs expands inline with sub-items
 */
(function() {
  document.addEventListener('DOMContentLoaded', function() {
    var overlay = document.querySelector('.Mobile-overlay');
    var menuBtn = document.querySelector('.Mobile-bar-menu');
    var body = document.body;

    if (!overlay || !menuBtn) return;

    // Inject a visible close button
    var closeBtn = document.createElement('button');
    closeBtn.className = 'mobile-close-btn';
    closeBtn.innerHTML = '&times;';
    closeBtn.setAttribute('aria-label', 'Close menu');
    overlay.insertBefore(closeBtn, overlay.firstChild);

    // Build inline sub-nav for Youth Programs from the folder data
    var folderBtns = document.querySelectorAll('.Mobile-overlay-nav-item--folder');
    folderBtns.forEach(function(btn) {
      var folderId = btn.getAttribute('data-controller-folder-toggle');
      var folder = document.querySelector('.Mobile-overlay-folder[data-controller-folder="' + folderId + '"]');
      if (!folder) return;

      // Create inline subnav
      var subnav = document.createElement('div');
      subnav.className = 'mobile-subnav';

      var links = folder.querySelectorAll('a.Mobile-overlay-folder-item');
      links.forEach(function(link) {
        var a = document.createElement('a');
        a.href = link.href;
        a.textContent = link.textContent.trim();
        subnav.appendChild(a);
      });

      // Insert subnav right after the folder button
      btn.parentNode.insertBefore(subnav, btn.nextSibling);

      // Toggle subnav on click
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        var isOpen = subnav.classList.contains('open');
        subnav.classList.toggle('open');
        btn.classList.toggle('open');
      });
    });

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
      // Close any open subnavs
      var openSubs = overlay.querySelectorAll('.mobile-subnav.open');
      openSubs.forEach(function(s) { s.classList.remove('open'); });
      var openBtns = overlay.querySelectorAll('.Mobile-overlay-nav-item--folder.open');
      openBtns.forEach(function(b) { b.classList.remove('open'); });
    }

    menuBtn.addEventListener('click', function(e) {
      e.preventDefault();
      if (body.classList.contains('is-mobile-overlay-active')) {
        closeMenu();
      } else {
        openMenu();
      }
    });

    closeBtn.addEventListener('click', function(e) {
      e.preventDefault();
      closeMenu();
    });

    // Close menu when a nav link is clicked
    var navLinks = overlay.querySelectorAll('a.Mobile-overlay-nav-item, .mobile-subnav a');
    navLinks.forEach(function(link) {
      link.addEventListener('click', function() {
        closeMenu();
      });
    });
  });
})();
