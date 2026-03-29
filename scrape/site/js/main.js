// Mobile nav toggle
document.addEventListener('DOMContentLoaded', function() {
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.querySelector('nav');

  if (toggle && nav) {
    toggle.addEventListener('click', function() {
      nav.classList.toggle('open');
    });
  }

  // Mobile dropdown toggle
  var dropdowns = document.querySelectorAll('.dropdown');
  dropdowns.forEach(function(dd) {
    var link = dd.querySelector('.dropdown-toggle');
    if (link) {
      link.addEventListener('click', function(e) {
        if (window.innerWidth <= 768) {
          e.preventDefault();
          dd.classList.toggle('open');
        }
      });
    }
  });

  // Contact form handler
  var form = document.getElementById('contact-form');
  if (form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      var name = form.querySelector('[name="name"]').value;
      var email = form.querySelector('[name="email"]').value;
      var subjectField = form.querySelector('[name="subject"]');
      var subjectText = subjectField ? subjectField.value : '';
      var message = form.querySelector('[name="message"]').value;
      var subject = encodeURIComponent(subjectText || ('Website Contact: ' + name));
      var body = encodeURIComponent('From: ' + name + '\nEmail: ' + email + '\nSubject: ' + subjectText + '\n\n' + message);
      window.location.href = 'mailto:info@lowermsfoundation.org?subject=' + subject + '&body=' + body;

      var status = document.querySelector('.form-status');
      if (status) {
        status.className = 'form-status success';
        status.textContent = 'Opening your email client to send the message...';
      }
    });
  }
});
