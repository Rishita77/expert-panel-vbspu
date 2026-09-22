const { chromium } = require('playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');

(async () => {
  const credentials = JSON.parse(fs.readFileSync('.local/demo-access.json', 'utf8'));
  const base = 'http://127.0.0.1:8000';
  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  try {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await context.newPage();
    const failures = [];
    page.on('pageerror', e => failures.push(e.message));
    page.on('response', r => { if (r.status() >= 500) failures.push(r.url()); });
    async function login(user) {
      await page.goto(base + '/office/login/');
      await page.locator('[name=username]').fill(user.username);
      await page.locator('[name=password]').fill(user.password);
      await page.getByRole('button', { name: 'साइन इन', exact: true }).click();
      await page.getByRole('heading', { name: 'कार्यालय कार्यक्षेत्र' }).waitFor();
    }
    await login(credentials.poc);
    await page.goto(base + '/office/allocation/run/d113a23d-ab91-40d9-8cd9-f637e38bd07c/');
    await page.getByRole('button', { name: 'अंतिम चयन प्रारूप बनाएँ', exact: true }).click();
    await page.getByRole('heading', { name: 'अंतिम चयन और लॉक', exact: true }).waitFor();
    await page.getByLabel('प्रबन्ध समिति निर्णय सन्दर्भ', { exact: true }).fill('DEMO-MC-1');
    await page.getByLabel('प्रबन्ध समिति निर्णय तिथि', { exact: true }).fill('2026-09-13');
    await page.getByLabel('VC निर्णय सन्दर्भ', { exact: true }).fill('DEMO-VC-1');
    await page.getByLabel('VC निर्णय तिथि', { exact: true }).fill('2026-09-13');
    const boxes = page.locator('input[name=members]');
    await boxes.nth(1).check(); await boxes.nth(2).check(); await boxes.nth(3).check(); await boxes.nth(4).check();
    await page.getByRole('button', { name: 'प्रारूप सहेजें', exact: true }).click();
    await page.getByRole('button', { name: 'समीक्षा हेतु प्रस्तुत करें', exact: true }).click();
    await page.getByText('समीक्षा हेतु प्रस्तुत', { exact: true }).waitFor();
    const selectionUrl = page.url();
    await page.screenshot({ path: 'test-results/final-selection-processor.png', fullPage: true });
    await context.clearCookies();
    await login(credentials.reviewer);
    await page.goto(selectionUrl);
    await page.getByRole('heading', { name: 'समीक्षक निर्णय', exact: true }).waitFor();
    assert.equal(await page.getByRole('button', { name: 'अंतिम रूप से लॉक करें', exact: true }).count(), 1);
    await page.screenshot({ path: 'test-results/final-selection-reviewer.png', fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1));
    assert.deepEqual(failures, []);
    console.log('Final-selection browser: POC draft/submit, reviewer view and mobile layout passed.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
