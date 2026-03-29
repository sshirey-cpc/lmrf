/**
 * Capture additional pages: camp-application and delta-day-camp
 * Then fix all links on summer-camps.html to point to them.
 */

import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';
import { URL } from 'url';
import https from 'https';
import http from 'http';

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const OUT = path.join(import.meta.dirname, 'rendered-site');

const EXTRA_PAGES = [
  { url: 'https://www.lowermsfoundation.org/camp-application', file: 'camp-application.html' },
  { url: 'https://www.lowermsfoundation.org/delta-day-camp', file: 'delta-day-camp.html' },
];

const NAV_MAP = {
  '/': 'index.html',
  '/who-we-are': 'who-we-are.html',
  '/our-programs': 'our-programs.html',
  '/summer-camps': 'summer-camps.html',
  '/new-page-2': 'river-stewards.html',
  '/get-involved': 'get-involved.html',
  '/calendar': 'calendar.html',
  '/lmrf': 'blog.html',
  '/contact': 'contact.html',
  '/donate': 'donate.html',
  '/home-1': 'our-programs.html',
  '/volunteer-1': 'get-involved.html',
  '/advocate': 'get-involved.html',
  '/camp-application': 'camp-application.html',
  '/delta-day-camp': 'delta-day-camp.html',
  '/camp-application-1': 'contact.html',
};

const assetMap = new Map();

function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    const mod = url.startsWith('https') ? https : http;
    mod.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return fetchUrl(res.headers.location).then(resolve).catch(reject);
      }
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => resolve(Buffer.concat(chunks)));
      res.on('error', reject);
    }).on('error', reject);
  });
}

function sanitize(name) {
  return name.replace(/[^a-zA-Z0-9._-]/g, '_').substring(0, 100);
}

async function downloadImage(remoteUrl) {
  if (assetMap.has(remoteUrl)) return assetMap.get(remoteUrl);
  try {
    const parsed = new URL(remoteUrl);
    const base = path.basename(parsed.pathname) || 'file';
    const cleanName = sanitize(base);
    const targetDir = path.join(OUT, 'images');
    const localPath = path.join(targetDir, cleanName);

    // If already exists from previous capture, reuse it
    if (fs.existsSync(localPath) && fs.statSync(localPath).size > 0) {
      const rel = 'images/' + cleanName;
      assetMap.set(remoteUrl, rel);
      return rel;
    }

    const data = await fetchUrl(remoteUrl);
    if (data.length === 0) {
      assetMap.set(remoteUrl, null);
      return null;
    }
    fs.writeFileSync(localPath, data);
    const rel = 'images/' + cleanName;
    assetMap.set(remoteUrl, rel);
    console.log(`  Image: ${rel}`);
    return rel;
  } catch (e) {
    console.log(`  FAIL: ${remoteUrl} (${e.message})`);
    assetMap.set(remoteUrl, null);
    return null;
  }
}

