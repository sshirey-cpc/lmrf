import puppeteer from 'puppeteer-core';

const browser = await puppeteer.launch({
  executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  headless: true, args: ['--no-sandbox'],
});

for (const [url, name] of [
  ['https://www.lowermsfoundation.org/our-programs?v=11', 'programs'],
  ['https://www.lowermsfoundation.org/summer-camps?v=11', 'summer-camps'],
]) {
  for (const [w, h, label] of [[1400, 900, 'desktop'], [375, 812, 'mobile']]) {
    const page = await browser.newPage();
    await page.setViewport({ width: w, height: h });
    await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });
    await new Promise(r => setTimeout(r, 2000));
    await page.screenshot({ path: `${name}-${label}.png`, fullPage: true });
    console.log(`Saved: ${name}-${label}.png`);
    await page.close();
  }
}

await browser.close();
