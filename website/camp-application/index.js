/**
 * LMRF Camp Application Cloud Function
 *
 * Accepts camp application submissions via POST, stores them in BigQuery,
 * and sends an email notification to info@lowermsfoundation.org.
 *
 * Entry point: campApplication
 */

const { BigQuery } = require("@google-cloud/bigquery");
const { google } = require("googleapis");

const PROJECT_ID = "balmy-limiter-491013-a8";
const DATASET = "lmrf_donations";
const TABLE = "camp_applications";
const SENDER_EMAIL = "info@lowermsfoundation.org";
const NOTIFY_EMAIL = "info@lowermsfoundation.org";

const ALLOWED_ORIGINS = [
  "https://lowermsfoundation.org",
  "https://www.lowermsfoundation.org",
  "http://localhost",
  "http://localhost:8080",
  "http://localhost:8768",
];

const REQUIRED_FIELDS = [
  "firstName", "lastName", "birthdate", "age",
  "currentGrade", "school", "parentName", "parentEmail",
  "parentPhone", "address1", "city1", "state1", "zip1", "essay",
];

function getCorsHeaders(origin) {
  const allowed = ALLOWED_ORIGINS.find((o) => origin && origin.startsWith(o));
  return {
    "Access-Control-Allow-Origin": allowed || ALLOWED_ORIGINS[0],
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "3600",
  };
}

async function getGmailAuth() {
  // Use Application Default Credentials with domain-wide delegation
  // (same approach as paypal-sync function)
  const auth = new google.auth.GoogleAuth({
    scopes: ["https://www.googleapis.com/auth/gmail.send"],
  });
  const client = await auth.getClient();
  client.subject = SENDER_EMAIL;
  return client;
}

function sanitize(val) {
  if (typeof val !== "string") return "";
  return val.replace(/<[^>]*>/g, "").trim();
}

// BigQuery
async function storeApplication(data) {
  const bq = new BigQuery({ projectId: PROJECT_ID });
  const table = bq.dataset(DATASET).table(TABLE);

  const row = {
    first_name: sanitize(data.firstName),
    last_name: sanitize(data.lastName),
    birthdate: sanitize(data.birthdate),
    age: Number(data.age) || 0,
    current_grade: sanitize(data.currentGrade),
    school: sanitize(data.school),
    student_email: sanitize(data.studentEmail),
    parent_name: sanitize(data.parentName),
    parent_email: sanitize(data.parentEmail),
    parent_phone: sanitize(data.parentPhone),
    student_phone: sanitize(data.studentPhone),
    address1: sanitize(data.address1),
    city1: sanitize(data.city1),
    state1: sanitize(data.state1),
    zip1: sanitize(data.zip1),
    address2: sanitize(data.address2),
    city2: sanitize(data.city2),
    state2: sanitize(data.state2),
    zip2: sanitize(data.zip2),
    essay: sanitize(data.essay),
    submitted_at: new Date().toISOString(),
  };

  await table.insert([row]);
  console.log(`Application stored for ${row.first_name} ${row.last_name}`);
  return row;
}

