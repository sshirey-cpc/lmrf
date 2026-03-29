/**
 * Static parallax fix: move each Parallax-item into its matching
 * Index-page section so background images render behind content.
 */
(function() {
  document.addEventListener('DOMContentLoaded', function() {
    var items = document.querySelectorAll('.Parallax-item');
    items.forEach(function(item) {
      var id = item.getAttribute('data-parallax-id');
      if (!id) return;

      // Find the matching section
      var section = document.querySelector(
        '[data-parallax-id="' + id + '"][data-parallax-original-element],' +
        '[data-collection-id="' + id + '"]'
      );
      if (!section || section === item) return;

      // Reset the inline styles that position it off-screen
      item.style.transform = 'none';
      item.style.top = '0';
      item.style.left = '0';
      item.style.width = '100%';
      item.style.height = '100%';
      item.style.position = 'absolute';

      // Fix the image inside
      var img = item.querySelector('img');
      if (img) {
        img.style.width = '100%';
        img.style.height = '100%';
        img.style.objectFit = 'cover';
        img.style.position = 'absolute';
        img.style.top = '0';
        img.style.left = '0';
      }

      var figure = item.querySelector('figure');
      if (figure) {
        figure.style.position = 'absolute';
        figure.style.top = '0';
        figure.style.left = '0';
        figure.style.right = '0';
        figure.style.bottom = '0';
        figure.style.overflow = 'hidden';
        figure.style.transform = 'none';
      }

      // Make the section a positioning context and insert the image
      section.style.position = 'relative';
      section.style.overflow = 'hidden';
      section.insertBefore(item, section.firstChild);

      // Ensure content is above the background
      var content = section.querySelector('.Index-page-content');
      if (content) {
        content.style.position = 'relative';
        content.style.zIndex = '2';
      }
    });

    // Clean up the now-empty parallax host
    var host = document.querySelector('.Parallax-host-outer');
    if (host && host.querySelectorAll('.Parallax-item').length === 0) {
      host.style.display = 'none';
    }
  });
})();
