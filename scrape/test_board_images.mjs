import puppeteer from 'puppeteer-core';

const browser = await puppeteer.launch({
  executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  headless: true, args: ['--no-sandbox'],
});

const page = await browser.newPage();
await page.setViewport({ width: 1400, height: 900 });
await page.goto('https://www.lowermsfoundation.org/who-we-are', { waitUntil: 'networkidle0', timeout: 30000 });
await new Promise(r => setTimeout(r, 3000));

const imgs = await page.evaluate(() => {
  const results = [];
  document.querySelectorAll('img').forEach(img => {
    const src = img.getAttribute('src') || '';
    if (src.includes('IMG_') || src.includes('john-ruskey')) {
      const rect = img.getBoundingClientRect();
      const style = window.getComputedStyle(img);
      const parent = img.parentElement;
      const parentStyle = parent ? window.getComputedStyle(parent) : null;
      results.push({
        src: src.split('/').pop(),
        width: rect.width,
        height: rect.height,
        display: style.display,
        visibility: style.visibility,
        opacity: style.opacity,
        naturalW: img.naturalWidth,
        naturalH: img.naturalHeight,
        complete: img.complete,
        parentTag: parent ? parent.tagName : 'none',
        parentDisplay: parentStyle ? parentStyle.display : 'N/A',
        parentOverflow: parentStyle ? parentStyle.overflow : 'N/A',
        parentHeight: parent ? parent.getBoundingClientRect().height : 0,
        inlineStyle: img.getAttribute('style') || '',
      });
    }
  });
  return results;
});

for (const img of imgs) {
  console.log(`\n${img.src}:`);
  console.log(`  rendered: ${img.width}x${img.height}, natural: ${img.naturalW}x${img.naturalH}`);
  console.log(`  display: ${img.display}, visibility: ${img.visibility}, complete: ${img.complete}`);
  console.log(`  parent: ${img.parentTag} display=${img.parentDisplay} overflow=${img.parentOverflow} height=${img.parentHeight}`);
  console.log(`  inline style: ${img.inlineStyle.substring(0, 100)}`);
}

await browser.close();
