const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
	product: 'firefox'
  });
  const page = await browser.newPage();
  await page.goto('https://www.bannerbear.com');
  await page.screenshot({ path: 'example.png' });

  await browser.close();
})()

