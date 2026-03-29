"""
Quick test to check if PayPal Transaction Search permissions are active.
Set env vars first:
  export PAYPAL_CLIENT_ID=your_client_id
  export PAYPAL_SECRET=your_secret
Run: python ~/lmrf/donations/test_paypal.py
"""
import os
import requests

CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
SECRET = os.environ.get("PAYPAL_SECRET", "")

resp = requests.post(
    "https://api-m.paypal.com/v1/oauth2/token",
    auth=(CLIENT_ID, SECRET),
    data={"grant_type": "client_credentials"},
)
token = resp.json().get("access_token", "")
scopes = resp.json().get("scope", "")

resp2 = requests.get(
    "https://api-m.paypal.com/v1/reporting/transactions",
    headers={"Authorization": f"Bearer {token}"},
    params={
        "start_date": "2026-03-26T00:00:00Z",
        "end_date": "2026-03-27T23:59:59Z",
        "fields": "all",
        "page_size": 10,
        "page": 1,
    },
)

if resp2.status_code == 200:
    data = resp2.json()
    print(f"SUCCESS! Transaction Search is working.")
    print(f"Transactions found: {data.get('total_items', 0)}")
    print(f"\nRun this to resume the scheduler:")
    print(f"  gcloud scheduler jobs resume paypal-sync-job --location=us-central1 --project=balmy-limiter-491013-a8")
else:
    print(f"Not ready yet (status {resp2.status_code}). PayPal permissions still propagating.")
    print(f"Try again in a few hours.")
