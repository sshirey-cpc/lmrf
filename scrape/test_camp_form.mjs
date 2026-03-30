import puppeteer from 'puppeteer-core';
import { createServer } from 'http';
import { readFileSync, existsSync } from 'fs';
import { join, extname } from 'path';

const siteDir = 'C:\\Users\\scott\\lmrf\\website\\site';
const mimeTypes = {
  '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.pdf': 'application/pdf',
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

server.listen(8768, async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true, args: ['--no-sandbox'],
  });

  const page = await browser.newPage();

  // Desktop
  await page.setViewport({ width: 1280, height: 900 });
  await page.goto('http://localhost:8768/camp-application', { waitUntil: 'networkidle0', timeout: 30000 });
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: 'C:/Users/scott/lmrf/scrape/camp-form-desktop.png', fullPage: true });
  console.log('Saved: camp-form-desktop.png');

  // Mobile
  await page.setViewport({ width: 375, height: 667 });
  await page.goto('http://localhost:8768/camp-application', { waitUntil: 'networkidle0', timeout: 30000 });
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: 'C:/Users/scott/lmrf/scrape/camp-form-mobile.png', fullPage: true });
  console.log('Saved: camp-form-mobile.png');

  await page.close();
  await browser.close();
  server.close();
});
