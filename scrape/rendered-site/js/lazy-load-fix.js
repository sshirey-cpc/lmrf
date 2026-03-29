/**
 * Fix Squarespace lazy-loaded images on static hosting.
 * Copies data-src to src for images that haven't loaded.
 */
(function() {
  function loadImages() {
    document.querySelectorAll('img[data-src]').forEach(function(img) {
      if (!img.src || img.src === '' || img.src === window.location.href) {
        img.src = img.getAttribute('data-src');
      }
    });
    document.querySelectorAll('img[data-image]').forEach(function(img) {
      if (!img.src || img.src === '' || img.src === window.location.href || img.naturalWidth === 0) {
        var dataSrc = img.getAttribute('data-image');
        if (dataSrc) img.src = dataSrc;
      }
    });
  }

  // Run immediately and again after DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadImages);
  } else {
    loadImages();
  }
  // And again after a short delay for any late-rendered content
  setTimeout(loadImages, 500);
  setTimeout(loadImages, 2000);
})();
