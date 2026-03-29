import puppeteer from 'puppeteer-core';

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

const browser = await puppeteer.launch({
  executablePath: CHROME, headless: true, args: ['--no-sandbox'],
});

const page = await browser.newPage();
await page.setViewport({ width: 375, height: 812 });
await page.goto('https://www.lowermsfoundation.org', { waitUntil: 'networkidle0', timeout: 30000 });

// Check hamburger button
const info = await page.evaluate(() => {
  const btn = document.querySelector('.Mobile-bar-menu');
  const bar = document.querySelector('.Mobile-bar');
  const overlay = document.querySelector('.Mobile-overlay');
  const header = document.querySelector('.Header');

  function getInfo(el, label) {
    if (!el) return { label, found: false };
    const rect = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    return {
      label,
      found: true,
      display: style.display,
      visibility: style.visibility,
      opacity: style.opacity,
      position: style.position,
      width: rect.width,
      height: rect.height,
      top: rect.top,
      zIndex: style.zIndex,
    };
  }

  return [
    getInfo(bar, 'Mobile-bar'),
    getInfo(btn, 'Mobile-bar-menu button'),
    getInfo(overlay, 'Mobile-overlay'),
    getInfo(header, 'Header'),
  ];
});

for (const i of info) {
  console.log(`\n${i.label}:`);
  delete i.label;
  for (const [k, v] of Object.entries(i)) {
    console.log(`  ${k}: ${v}`);
  }
}

await page.screenshot({ path: 'mobile-test.png', fullPage: false });
console.log('\nScreenshot: mobile-test.png');

await browser.close();
