import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';
import { URL } from 'url';
import https from 'https';
import http from 'http';

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const OUT = path.join(import.meta.dirname, 'rendered-site');

const BLOG_POSTS = [
  '/lmrf/2019/6/8/meet-the-disciples',
  '/lmrf/2019/6/8/day-5-smiths-point-to-home',
  '/lmrf/2019/6/8/day-4-island-67-to-smiths-point',
  '/lmrf/2019/6/8/day-3-island-64-to-island-67',
  '/lmrf/2019/6/8/day-2-island-62-to-island-64',
  '/lmrf/2019/6/8/day-1-helena-to-island-62',
  '/lmrf/2019/4/22/summer-camp-video',
  '/lmrf/2018/7/11/delta-adventure-day-camp',
  '/lmrf/2018/6/16/day-5-circles-and-boxes',
  '/lmrf/2018/6/16/day-4-genesis',
  '/lmrf/2018/6/16/day-3-leadership',
  '/lmrf/2018/6/16/day-2-challenge',
  '/lmrf/2018/6/11/day-1-no-fear',
  '/lmrf/2018/6/4/creating-a-new-generation-of-stewards',
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
  '/volunteer-1': 'volunteer.html',
  '/advocate': 'advocate.html',
  '/camp-application': 'camp-application.html',
  '/delta-day-camp': 'delta-day-camp.html',
  '/camp-application-1': 'contact.html',
};

const PAYPAL = 'https://www.paypal.com/donate?token=fPg9LuFa9121K_HDyZVHkUs4L6Xuwg3gKG4w_MSfisa1zzrcq-PtnNC190Fc_6-8vZjTLSvpb0Lmd7eL';

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
    console.log(`    Image: ${rel}`);
    return rel;
  } catch (e) {
    assetMap.set(remoteUrl, null);
    return null;
  }
}

