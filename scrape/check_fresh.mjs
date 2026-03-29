import puppeteer from 'puppeteer-core';

const browser = await puppeteer.launch({
  executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  headless: true, args: ['--no-sandbox'],
});

for (const [url, name] of [
  ['https://www.lowermsfoundation.org/our-programs?v=14', 'programs-fresh'],
  ['https://www.lowermsfoundation.org/summer-camps?v=14', 'summer-camps-fresh'],
]) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 900 });
  await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });
  await new Promise(r => setTimeout(r, 3000));
  await page.screenshot({ path: `${name}.png`, fullPage: true });
  console.log(`Saved: ${name}.png`);
  await page.close();
}

await browser.close();