// Email
function buildNotificationHtml(data) {
  const name = `${sanitize(data.firstName)} ${sanitize(data.lastName)}`;
  const mailingSection = data.address2
    ? `<tr><td style="padding:4px 8px;font-weight:bold;">Mailing Address</td>
        <td style="padding:4px 8px;">${sanitize(data.address2)}<br>${sanitize(data.city2)}, ${sanitize(data.state2)} ${sanitize(data.zip2)}</td></tr>`
    : "";

  const studentEmailRow = data.studentEmail
    ? `<tr><td style="padding:4px 8px;font-weight:bold;">Student Email</td>
        <td style="padding:4px 8px;">${sanitize(data.studentEmail)}</td></tr>`
    : "";
  const studentPhoneRow = data.studentPhone
    ? `<tr><td style="padding:4px 8px;font-weight:bold;">Student Phone</td>
        <td style="padding:4px 8px;">${sanitize(data.studentPhone)}</td></tr>`
    : "";

  return `
<div style="font-family:Arial,sans-serif;max-width:600px;">
  <h2 style="color:#2c5f2d;">New Adventure Camp Application: ${name}</h2>
  <h3 style="color:#333;margin-top:16px;">Student</h3>
  <table style="border-collapse:collapse;width:100%;">
    <tr><td style="padding:4px 8px;font-weight:bold;">Name</td>
        <td style="padding:4px 8px;">${name}</td></tr>
    <tr><td style="padding:4px 8px;font-weight:bold;">Birthdate</td>
        <td style="padding:4px 8px;">${sanitize(data.birthdate)}</td></tr>
    <tr><td style="padding:4px 8px;font-weight:bold;">Age</td>
        <td style="padding:4px 8px;">${data.age}</td></tr>
    <tr><td style="padding:4px 8px;font-weight:bold;">Current Grade</td>
        <td style="padding:4px 8px;">${sanitize(data.currentGrade)}</td></tr>
    <tr><td style="padding:4px 8px;font-weight:bold;">School</td>
        <td style="padding:4px 8px;">${sanitize(data.school)}</td></tr>${studentEmailRow}${studentPhoneRow}
  </table>
  <h3 style="color:#333;margin-top:16px;">Parent / Guardian</h3>
  <table style="border-collapse:collapse;width:100%;">
    <tr><td style="padding:4px 8px;font-weight:bold;">Name</td>
        <td style="padding:4px 8px;">${sanitize(data.parentName)}</td></tr>
    <tr><td style="padding:4px 8px;font-weight:bold;">Email</td>
        <td style="padding:4px 8px;">${sanitize(data.parentEmail)}</td></tr>
    <tr><td style="padding:4px 8px;font-weight:bold;">Phone</td>
        <td style="padding:4px 8px;">${sanitize(data.parentPhone)}</td></tr>
  </table>
  <h3 style="color:#333;margin-top:16px;">Address</h3>
  <table style="border-collapse:collapse;width:100%;">
    <tr><td style="padding:4px 8px;font-weight:bold;">Physical Address</td>
        <td style="padding:4px 8px;">${sanitize(data.address1)}<br>${sanitize(data.city1)}, ${sanitize(data.state1)} ${sanitize(data.zip1)}</td></tr>${mailingSection}
  </table>
  <h3 style="color:#2c5f2d;margin-top:16px;">Why are you interested in camp?</h3>
  <p style="white-space:pre-wrap;">${sanitize(data.essay)}</p>
</div>`;
}

async function sendNotification(data) {
  const auth = await getGmailAuth();
  const gmail = google.gmail({ version: "v1", auth });
  const name = `${sanitize(data.firstName)} ${sanitize(data.lastName)}`;
  const subject = `New Adventure Camp Application: ${name}`;
  const html = buildNotificationHtml(data);

  const messageParts = [
    `From: LMRF Adventure Camp <${SENDER_EMAIL}>`,
    `To: ${NOTIFY_EMAIL}`,
    `Subject: ${subject}`,
    "MIME-Version: 1.0",
    'Content-Type: text/html; charset="UTF-8"',
    "",
    html,
  ];
  const raw = Buffer.from(messageParts.join("\r\n"))
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");

  await gmail.users.messages.send({
    userId: "me",
    requestBody: { raw },
  });
  console.log(`Notification email sent for ${name}`);
}

// Entry point
exports.campApplication = async (req, res) => {
  const origin = req.headers.origin || "";
  const cors = getCorsHeaders(origin);
  res.set(cors);

  if (req.method === "OPTIONS") {
    return res.status(204).send("");
  }

  if (req.method !== "POST") {
    return res.status(405).json({ success: false, message: "Method not allowed" });
  }

  try {
    const data = req.body;
    if (!data || typeof data !== "object") {
      return res.status(400).json({ success: false, message: "Invalid request body" });
    }

    const missing = REQUIRED_FIELDS.filter((f) => !data[f] || String(data[f]).trim() === "");
    if (missing.length > 0) {
      return res.status(400).json({
        success: false,
        message: `Missing required fields: ${missing.join(", ")}`,
      });
    }

    await storeApplication(data);

    try {
      await sendNotification(data);
    } catch (emailErr) {
      console.error(`Email notification failed: ${emailErr.message}`);
    }

    return res.status(200).json({ success: true, message: "Application submitted" });
  } catch (err) {
    console.error(`Camp application error: ${err.message}`);
    return res.status(500).json({ success: false, message: "Internal server error" });
  }
};
