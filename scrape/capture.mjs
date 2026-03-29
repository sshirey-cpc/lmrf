/**
 * Capture fully-rendered DOM from lowermsfoundation.org using Puppeteer.
 * Downloads all images locally, rewrites paths, applies targeted changes.
 */

import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';
import { URL } from 'url';
import https from 'https';
import http from 'http';

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const OUT = path.join(import.meta.dirname, 'rendered-site');
const IMAGES_DIR = path.join(OUT, 'images');
const CSS_DIR = path.join(OUT, 'css');
const FONTS_DIR = path.join(OUT, 'fonts');

const PAGES = [
  { url: 'https://www.lowermsfoundation.org/', file: 'index.html' },
  { url: 'https://www.lowermsfoundation.org/who-we-are', file: 'who-we-are.html' },
  { url: 'https://www.lowermsfoundation.org/our-programs', file: 'our-programs.html' },
  { url: 'https://www.lowermsfoundation.org/summer-camps', file: 'summer-camps.html' },
  { url: 'https://www.lowermsfoundation.org/new-page-2', file: 'river-stewards.html' },
  { url: 'https://www.lowermsfoundation.org/get-involved', file: 'get-involved.html' },
  { url: 'https://www.lowermsfoundation.org/calendar', file: 'calendar.html' },
  { url: 'https://www.lowermsfoundation.org/lmrf', file: 'blog.html' },
  { url: 'https://www.lowermsfoundation.org/contact', file: 'contact.html' },
  { url: 'https://www.lowermsfoundation.org/donate', file: 'donate.html' },
];

const PAYPAL = 'https://www.paypal.com/donate?token=fPg9LuFa9121K_HDyZVHkUs4L6Xuwg3gKG4w_MSfisa1zzrcq-PtnNC190Fc_6-8vZjTLSvpb0Lmd7eL';

const GCAL = `<iframe src="https://calendar.google.com/calendar/embed?src=c_1ef3475e4f299305a635b1d46e77d427818dae70fffeed0e56306c2926e14bc1%40group.calendar.google.com&ctz=America%2FChicago" style="border: 0" width="800" height="600" frameborder="0" scrolling="no"></iframe>`;

// Track downloaded assets to avoid duplicates
const assetMap = new Map(); // remote URL -> local relative path

function fetch(url) {
  return new Promise((resolve, reject) => {
    const mod = url.startsWith('https') ? https : http;
    mod.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return fetch(res.headers.location).then(resolve).catch(reject);
      }
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => resolve(Buffer.concat(chunks)));
      res.on('error', reject);
    }).on('error', reject);
  });
}

function sanitizeFilename(name) {
  return name.replace(/[^a-zA-Z0-9._-]/g, '_').substring(0, 100);
}

async function downloadAsset(remoteUrl, subdir, prefix = '') {
  if (assetMap.has(remoteUrl)) return assetMap.get(remoteUrl);

  try {
    const parsed = new URL(remoteUrl);
    const ext = path.extname(parsed.pathname) || '.bin';
    const base = path.basename(parsed.pathname) || 'file';
    const cleanName = prefix + sanitizeFilename(base);

    const targetDir = path.join(OUT, subdir);
    fs.mkdirSync(targetDir, { recursive: true });

    // Avoid name collisions
    let localName = cleanName;
    let i = 1;
    while (fs.existsSync(path.join(targetDir, localName))) {
      const nameNoExt = cleanName.replace(/\.[^.]+$/, '');
      localName = `${nameNoExt}_${i}${ext}`;
      i++;
    }

    const data = await fetch(remoteUrl);
    if (data.length === 0) {
      console.log(`  EMPTY: ${remoteUrl}`);
      assetMap.set(remoteUrl, null);
      return null;
    }

    fs.writeFileSync(path.join(targetDir, localName), data);
    const relPath = `${subdir}/${localName}`;
    assetMap.set(remoteUrl, relPath);
    return relPath;
  } catch (e) {
    console.log(`  FAIL: ${remoteUrl} (${e.message})`);
    assetMap.set(remoteUrl, null);
    return null;
  }
}

