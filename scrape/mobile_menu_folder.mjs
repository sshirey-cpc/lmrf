import puppeteer from 'puppeteer-core';

const browser = await puppeteer.launch({
  executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  headless: true, args: ['--no-sandbox'],
});

const page = await browser.newPage();
await page.setViewport({ width: 375, height: 812 });
await page.goto('https://www.lowermsfoundation.org/?v=28', {
  waitUntil: 'networkidle0', timeout: 30000,
});
await new Promise(r => setTimeout(r, 3000));

// Open hamburger menu
await page.click('.Mobile-bar-menu');
await new Promise(r => setTimeout(r, 1500));

// Click Youth Programs folder
await page.click('.Mobile-overlay-nav-item--folder');
await new Promise(r => setTimeout(r, 1000));

await page.screenshot({ path: 'mobile-menu-folder.png', fullPage: true });
console.log('Saved: mobile-menu-folder.png');

await page.close();
await browser.close();
