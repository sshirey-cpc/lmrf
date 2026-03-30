"""Send confirmation emails to existing applicants who didn't get one."""
import base64
import json
from email.mime.text import MIMEText
from googleapiclient.discovery import build
import google.auth

SENDER_EMAIL = "info@lowermsfoundation.org"

def get_gmail():
    credentials, project = google.auth.default(
        scopes=["https://www.googleapis.com/auth/gmail.send"]
    )
    delegated = credentials.with_subject(SENDER_EMAIL)
    return build("gmail", "v1", credentials=delegated)

def send_email(gmail, to, cc, subject, html):
    msg = MIMEText(html, "html")
    msg["From"] = f"LMRF <{SENDER_EMAIL}>"
    msg["To"] = to
    if cc:
        msg["Cc"] = cc
    msg["Subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"  Sent to {to}" + (f" (cc: {cc})" if cc else ""))

gmail = get_gmail()

# 1. Camp application - Abe Hudson
print("Sending camp confirmation to Abe Hudson...")
camp_html = """
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <h2 style="color:#2c5f2d;">Welcome to the Adventure!</h2>
  <p>Thank you for applying to the <strong>Mississippi River Adventure Camp</strong>! We're excited that Abe wants to join us on the river this summer.</p>
  <p>We've received your application and will be in touch soon with next steps.</p>
  <p>To secure your spot, please pay the <strong>$25 deposit</strong> within 30 days:</p>
  <p style="text-align:center;margin:24px 0;">
    <a href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=7F349QJ9M274Y&item_name=Adventure+Camp+Deposit+-+%2425" style="display:inline-block;padding:14px 36px;background:#d48b3e;color:#fff;text-decoration:none;border-radius:25px;font-size:16px;font-weight:600;">Pay $25 Deposit via PayPal</a>
  </p>
  <p>Questions? Contact Abe Hudson at 662-822-9984 or <a href="mailto:info@lowermsfoundation.org" style="color:#d48b3e;">info@lowermsfoundation.org</a></p>
  <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
  <p style="font-size:12px;color:#999;">Lower Mississippi River Foundation<br>PO Box 127, Helena, AR 72342<br>(870) 228-2421</p>
</div>
"""
send_email(gmail, "abe@therealdelta.com", "abeemhudson@icloud.com",
           "Welcome to the Adventure! - Mississippi River Adventure Camp", camp_html)

# 2. Canoe signup - Abe Hudson
print("Sending canoe confirmation to Abe Hudson...")
canoe_html = """
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <h2 style="color:#2c5f2d;">You're All Set!</h2>
  <p>Thank you for signing up for the <strong>Community Canoe Trip</strong>! We're excited to have you join us on the river.</p>
  <p><strong>Trip Date:</strong> April 24 - Helena, AR<br>
  <strong>Participants:</strong> 2</p>
  <p>We'll confirm your reservation via email. Please remember:</p>
  <ul style="color:#444;line-height:1.8;">
    <li>Reservations required - 18 max, first come first served</li>
    <li>Pack water bottles, snacks, sun/bug protection, and shoes that can get wet</li>
    <li>Pack electronics in dry bags or zip lock bags</li>
    <li>Dress for possible rainy weather</li>
  </ul>
  <p>Questions? Contact John Ruskey at (662) 902-7841 or Ceili Hale at (601) 918-6810.</p>
  <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
  <p style="font-size:12px;color:#999;">Community Canoe Trips are made possible by the Lower Mississippi River Foundation.<br>PO Box 127, Helena, AR 72342 | (870) 228-2421<br><a href="https://www.lowermsfoundation.org/donate" style="color:#d48b3e;">Support our mission with a donation</a></p>
</div>
"""
send_email(gmail, "abe@therealdelta.com", None,
           "You're All Set! - Community Canoe Trip", canoe_html)

print("\nDone!")
