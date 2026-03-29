import puppeteer from 'puppeteer-core';

const browser = await puppeteer.launch({
  executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  headless: true, args: ['--no-sandbox'],
});

const pages = [
  ['/', 'home'],
  ['/who-we-are', 'who-we-are'],
  ['/our-programs', 'our-programs'],
  ['/summer-camps', 'summer-camps'],
  ['/new-page-2', 'river-stewards'],
  ['/get-involved', 'get-involved'],
  ['/calendar', 'calendar'],
  ['/lmrf', 'blog'],
  ['/contact', 'contact'],
  ['/donate', 'donate'],
  ['/camp-application', 'camp-application'],
  ['/delta-day-camp', 'delta-day-camp'],
  ['/volunteer-1', 'volunteer'],
  ['/advocate', 'advocate'],
];

for (const [path, name] of pages) {
  const page = await browser.newPage();
  await page.setViewport({ width: 375, height: 812 });
  try {
    await page.goto(`https://www.lowermsfoundation.org${path}?v=29`, {
      waitUntil: 'networkidle0', timeout: 30000,
    });
    await new Promise(r => setTimeout(r, 3000));
    await page.screenshot({ path: `mobile-${name}.png`, fullPage: true });
    console.log(`Saved: mobile-${name}.png`);
  } catch (e) {
    console.log(`ERROR: ${name} - ${e.message}`);
  }
  await page.close();
}

await browser.close();
