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
  // Domain-wide delegation from Cloud Functions (Gen2/Cloud Run):
  // Use IAM credentials API to sign a JWT, then exchange for token
  const { GoogleAuth } = require("google-auth-library");
  const auth = new GoogleAuth();
  const client = await auth.getClient();
  const sa = client.email || (await auth.getCredentials()).client_email;

  // Sign a JWT with subject claim using IAM signJwt
  const now = Math.floor(Date.now() / 1000);
  const claim = JSON.stringify({
    iss: sa,
    sub: SENDER_EMAIL,
    scope: "https://www.googleapis.com/auth/gmail.send",
    aud: "https://oauth2.googleapis.com/token",
    iat: now,
    exp: now + 3600,
  });

  // Call IAM signJwt API
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

  // Exchange signed JWT for access token
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

function buildConfirmationHtml(data) {
  const name = `${sanitize(data.firstName)} ${sanitize(data.lastName)}`;
  const paypalUrl = "https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=7F349QJ9M274Y&item_name=Adventure+Camp+Deposit+-+%2425";
  return `
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <h2 style="color:#2c5f2d;">Welcome to the Adventure!</h2>
  <p>Thank you for applying to the <strong>Mississippi River Adventure Camp</strong>! We're excited that ${name} wants to join us on the river this summer.</p>
  <p>We've received your application and will be in touch soon with next steps.</p>
  <p>To secure your spot, please pay the <strong>$25 deposit</strong> within 30 days:</p>
  <p style="text-align:center;margin:24px 0;">
    <a href="${paypalUrl}" style="display:inline-block;padding:14px 36px;background:#d48b3e;color:#fff;text-decoration:none;border-radius:25px;font-size:16px;font-weight:600;">Pay $25 Deposit via PayPal</a>
  </p>
  <p>Questions? Contact Abe Hudson at 662-822-9984 or <a href="mailto:info@lowermsfoundation.org" style="color:#d48b3e;">info@lowermsfoundation.org</a></p>
  <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
  <p style="font-size:12px;color:#999;">Lower Mississippi River Foundation<br>PO Box 127, Helena, AR 72342<br>(870) 228-2421</p>
</div>`;
}

async function sendEmail(gmail, to, cc, subject, html) {
  const messageParts = [
    `From: LMRF Adventure Camp <${SENDER_EMAIL}>`,
    `To: ${to}`,
  ];
  if (cc) messageParts.push(`Cc: ${cc}`);
  messageParts.push(
    `Subject: ${subject}`,
    "MIME-Version: 1.0",
    'Content-Type: text/html; charset="UTF-8"',
    "",
    html,
  );
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

  // 1. Internal notification to info@
  await sendEmail(
    gmail,
    NOTIFY_EMAIL,
    null,
    `New Adventure Camp Application: ${name}`,
    buildNotificationHtml(data),
  );
  console.log(`Internal notification sent for ${name}`);

  // 2. Confirmation to parent (CC student if email provided)
  const parentEmail = sanitize(data.parentEmail);
  const studentEmail = sanitize(data.studentEmail);
  await sendEmail(
    gmail,
    parentEmail,
    studentEmail || null,
    "Welcome to the Adventure! - Mississippi River Adventure Camp",
    buildConfirmationHtml(data),
  );
  console.log(`Confirmation email sent to ${parentEmail}${studentEmail ? " (cc: " + studentEmail + ")" : ""}`);
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
