from fpdf import FPDF
import os

img_dir = os.path.expanduser("~/lmrf/scrape/pdf-images")
out_path = os.path.expanduser("~/lmrf/scrape/Summer-Camp-Application-2026.pdf")

class CampPDF(FPDF):
    pass

pdf = CampPDF('P', 'mm', 'Letter')
pdf.set_auto_page_break(auto=True, margin=20)

# ─── PAGE 1: Flyer ───
pdf.add_page()

# Title
pdf.set_font("Times", 'B', 38)
pdf.cell(0, 16, "Mississippi River Summer", ln=True, align='C')
pdf.cell(0, 16, "Leadership Camp", ln=True, align='C')

# Date
pdf.ln(2)
pdf.set_font("Times", '', 20)
pdf.cell(0, 9, "Summer 2026", ln=True, align='C')
pdf.set_font("Times", '', 14)
pdf.cell(0, 7, "Trip 1: May 25th - 28th (Girls)", ln=True, align='C')
pdf.cell(0, 7, "Trip 2: June 1st - 4th (Boys)", ln=True, align='C')
pdf.cell(0, 7, "Rain Dates: June 8th - 11th", ln=True, align='C')

# Description
pdf.ln(3)
pdf.set_font("Times", '', 11)
pdf.multi_cell(0, 5,
    "Want to do something different this summer? Join us for an unforgettable experience as "
    "you become part of the crew on a canoe voyage down the Mississippi River. You'll take on new and "
    "exciting challenges, conquer your fears and spend time experiencing the natural beauty of the river.",
    align='C')

# Main photo
pdf.ln(2)
main_img = os.path.join(img_dir, "page1_img1.jpeg")
img_w = 130
x = (215.9 - img_w) / 2
pdf.image(main_img, x=x, w=img_w)

# Three smaller photos in a row
pdf.ln(2)
small_w = 42
margin = 5
total = small_w * 3 + margin * 2
start_x = (215.9 - total) / 2
y = pdf.get_y()

for i, fname in enumerate(["page1_img2.jpeg", "page1_img3.jpeg", "page1_img4.jpeg"]):
    img_path = os.path.join(img_dir, fname)
    xi = start_x + i * (small_w + margin)
    pdf.image(img_path, x=xi, y=y, w=small_w)

# Move below the small images
pdf.set_y(y + 29)

# Contact info
pdf.ln(3)
pdf.set_font("Times", '', 11)
pdf.cell(0, 5, "For more information or to apply, visit", ln=True, align='C')
pdf.set_font("Times", 'B', 11)
pdf.cell(0, 5, "lowermsfoundation.org", ln=True, align='C')
pdf.set_font("Times", '', 11)
pdf.cell(0, 5, "Or contact us", ln=True, align='C')
pdf.cell(0, 5, "Abe Hudson: Camp Leader - 662-822-9984", ln=True, align='C')
pdf.cell(0, 5, "info@lowermsfoundation.org", ln=True, align='C')


# ─── PAGE 2: FAQ ───
pdf.add_page()

pdf.set_font("Times", '', 11)
pdf.multi_cell(0, 5.5,
    "Are you ready to embark on an adventure of a lifetime? On this four day trip, you will be part of the crew "
    "as we travel down the river. Each day we will wake up, cook breakfast, load up the boats and paddle "
    "approximately 20 miles on the river. While on the water you will help maneuver the boat, and learn from "
    "the experienced guides about how to navigate on the water.",
    align='C')

pdf.ln(4)
pdf.multi_cell(0, 5.5,
    "We will stop along the way to go for walks, swims or learn about the wildlife along the Mississippi. You'll "
    "learn how to cook over a fire and set up camp. Each night you'll sleep on beautiful sandy beaches along "
    "the river.",
    align='C')

pdf.ln(6)
pdf.set_font("Times", 'B', 14)
pdf.cell(0, 8, "Frequently Asked Questions", ln=True, align='C')
pdf.ln(2)

# FAQ items
faqs = [
    ("When is the trip?", " Trip 1: May 25th-28th (Girls)    Trip 2: June 1st-4th (Boys)"),
    ("Who is eligible?", " Students in grades 3rd through 11th"),
    ("Do I need any experience?", " No! All experience levels are welcome. Our experienced guides will teach you everything you need to know about how to paddle on the Mighty Mississippi."),
    ("Do I need to know how to swim?", "  No, participants wear life jackets at all times. Our instructors will work with you on improving your swimming while on the trip."),
    ("Is it safe?", " Our number one goal is safety on the water. Our guides are experienced and will show you how to paddle safely.  Life jackets will be provided and will be worn at all times when on the boats."),
    ("What will I need?", " You will need clothes, a rain jacket, sunscreen, a headlamp or flashlight, a hat and two pairs of shoes. We will provide each participant with a tent, sleeping bag and lifejacket. All meals and canoeing equipment will be provided for each participant."),
    ("Can I bring my phone or other electronics?", " We suggest that you do not. Electronics can easily get ruined by the water or sand.  We will have a phone available that you can use to call home if needed. If you do bring electronics with you they should only be used during free time."),
    ("How much does it cost?", "  The cost of the trip is $1000.  Scholarships are available for residents of Arkansas and Mississippi Delta to cover 90% of the cost (Residents pay a $100 fee)"),
    ("How do I sign up?", " Complete the attached form and return to us with your $20 deposit.  As soon as we receive your application and payment your spot on the trip is reserved.  We will send you additional information and forms to fill out. You must return these forms and the remainder of your payment within 30 days of them being mailed."),
]

