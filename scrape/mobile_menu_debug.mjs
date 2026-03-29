import puppeteer from 'puppeteer-core';

const browser = await puppeteer.launch({
  executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  headless: true, args: ['--no-sandbox'],
});

const page = await browser.newPage();
// iPhone SE viewport
await page.setViewport({ width: 375, height: 667 });
await page.goto('https://www.lowermsfoundation.org/?v=30', {
  waitUntil: 'networkidle0', timeout: 30000,
});
await new Promise(r => setTimeout(r, 3000));

// Open menu
await page.click('.Mobile-bar-menu');
await new Promise(r => setTimeout(r, 1500));

// Screenshot at actual viewport size (not full page)
await page.screenshot({ path: 'menu-viewport.png', fullPage: false });
console.log('Saved: menu-viewport.png (viewport only)');

// Full page screenshot to see everything
await page.screenshot({ path: 'menu-fullpage.png', fullPage: true });
console.log('Saved: menu-fullpage.png (full page)');

// Check if menu is scrollable — get overlay dimensions
const overlayInfo = await page.evaluate(() => {
  const overlay = document.querySelector('.Mobile-overlay');
  const menuMain = document.querySelector('.Mobile-overlay-menu-main');
  const nav = document.querySelector('.Mobile-overlay-nav--primary');
  const items = document.querySelectorAll('.Mobile-overlay-nav-item, .Mobile-overlay-nav-item--folder');
  const secondaryItems = document.querySelectorAll('.Mobile-overlay-nav--secondary .Mobile-overlay-nav-item');

  return {
    overlayDisplay: overlay ? getComputedStyle(overlay).display : 'not found',
    overlayHeight: overlay ? overlay.scrollHeight : 0,
    overlayClientHeight: overlay ? overlay.clientHeight : 0,
    overlayOverflow: overlay ? getComputedStyle(overlay).overflow : '',
    menuMainDisplay: menuMain ? getComputedStyle(menuMain).display : 'not found',
    navItemCount: items.length,
    secondaryCount: secondaryItems.length,
    itemTexts: Array.from(items).map(i => ({
      text: i.textContent.trim(),
      visible: i.offsetHeight > 0,
      top: i.getBoundingClientRect().top,
      bottom: i.getBoundingClientRect().bottom,
    })),
    secondaryTexts: Array.from(secondaryItems).map(i => ({
      text: i.textContent.trim(),
      visible: i.offsetHeight > 0,
      top: i.getBoundingClientRect().top,
    })),
    viewportHeight: window.innerHeight,
  };
});
console.log(JSON.stringify(overlayInfo, null, 2));

await page.close();
await browser.close();
