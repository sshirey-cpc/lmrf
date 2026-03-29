import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';
import https from 'https';
import http from 'http';
import { URL } from 'url';

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const OUT = path.join(import.meta.dirname, 'rendered-site');

const PAGES = [
  { url: 'https://www.lowermsfoundation.org/volunteer-1', file: 'volunteer.html' },
  { url: 'https://www.lowermsfoundation.org/advocate', file: 'advocate.html' },
];

const NAV_MAP = {
  '/': 'index.html', '/who-we-are': 'who-we-are.html',
  '/our-programs': 'our-programs.html', '/summer-camps': 'summer-camps.html',
  '/new-page-2': 'river-stewards.html', '/get-involved': 'get-involved.html',
  '/calendar': 'calendar.html', '/lmrf': 'blog.html',
  '/contact': 'contact.html', '/donate': 'donate.html',
  '/home-1': 'our-programs.html', '/volunteer-1': 'volunteer.html',
  '/advocate': 'advocate.html', '/camp-application': 'camp-application.html',
  '/delta-day-camp': 'delta-day-camp.html', '/camp-application-1': 'contact.html',
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
    if (fs.existsSync(localPath) && fs.statSync(localPath).size > 0) {
      const rel = 'images/' + cleanName;
      assetMap.set(remoteUrl, rel);
      return rel;
    }
    const data = await fetchUrl(remoteUrl);
    if (data.length === 0) { assetMap.set(remoteUrl, null); return null; }
    fs.writeFileSync(localPath, data);
    const rel = 'images/' + cleanName;
    assetMap.set(remoteUrl, rel);
    console.log(`  Image: ${rel}`);
    return rel;
  } catch (e) {
    assetMap.set(remoteUrl, null);
    return null;
  }
}

function rewriteLinks(html) {
  for (const [orig, local] of Object.entries(NAV_MAP)) {
    html = html.replaceAll(`href="${orig}"`, `href="${local}"`);
    html = html.replaceAll(`href="${orig}/"`, `href="${local}"`);
    html = html.replaceAll(`href="https://www.lowermsfoundation.org${orig}"`, `href="${local}"`);
    html = html.replaceAll(`href="https://www.lowermsfoundation.org${orig}/"`, `href="${local}"`);
  }
  html = html.replaceAll('href="/s/', 'href="files/');
  html = html.replace(/href="\/lmrf\//g, 'href="https://www.lowermsfoundation.org/lmrf/');
  html = html.replaceAll('<base href="">', '');
  html = html.replace(/href="https:\/\/images\.squarespace-cdn\.com\/[^"]*favicon[^"]*"/g, 'href="favicon.ico"');
  html = html.replace(/<link[^>]*href="https:\/\/images\.squarespace-cdn\.com"[^>]*>/g, '');
  // Donate nav -> PayPal
  const PAYPAL = 'https://www.paypal.com/donate?token=fPg9LuFa9121K_HDyZVHkUs4L6Xuwg3gKG4w_MSfisa1zzrcq-PtnNC190Fc_6-8vZjTLSvpb0Lmd7eL';
  html = html.replace(
    /href="donate\.html" class="Header-nav-item">Donate/g,
    `href="${PAYPAL}" target="_blank" rel="noopener" class="Header-nav-item">Donate`
  );
  html = html.replace(
    /href="donate\.html" class="Mobile-overlay-nav-item">\n\s*Donate/g,
    `href="${PAYPAL}" target="_blank" rel="noopener" class="Mobile-overlay-nav-item">\n        Donate`
  );
  return html;
}

async function processImages(html) {
  const imgRegex = /(?:src|data-src|data-image)="(https?:\/\/images\.squarespace-cdn\.com[^"]+)"/g;
  const imgUrls = new Set();
  let match;
  while ((match = imgRegex.exec(html)) !== null) {
    imgUrls.add(match[1].split('?')[0]);
  }
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

(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: true, args: ['--no-sandbox'],
  });

  for (const { url, file } of PAGES) {
    console.log(`\nCapturing: ${url}`);
    const page = await browser.newPage();
    await page.setViewport({ width: 1400, height: 900 });
    await page.goto(url, { waitUntil: 'networkidle0', timeout: 45000 });
    await new Promise(r => setTimeout(r, 3000));
    let html = await page.content();
    await page.close();

    html = await processImages(html);
    html = rewriteLinks(html);
    html = html.replace('</head>', '<link rel="stylesheet" href="css/static-fixes.css">\n</head>');
    html = html.replace('</body>', '<script src="js/parallax-fix.js"></script>\n</body>');

    // Add newsletter handler
    const nlScript = `
<script>
(function() {
  var forms = document.querySelectorAll('.newsletter-form');
  forms.forEach(function(form) {
    form.onsubmit = function(e) {
      e.preventDefault();
      var emailInput = form.querySelector('input[type=email]');
      if (!emailInput || !emailInput.value) { alert('Please enter your email address.'); return false; }
      window.location.href = 'mailto:info@lowermsfoundation.org?subject=' +
        encodeURIComponent('Newsletter Signup') +
        '&body=' + encodeURIComponent('Please add me to the newsletter: ' + emailInput.value);
      var btn = form.querySelector('button');
      if (btn) btn.textContent = 'Opening email client...';
      return false;
    };
  });
})();
</script>`;
    html = html.replace('</body>', nlScript + '\n</body>');

    // Replace Squarespace form onsubmit
    html = html.replace(
      /onsubmit="return \(function \(form\) \{[\s\S]*?\}\)\(this\);"/g,
      'onsubmit="return false;"'
    );

    fs.writeFileSync(path.join(OUT, file), html, 'utf-8');
    console.log(`  Saved: ${file} (${html.length.toLocaleString()} bytes)`);
  }

  await browser.close();

  // Now fix get-involved.html to point to these new pages
  console.log('\nFixing get-involved.html links...');
  let giHtml = fs.readFileSync(path.join(OUT, 'get-involved.html'), 'utf-8');
  giHtml = giHtml.replaceAll('href="get-involved.html" class="sqs-block-button-element--large sqs-button-element--secondary sqs-block-button-element" data-sqsp-button="" data-initialized="true">\n      Volunteer',
    'href="volunteer.html" class="sqs-block-button-element--large sqs-button-element--secondary sqs-block-button-element" data-sqsp-button="" data-initialized="true">\n      Volunteer');
  giHtml = giHtml.replaceAll('href="get-involved.html" class="sqs-block-button-element--large sqs-button-element--secondary sqs-block-button-element" data-sqsp-button="" data-initialized="true">\n      Become an Advocate',
    'href="advocate.html" class="sqs-block-button-element--large sqs-button-element--secondary sqs-block-button-element" data-sqsp-button="" data-initialized="true">\n      Become an Advocate');
  fs.writeFileSync(path.join(OUT, 'get-involved.html'), giHtml, 'utf-8');
  console.log('  Fixed: Volunteer -> volunteer.html');
  console.log('  Fixed: Become an Advocate -> advocate.html');

  // Also fix any other pages that link to /volunteer-1 or /advocate
  for (const f of fs.readdirSync(OUT).filter(f => f.endsWith('.html'))) {
    let html = fs.readFileSync(path.join(OUT, f), 'utf-8');
    const orig = html;
    html = html.replaceAll('href="get-involved.html">Volunteer', 'href="volunteer.html">Volunteer');
    if (html !== orig) {
      fs.writeFileSync(path.join(OUT, f), html, 'utf-8');
      console.log(`  Also fixed in: ${f}`);
    }
  }

  console.log('\nDone!');
})();