async function captureRenderedPage(browser, pageUrl) {
  console.log(`\nCapturing: ${pageUrl}`);
  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 900 });

  // Collect all loaded stylesheets
  const stylesheetUrls = new Set();
  page.on('response', (response) => {
    const url = response.url();
    if (response.request().resourceType() === 'stylesheet') {
      stylesheetUrls.add(url);
    }
  });

  await page.goto(pageUrl, { waitUntil: 'networkidle0', timeout: 45000 });

  // Wait a bit more for any lazy-loaded images
  await new Promise(r => setTimeout(r, 2000));

  // Extract all computed styles as inline <style> blocks
  const allStyles = await page.evaluate(() => {
    const styles = [];
    for (const sheet of document.styleSheets) {
      try {
        const rules = [];
        for (const rule of sheet.cssRules) {
          rules.push(rule.cssText);
        }
        styles.push(rules.join('\n'));
      } catch (e) {
        // Cross-origin stylesheet, skip (we'll download it separately)
      }
    }
    return styles;
  });

  // Get the rendered DOM
  const html = await page.content();

  await page.close();
  return { html, allStyles, stylesheetUrls: [...stylesheetUrls] };
}

function rewriteInternalLinks(html) {
  // Map original paths to our new filenames
  const linkMap = {
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
  };

  for (const [origPath, newFile] of Object.entries(linkMap)) {
    // Replace href="/path" with href="newFile"
    const escaped = origPath.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    html = html.replace(
      new RegExp(`href="${escaped}"`, 'g'),
      `href="${newFile}"`
    );
    html = html.replace(
      new RegExp(`href="${escaped}/"`, 'g'),
      `href="${newFile}"`
    );
    // Also catch full URLs
    html = html.replace(
      new RegExp(`href="https://www\\.lowermsfoundation\\.org${escaped}"`, 'g'),
      `href="${newFile}"`
    );
    html = html.replace(
      new RegExp(`href="https://www\\.lowermsfoundation\\.org${escaped}/"`, 'g'),
      `href="${newFile}"`
    );
  }

  return html;
}

async function processHtml(html, stylesheetUrls) {
  // 1. Download and localize images from squarespace CDN
  const imgRegex = /(?:src|srcset|data-src|data-image)="(https?:\/\/images\.squarespace-cdn\.com[^"]+)"/g;
  let match;
  const imageUrls = new Set();
  while ((match = imgRegex.exec(html)) !== null) {
    // srcset can have multiple URLs
    const val = match[1];
    for (const part of val.split(',')) {
      const url = part.trim().split(/\s+/)[0];
      if (url.startsWith('http')) imageUrls.add(url.split('?')[0]); // strip format params
    }
  }

  // Also find images in background-image styles
  const bgRegex = /url\(['"]?(https?:\/\/images\.squarespace-cdn\.com[^'")\s]+)['"]?\)/g;
  while ((match = bgRegex.exec(html)) !== null) {
    imageUrls.add(match[1].split('?')[0]);
  }

  // Also find static1.squarespace.com images
  const static1Regex = /(?:src|href|url\()['"]?(https?:\/\/static1\.squarespace\.com[^'")\s>]+)['"]?/g;
  while ((match = static1Regex.exec(html)) !== null) {
    imageUrls.add(match[1].split('?')[0]);
  }

  console.log(`  Found ${imageUrls.size} images to download`);

  let imgCount = 0;
  for (const imgUrl of imageUrls) {
    imgCount++;
    const localPath = await downloadAsset(imgUrl, 'images');
    if (localPath) {
      // Replace all occurrences of this image URL (with any query params)
      const escaped = imgUrl.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      html = html.replace(new RegExp(escaped + '[^"\'\\)\\s]*', 'g'), localPath);
    }
    if (imgCount % 10 === 0) console.log(`  Downloaded ${imgCount}/${imageUrls.size} images`);
  }

  // 2. Download external stylesheets
  for (const cssUrl of stylesheetUrls) {
    if (cssUrl.includes('squarespace') || cssUrl.includes('fonts.googleapis')) {
      const localPath = await downloadAsset(cssUrl, 'css');
      if (localPath) {
        const escaped = cssUrl.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        html = html.replace(new RegExp(escaped, 'g'), localPath);
      }
    }
  }

  // 3. Rewrite internal navigation links
  html = rewriteInternalLinks(html);

  return html;
}

function applyDonateLink(html) {
  // Make all donate nav links point to PayPal
  html = html.replace(
    /href="donate\.html"/g,
    `href="${PAYPAL}" target="_blank" rel="noopener"`
  );
  return html;
}

function applyCalendarEmbed(html) {
  // Replace the calendar page body content with Google Calendar
  // Find the main content area (between the nav and footer)
  // Look for common Squarespace content wrappers
  const markers = [
    { start: '<main', end: '</main>' },
    { start: 'class="Main-content"', end: null },
    { start: 'class="Index"', end: null },
  ];

  // Simple approach: find the content between header and footer, replace
  const mainStart = html.indexOf('<main');
  const mainEnd = html.indexOf('</main>');
  if (mainStart !== -1 && mainEnd !== -1) {
    const before = html.substring(0, html.indexOf('>', mainStart) + 1);
    const after = html.substring(mainEnd);
    html = before + `
      <div style="max-width:900px; margin:60px auto; text-align:center; padding:20px;">
        <h1 style="margin-bottom:40px;">Calendar</h1>
        ${GCAL}
      </div>
    ` + after;
  }

  return html;
}

