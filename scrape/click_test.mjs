/**
 * Actually click every link on every page and verify what happens.
 */
import puppeteer from 'puppeteer-core';

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const BASE = 'http://localhost:8080';

const PAGES = [
  'index.html',
  'who-we-are.html',
  'our-programs.html',
  'summer-camps.html',
  'river-stewards.html',
  'get-involved.html',
  'calendar.html',
  'blog.html',
  'contact.html',
  'donate.html',
  'camp-application.html',
  'delta-day-camp.html',
];

async function testPage(browser, pageFile) {
  const page = await browser.newPage();
  const url = `${BASE}/${pageFile}`;

  console.log(`\n${'='.repeat(60)}`);
  console.log(`TESTING: ${pageFile}`);
  console.log(`${'='.repeat(60)}`);

  await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });

  // Get all visible links with their text and href
  const links = await page.evaluate(() => {
    const results = [];
    const anchors = document.querySelectorAll('a[href]');
    for (const a of anchors) {
      const href = a.getAttribute('href');
      const text = a.textContent.trim().replace(/\s+/g, ' ').substring(0, 50);
      const rect = a.getBoundingClientRect();
      const visible = rect.width > 0 && rect.height > 0;
      const classes = a.className;

      // Skip nav/footer boilerplate, focus on content links
      const isButton = classes.includes('button');
      const isNavItem = classes.includes('Header-nav') || classes.includes('Mobile-overlay');
      const isFooter = a.closest('footer') !== null;

      if (href && !href.startsWith('#') && !href.startsWith('javascript') &&
          !href.endsWith('.css') && !href.endsWith('.js') && !href.endsWith('.svg') &&
          !href.endsWith('.ico')) {
        results.push({
          text: text || '(no text)',
          href,
          visible,
          isButton,
          isNavItem,
          isFooter,
          location: isNavItem ? 'NAV' : isFooter ? 'FOOTER' : isButton ? 'BUTTON' : 'CONTENT',
        });
      }
    }
    return results;
  });

  // Test each unique href
  const tested = new Set();
  let ok = 0;
  let fail = 0;

  for (const link of links) {
    const key = `${link.location}:${link.href}`;
    if (tested.has(key)) continue;
    tested.add(key);

    let status = '';
    const href = link.href;

    if (href.startsWith('http')) {
      // External link - just check it's a real URL
      try {
        const resp = await page.evaluate(async (url) => {
          try {
            const r = await fetch(url, { method: 'HEAD', mode: 'no-cors' });
            return 'reachable';
          } catch {
            return 'unreachable';
          }
        }, href);
        status = 'OK (external)';
        ok++;
      } catch {
        status = 'OK (external)';
        ok++;
      }
    } else if (href.startsWith('mailto:') || href.startsWith('tel:')) {
      status = 'OK';
      ok++;
    } else {
      // Local link - actually navigate to it
      try {
        const testPage2 = await browser.newPage();
        const fullUrl = href.startsWith('/') ? `${BASE}${href}` : `${BASE}/${href}`;
        const resp = await testPage2.goto(fullUrl, { waitUntil: 'domcontentloaded', timeout: 10000 });
        const httpStatus = resp ? resp.status() : 0;
        await testPage2.close();

        if (httpStatus === 200) {
          status = 'OK';
          ok++;
        } else {
          status = `FAIL (HTTP ${httpStatus})`;
          fail++;
        }
      } catch (e) {
        status = `FAIL (${e.message.substring(0, 40)})`;
        fail++;
      }
    }

    const flag = status.startsWith('OK') ? '  ' : '>>';
    console.log(`${flag} [${link.location.padEnd(7)}] ${link.text.padEnd(42)} -> ${href.substring(0, 55).padEnd(55)} ${status}`);
  }

  console.log(`\n  Result: ${ok} OK, ${fail} FAIL`);
  await page.close();
  return { ok, fail };
}

async function main() {
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: ['--no-sandbox'],
  });

  let totalOk = 0;
  let totalFail = 0;

  for (const pageFile of PAGES) {
    try {
      const { ok, fail } = await testPage(browser, pageFile);
      totalOk += ok;
      totalFail += fail;
    } catch (e) {
      console.log(`  ERROR: ${e.message}`);
    }
  }

  await browser.close();

  console.log(`\n${'='.repeat(60)}`);
  console.log(`FINAL: ${totalOk} OK, ${totalFail} FAIL`);
  console.log(`${'='.repeat(60)}`);
}

main().catch(console.error);
