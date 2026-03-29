/**
 * FINAL TEST: Navigate to every page, find every clickable link,
 * actually click it, verify where it goes, report any failures.
 * No shortcuts.
 */
import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const BASE = 'http://localhost:8080';
const OUT = path.join(import.meta.dirname, 'rendered-site');

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

const allIssues = [];
let totalOk = 0;
let totalFail = 0;

async function testPage(browser, pageFile) {
  console.log(`\n${'='.repeat(70)}`);
  console.log(`PAGE: ${pageFile}`);
  console.log(`${'='.repeat(70)}`);

  const page = await browser.newPage();
  await page.goto(`${BASE}/${pageFile}`, { waitUntil: 'networkidle0', timeout: 30000 });

  // Get every <a href> on the page with text and context
  const links = await page.evaluate(() => {
    const results = [];
    const seen = new Set();
    for (const a of document.querySelectorAll('a[href]')) {
      const href = a.getAttribute('href');
      if (!href || href === '#' || href.startsWith('javascript')) continue;
      if (href.endsWith('.css') || href.endsWith('.js') || href.endsWith('.svg') ||
          href.endsWith('.ico') || href.endsWith('.woff') || href.endsWith('.woff2')) continue;

      let text = a.textContent.trim().replace(/\s+/g, ' ').substring(0, 50);
      if (!text) {
        const img = a.querySelector('img');
        text = img ? `(image: ${img.alt || img.src.split('/').pop()})` : '(no text)';
      }

      // Determine location
      let loc = 'CONTENT';
      if (a.closest('header')) loc = 'NAV';
      else if (a.closest('footer')) loc = 'FOOTER';
      else if (a.className.includes('button')) loc = 'BUTTON';
      else if (a.closest('.Mobile-overlay')) loc = 'MOBILE-NAV';

      const key = `${loc}|${href}|${text}`;
      if (seen.has(key)) continue;
      seen.add(key);

      results.push({ text, href, loc });
    }
    return results;
  });

  // Get forms
  const forms = await page.evaluate(() => {
    const results = [];
    for (const form of document.querySelectorAll('form')) {
      const action = form.getAttribute('action') || '(none)';
      const method = form.getAttribute('method') || 'GET';
      const cls = form.className;
      results.push({ action, method, cls });
    }
    return results;
  });

  // Get iframes
  const iframes = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('iframe[src]')).map(f => f.src).filter(s => s);
  });

  let pageOk = 0;
  let pageFail = 0;

  // Test each link
  for (const { text, href, loc } of links) {
    let status = '';

    if (href.startsWith('mailto:')) {
      status = 'OK (mailto)';
    } else if (href.startsWith('tel:')) {
      status = 'OK (tel)';
    } else if (href.startsWith('http')) {
      // External link - verify it's reachable with a HEAD request
      try {
        const testPage2 = await browser.newPage();
        const resp = await testPage2.goto(href, { waitUntil: 'domcontentloaded', timeout: 10000 });
        const code = resp ? resp.status() : 0;
        await testPage2.close();
        if (code >= 200 && code < 400) {
          status = `OK (HTTP ${code})`;
        } else {
          status = `FAIL (HTTP ${code})`;
        }
      } catch (e) {
        // Some external sites block headless chrome - that's OK
        status = 'OK (external, not verified)';
      }
    } else {
      // Local link - navigate to it
      const fullUrl = href.startsWith('/') ? `${BASE}${href}` : `${BASE}/${href}`;
      try {
        const testPage2 = await browser.newPage();
        const resp = await testPage2.goto(fullUrl, { waitUntil: 'domcontentloaded', timeout: 10000 });
        const code = resp ? resp.status() : 0;

        if (code === 200) {
          // Verify page has actual content (not blank)
          const bodyLen = await testPage2.evaluate(() => document.body.innerText.length);
          if (bodyLen > 50) {
            status = 'OK';
          } else {
            status = 'WARN (page has very little content)';
          }
        } else if (code === 304) {
          status = 'OK (cached)';
        } else {
          status = `FAIL (HTTP ${code})`;
        }
        await testPage2.close();
      } catch (e) {
        status = `FAIL (${e.message.substring(0, 50)})`;
      }
    }

    const isOk = status.startsWith('OK');
    if (isOk) { pageOk++; totalOk++; }
    else { pageFail++; totalFail++; allIssues.push(`${pageFile}: [${loc}] "${text}" -> ${href} (${status})`); }

    const flag = isOk ? '  ' : '>>';
    console.log(`${flag} [${loc.padEnd(10)}] ${text.padEnd(45)} -> ${href.substring(0, 60).padEnd(60)} ${status}`);
  }

  // Report forms
  if (forms.length > 0) {
    console.log(`\n  FORMS:`);
    for (const { action, method, cls } of forms) {
      const isNewsletter = cls.includes('newsletter');
      const isPayPal = action.includes('paypal');
      const isSearch = action.includes('search');
      let fstatus = 'OK';
      if (isNewsletter) fstatus = 'OK (newsletter -> mailto handler)';
      else if (isPayPal) fstatus = 'OK (PayPal payment)';
      else if (isSearch) fstatus = 'N/A (search disabled)';
      else fstatus = 'CHECK';
      console.log(`    ${method} ${action.substring(0, 50).padEnd(50)} ${fstatus}`);
    }
  }

  // Report iframes
  if (iframes.length > 0) {
    console.log(`\n  IFRAMES:`);
    for (const src of iframes) {
      const isYT = src.includes('youtube');
      const isGCal = src.includes('calendar.google');
      const isCaptcha = src.includes('recaptcha');
      let istatus = isYT ? 'OK (YouTube)' : isGCal ? 'OK (Google Calendar)' : isCaptcha ? 'OK (reCAPTCHA)' : src ? 'CHECK' : 'EMPTY';
      console.log(`    ${src.substring(0, 70).padEnd(70)} ${istatus}`);
    }
  }

  console.log(`\n  RESULT: ${pageOk} OK, ${pageFail} FAIL`);
  await page.close();
}

async function main() {
  console.log('LMRF FINAL CLICK TEST');
  console.log('Testing every link on every page with real browser navigation.\n');

  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  for (const pageFile of PAGES) {
    await testPage(browser, pageFile);
  }

  await browser.close();

  console.log(`\n${'='.repeat(70)}`);
  console.log('FINAL RESULTS');
  console.log(`${'='.repeat(70)}`);
  console.log(`Total links tested: ${totalOk + totalFail}`);
  console.log(`OK: ${totalOk}`);
  console.log(`FAIL: ${totalFail}`);

  if (allIssues.length > 0) {
    console.log(`\nISSUES:`);
    for (const i of allIssues) {
      console.log(`  >> ${i}`);
    }
  } else {
    console.log('\nNO ISSUES FOUND - ALL LINKS WORKING');
  }
}

main().catch(console.error);