function rewriteLinks(html) {
  // Rewrite internal navigation links
  for (const [orig, local] of Object.entries(NAV_MAP)) {
    // href="/path"
    html = html.replaceAll(`href="${orig}"`, `href="${local}"`);
    html = html.replaceAll(`href="${orig}/"`, `href="${local}"`);
    // Full URL versions
    html = html.replaceAll(
      `href="https://www.lowermsfoundation.org${orig}"`,
      `href="${local}"`
    );
    html = html.replaceAll(
      `href="https://www.lowermsfoundation.org${orig}/"`,
      `href="${local}"`
    );
  }

  // Fix PDF download links
  html = html.replaceAll('href="/s/', 'href="files/');

  // Fix blog links to point to live site
  html = html.replace(/href="\/lmrf\//g, 'href="https://www.lowermsfoundation.org/lmrf/');

  // Remove base href
  html = html.replaceAll('<base href="">', '');

  // Fix favicon
  html = html.replace(
    /href="https:\/\/images\.squarespace-cdn\.com\/[^"]*favicon[^"]*"/g,
    'href="favicon.ico"'
  );

  // Fix preconnect to squarespace CDN
  html = html.replace(
    /<link[^>]*href="https:\/\/images\.squarespace-cdn\.com"[^>]*>/g,
    ''
  );

  return html;
}

async function processImages(html) {
  // Find all squarespace CDN image references
  const imgRegex = /(?:src|data-src|data-image)="(https?:\/\/images\.squarespace-cdn\.com[^"]+)"/g;
  const imgUrls = new Set();
  let match;
  while ((match = imgRegex.exec(html)) !== null) {
    imgUrls.add(match[1].split('?')[0]);
  }

  // Also background images
  const bgRegex = /url\(['"]?(https?:\/\/images\.squarespace-cdn\.com[^'")\s]+)['"]?\)/g;
  while ((match = bgRegex.exec(html)) !== null) {
    imgUrls.add(match[1].split('?')[0]);
  }

  console.log(`  Found ${imgUrls.size} images`);

  for (const imgUrl of imgUrls) {
    const local = await downloadImage(imgUrl);
    if (local) {
      const escaped = imgUrl.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      html = html.replace(new RegExp(escaped + '[^"\'\\)\\s]*', 'g'), local);
    }
  }

  return html;
}

async function main() {
  console.log('Launching Chrome...');
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  for (const { url, file } of EXTRA_PAGES) {
    console.log(`\nCapturing: ${url}`);
    const page = await browser.newPage();
    await page.setViewport({ width: 1400, height: 900 });
    await page.goto(url, { waitUntil: 'networkidle0', timeout: 45000 });
    await new Promise(r => setTimeout(r, 3000));

    let html = await page.content();
    await page.close();

    // Process images
    html = await processImages(html);

    // Rewrite links
    html = rewriteLinks(html);

    // Add static fixes
    html = html.replace('</head>', '<link rel="stylesheet" href="css/static-fixes.css">\n</head>');
    html = html.replace('</body>', '<script src="js/parallax-fix.js"></script>\n</body>');

    // Save
    fs.writeFileSync(path.join(OUT, file), html, 'utf-8');
    console.log(`  Saved: ${file} (${html.length.toLocaleString()} bytes)`);
  }

  await browser.close();

  // Now fix summer-camps.html links
  console.log('\nFixing summer-camps.html links...');
  let scHtml = fs.readFileSync(path.join(OUT, 'summer-camps.html'), 'utf-8');
  scHtml = scHtml.replaceAll('href="contact.html" class="sqs-block-button-element--small sqs-button-element--tertiary sqs-block-button-element">\n      Learn More and Apply Online!',
    'href="camp-application.html" class="sqs-block-button-element--small sqs-button-element--tertiary sqs-block-button-element">\n      Learn More and Apply Online!');
  scHtml = scHtml.replaceAll('href="contact.html" class="sqs-block-button-element--small sqs-button-element--tertiary sqs-block-button-element">\n      Learn More and Register Online',
    'href="delta-day-camp.html" class="sqs-block-button-element--small sqs-button-element--tertiary sqs-block-button-element">\n      Learn More and Register Online');
  fs.writeFileSync(path.join(OUT, 'summer-camps.html'), scHtml, 'utf-8');
  console.log('  Fixed: Learn More and Apply Online! -> camp-application.html');
  console.log('  Fixed: Learn More and Register Online -> delta-day-camp.html');

  // Also fix any other pages that might link to these
  for (const f of fs.readdirSync(OUT).filter(f => f.endsWith('.html'))) {
    let html = fs.readFileSync(path.join(OUT, f), 'utf-8');
    const orig = html;
    html = html.replaceAll('href="/camp-application"', 'href="camp-application.html"');
    html = html.replaceAll('href="/delta-day-camp"', 'href="delta-day-camp.html"');
    html = html.replaceAll('href="/camp-application-1"', 'href="contact.html"');
    if (html !== orig) {
      fs.writeFileSync(path.join(OUT, f), html, 'utf-8');
      console.log(`  Also fixed links in: ${f}`);
    }
  }

  console.log('\nDone!');
}

main().catch(console.error);
