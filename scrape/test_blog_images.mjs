import puppeteer from 'puppeteer-core';

const browser = await puppeteer.launch({
  executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  headless: true, args: ['--no-sandbox'],
});
const page = await browser.newPage();
const failedImages = [];
page.on('requestfailed', r => {
  if (r.url().includes('IMG_')) failedImages.push('FAILED: ' + r.url());
});
await page.goto('https://www.lowermsfoundation.org/lmrf/2018/6/11/day-1-no-fear/', { waitUntil: 'networkidle0', timeout: 30000 });
await new Promise(r => setTimeout(r, 3000));
await page.screenshot({ path: 'C:/Users/scott/lmrf/scrape/blog-post-test.png', fullPage: true });

const imgs = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('img')).map(i => ({
    src: i.src,
    naturalWidth: i.naturalWidth,
    displayed: i.offsetWidth > 0
  }));
});
imgs.filter(i => i.src.includes('IMG_')).forEach(i => console.log(JSON.stringify(i)));
console.log('Failed:', failedImages);

await browser.close();
