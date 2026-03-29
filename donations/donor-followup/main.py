"""
Donor follow-up automation.
Runs weekly via Cloud Scheduler.
- First-time donors: welcome + impact message
- Recurring donors: giving summary + impact update
"""

import base64
import json
import uuid
from datetime import datetime, timezone
from email.mime.text import MIMEText

import functions_framework
from google.cloud import bigquery, secretmanager
from googleapiclient.discovery import build

PROJECT_ID = "balmy-limiter-491013-a8"
DATASET = "lmrf_donations"
SENDER_EMAIL = "info@lowermsfoundation.org"


def get_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def get_gmail_service():
    import google.auth
    credentials, project = google.auth.default(
        scopes=["https://www.googleapis.com/auth/gmail.send"]
    )
    delegated = credentials.with_subject(SENDER_EMAIL)
    return build("gmail", "v1", credentials=delegated)


def send_email(service, to_email, subject, body_text):
    message = MIMEText(body_text)
    message["to"] = to_email
    message["from"] = SENDER_EMAIL
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        print(f"Sent follow-up to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send to {to_email}: {e}")
        return False


def log_email(bq_client, donor_email, donor_name, email_type, subject):
    row = {
        "email_id": str(uuid.uuid4()),
        "donor_email": donor_email,
        "donor_name": donor_name,
        "email_type": email_type,
        "subject": subject,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "transaction_id": "",
    }
    bq_client.insert_rows_json(f"{PROJECT_ID}.{DATASET}.emails_sent", [row])


def build_first_time_email(donor_name, amount):
    first_name = donor_name.split()[0] if donor_name and donor_name != "Anonymous" else "Friend"
    return f"""Dear {first_name},

We wanted to follow up and say thank you once more for your recent gift of ${amount:.2f} to the Lower Mississippi River Foundation. As a first-time donor, we want you to know just how much your support means to us.

Here's a glimpse of what your donation helps make possible:

  - Our Summer Leadership Camp takes students on four-day canoe voyages down the Mississippi, building confidence, teamwork, and environmental awareness. Many of these young people have never experienced the river despite living just miles from its banks.

  - Our River Stewards program engages youth year-round in learning about river health, planning community events, and becoming advocates for the Mississippi.

  - Our school programs bring hands-on river education directly into classrooms across the Arkansas and Mississippi Delta.

Your gift helps us continue this important work. We'd love for you to stay connected:

  - Visit our website: lowermsfoundation.org
  - Follow us on Facebook for photos and updates
  - Consider becoming a monthly supporter to provide sustained impact

Thank you for investing in the future of the Lower Mississippi River.

Warmly,

The Lower Mississippi River Foundation
PO Box 127 | Helena, AR 72342
(870) 228-2421 | info@lowermsfoundation.org
"""


def build_recurring_email(donor_name, total_donated, donation_count, months_giving):
    first_name = donor_name.split()[0] if donor_name and donor_name != "Anonymous" else "Friend"
    return f"""Dear {first_name},

Thank you for being a sustaining supporter of the Lower Mississippi River Foundation! We wanted to share a quick update on your giving and the impact it's making.

Your Giving Summary:
  - Total contributions: ${total_donated:.2f}
  - Number of gifts: {donation_count}

Your consistent generosity provides the stable foundation we need to plan and deliver our programs with confidence. Here's what we've been up to recently:

  - Summer Leadership Camp preparations are underway for 2026, with trips planned for both girls and boys in late May and early June.

  - Our River Stewards continue to meet after school, learning about river ecology and planning community engagement events.

  - We're expanding our reach to connect even more Delta youth with the river through school partnerships.

None of this would be possible without dedicated supporters like you. Thank you for standing with us.

If you'd like to get more involved — whether volunteering, attending an event, or spreading the word — we'd love to hear from you.

With deep appreciation,

The Lower Mississippi River Foundation
PO Box 127 | Helena, AR 72342
(870) 228-2421 | info@lowermsfoundation.org
"""


@functions_framework.http
def donor_followup(request):
    """Weekly follow-up processor."""
    try:
        bq_client = bigquery.Client(project=PROJECT_ID)
        gmail = get_gmail_service()

        # Find first-time donors from the past 7 days who haven't received a follow-up
        first_time_query = f"""
        SELECT d.donor_email, d.donor_name, d.total_donated
        FROM `{PROJECT_ID}.{DATASET}.donors` d
        WHERE d.donation_count = 1
          AND d.first_donation_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
          AND d.donor_email != ''
          AND d.donor_email NOT IN (
            SELECT e.donor_email FROM `{PROJECT_ID}.{DATASET}.emails_sent` e
            WHERE e.email_type = 'first_time_followup'
          )
        """
        first_timers = list(bq_client.query(first_time_query).result())
        print(f"Found {len(first_timers)} first-time donors for follow-up")

        for row in first_timers:
            subject = "Your Impact on the Mississippi River"
            body = build_first_time_email(row.donor_name, row.total_donated)
            if send_email(gmail, row.donor_email, subject, body):
                log_email(bq_client, row.donor_email, row.donor_name,
                         "first_time_followup", subject)

        # Find recurring donors who haven't received a summary in 30 days
        recurring_query = f"""
        SELECT d.donor_email, d.donor_name, d.total_donated, d.donation_count,
               d.first_donation_date,
               TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), d.first_donation_date, DAY) AS days_giving
        FROM `{PROJECT_ID}.{DATASET}.donors` d
        WHERE d.is_recurring = TRUE
          AND d.donation_count > 1
          AND d.donor_email != ''
          AND d.donor_email NOT IN (
            SELECT e.donor_email FROM `{PROJECT_ID}.{DATASET}.emails_sent` e
            WHERE e.email_type = 'recurring_summary'
              AND e.sent_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
          )
        """
        recurring = list(bq_client.query(recurring_query).result())
        print(f"Found {len(recurring)} recurring donors for summary")

        for row in recurring:
            months = max(1, row.days_giving // 30)
            subject = "Your Giving Impact — A Quick Update"
            body = build_recurring_email(row.donor_name, row.total_donated,
                                         row.donation_count, months)
            if send_email(gmail, row.donor_email, subject, body):
                log_email(bq_client, row.donor_email, row.donor_name,
                         "recurring_summary", subject)

        total = len(first_timers) + len(recurring)
        msg = f"Follow-up complete: {len(first_timers)} first-time, {len(recurring)} recurring donors contacted."
        print(msg)
        return msg, 200

    except Exception as e:
        print(f"Follow-up error: {e}")
        return f"Error: {e}", 500
