"""Replace Squarespace camp application form with working HTML form."""
import os

with open(r'C:\Users\scott\lmrf\website\site\camp-application.html', 'r', encoding='utf-8') as f:
    content = f.read()

form_block_start = 77735
form_end = 123698

new_form = '''<div class="sqs-block html-block sqs-block-html" data-block-type="2"><div class="sqs-block-content">
<style>
.camp-form { max-width: 640px; margin: 0 auto; font-family: inherit; }
.camp-form h3 { margin-top: 24px; margin-bottom: 8px; color: #d48b3e; font-size: 16px; text-transform: uppercase; letter-spacing: 1px; }
.camp-form label { display: block; margin-top: 12px; font-weight: 600; font-size: 14px; color: #333; }
.camp-form input, .camp-form select, .camp-form textarea {
  width: 100%; padding: 10px 12px; margin-top: 4px; border: 1px solid #ccc;
  border-radius: 4px; font-size: 14px; font-family: inherit; box-sizing: border-box;
}
.camp-form input:focus, .camp-form select:focus, .camp-form textarea:focus {
  outline: none; border-color: #d48b3e;
}
.camp-form textarea { height: 120px; resize: vertical; }
.camp-form .form-row { display: flex; gap: 12px; }
.camp-form .form-row > div { flex: 1; }
@media (max-width: 600px) { .camp-form .form-row { flex-direction: column; gap: 0; } }
.camp-form .required::after { content: " *"; color: #c00; }
.camp-form button[type="submit"] {
  display: block; width: 100%; margin-top: 24px; padding: 14px;
  background: #d48b3e; color: #fff; border: none; border-radius: 25px;
  font-size: 16px; font-weight: 600; cursor: pointer; letter-spacing: 1px;
}
.camp-form button[type="submit"]:hover { background: #b8742f; }
.camp-form .form-note { font-size: 12px; color: #777; margin-top: 4px; }
.camp-form .form-success { display: none; text-align: center; padding: 40px 20px; }
.camp-form .form-success h3 { color: #2a7f2a; font-size: 20px; }
</style>
<div class="camp-form">
  <div id="camp-form-fields">
    <h3>Participant Information</h3>

    <div class="form-row">
      <div>
        <label class="required">First Name</label>
        <input type="text" id="cf-firstName" required>
      </div>
      <div>
        <label class="required">Last Name</label>
        <input type="text" id="cf-lastName" required>
      </div>
    </div>

    <div class="form-row">
      <div>
        <label class="required">Birth Date</label>
        <input type="date" id="cf-birthdate" required>
      </div>
      <div>
        <label class="required">Age</label>
        <input type="number" id="cf-age" min="5" max="18" required>
      </div>
    </div>

    <div class="form-row">
      <div>
        <label class="required">Current Grade Level</label>
        <select id="cf-grade" required>
          <option value="" disabled selected>Select a grade</option>
          <option>3rd</option><option>4th</option><option>5th</option>
          <option>6th</option><option>7th</option><option>8th</option>
          <option>9th</option><option>10th</option><option>11th</option>
        </select>
      </div>
      <div>
        <label class="required">Current School</label>
        <input type="text" id="cf-school" required>
      </div>
    </div>

    <h3>Contact Information</h3>

    <div class="form-row">
      <div>
        <label class="required">Email Address</label>
        <input type="email" id="cf-email" required>
      </div>
      <div>
        <label class="required">Phone</label>
        <input type="tel" id="cf-phone" required>
      </div>
    </div>

    <label>Parent/Guardian Phone (if different)</label>
    <input type="tel" id="cf-parentPhone">

    <h3>Physical Address</h3>

    <label class="required">Address</label>
    <input type="text" id="cf-address1" required>

    <div class="form-row">
      <div>
        <label class="required">City</label>
        <input type="text" id="cf-city1" required>
      </div>
      <div>
        <label class="required">State</label>
        <input type="text" id="cf-state1" required>
      </div>
      <div>
        <label class="required">ZIP Code</label>
        <input type="text" id="cf-zip1" required>
      </div>
    </div>

    <h3>Mailing Address <span style="font-weight:normal;font-size:12px;color:#777;">(if different than above)</span></h3>

    <label>Address</label>
    <input type="text" id="cf-address2">

    <div class="form-row">
      <div>
        <label>City</label>
        <input type="text" id="cf-city2">
      </div>
      <div>
        <label>State</label>
        <input type="text" id="cf-state2">
      </div>
      <div>
        <label>ZIP Code</label>
        <input type="text" id="cf-zip2">
      </div>
    </div>

    <h3>Tell Us About Yourself</h3>

    <label class="required">Please explain why you are interested in joining this trip! (5-10 sentences)</label>
    <textarea id="cf-essay" required></textarea>

    <div style="margin-top:16px;">
      <label><input type="checkbox" id="cf-deposit" required style="width:auto;margin-right:8px;">
        I understand that a $25 deposit is required within 30 days to secure my spot.</label>
    </div>

    <button type="submit" id="cf-submit">Submit Application</button>
    <p class="form-note" style="text-align:center;margin-top:8px;">After submitting, you will be directed to pay the $25 deposit via PayPal.</p>
  </div>

  <div class="form-success" id="camp-form-success">
    <h3>Application Submitted!</h3>
    <p>Thank you for applying to the Mississippi River Summer Leadership Camp.</p>
    <p>You will be redirected to PayPal to pay the $25 deposit.</p>
    <p>If you are not redirected, <a id="paypal-link" href="#">click here</a>.</p>
  </div>
</div>

<script>
(function() {
  var form = document.getElementById('camp-form-fields');
  var btn = document.getElementById('cf-submit');
  var success = document.getElementById('camp-form-success');

  btn.addEventListener('click', function(e) {
    e.preventDefault();

    var required = form.querySelectorAll('[required]');
    var valid = true;
    required.forEach(function(el) {
      if (!el.value || (el.type === 'checkbox' && !el.checked)) {
        el.style.borderColor = '#c00';
        valid = false;
      } else {
        el.style.borderColor = '#ccc';
      }
    });
    if (!valid) { alert('Please fill in all required fields.'); return; }

    btn.disabled = true;
    btn.textContent = 'Submitting...';

    var data = {
      firstName: document.getElementById('cf-firstName').value,
      lastName: document.getElementById('cf-lastName').value,
      birthdate: document.getElementById('cf-birthdate').value,
      age: document.getElementById('cf-age').value,
      currentGrade: document.getElementById('cf-grade').value,
      school: document.getElementById('cf-school').value,
      email: document.getElementById('cf-email').value,
      phone: document.getElementById('cf-phone').value,
      parentPhone: document.getElementById('cf-parentPhone').value,
      address1: document.getElementById('cf-address1').value,
      city1: document.getElementById('cf-city1').value,
      state1: document.getElementById('cf-state1').value,
      zip1: document.getElementById('cf-zip1').value,
      address2: document.getElementById('cf-address2').value,
      city2: document.getElementById('cf-city2').value,
      state2: document.getElementById('cf-state2').value,
      zip2: document.getElementById('cf-zip2').value,
      essay: document.getElementById('cf-essay').value
    };

    fetch('https://us-central1-balmy-limiter-491013-a8.cloudfunctions.net/camp-application', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    .then(function(r) { return r.json(); })
    .then(function(resp) {
      form.style.display = 'none';
      success.style.display = 'block';
      var paypalUrl = 'https://www.paypal.com/donate/?hosted_button_id=LMRF_CAMP_DEPOSIT&amount=25&item_name=Camp+Deposit+-+' + encodeURIComponent(data.firstName + ' ' + data.lastName);
      document.getElementById('paypal-link').href = paypalUrl;
      setTimeout(function() { window.location.href = paypalUrl; }, 3000);
    })
    .catch(function(err) {
      alert('There was an error submitting your application. Please try again or contact info@lowermsfoundation.org');
      btn.disabled = false;
      btn.textContent = 'Submit Application';
    });
  });
})();
</script>
</div></div>'''

new_content = content[:form_block_start] + new_form + content[form_end:]

with open(r'C:\Users\scott\lmrf\website\site\camp-application.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f'Form replaced. Old: {form_end - form_block_start} bytes, New: {len(new_form)} bytes.')
