import puppeteer from 'puppeteer-core';

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

const browser = await puppeteer.launch({
  executablePath: CHROME, headless: true, args: ['--no-sandbox'],
});

const page = await browser.newPage();
await page.setViewport({ width: 375, height: 812 });
await page.goto('https://www.lowermsfoundation.org', { waitUntil: 'networkidle0', timeout: 30000 });

console.log('Before click:');
let overlayDisplay = await page.evaluate(() => {
  return window.getComputedStyle(document.querySelector('.Mobile-overlay')).display;
});
console.log('  Overlay display:', overlayDisplay);

// Click the hamburger
await page.click('.Mobile-bar-menu');
await new Promise(r => setTimeout(r, 500));

console.log('After click:');
overlayDisplay = await page.evaluate(() => {
  const o = document.querySelector('.Mobile-overlay');
  const style = window.getComputedStyle(o);
  return {
    display: style.display,
    visibility: style.visibility,
    width: o.getBoundingClientRect().width,
    height: o.getBoundingClientRect().height,
    bodyClass: document.body.className.includes('is-mobile-overlay-active'),
  };
});
console.log('  Overlay:', JSON.stringify(overlayDisplay));

await page.screenshot({ path: 'mobile-after-click.png', fullPage: false });
console.log('Screenshot: mobile-after-click.png');

await browser.close();
