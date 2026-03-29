/**
 * Full site scrub — desktop and mobile.
 * Takes screenshots, tests links, checks images, forms, iframes.
 */
import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SITE = 'https://www.lowermsfoundation.org';
const SCRUB_DIR = path.join(import.meta.dirname, 'scrub-results');

const PAGES = [
  { path: '/', name: 'home' },
  { path: '/who-we-are', name: 'who-we-are' },
  { path: '/our-programs', name: 'our-programs' },
  { path: '/summer-camps', name: 'summer-camps' },
  { path: '/new-page-2', name: 'river-stewards' },
  { path: '/get-involved', name: 'get-involved' },
  { path: '/calendar', name: 'calendar' },
  { path: '/lmrf', name: 'blog' },
  { path: '/contact', name: 'contact' },
  { path: '/donate', name: 'donate' },
  { path: '/camp-application', name: 'camp-application' },
  { path: '/delta-day-camp', name: 'delta-day-camp' },
  { path: '/volunteer-1', name: 'volunteer' },
  { path: '/advocate', name: 'advocate' },
];

const VIEWPORTS = [
  { name: 'desktop', width: 1400, height: 900 },
  { name: 'mobile', width: 375, height: 812 },
];

const issues = [];

function log(msg) {
  console.log(msg);
}

function issue(page, viewport, msg) {
  const entry = `[${page}][${viewport}] ${msg}`;
  issues.push(entry);
  console.log(`  >> ISSUE: ${msg}`);
}

