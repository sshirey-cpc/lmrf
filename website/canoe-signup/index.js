/**
 * LMRF Community Canoe Trip Sign-Up Cloud Function
 *
 * Accepts sign-up submissions via POST, stores them in BigQuery,
 * and sends an email notification to info@lowermsfoundation.org.
 *
 * Entry point: canoeSignup
 */

const { BigQuery } = require("@google-cloud/bigquery");
const { google } = require("googleapis");

const PROJECT_ID = "balmy-limiter-491013-a8";
const DATASET = "lmrf_donations";
const TABLE = "canoe_signups";
const SENDER_EMAIL = "info@lowermsfoundation.org";
const NOTIFY_EMAIL = "info@lowermsfoundation.org";

const ALLOWED_ORIGINS = [
  "https://lowermsfoundation.org",
  "https://www.lowermsfoundation.org",
  "http://localhost",
  "http://localhost:8080",
  "http://localhost:8768",
];

const REQUIRED_CONTACT_FIELDS = [
  "firstName", "lastName", "email", "phone",
  "address", "city", "state", "zip", "tripDate",
];

const REQUIRED_PARTICIPANT_FIELDS = ["name", "age", "weight", "firstTime"];

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
async function storeSignup(data) {
  const bq = new BigQuery({ projectId: PROJECT_ID });
  const table = bq.dataset(DATASET).table(TABLE);

  const row = {
    contact_first_name: sanitize(data.firstName),
    contact_last_name: sanitize(data.lastName),
    contact_email: sanitize(data.email),
    contact_phone: sanitize(data.phone),
    contact_address: sanitize(data.address),
    contact_city: sanitize(data.city),
    contact_state: sanitize(data.state),
    contact_zip: sanitize(data.zip),
    trip_date: sanitize(data.tripDate),
    participant_count: Array.isArray(data.participants) ? data.participants.length : 0,
    participants_json: JSON.stringify(data.participants || []),
    submitted_at: new Date().toISOString(),
  };

  await table.insert([row]);
  console.log(`Sign-up stored for ${row.contact_first_name} ${row.contact_last_name}`);
  return row;
}

// Email
function buildNotificationHtml(data) {
  const name = `${sanitize(data.firstName)} ${sanitize(data.lastName)}`;
  const participants = data.participants || [];

  let participantRows = "";
  participants.forEach((p, i) => {
    participantRows += `
    <tr style="background:${i % 2 === 0 ? "#f9f6f2" : "#fff"};">
      <td style="padding:6px 10px;font-weight:bold;">${i + 1}</td>
      <td style="padding:6px 10px;">${sanitize(p.name)}</td>
      <td style="padding:6px 10px;">${sanitize(String(p.age))}</td>
      <td style="padding:6px 10px;">${sanitize(String(p.weight))} lbs</td>
      <td style="padding:6px 10px;">${sanitize(p.firstTime)}</td>
      <td style="padding:6px 10px;">${sanitize(p.phone) || "&mdash;"}</td>
      <td style="padding:6px 10px;">${sanitize(p.email) || "&mdash;"}</td>
    </tr>`;
    if (p.address) {
      participantRows += `
    <tr style="background:${i % 2 === 0 ? "#f9f6f2" : "#fff"};">
      <td></td>
      <td colspan="6" style="padding:2px 10px 8px;font-size:13px;color:#666;">
        Address: ${sanitize(p.address)}, ${sanitize(p.city)}, ${sanitize(p.state)} ${sanitize(p.zip)}
      </td>
    </tr>`;
    }
  });

  return `
<div style="font-family:Arial,sans-serif;max-width:700px;">
  <h2 style="color:#d48b3e;">New Community Canoe Trip Sign-Up</h2>

  <h3 style="color:#333;margin-top:16px;">Contact Information</h3>
  <table style="border-collapse:collapse;width:100%;">
    <tr><td style="padding:4px 8px;font-weight:bold;">Name</td>
        <td style="padding:4px 8px;">${name}</td></tr>
    <tr><td style="padding:4px 8px;font-weight:bold;">Email</td>
        <td style="padding:4px 8px;">${sanitize(data.email)}</td></tr>
    <tr><td style="padding:4px 8px;font-weight:bold;">Phone</td>
        <td style="padding:4px 8px;">${sanitize(data.phone)}</td></tr>
    <tr><td style="padding:4px 8px;font-weight:bold;">Address</td>
        <td style="padding:4px 8px;">${sanitize(data.address)}<br>${sanitize(data.city)}, ${sanitize(data.state)} ${sanitize(data.zip)}</td></tr>
    <tr><td style="padding:4px 8px;font-weight:bold;">Trip Date</td>
        <td style="padding:4px 8px;font-weight:bold;color:#d48b3e;">${sanitize(data.tripDate)}</td></tr>
  </table>

  <h3 style="color:#333;margin-top:16px;">Participants (${participants.length})</h3>
  <table style="border-collapse:collapse;width:100%;font-size:14px;">
    <tr style="background:#d48b3e;color:#fff;">
      <th style="padding:6px 10px;text-align:left;">#</th>
      <th style="padding:6px 10px;text-align:left;">Name</th>
      <th style="padding:6px 10px;text-align:left;">Age</th>
      <th style="padding:6px 10px;text-align:left;">Weight</th>
      <th style="padding:6px 10px;text-align:left;">First Time?</th>
      <th style="padding:6px 10px;text-align:left;">Phone</th>
      <th style="padding:6px 10px;text-align:left;">Email</th>
    </tr>
    ${participantRows}
  </table>
</div>`;
}

async function sendNotification(data) {
  const auth = await getGmailAuth();
  const gmail = google.gmail({ version: "v1", auth });
  const name = `${sanitize(data.firstName)} ${sanitize(data.lastName)}`;
  const subject = `New Canoe Trip Sign-Up: ${name} — ${sanitize(data.tripDate)}`;
  const html = buildNotificationHtml(data);

  const messageParts = [
    `From: LMRF Canoe Trips <${SENDER_EMAIL}>`,
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
exports.canoeSignup = async (req, res) => {
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

    // Validate contact fields
    const missingContact = REQUIRED_CONTACT_FIELDS.filter(
      (f) => !data[f] || String(data[f]).trim() === ""
    );
    if (missingContact.length > 0) {
      return res.status(400).json({
        success: false,
        message: `Missing required contact fields: ${missingContact.join(", ")}`,
      });
    }

    // Validate participants
    if (!Array.isArray(data.participants) || data.participants.length === 0) {
      return res.status(400).json({
        success: false,
        message: "At least one participant is required.",
      });
    }

    if (data.participants.length > 18) {
      return res.status(400).json({
        success: false,
        message: "Maximum of 18 participants per trip.",
      });
    }

    for (let i = 0; i < data.participants.length; i++) {
      const p = data.participants[i];
      const missingP = REQUIRED_PARTICIPANT_FIELDS.filter(
        (f) => !p[f] || String(p[f]).trim() === ""
      );
      if (missingP.length > 0) {
        return res.status(400).json({
          success: false,
          message: `Participant ${i + 1}: missing required fields: ${missingP.join(", ")}`,
        });
      }
    }

    await storeSignup(data);

    try {
      await sendNotification(data);
    } catch (emailErr) {
      console.error(`Email notification failed: ${emailErr.message}`);
    }

    return res.status(200).json({ success: true, message: "Sign-up submitted" });
  } catch (err) {
    console.error(`Canoe sign-up error: ${err.message}`);
    return res.status(500).json({ success: false, message: "Internal server error" });
  }
};
