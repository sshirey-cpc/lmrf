import puppeteer from 'puppeteer-core';
import { createServer } from 'http';
import { readFileSync, existsSync } from 'fs';
import { join, extname } from 'path';

const siteDir = 'C:\\Users\\scott\\lmrf\\website\\site';
const mimeTypes = {
  '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
};

const server = createServer((req, res) => {
  let url = req.url.split('?')[0];
  if (url === '/') url = '/index.html';
  if (!extname(url)) url += '.html';
  const filePath = join(siteDir, url);
  if (existsSync(filePath)) {
    res.writeHead(200, { 'Content-Type': mimeTypes[extname(filePath)] || 'application/octet-stream' });
    res.end(readFileSync(filePath));
  } else {
    res.writeHead(404); res.end('Not found');
  }
});

server.listen(8769, async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true, args: ['--no-sandbox'],
  });
  const page = await browser.newPage();

  await page.setViewport({ width: 1280, height: 900 });
  await page.goto('http://localhost:8769/community-canoe', { waitUntil: 'networkidle0', timeout: 30000 });
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: 'C:/Users/scott/lmrf/scrape/canoe-desktop.png', fullPage: true });
  console.log('Saved: canoe-desktop.png');

  await page.setViewport({ width: 375, height: 667 });
  await page.goto('http://localhost:8769/community-canoe', { waitUntil: 'networkidle0', timeout: 30000 });
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: 'C:/Users/scott/lmrf/scrape/canoe-mobile.png', fullPage: true });
  console.log('Saved: canoe-mobile.png');

  // Also check nav dropdown on homepage
  await page.setViewport({ width: 1280, height: 900 });
  await page.goto('http://localhost:8769/', { waitUntil: 'networkidle0', timeout: 30000 });
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: 'C:/Users/scott/lmrf/scrape/nav-check.png', fullPage: false });
  console.log('Saved: nav-check.png');

  await browser.close();
  server.close();
});
