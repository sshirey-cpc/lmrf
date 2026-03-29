"""
PayPal webhook handler — real-time donation processing.
Receives PAYMENT.SALE.COMPLETED events, logs to BigQuery,
and sends a personalized thank-you email via Gmail API.
"""

import base64
import json
import uuid
from datetime import datetime, timezone
from email.mime.text import MIMEText

import functions_framework
import requests
from google.cloud import bigquery, secretmanager
from google.oauth2 import service_account
from googleapiclient.discovery import build

PROJECT_ID = "balmy-limiter-491013-a8"
DATASET = "lmrf_donations"
PAYPAL_API = "https://api-m.paypal.com"
SENDER_EMAIL = "info@lowermsfoundation.org"


def get_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def get_paypal_token():
    client_id = get_secret("paypal-client-id")
    client_secret = get_secret("paypal-secret")
    resp = requests.post(
        f"{PAYPAL_API}/v1/oauth2/token",
        auth=(client_id, client_secret),
        data={"grant_type": "client_credentials"},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def verify_webhook(headers, body, webhook_id):
    """Verify PayPal webhook signature."""
    token = get_paypal_token()
    verification = {
        "auth_algo": headers.get("PAYPAL-AUTH-ALGO", ""),
        "cert_url": headers.get("PAYPAL-CERT-URL", ""),
        "transmission_id": headers.get("PAYPAL-TRANSMISSION-ID", ""),
        "transmission_sig": headers.get("PAYPAL-TRANSMISSION-SIG", ""),
        "transmission_time": headers.get("PAYPAL-TRANSMISSION-TIME", ""),
        "webhook_id": webhook_id,
        "webhook_event": body,
    }
    resp = requests.post(
        f"{PAYPAL_API}/v1/notifications/verify-webhook-signature",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=verification,
    )
    if resp.status_code == 200:
        return resp.json().get("verification_status") == "SUCCESS"
    return False


def get_gmail_service():
    """Build Gmail API service using domain-wide delegation."""
    creds_json = get_secret("gmail-service-account")
    creds_info = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/gmail.send"],
        subject=SENDER_EMAIL,
    )
    return build("gmail", "v1", credentials=credentials)


def send_thank_you_email(donor_name, donor_email, amount):
    """Send personalized thank-you email."""
    first_name = donor_name.split()[0] if donor_name and donor_name != "Anonymous" else "Friend"

    subject = "Thank You for Your Generous Donation!"
    body = f"""Dear {first_name},

Thank you so much for your generous donation of ${amount:.2f} to the Lower Mississippi River Foundation!

Your support makes a real difference in our mission to promote stewardship of the Lower and Middle Mississippi River. Because of donors like you, we are able to:

  - Provide educational programs that connect youth to the river
  - Offer summer leadership camps that build confidence and environmental awareness
  - Support River Stewards who actively participate in promoting the health of the river
  - Create opportunities for the community to experience and appreciate the Mississippi

Every dollar you give goes directly toward protecting this incredible natural resource and inspiring the next generation of river stewards.

If you have any questions about your donation or would like to learn more about our programs, please don't hesitate to reach out.

With gratitude,

The Lower Mississippi River Foundation
PO Box 127
Helena, AR 72342
(870) 228-2421
info@lowermsfoundation.org
lowermsfoundation.org
"""

    message = MIMEText(body)
    message["to"] = donor_email
    message["from"] = SENDER_EMAIL
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        service = get_gmail_service()
        service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
        print(f"Thank-you email sent to {donor_email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {donor_email}: {e}")
        return False