function applyContactForm(html) {
  // Add mailto handler for contact form
  const script = `
<script>
document.addEventListener('DOMContentLoaded', function() {
  var forms = document.querySelectorAll('form');
  forms.forEach(function(form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      var data = new FormData(form);
      var fields = {};
      for (var pair of data.entries()) {
        fields[pair[0].toLowerCase()] = pair[1];
      }
      var name = fields.name || fields.fname || '';
      var email = fields.email || fields['email-yui'] || '';
      var msg = fields.message || fields.comment || fields.textarea || '';
      var subj = 'Website Contact' + (name ? ' from ' + name : '');
      var body = (name ? 'From: ' + name + '\\n' : '') +
                 (email ? 'Email: ' + email + '\\n\\n' : '') + msg;
      window.location.href = 'mailto:info@lowermsfoundation.org?subject=' +
        encodeURIComponent(subj) + '&body=' + encodeURIComponent(body);
    });
  });
});
</script>`;

  html = html.replace('</body>', script + '\n</body>');
  return html;
}

function cleanupForStatic(html) {
  // Remove Squarespace-specific scripts that won't work statically
  // Remove SQUARESPACE_CONTEXT (contains API keys, session data)
  html = html.replace(/<script[^>]*>[\s\S]*?Static\.SQUARESPACE_CONTEXT[\s\S]*?<\/script>/g, '');

  // Remove analytics/tracking
  html = html.replace(/<script[^>]*>[\s\S]*?squarespace-analytics[\s\S]*?<\/script>/g, '');
  html = html.replace(/<script[^>]*>[\s\S]*?SquarespaceSiteVerification[\s\S]*?<\/script>/g, '');

  // Remove Squarespace commerce scripts
  html = html.replace(/<script[^>]*>[\s\S]*?squarespace-commerce[\s\S]*?<\/script>/g, '');

  // Fix any remaining absolute URLs to the site
  html = html.replace(/https:\/\/www\.lowermsfoundation\.org\//g, '');

  return html;
}

async function main() {
  // Clean output
  if (fs.existsSync(OUT)) fs.rmSync(OUT, { recursive: true });
  fs.mkdirSync(IMAGES_DIR, { recursive: true });
  fs.mkdirSync(CSS_DIR, { recursive: true });
  fs.mkdirSync(FONTS_DIR, { recursive: true });

  console.log('Launching Chrome...');
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  // First, capture all pages and collect all stylesheets
  const allStylesheetUrls = new Set();
  const capturedPages = [];

  for (const { url, file } of PAGES) {
    try {
      const result = await captureRenderedPage(browser, url);
      result.stylesheetUrls.forEach(u => allStylesheetUrls.add(u));
      capturedPages.push({ ...result, file, url });
    } catch (e) {
      console.log(`  ERROR capturing ${url}: ${e.message}`);
    }
  }

  await browser.close();
  console.log(`\nCaptured ${capturedPages.length} pages, ${allStylesheetUrls.size} stylesheets`);

  // Download all stylesheets once
  console.log('\nDownloading stylesheets...');
  for (const cssUrl of allStylesheetUrls) {
    await downloadAsset(cssUrl, 'css');
  }

  // Process and save each page
  for (const { html: rawHtml, file, url, stylesheetUrls } of capturedPages) {
    console.log(`\nProcessing: ${file}`);
    let html = rawHtml;

    // Download images and rewrite URLs
    html = await processHtml(html, stylesheetUrls);

    // Apply targeted changes
    html = applyDonateLink(html);
    html = cleanupForStatic(html);

    if (file === 'calendar.html') {
      html = applyCalendarEmbed(html);
    }
    if (file === 'contact.html') {
      html = applyContactForm(html);
    }

    // Save
    fs.writeFileSync(path.join(OUT, file), html, 'utf-8');
    console.log(`  Saved: ${file}`);
  }

  // Summary
  const imgCount = fs.readdirSync(IMAGES_DIR).length;
  const cssCount = fs.readdirSync(CSS_DIR).length;
  console.log(`\n${'='.repeat(50)}`);
  console.log(`Done! Output: ${OUT}`);
  console.log(`  Pages: ${capturedPages.length}`);
  console.log(`  Images: ${imgCount}`);
  console.log(`  Stylesheets: ${cssCount}`);
  console.log(`\nOpen ${path.join(OUT, 'index.html')} to preview.`);
}

main().catch(console.error);