async function scrubPage(browser, pagePath, pageName) {
  for (const vp of VIEWPORTS) {
    log(`\n--- ${pageName} (${vp.name} ${vp.width}x${vp.height}) ---`);

    const page = await browser.newPage();
    await page.setViewport({ width: vp.width, height: vp.height });

    try {
      const resp = await page.goto(`${SITE}${pagePath}`, {
        waitUntil: 'networkidle0', timeout: 30000,
      });

      if (!resp || resp.status() !== 200) {
        issue(pageName, vp.name, `HTTP ${resp ? resp.status() : 'no response'}`);
        await page.close();
        continue;
      }

      // Wait for rendering
      await new Promise(r => setTimeout(r, 2000));

      // Screenshot
      const ssPath = path.join(SCRUB_DIR, `${pageName}-${vp.name}.png`);
      await page.screenshot({ path: ssPath, fullPage: true });
      log(`  Screenshot: ${ssPath}`);

      // Check broken images
      const brokenImages = await page.evaluate(() => {
        const broken = [];
        document.querySelectorAll('img').forEach(img => {
          if (img.src && !img.complete) {
            broken.push(img.src);
          } else if (img.naturalWidth === 0 && img.src && !img.src.includes('pixel.gif')) {
            broken.push(img.src);
          }
        });
        return broken;
      });
      if (brokenImages.length > 0) {
        issue(pageName, vp.name, `${brokenImages.length} broken images: ${brokenImages.slice(0, 3).join(', ')}`);
      } else {
        log(`  Images: OK`);
      }

      // Check mobile nav (mobile only)
      if (vp.name === 'mobile') {
        const mobileNav = await page.evaluate(() => {
          const bar = document.querySelector('.Mobile-bar');
          const btn = document.querySelector('.Mobile-bar-menu');
          if (!bar || !btn) return { barVisible: false, btnVisible: false };

          const barStyle = window.getComputedStyle(bar);
          const btnStyle = window.getComputedStyle(btn);
          const btnRect = btn.getBoundingClientRect();

          // Check all SVGs in the button for visibility
          const svgs = btn.querySelectorAll('svg');
          const visibleSvgs = [];
          svgs.forEach(svg => {
            const s = window.getComputedStyle(svg);
            if (s.display !== 'none' && s.visibility !== 'hidden') {
              visibleSvgs.push(svg.className.baseVal);
            }
          });

          return {
            barVisible: barStyle.display !== 'none',
            barHeight: bar.getBoundingClientRect().height,
            btnVisible: btnStyle.display !== 'none' && btnRect.width > 0,
            btnSize: `${btnRect.width}x${btnRect.height}`,
            visibleSvgs,
            totalSvgs: svgs.length,
          };
        });

        if (!mobileNav.barVisible) {
          issue(pageName, vp.name, 'Mobile bar not visible');
        } else if (!mobileNav.btnVisible) {
          issue(pageName, vp.name, 'Mobile menu button not visible');
        } else if (mobileNav.visibleSvgs.length === 0) {
          issue(pageName, vp.name, `Menu button visible but NO icon SVG showing (${mobileNav.totalSvgs} SVGs all hidden)`);
        } else {
          log(`  Mobile nav: bar=${mobileNav.barHeight}px, btn=${mobileNav.btnSize}, icon=${mobileNav.visibleSvgs[0]}`);
        }

        // Try clicking hamburger
        try {
          await page.click('.Mobile-bar-menu');
          await new Promise(r => setTimeout(r, 500));

          const overlayOpen = await page.evaluate(() => {
            const o = document.querySelector('.Mobile-overlay');
            if (!o) return false;
            const s = window.getComputedStyle(o);
            return s.display !== 'none' && o.getBoundingClientRect().width > 0;
          });

          if (overlayOpen) {
            log(`  Mobile menu opens: YES`);

            // Check nav links in overlay
            const navLinks = await page.evaluate(() => {
              const links = [];
              document.querySelectorAll('.Mobile-overlay-nav-item').forEach(a => {
                if (a.tagName === 'A') {
                  links.push({ text: a.textContent.trim(), href: a.getAttribute('href') });
                }
              });
              return links;
            });
            log(`  Mobile nav links: ${navLinks.length} (${navLinks.map(l => l.text).join(', ')})`);

            // Screenshot with menu open
            const ssMenuPath = path.join(SCRUB_DIR, `${pageName}-mobile-menu-open.png`);
            await page.screenshot({ path: ssMenuPath, fullPage: false });

            // Close it
            const closeBtn = await page.$('.Mobile-overlay-close');
            if (closeBtn) await closeBtn.click();
            await new Promise(r => setTimeout(r, 300));
          } else {
            issue(pageName, vp.name, 'Mobile menu does NOT open on click');
          }
        } catch (e) {
          issue(pageName, vp.name, `Click test failed: ${e.message}`);
        }
      }

      // Check desktop nav (desktop only)
      if (vp.name === 'desktop') {
        const desktopNav = await page.evaluate(() => {
          const header = document.querySelector('.Header');
          if (!header) return { visible: false };
          const style = window.getComputedStyle(header);
          const links = [];
          header.querySelectorAll('.Header-nav-item').forEach(a => {
            links.push({ text: a.textContent.trim(), href: a.getAttribute('href') });
          });
          return {
            visible: style.display !== 'none',
            height: header.getBoundingClientRect().height,
            links,
          };
        });

        if (!desktopNav.visible || desktopNav.height === 0) {
          issue(pageName, vp.name, 'Desktop header not visible');
        } else {
          log(`  Desktop nav: ${desktopNav.links.length} links, height=${desktopNav.height}px`);
        }
      }

      // Check forms
      const forms = await page.evaluate(() => {
        const results = [];
        document.querySelectorAll('form').forEach(form => {
          const action = form.getAttribute('action') || '';
          const cls = form.className;
          const inputs = form.querySelectorAll('input, textarea, select').length;
          const submitBtn = form.querySelector('button[type=submit], input[type=submit], button:not([type])');
          results.push({
            action: action.substring(0, 60),
            cls: cls.substring(0, 40),
            inputs,
            hasSubmit: !!submitBtn,
          });
        });
        return results;
      });
      if (forms.length > 0) {
        for (const f of forms) {
          if (f.action.includes('squarespace') && !f.cls.includes('newsletter')) {
            issue(pageName, vp.name, `Form still pointing to Squarespace: ${f.action}`);
          }
        }
        log(`  Forms: ${forms.length}`);
      }

      // Check iframes
      const iframes = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('iframe')).map(f => ({
          src: f.src || '',
          width: f.getBoundingClientRect().width,
          height: f.getBoundingClientRect().height,
        })).filter(f => f.src && !f.src.includes('recaptcha'));
      });
      if (iframes.length > 0) {
        for (const f of iframes) {
          if (f.width === 0 || f.height === 0) {
            issue(pageName, vp.name, `Hidden iframe: ${f.src.substring(0, 60)}`);
          } else {
            log(`  Iframe: ${f.src.substring(0, 50)} (${f.width}x${f.height})`);
          }
        }
      }

      // Check content buttons
      const buttons = await page.evaluate(() => {
        const results = [];
        document.querySelectorAll('a[class*="button"]').forEach(a => {
          const text = a.textContent.trim().replace(/\s+/g, ' ');
          const href = a.getAttribute('href') || '';
          const rect = a.getBoundingClientRect();
          if (text) {
            results.push({
              text: text.substring(0, 50),
              href: href.substring(0, 80),
              visible: rect.width > 0 && rect.height > 0,
            });
          }
        });
        return results;
      });
      if (buttons.length > 0) {
        log(`  Buttons: ${buttons.length}`);
        for (const b of buttons) {
          if (!b.href || b.href === '#') {
            issue(pageName, vp.name, `Empty button: "${b.text}"`);
          }
          if (!b.visible) {
            // Not necessarily an issue on mobile where desktop buttons may be hidden
            if (vp.name === 'desktop') {
              issue(pageName, vp.name, `Hidden button: "${b.text}"`);
            }
          }
        }
      }

      // Check footer
      const footer = await page.evaluate(() => {
        const f = document.querySelector('footer, .Footer');
        if (!f) return null;
        return {
          visible: f.getBoundingClientRect().height > 0,
          hasContact: f.textContent.includes('870'),
          hasEmail: f.textContent.includes('info@lowermsfoundation.org'),
        };
      });
      if (!footer || !footer.visible) {
        issue(pageName, vp.name, 'Footer not visible');
      } else {
        log(`  Footer: OK`);
      }

    } catch (e) {
      issue(pageName, vp.name, `Page load error: ${e.message}`);
    }

    await page.close();
  }
}