pdf.set_font("Times", '', 11)
for q, a in faqs:
    pdf.set_font("Times", 'B', 11)
    x_start = pdf.get_x()
    y_start = pdf.get_y()
    # Write bold question inline with regular answer
    pdf.write(5.5, q)
    pdf.set_font("Times", '', 11)
    pdf.write(5.5, a)
    pdf.ln(8)

pdf.ln(4)
pdf.set_font("Times", 'B', 11)
pdf.write(5.5, "Questions:")
pdf.set_font("Times", '', 11)
pdf.write(5.5, " Please send questions to info@lowermsfoundation.org or call 662-822-9984")

pdf.ln(12)
pdf.set_font("Times", 'B', 12)
pdf.cell(0, 6, "Mail completed application and payment to", ln=True, align='C')
pdf.set_font("Times", '', 12)
pdf.cell(0, 6, "Lower Mississippi River Foundation", ln=True, align='C')
pdf.cell(0, 6, "107 Perry St", ln=True, align='C')
pdf.cell(0, 6, "Helena, AR 72342", ln=True, align='C')


# ─── PAGE 3: Application Form ───
pdf.add_page()

pdf.set_font("Times", 'B', 14)
pdf.cell(0, 8, "Application - Mississippi River Summer Leadership Program", ln=True, align='C')
pdf.ln(4)
pdf.set_font("Times", 'B', 12)
pdf.cell(0, 7, "Participant Information", ln=True, align='C')
pdf.ln(2)
pdf.set_font("Times", '', 10)
pdf.multi_cell(0, 5,
    "Return this completed application and your $20 deposit to reserve your spot. We will send you "
    "additional information and forms to fill out when we receive your information. You must return "
    "these forms and the remainder of your payment within 30 days of them being mailed to you.",
    align='C')

pdf.ln(6)

# Form fields
def form_line(label, width=170):
    pdf.set_font("Times", '', 11)
    label_w = pdf.get_string_width(label) + 2
    pdf.cell(label_w, 8, label)
    # Draw underline for fill-in
    x = pdf.get_x()
    y = pdf.get_y() + 7
    pdf.line(x, y, x + (width - label_w), y)
    pdf.ln(10)

def form_line_multi(items):
    """Multiple fields on one line"""
    pdf.set_font("Times", '', 11)
    x_start = pdf.l_margin
    total_w = 215.9 - pdf.l_margin - pdf.r_margin
    per_item = total_w / len(items)
    for i, label in enumerate(items):
        x = x_start + i * per_item
        label_w = pdf.get_string_width(label) + 2
        pdf.set_xy(x, pdf.get_y())
        pdf.cell(label_w, 8, label)
        lx = x + label_w
        ly = pdf.get_y() + 7
        pdf.line(lx, ly, x + per_item - 4, ly)
    pdf.ln(10)

form_line("Name:")
form_line_multi(["Birth Date:", "Age:"])
form_line_multi(["Current grade level:", "School:"])
form_line("Address (Physical):")
form_line_multi(["City:", "State:", "Zip Code:"])
form_line_multi(["Phone:", "Email:"])
form_line("Address (Mailing, if different than above):")
form_line_multi(["City:", "State:", "Zip Code:"])
form_line_multi(["Phone:", "Email:"])

pdf.ln(4)
pdf.set_font("Times", '', 11)
pdf.cell(0, 7, "Please explain why you are interested in attending this trip!", ln=True)
pdf.ln(2)

# Draw lines for writing
for i in range(6):
    y = pdf.get_y()
    pdf.line(pdf.l_margin, y, 215.9 - pdf.r_margin, y)
    pdf.ln(10)

pdf.ln(8)
pdf.set_font("Times", 'B', 12)
pdf.cell(0, 6, "Mail completed application and payment to", ln=True, align='C')
pdf.set_font("Times", '', 12)
pdf.cell(0, 6, "Lower Mississippi River Foundation", ln=True, align='C')
pdf.cell(0, 6, "107 Perry St", ln=True, align='C')
pdf.cell(0, 6, "Helena, AR 72342", ln=True, align='C')

pdf.output(out_path)
print(f"Created: {out_path}")
