import puppeteer from 'puppeteer-core';

const browser = await puppeteer.launch({
  executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  headless: true, args: ['--no-sandbox'],
});

const page = await browser.newPage();
await page.setViewport({ width: 1400, height: 900 });
await page.goto('https://www.lowermsfoundation.org/summer-camps?v=10', { waitUntil: 'networkidle0', timeout: 30000 });
await new Promise(r => setTimeout(r, 3000));
await page.screenshot({ path: 'summer-camps-desktop-full.png', fullPage: true });
console.log('Saved: summer-camps-desktop-full.png');

await browser.close();
