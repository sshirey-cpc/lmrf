import puppeteer from 'puppeteer-core';

const browser = await puppeteer.launch({
  executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  headless: true, args: ['--no-sandbox'],
});

const page = await browser.newPage();
await page.setViewport({ width: 375, height: 812 });
await page.goto('https://www.lowermsfoundation.org/?v=9', { waitUntil: 'networkidle0', timeout: 30000 });
await new Promise(r => setTimeout(r, 3000));
await page.screenshot({ path: 'mobile-now.png', fullPage: false });
console.log('Saved: mobile-now.png');

// Also click the menu
await page.click('.Mobile-bar-menu');
await new Promise(r => setTimeout(r, 500));
await page.screenshot({ path: 'mobile-menu-now.png', fullPage: false });
console.log('Saved: mobile-menu-now.png');

await browser.close();