function pathToLocal(origPath) {
  // Convert /lmrf/2018/6/11/day-1-no-fear to lmrf/2018/6/11/day-1-no-fear/index.html
  const clean = origPath.replace(/^\//, '').replace(/\/$/, '');
  return clean + '/index.html';
}

function relativeFrom(fromFile, toFile) {
  // Calculate relative path from one file to another
  const fromDir = path.dirname(fromFile);
  return path.relative(fromDir, toFile).replace(/\\/g, '/');
}

function rewriteLinks(html, localFile) {
  // Rewrite nav links to relative paths
  for (const [orig, target] of Object.entries(NAV_MAP)) {
    const rel = relativeFrom(localFile, target);
    html = html.replaceAll(`href="${orig}"`, `href="${rel}"`);
    html = html.replaceAll(`href="${orig}/"`, `href="${rel}"`);
    html = html.replaceAll(`href="https://www.lowermsfoundation.org${orig}"`, `href="${rel}"`);
    html = html.replaceAll(`href="https://www.lowermsfoundation.org${orig}/"`, `href="${rel}"`);
  }

  // Rewrite blog post links to local paths
  for (const postPath of BLOG_POSTS) {
    const postLocal = pathToLocal(postPath);
    const rel = relativeFrom(localFile, postLocal);
    html = html.replaceAll(`href="${postPath}"`, `href="${rel}"`);
    html = html.replaceAll(`href="https://www.lowermsfoundation.org${postPath}"`, `href="${rel}"`);
  }

  // Fix /lmrf?author= links -> blog.html
  html = html.replace(/href="\/lmrf\?[^"]*"/g, `href="${relativeFrom(localFile, 'blog.html')}"`);
  html = html.replace(/href="https:\/\/www\.lowermsfoundation\.org\/lmrf\?[^"]*"/g, `href="${relativeFrom(localFile, 'blog.html')}"`);

  // PDF downloads
  html = html.replaceAll('href="/s/', `href="${relativeFrom(localFile, 'files/')}/`);

  // Clean up
  html = html.replaceAll('<base href="">', '');
  html = html.replace(/href="https:\/\/images\.squarespace-cdn\.com\/[^"]*favicon[^"]*"/g,
    `href="${relativeFrom(localFile, 'favicon.ico')}"`);
  html = html.replace(/<link[^>]*href="https:\/\/images\.squarespace-cdn\.com"[^>]*>/g, '');

  // Donate nav -> PayPal, content donate -> donate.html
  const donateRel = relativeFrom(localFile, 'donate.html');
  html = html.replace(
    new RegExp(`href="${donateRel.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}" class="Header-nav-item">Donate`, 'g'),
    `href="${PAYPAL}" target="_blank" rel="noopener" class="Header-nav-item">Donate`
  );
  html = html.replace(
    new RegExp(`href="${donateRel.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}" class="Mobile-overlay-nav-item">\\s*Donate`, 'g'),
    `href="${PAYPAL}" target="_blank" rel="noopener" class="Mobile-overlay-nav-item">\n        Donate`
  );

  // Fix YouTube protocol-relative
  html = html.replaceAll('src="//www.youtube.com', 'src="https://www.youtube.com');

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

  for (const postPath of BLOG_POSTS) {
    const url = `https://www.lowermsfoundation.org${postPath}`;
    const localFile = pathToLocal(postPath);
    const localDir = path.join(OUT, path.dirname(localFile));

    console.log(`\nCapturing: ${postPath}`);
    console.log(`  -> ${localFile}`);

    const page = await browser.newPage();
    await page.setViewport({ width: 1400, height: 900 });
    try {
      await page.goto(url, { waitUntil: 'networkidle0', timeout: 45000 });
      await new Promise(r => setTimeout(r, 3000));
    } catch (e) {
      console.log(`  ERROR loading page: ${e.message}`);
      await page.close();
      continue;
    }

    let html = await page.content();
    await page.close();

    // Process images - rewrite to relative paths from this blog post's location
    html = await processImages(html);
    // Image paths need to be relative from the blog post directory
    const depth = localFile.split('/').length - 1;
    const prefix = '../'.repeat(depth);
    html = html.replaceAll('src="images/', `src="${prefix}images/`);
    html = html.replaceAll("src='images/", `src='${prefix}images/`);

    // Rewrite links
    html = rewriteLinks(html, localFile);

    // Add static fixes (relative path)
    html = html.replace('</head>',
      `<link rel="stylesheet" href="${prefix}css/static-fixes.css">\n</head>`);
    html = html.replace('</body>',
      `<script src="${prefix}js/parallax-fix.js"></script>\n</body>`);

    // Fix CSS/JS paths that are relative to root
    html = html.replaceAll('href="css/', `href="${prefix}css/`);
    html = html.replaceAll('src="js/', `src="${prefix}js/`);
    html = html.replaceAll('src="js_site-bundle.js"', `src="${prefix}js_site-bundle.js"`);
    html = html.replaceAll('href="favicon.ico"', `href="${prefix}favicon.ico"`);

    // Newsletter handler
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

    // Save
    fs.mkdirSync(localDir, { recursive: true });
    fs.writeFileSync(path.join(OUT, localFile), html, 'utf-8');
    console.log(`  Saved: ${localFile} (${html.length.toLocaleString()} bytes)`);
  }

  await browser.close();

  // Now update blog.html to point to local blog posts instead of live site
  console.log('\nUpdating blog.html links...');
  let blogHtml = fs.readFileSync(path.join(OUT, 'blog.html'), 'utf-8');
  for (const postPath of BLOG_POSTS) {
    const localFile = pathToLocal(postPath);
    const rel = localFile; // blog.html is at root level
    blogHtml = blogHtml.replaceAll(
      `href="https://www.lowermsfoundation.org${postPath}"`,
      `href="${rel}"`
    );
    // Also catch any that were already relative
    blogHtml = blogHtml.replaceAll(`href="${postPath}"`, `href="${rel}"`);
  }
  // Fix author links
  blogHtml = blogHtml.replace(/href="https:\/\/www\.lowermsfoundation\.org\/lmrf\?[^"]*"/g, 'href="blog.html"');
  fs.writeFileSync(path.join(OUT, 'blog.html'), blogHtml, 'utf-8');
  console.log('  Updated blog.html');

  // Also update any other pages that link to blog posts
  for (const f of fs.readdirSync(OUT).filter(f => f.endsWith('.html'))) {
    let html = fs.readFileSync(path.join(OUT, f), 'utf-8');
    const orig = html;
    for (const postPath of BLOG_POSTS) {
      const localFile = pathToLocal(postPath);
      html = html.replaceAll(
        `href="https://www.lowermsfoundation.org${postPath}"`,
        `href="${localFile}"`
      );
    }
    if (html !== orig) {
      fs.writeFileSync(path.join(OUT, f), html, 'utf-8');
      console.log(`  Updated links in: ${f}`);
    }
  }

  console.log('\nDone! Blog posts captured.');
  console.log(`Total blog post files: ${BLOG_POSTS.length}`);
})();