def log_transaction(bq_client, txn_id, donor_email, donor_name, amount, is_recurring, subscription_id, raw):
    """Insert transaction into BigQuery."""
    row = {
        "transaction_id": txn_id,
        "donor_email": donor_email,
        "donor_name": donor_name,
        "amount": amount,
        "currency": "USD",
        "status": "COMPLETED",
        "transaction_date": datetime.now(timezone.utc).isoformat(),
        "payment_source": "webhook",
        "is_recurring": is_recurring,
        "subscription_id": subscription_id or "",
        "raw_json": json.dumps(raw),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    table_ref = f"{PROJECT_ID}.{DATASET}.transactions"

    # Skip duplicates
    dup = bq_client.query(
        f"SELECT 1 FROM `{table_ref}` WHERE transaction_id = @txn_id LIMIT 1",
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("txn_id", "STRING", txn_id)]
        ),
    ).result()
    if dup.total_rows > 0:
        return False

    errors = bq_client.insert_rows_json(table_ref, [row])
    if errors:
        print(f"BigQuery insert error: {errors}")
        return False

    # Upsert donor
    upsert_query = f"""
    MERGE `{PROJECT_ID}.{DATASET}.donors` AS target
    USING (SELECT @email AS donor_email, @name AS donor_name,
                  CURRENT_TIMESTAMP() AS txn_date, @amount AS amount,
                  @is_recurring AS is_recurring) AS source
    ON target.donor_email = source.donor_email
    WHEN MATCHED THEN UPDATE SET
        donor_name = source.donor_name,
        last_donation_date = source.txn_date,
        total_donated = target.total_donated + source.amount,
        donation_count = target.donation_count + 1,
        is_recurring = source.is_recurring OR target.is_recurring,
        updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN INSERT
        (donor_email, donor_name, first_donation_date, last_donation_date,
         total_donated, donation_count, is_recurring, created_at, updated_at)
    VALUES
        (source.donor_email, source.donor_name, source.txn_date, source.txn_date,
         source.amount, 1, source.is_recurring, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP())
    """
    bq_client.query(
        upsert_query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", donor_email),
                bigquery.ScalarQueryParameter("name", "STRING", donor_name),
                bigquery.ScalarQueryParameter("amount", "FLOAT64", amount),
                bigquery.ScalarQueryParameter("is_recurring", "BOOL", is_recurring),
            ]
        ),
    ).result()
    return True


def log_email_sent(bq_client, donor_email, donor_name, email_type, subject, txn_id):
    """Track sent emails in BigQuery."""
    row = {
        "email_id": str(uuid.uuid4()),
        "donor_email": donor_email,
        "donor_name": donor_name,
        "email_type": email_type,
        "subject": subject,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "transaction_id": txn_id,
    }
    bq_client.insert_rows_json(f"{PROJECT_ID}.{DATASET}.emails_sent", [row])


@functions_framework.http
def donation_received(request):
    """PayPal webhook endpoint."""
    try:
        body = request.get_json(silent=True)
        if not body:
            return "No payload", 400

        event_type = body.get("event_type", "")
        print(f"Received PayPal webhook: {event_type}")

        # Only process completed payments
        if event_type not in ("PAYMENT.SALE.COMPLETED", "PAYMENT.CAPTURE.COMPLETED"):
            return "Event type ignored", 200

        resource = body.get("resource", {})
        amount = float(resource.get("amount", {}).get("total",
                       resource.get("amount", {}).get("value", 0)))
        if amount <= 0:
            return "Non-positive amount ignored", 200

        # Extract donor info
        payer = resource.get("payer", body.get("resource", {}).get("payer", {}))
        payer_info = payer.get("payer_info", payer)
        donor_email = payer_info.get("email_address", payer_info.get("email", ""))
        payer_name = payer_info.get("name", payer_info.get("payer_name", {}))
        if isinstance(payer_name, dict):
            first = payer_name.get("given_name", payer_name.get("first_name", ""))
            last = payer_name.get("surname", payer_name.get("last_name", ""))
            donor_name = f"{first} {last}".strip()
        else:
            donor_name = str(payer_name)

        if not donor_name:
            donor_name = "Anonymous"

        txn_id = resource.get("id", "")
        subscription_id = resource.get("billing_agreement_id", "")
        is_recurring = bool(subscription_id)

        bq_client = bigquery.Client(project=PROJECT_ID)

        # Log to BigQuery
        is_new = log_transaction(bq_client, txn_id, donor_email, donor_name,
                                 amount, is_recurring, subscription_id, body)

        # Send thank-you email (only for new transactions)
        if is_new and donor_email:
            email_sent = send_thank_you_email(donor_name, donor_email, amount)
            if email_sent:
                log_email_sent(bq_client, donor_email, donor_name, "thank_you",
                              "Thank You for Your Generous Donation!", txn_id)

        return "OK", 200

    except Exception as e:
        print(f"Webhook error: {e}")
        return f"Error: {e}", 500
