"""
PayPal → BigQuery sync + thank-you emails.
Pulls donation transactions from PayPal REST API, upserts into BigQuery,
sends thank-you emails to donors, and notifies info@lowermsfoundation.org.
Triggered by Cloud Scheduler (every 15 minutes).
"""

import base64
import json
import uuid
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

import functions_framework
import requests
from google.cloud import bigquery, secretmanager
from googleapiclient.discovery import build

PROJECT_ID = "balmy-limiter-491013-a8"
DATASET = "lmrf_donations"
PAYPAL_API = "https://api-m.paypal.com"
SENDER_EMAIL = "info@lowermsfoundation.org"
NOTIFY_EMAIL = "info@lowermsfoundation.org"


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
        headers={"Accept": "application/json"},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_transactions(token, start_date, end_date):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    all_transactions = []
    page = 1
    while True:
        params = {
            "start_date": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_date": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "fields": "all",
            "page_size": 100,
            "page": page,
        }
        resp = requests.get(
            f"{PAYPAL_API}/v1/reporting/transactions",
            headers=headers,
            params=params,
        )
        if resp.status_code == 403:
            print(f"PayPal 403 response: {resp.text}")
            print("Transaction Search API may not be enabled. Check PayPal Developer Dashboard → App → Features.")
            resp.raise_for_status()
        resp.raise_for_status()
        data = resp.json()
        transactions = data.get("transaction_details", [])
        if not transactions:
            break
        all_transactions.extend(transactions)
        total_pages = data.get("total_pages", 1)
        if page >= total_pages:
            break
        page += 1
    return all_transactions


def parse_transaction(txn):
    info = txn.get("transaction_info", {})
    payer = txn.get("payer_info", {})
    payer_name = payer.get("payer_name", {})

    name_parts = []
    if payer_name.get("given_name"):
        name_parts.append(payer_name["given_name"])
    if payer_name.get("surname"):
        name_parts.append(payer_name["surname"])
    donor_name = " ".join(name_parts) if name_parts else "Anonymous"

    amount_obj = info.get("transaction_amount", {})
    amount = float(amount_obj.get("value", 0))
    if amount <= 0:
        return None

    txn_date = info.get("transaction_initiation_date", "")
    if txn_date:
        txn_date = txn_date.replace("+0000", "+00:00")

    subscription_id = info.get("paypal_reference_id", "")
    is_recurring = info.get("paypal_reference_id_type") == "SUB"

    return {
        "transaction_id": info.get("transaction_id", ""),
        "donor_email": payer.get("email_address", ""),
        "donor_name": donor_name,
        "amount": amount,
        "currency": amount_obj.get("currency_code", "USD"),
        "status": info.get("transaction_status", ""),
        "transaction_date": txn_date,
        "payment_source": info.get("payment_tracking_id", ""),
        "is_recurring": is_recurring,
        "subscription_id": subscription_id,
        "raw_json": json.dumps(txn),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def upsert_donor(bq_client, row):
    query = f"""
    MERGE `{PROJECT_ID}.{DATASET}.donors` AS target
    USING (SELECT @email AS donor_email, @name AS donor_name,
                  @date AS txn_date, @amount AS amount,
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
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email", "STRING", row["donor_email"]),
                bigquery.ScalarQueryParameter("name", "STRING", row["donor_name"]),
                bigquery.ScalarQueryParameter("date", "TIMESTAMP", row["transaction_date"]),
                bigquery.ScalarQueryParameter("amount", "FLOAT64", row["amount"]),
                bigquery.ScalarQueryParameter("is_recurring", "BOOL", row["is_recurring"]),
            ]
        ),
    ).result()


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
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False


def send_thank_you(service, donor_name, donor_email, amount):
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
    return send_email(service, donor_email, subject, body)


def send_notification(service, donor_name, donor_email, amount, is_recurring):
    """Notify LMRF staff about new donation."""
    recurring_label = " (RECURRING)" if is_recurring else ""
    subject = f"New Donation: ${amount:.2f} from {donor_name}{recurring_label}"
    body = f"""New donation received!

Donor: {donor_name}
Email: {donor_email}
Amount: ${amount:.2f}
Type: {"Recurring" if is_recurring else "One-time"}
Date: {datetime.now(timezone.utc).strftime("%B %d, %Y at %I:%M %p UTC")}

This donation has been logged to BigQuery and a thank-you email has been sent to the donor.
"""
    return send_email(service, NOTIFY_EMAIL, subject, body)


def log_email_sent(bq_client, donor_email, donor_name, email_type, subject, txn_id):
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
def paypal_sync(request):
    """Main entry point — triggered by Cloud Scheduler every 15 minutes."""
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=2)

        token = get_paypal_token()
        transactions = fetch_transactions(token, start_date, end_date)

        bq_client = bigquery.Client(project=PROJECT_ID)
        table_ref = f"{PROJECT_ID}.{DATASET}.transactions"

        # Try to init Gmail service (may fail if not configured yet)
        gmail = None
        try:
            gmail = get_gmail_service()
        except Exception as e:
            print(f"Gmail not configured yet, skipping emails: {e}")

        inserted = 0
        for txn in transactions:
            row = parse_transaction(txn)
            if not row:
                continue

            # Skip duplicates
            dup_check = bq_client.query(
                f"SELECT 1 FROM `{table_ref}` WHERE transaction_id = @txn_id LIMIT 1",
                job_config=bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("txn_id", "STRING", row["transaction_id"])
                    ]
                ),
            ).result()
            if dup_check.total_rows > 0:
                continue

            errors = bq_client.insert_rows_json(table_ref, [row])
            if errors:
                print(f"BigQuery insert error: {errors}")
                continue

            upsert_donor(bq_client, row)
            inserted += 1

            # Send thank-you email to donor
            if gmail and row["donor_email"]:
                thank_you_subject = "Thank You for Your Generous Donation!"
                if send_thank_you(gmail, row["donor_name"], row["donor_email"], row["amount"]):
                    log_email_sent(bq_client, row["donor_email"], row["donor_name"],
                                  "thank_you", thank_you_subject, row["transaction_id"])

                # Notify LMRF staff
                send_notification(gmail, row["donor_name"], row["donor_email"],
                                 row["amount"], row["is_recurring"])

        msg = f"PayPal sync complete: {len(transactions)} fetched, {inserted} new transactions inserted."
        print(msg)
        return msg, 200

    except Exception as e:
        print(f"PayPal sync error: {e}")
        return f"Error: {e}", 500
