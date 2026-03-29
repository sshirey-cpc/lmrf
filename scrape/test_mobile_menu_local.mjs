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
    const ext = extname(filePath);
    res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'application/octet-stream' });
    res.end(readFileSync(filePath));
  } else {
    res.writeHead(404);
    res.end('Not found');
  }
});

server.listen(8765, async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true, args: ['--no-sandbox'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 375, height: 812 });
  await page.goto('http://localhost:8765/', { waitUntil: 'networkidle0', timeout: 30000 });
  await new Promise(r => setTimeout(r, 2000));

  // Open menu
  await page.click('.Mobile-bar-menu');
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: 'local-menu-open.png', fullPage: false });
  console.log('Saved: local-menu-open.png');

  // Click Youth Programs
  await page.click('.Mobile-overlay-nav-item--folder');
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: 'local-menu-folder.png', fullPage: false });
  console.log('Saved: local-menu-folder.png');

  // Click Back
  await page.click('.Mobile-overlay-folder-item--toggle');
  await new Promise(r => setTimeout(r, 500));
  await page.screenshot({ path: 'local-menu-back.png', fullPage: false });
  console.log('Saved: local-menu-back.png');

  await page.close();
  await browser.close();
  server.close();
});
