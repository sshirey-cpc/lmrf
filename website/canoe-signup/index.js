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
  // Domain-wide delegation from Cloud Functions (Gen2/Cloud Run):
  // Use IAM credentials API to sign a JWT, then exchange for token
  const { GoogleAuth } = require("google-auth-library");
  const auth = new GoogleAuth();
  const client = await auth.getClient();
  const sa = client.email || (await auth.getCredentials()).client_email;

  const now = Math.floor(Date.now() / 1000);
  const claim = JSON.stringify({
    iss: sa,
    sub: SENDER_EMAIL,
    scope: "https://www.googleapis.com/auth/gmail.send",
    aud: "https://oauth2.googleapis.com/token",
    iat: now,
    exp: now + 3600,
  });

  const iamUrl = `https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/${sa}:signJwt`;
  const accessToken = await client.getAccessToken();
  const signRes = await fetch(iamUrl, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${accessToken.token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ payload: claim }),
  });
  const signData = await signRes.json();

  if (!signData.signedJwt) {
    throw new Error(`JWT signing failed: ${JSON.stringify(signData)}`);
  }

  const tokenRes = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer&assertion=${signData.signedJwt}`,
  });
  const tokenData = await tokenRes.json();

  if (!tokenData.access_token) {
    throw new Error(`Token exchange failed: ${JSON.stringify(tokenData)}`);
  }

  const oauth2 = new google.auth.OAuth2();
  oauth2.setCredentials({ access_token: tokenData.access_token });
  return oauth2;
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

function buildConfirmationHtml(data) {
  const name = `${sanitize(data.firstName)} ${sanitize(data.lastName)}`;
  const tripDate = sanitize(data.tripDate);
  const participantCount = data.participants ? data.participants.length : 1;
  return `
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <h2 style="color:#2c5f2d;">You're All Set!</h2>
  <p>Thank you for signing up for the <strong>Community Canoe Trip</strong>! We're excited to have you join us on the river.</p>
  <p><strong>Trip Date:</strong> ${tripDate}<br>
  <strong>Participants:</strong> ${participantCount}</p>
  <p>We'll confirm your reservation via email. Please remember:</p>
  <ul style="color:#444;line-height:1.8;">
    <li>Reservations required - 18 max, first come first served</li>
    <li>Pack water bottles, snacks, sun/bug protection, and shoes that can get wet</li>
    <li>Pack electronics in dry bags or zip lock bags</li>
    <li>Dress for possible rainy weather</li>
  </ul>
  <p>Questions? Contact John Ruskey at (662) 902-7841 or Ceili Hale at (601) 918-6810.</p>
  <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
  <p style="font-size:12px;color:#999;">Community Canoe Trips are made possible by the Lower Mississippi River Foundation.<br>PO Box 127, Helena, AR 72342 | (870) 228-2421<br><a href="https://www.lowermsfoundation.org/donate" style="color:#d48b3e;">Support our mission with a donation</a></p>
</div>`;
}

async function sendEmail(gmail, to, subject, html) {
  const messageParts = [
    `From: LMRF Canoe Trips <${SENDER_EMAIL}>`,
    `To: ${to}`,
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
}

async function sendNotification(data) {
  const auth = await getGmailAuth();
  const gmail = google.gmail({ version: "v1", auth });
  const name = `${sanitize(data.firstName)} ${sanitize(data.lastName)}`;

  // 1. Internal notification
  await sendEmail(
    gmail,
    NOTIFY_EMAIL,
    `New Canoe Trip Sign-Up: ${name} - ${sanitize(data.tripDate)}`,
    buildNotificationHtml(data),
  );
  console.log(`Internal notification sent for ${name}`);

  // 2. Confirmation to the person who signed up
  const contactEmail = sanitize(data.email);
  await sendEmail(
    gmail,
    contactEmail,
    "You're All Set! - Community Canoe Trip",
    buildConfirmationHtml(data),
  );
  console.log(`Confirmation email sent to ${contactEmail}`);
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
