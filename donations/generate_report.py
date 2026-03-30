"""Generate LMRF Donation Report for the board."""
import subprocess, os, json, csv
from datetime import datetime

BQ_ENV = os.environ.copy()
BQ_ENV["CLOUDSDK_PYTHON"] = r"C:\Users\scott\AppData\Local\Google\Cloud SDK\google-cloud-sdk\platform\bundledpython\python.exe"
BQ_CMD = r"C:\Users\scott\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\bq.cmd"
P = "balmy-limiter-491013-a8"
D = "lmrf_donations"

def bq(sql):
    r = subprocess.run([BQ_CMD, "query", "--use_legacy_sql=false", "--format=json", "--max_rows=1000", sql],
                       capture_output=True, text=True, env=BQ_ENV)
    if r.returncode != 0:
        print(f"BQ ERROR: {r.stderr[:200]}")
        return []
    try:
        return json.loads(r.stdout) if r.stdout.strip() else []
    except json.JSONDecodeError:
        print(f"JSON ERROR: {r.stdout[:200]}")
        return []

# Pull data
yearly = bq(f"SELECT CAST(EXTRACT(YEAR FROM transaction_date) AS STRING) as year, ROUND(SUM(amount),2) as total, COUNT(*) as gifts, COUNT(DISTINCT donor_email) as donors FROM `{P}.{D}.transactions` GROUP BY year ORDER BY year")
monthly = bq(f"SELECT FORMAT_TIMESTAMP('%Y-%m', transaction_date) as month, ROUND(SUM(amount),2) as total, COUNT(*) as gifts FROM `{P}.{D}.transactions` WHERE transaction_date >= TIMESTAMP('2025-04-01') GROUP BY month ORDER BY month")
donors = bq(f"SELECT donor_name, donor_email, total_donated, donation_count, first_donation_date, last_donation_date, is_recurring FROM `{P}.{D}.donors` ORDER BY total_donated DESC")
recurring = [d for d in donors if d.get("is_recurring")]
one_time = [d for d in donors if not d.get("is_recurring")]

report_date = datetime.now().strftime("%B %d, %Y")
report_file = os.path.expanduser("~/lmrf/donations/LMRF_Donation_Report.csv")

# Write CSV
with open(report_file, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)

    w.writerow(["LMRF Donation Report"])
    w.writerow([f"Generated: {report_date}"])
    w.writerow([])

    # Summary
    total_amt = sum(float(d["total_donated"]) for d in donors)
    w.writerow(["SUMMARY"])
    w.writerow(["Total Donations (3 years)", f"${total_amt:,.2f}"])
    w.writerow(["Total Transactions", sum(int(d["donation_count"]) for d in donors)])
    w.writerow(["Unique Donors", len(donors)])
    w.writerow(["Recurring Donors", len(recurring)])
    w.writerow(["One-Time Donors", len(one_time)])
    w.writerow([])

    # Yearly
    w.writerow(["DONATIONS BY YEAR"])
    w.writerow(["Year", "Total", "Transactions", "Unique Donors"])
    for y in yearly:
        w.writerow([y["year"], f"${float(y['total']):,.2f}", y["gifts"], y["donors"]])
    w.writerow([])

    # Monthly (last 12)
    w.writerow(["MONTHLY TREND (Last 12 Months)"])
    w.writerow(["Month", "Total", "Transactions"])
    for m in monthly:
        w.writerow([m["month"], f"${float(m['total']):,.2f}", m["gifts"]])
    w.writerow([])

    # All donors
    w.writerow(["ALL DONORS"])
    w.writerow(["Name", "Email", "Total Donated", "# Gifts", "First Gift", "Last Gift", "Recurring"])
    for d in donors:
        w.writerow([
            d["donor_name"],
            d["donor_email"],
            f"${float(d['total_donated']):,.2f}",
            d["donation_count"],
            d["first_donation_date"][:10] if d.get("first_donation_date") else "",
            d["last_donation_date"][:10] if d.get("last_donation_date") else "",
            "Yes" if d.get("is_recurring") else "No",
        ])

print(f"Report saved: {report_file}")
print(f"\nYou can open this in Excel or Google Sheets.")