async function main() {
  fs.mkdirSync(SCRUB_DIR, { recursive: true });

  log('LMRF SITE SCRUB — DESKTOP & MOBILE');
  log(`Testing ${PAGES.length} pages x ${VIEWPORTS.length} viewports = ${PAGES.length * VIEWPORTS.length} checks`);
  log(`Site: ${SITE}`);
  log(`Screenshots: ${SCRUB_DIR}\n`);

  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: true, args: ['--no-sandbox'],
  });

  for (const { path: pagePath, name } of PAGES) {
    await scrubPage(browser, pagePath, name);
  }

  await browser.close();

  // Summary
  log(`\n${'='.repeat(60)}`);
  log('SCRUB COMPLETE');
  log(`${'='.repeat(60)}`);
  log(`Pages tested: ${PAGES.length}`);
  log(`Viewports: ${VIEWPORTS.map(v => v.name).join(', ')}`);
  log(`Total issues: ${issues.length}`);

  if (issues.length > 0) {
    log('\nISSUES FOUND:');
    for (const i of issues) {
      log(`  >> ${i}`);
    }
  } else {
    log('\nNO ISSUES FOUND');
  }

  // Write report
  const report = [
    'LMRF Site Scrub Report',
    `Date: ${new Date().toISOString()}`,
    `Site: ${SITE}`,
    '',
    `Total issues: ${issues.length}`,
    '',
    ...issues.map(i => `ISSUE: ${i}`),
  ].join('\n');
  fs.writeFileSync(path.join(SCRUB_DIR, 'report.txt'), report);
  log(`\nReport saved: ${path.join(SCRUB_DIR, 'report.txt')}`);
}

main().catch(console.error);
