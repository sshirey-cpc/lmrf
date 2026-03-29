import puppeteer from 'puppeteer-core';

const browser = await puppeteer.launch({
  executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  headless: true, args: ['--no-sandbox'],
});

const page = await browser.newPage();
await page.setViewport({ width: 375, height: 812 });
await page.goto('https://www.lowermsfoundation.org/?v=7', { waitUntil: 'networkidle0', timeout: 30000 });

// Get detailed info about the hamburger area
const info = await page.evaluate(() => {
  const bar = document.querySelector('.Mobile-bar');
  const btn = document.querySelector('.Mobile-bar-menu');
  const svg = btn ? btn.querySelector('svg') : null;
  const lines = svg ? svg.querySelectorAll('line') : [];

  // What's the actual HTML of the button?
  const btnHtml = btn ? btn.innerHTML.substring(0, 500) : 'NOT FOUND';

  // What color is the mobile bar background?
  const barStyle = bar ? window.getComputedStyle(bar) : null;
  const barBg = barStyle ? barStyle.backgroundColor : 'N/A';

  return {
    barBg,
    btnHtml,
    lineCount: lines.length,
    svgDisplay: svg ? window.getComputedStyle(svg).display : 'N/A',
  };
});
console.log('Mobile bar background:', info.barBg);
console.log('Button HTML:', info.btnHtml);
console.log('SVG line count:', info.lineCount);
console.log('SVG display:', info.svgDisplay);

await page.screenshot({ path: 'mobile-live.png', fullPage: false });
console.log('\nScreenshot saved: mobile-live.png');

await browser.close();
