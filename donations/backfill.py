"""
Historical backfill: Pull 3 years of PayPal transactions into BigQuery.
Uses bq CLI to insert rows (avoids ADC setup issues).
PayPal limits each query to 31 days, so we chunk into monthly windows.
"""

import json
import os
import subprocess
import tempfile
import time
from datetime import datetime, timedelta, timezone

import requests

PROJECT_ID = "balmy-limiter-491013-a8"
DATASET = "lmrf_donations"
PAYPAL_API = "https://api-m.paypal.com"
CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
SECRET = os.environ.get("PAYPAL_SECRET", "")

BQ_ENV = os.environ.copy()
BQ_ENV["CLOUDSDK_PYTHON"] = "C:\\Users\\scott\\AppData\\Local\\Google\\Cloud SDK\\google-cloud-sdk\\platform\\bundledpython\\python.exe"
BQ_CMD = "C:\\Users\\scott\\AppData\\Local\\Google\\Cloud SDK\\google-cloud-sdk\\bin\\bq.cmd"


def get_token():
    resp = requests.post(
        f"{PAYPAL_API}/v1/oauth2/token",
        auth=(CLIENT_ID, SECRET),
        data={"grant_type": "client_credentials"},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_transactions(token, start_date, end_date):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    all_txns = []
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
        if resp.status_code == 429:
            print("  Rate limited, waiting 30s...")
            time.sleep(30)
            continue
        resp.raise_for_status()
        data = resp.json()
        txns = data.get("transaction_details", [])
        if not txns:
            break
        all_txns.extend(txns)
        total_pages = data.get("total_pages", 1)
        if page >= total_pages:
            break
        page += 1
        time.sleep(1)
    return all_txns


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
        "transaction_date": txn_date if txn_date else datetime.now(timezone.utc).isoformat(),
        "payment_source": info.get("payment_tracking_id", ""),
        "is_recurring": is_recurring,
        "subscription_id": subscription_id or "",
        "raw_json": json.dumps(txn),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def bq_insert_rows(rows):
    """Insert rows into BigQuery using bq CLI with newline-delimited JSON."""
    if not rows:
        return 0
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
        tmpfile = f.name

    try:
        result = subprocess.run(
            [BQ_CMD, "load", "--source_format=NEWLINE_DELIMITED_JSON",
             f"{PROJECT_ID}:{DATASET}.transactions", tmpfile],
            capture_output=True, text=True, env=BQ_ENV
        )
        if result.returncode != 0:
            print(f"  bq load error: {result.stderr[:200]}")
            return 0
        return len(rows)
    finally:
        os.unlink(tmpfile)


def bq_query(sql):
    """Run a BigQuery query via bq CLI."""
    result = subprocess.run(
        [BQ_CMD, "query", "--use_legacy_sql=false", "--format=json", sql],
        capture_output=True, text=True, env=BQ_ENV
    )
    if result.returncode != 0:
        print(f"  bq query error: {result.stderr[:200]}")
        return []
    try:
        return json.loads(result.stdout) if result.stdout.strip() else []
    except json.JSONDecodeError:
        return []


def main():
    print("Starting 3-year historical backfill...")
    token = get_token()

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=3 * 365)

    window_start = start
    total_inserted = 0
    total_fetched = 0

    while window_start < end:
        window_end = min(window_start + timedelta(days=31), end)
        period = f"{window_start.strftime('%Y-%m-%d')} to {window_end.strftime('%Y-%m-%d')}"
        print(f"\nFetching: {period}")

        try:
            txns = fetch_transactions(token, window_start, window_end)
        except requests.exceptions.HTTPError as e:
            if "401" in str(e):
                print("  Token expired, refreshing...")
                token = get_token()
                txns = fetch_transactions(token, window_start, window_end)
            else:
                print(f"  Error: {e}")
                window_start = window_end
                continue

        print(f"  Found {len(txns)} transactions")
        total_fetched += len(txns)

        batch = []
        for txn in txns:
            row = parse_transaction(txn)
            if row:
                batch.append(row)

        if batch:
            inserted = bq_insert_rows(batch)
            total_inserted += inserted
            if inserted:
                print(f"  Inserted {inserted} donations")

        window_start = window_end
        time.sleep(2)

    print(f"\n--- Backfill complete ---")
    print(f"Total fetched: {total_fetched}")
    print(f"Total inserted: {total_inserted}")

    # Rebuild donors table
    print(f"\nRebuilding donors table...")
    bq_query(f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.donors` AS
    SELECT
        donor_email,
        ANY_VALUE(donor_name) AS donor_name,
        MIN(transaction_date) AS first_donation_date,
        MAX(transaction_date) AS last_donation_date,
        SUM(amount) AS total_donated,
        COUNT(*) AS donation_count,
        LOGICAL_OR(is_recurring) AS is_recurring,
        MIN(created_at) AS created_at,
        CURRENT_TIMESTAMP() AS updated_at
    FROM `{PROJECT_ID}.{DATASET}.transactions`
    WHERE donor_email != ''
    GROUP BY donor_email
    """)

    # Count results
    result = bq_query(f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET}.transactions`")
    txn_count = result[0]["cnt"] if result else "?"
    result = bq_query(f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET}.donors`")
    donor_count = result[0]["cnt"] if result else "?"
    print(f"Transactions: {txn_count}")
    print(f"Unique donors: {donor_count}")
    print("Done! You can now open this in Connected Sheets.")


if __name__ == "__main__":
    main()
