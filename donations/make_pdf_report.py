"""Generate one-page LMRF Donation Summary PDF for board meeting."""
import json, os
from fpdf import FPDF
from datetime import datetime

with open(os.path.expanduser("~/lmrf/donations/lmrf_data.json")) as f:
    data = json.load(f)

yearly = data["yearly"]
monthly = data["monthly"]
donors = data["donors"]
recurring = data["recurring"]
onetime = data["onetime"]
total_amt = sum(float(d["total_donated"]) for d in donors)
total_txn = sum(int(d["donation_count"]) for d in donors)
total_donors = len(donors)

pdf = FPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=False)

# Header
pdf.set_font("Helvetica", "B", 18)
pdf.cell(0, 10, "Lower Mississippi River Foundation", new_x="LMARGIN", new_y="NEXT", align="C")
pdf.set_font("Helvetica", "", 12)
pdf.cell(0, 7, "Donation Summary Report", new_x="LMARGIN", new_y="NEXT", align="C")
pdf.set_font("Helvetica", "", 9)
pdf.cell(0, 5, f"Generated {datetime.now().strftime('%B %d, %Y')}  |  Data: PayPal (3 years)", new_x="LMARGIN", new_y="NEXT", align="C")
pdf.ln(4)

# Summary boxes
pdf.set_fill_color(245, 240, 230)
box_w = 45
pdf.set_font("Helvetica", "B", 11)
x_start = 10
for label, val in [("Total Raised", f"${total_amt:,.2f}"), ("Transactions", str(total_txn)), ("Unique Donors", str(total_donors)), ("Recurring", str(recurring))]:
    pdf.set_xy(x_start, pdf.get_y())
    pdf.cell(box_w, 7, label, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(x_start, pdf.get_y())
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(box_w, 9, val, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_xy(x_start + box_w + 2, pdf.get_y() - 16)
    x_start += box_w + 2
pdf.set_y(pdf.get_y() + 18)
pdf.ln(2)

# Donations by Year
pdf.set_font("Helvetica", "B", 11)
pdf.cell(0, 7, "Donations by Year", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "B", 8)
pdf.set_fill_color(210, 139, 62)
pdf.set_text_color(255, 255, 255)
pdf.cell(25, 6, "Year", border=1, fill=True, align="C")
pdf.cell(35, 6, "Total", border=1, fill=True, align="C")
pdf.cell(30, 6, "Transactions", border=1, fill=True, align="C")
pdf.cell(30, 6, "Donors", border=1, fill=True, align="C")
pdf.ln()
pdf.set_text_color(0, 0, 0)
pdf.set_font("Helvetica", "", 8)
for y in yearly:
    note = " (Q1)" if y["year"] == "2026" else ""
    pdf.cell(25, 5, y["year"] + note, border=1, align="C")
    pdf.cell(35, 5, f"${float(y['total']):,.2f}", border=1, align="R")
    pdf.cell(30, 5, y["gifts"], border=1, align="C")
    pdf.cell(30, 5, y["donors"], border=1, align="C")
    pdf.ln()
pdf.ln(3)

# Monthly trend
pdf.set_font("Helvetica", "B", 11)
pdf.cell(0, 7, "Monthly Trend (Last 12 Months)", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "B", 8)
pdf.set_fill_color(210, 139, 62)
pdf.set_text_color(255, 255, 255)
pdf.cell(25, 6, "Month", border=1, fill=True, align="C")
pdf.cell(30, 6, "Total", border=1, fill=True, align="C")
pdf.cell(25, 6, "Gifts", border=1, fill=True, align="C")
pdf.ln()
pdf.set_text_color(0, 0, 0)
pdf.set_font("Helvetica", "", 8)
for m in monthly:
    pdf.cell(25, 5, m["month"], border=1, align="C")
    pdf.cell(30, 5, f"${float(m['total']):,.2f}", border=1, align="R")
    pdf.cell(25, 5, m["gifts"], border=1, align="C")
    pdf.ln()
pdf.ln(3)

# Top donors (fit remaining space)
pdf.set_font("Helvetica", "B", 11)
pdf.cell(0, 7, "Top Donors", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "B", 8)
pdf.set_fill_color(210, 139, 62)
pdf.set_text_color(255, 255, 255)
pdf.cell(55, 6, "Name", border=1, fill=True)
pdf.cell(28, 6, "Total", border=1, fill=True, align="C")
pdf.cell(18, 6, "Gifts", border=1, fill=True, align="C")
pdf.cell(22, 6, "Type", border=1, fill=True, align="C")
pdf.ln()
pdf.set_text_color(0, 0, 0)
pdf.set_font("Helvetica", "", 8)
remaining = 280 - pdf.get_y()
max_rows = min(int(remaining / 5), len(donors))
for d in donors[:max_rows]:
    dtype = "Recurring" if d.get("is_recurring") is True or d.get("is_recurring") == "true" else "One-time"
    name = d["donor_name"][:28]
    pdf.cell(55, 5, name, border=1)
    pdf.cell(28, 5, f"${float(d['total_donated']):,.2f}", border=1, align="R")
    pdf.cell(18, 5, d["donation_count"], border=1, align="C")
    pdf.cell(22, 5, dtype, border=1, align="C")
    pdf.ln()

# Footer
pdf.set_y(282)
pdf.set_font("Helvetica", "I", 7)
pdf.cell(0, 4, "Source: PayPal Transaction API  |  Data auto-syncs every 15 minutes to BigQuery  |  info@lowermsfoundation.org", align="C")

out = os.path.expanduser("~/lmrf/donations/LMRF_Donation_Summary.pdf")
pdf.output(out)
print(f"PDF saved: {out}")
