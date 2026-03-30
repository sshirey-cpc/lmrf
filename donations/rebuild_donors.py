"""Rebuild donors table from transactions."""
import subprocess, os, json

BQ_ENV = os.environ.copy()
BQ_ENV["CLOUDSDK_PYTHON"] = r"C:\Users\scott\AppData\Local\Google\Cloud SDK\google-cloud-sdk\platform\bundledpython\python.exe"
BQ_CMD = r"C:\Users\scott\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\bq.cmd"

PROJECT = "balmy-limiter-491013-a8"
DATASET = "lmrf_donations"

def bq(sql):
    r = subprocess.run([BQ_CMD, "query", "--use_legacy_sql=false", "--format=json", sql],
                       capture_output=True, text=True, env=BQ_ENV)
    if r.returncode != 0:
        print(f"ERROR: {r.stderr[:300]}")
    try:
        return json.loads(r.stdout) if r.stdout.strip() else []
    except json.JSONDecodeError:
        return []

# Rebuild donors
bq(f"""
CREATE OR REPLACE TABLE `{PROJECT}.{DATASET}.donors` AS
SELECT
    donor_email,
    ANY_VALUE(donor_name) AS donor_name,
    MIN(transaction_date) AS first_donation_date,
    MAX(transaction_date) AS last_donation_date,
    ROUND(SUM(amount),2) AS total_donated,
    COUNT(*) AS donation_count,
    LOGICAL_OR(is_recurring) AS is_recurring,
    MIN(created_at) AS created_at,
    CURRENT_TIMESTAMP() AS updated_at
FROM `{PROJECT}.{DATASET}.transactions`
WHERE donor_email IS NOT NULL AND donor_email != ''
GROUP BY donor_email
""")

# Summary
txn = bq(f"SELECT COUNT(*) as cnt FROM `{PROJECT}.{DATASET}.transactions`")
donors = bq(f"SELECT COUNT(*) as cnt FROM `{PROJECT}.{DATASET}.donors`")
total = bq(f"SELECT ROUND(SUM(amount),2) as total FROM `{PROJECT}.{DATASET}.transactions`")
recurring = bq(f"SELECT COUNT(*) as cnt FROM `{PROJECT}.{DATASET}.donors` WHERE is_recurring = true")
top = bq(f"SELECT donor_name, total_donated, donation_count FROM `{PROJECT}.{DATASET}.donors` ORDER BY total_donated DESC LIMIT 10")

print(f"\n--- Donor Database Summary ---")
print(f"Total transactions: {txn[0]['cnt'] if txn else '?'}")
print(f"Unique donors: {donors[0]['cnt'] if donors else '?'}")
print(f"Total donated: ${total[0]['total'] if total else '?'}")
print(f"Recurring donors: {recurring[0]['cnt'] if recurring else '?'}")
print(f"\nTop 10 donors:")
for d in (top or []):
    print(f"  {d['donor_name']:30s} ${float(d['total_donated']):>10.2f}  ({d['donation_count']} gifts)")
