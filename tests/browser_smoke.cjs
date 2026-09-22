// Run against the loopback preview. Uses Playwright from NODE_PATH or local installation.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const out = path.join(process.cwd(), 'test-results');
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.PLAYWRIGHT_CHANNEL ? { channel: process.env.PLAYWRIGHT_CHANNEL } : {}),
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
    const failures = [];
    page.on('pageerror', e => failures.push(e.message));
    page.on('response', r => { if (r.status() >= 400) failures.push(`${r.status()} ${r.url()}`); });
    await page.goto('http://127.0.0.1:8000/');
    await page.getByRole('heading', { name: /निष्पक्ष चयन/ }).waitFor();
    await page.screenshot({ path: path.join(out, 'overview-desktop.png'), fullPage: true });
    await page.getByRole('link', { name: /अनुरोध का प्रारूप बनाएँ/ }).click();
    await page.getByLabel('महाविद्यालय का नाम', { exact: true }).fill('परीक्षण महाविद्यालय — जौनपुर');
    await page.getByLabel('विभाग / विषय', { exact: true }).fill('हिन्दी / Political Science');
    await page.getByLabel('नियुक्ति का पद', { exact: true }).selectOption('subject_expert');
    await page.getByLabel('प्रस्तावित चयन तिथि', { exact: true }).fill('2026-09-30');
    await page.getByRole('button', { name: /विवरण का पूर्वावलोकन/ }).click();
    await page.getByRole('heading', { name: 'दर्ज विवरण की समीक्षा' }).waitFor();
    assert(await page.getByText('परीक्षण महाविद्यालय — जौनपुर', { exact: true }).isVisible());
    assert(await page.getByText('हिन्दी / Political Science', { exact: true }).isVisible());
    await page.screenshot({ path: path.join(out, 'hindi-preview.png'), fullPage: true });
    await page.getByRole('button', { name: /वापस जाकर सुधारें/ }).click();
    await page.getByLabel('महाविद्यालय का नाम', { exact: true }).waitFor();
    assert.equal(await page.getByLabel('महाविद्यालय का नाम', { exact: true }).inputValue(), 'परीक्षण महाविद्यालय — जौनपुर');
    await page.goto('http://127.0.0.1:8000/policies/');
    await page.locator('.policy-tabs').getByRole('link', { name: 'विषय विशेषज्ञ / प्रवक्ता' }).click();
    await page.locator('#policy-content[data-policy-type="subject_expert"]').waitFor();
    assert(await page.getByText('अस्थायी संरचना — कुलपति की पुष्टि शेष', { exact: true }).isVisible());
    assert.equal(await page.locator('.policy-tabs a[aria-current="page"]').count(), 1);
    assert.equal(new URL(page.url()).searchParams.get('type'), 'subject_expert');
    await page.locator('.policy-tabs').getByRole('link', { name: 'विभागाध्यक्ष', exact: true }).click();
    await page.locator('#policy-content[data-policy-type="hod"]').waitFor();
    assert.equal(await page.locator('.provisional').count(), 0);
    await page.screenshot({ path: path.join(out, 'composition-desktop.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    for (const route of ['/', '/intake/', '/policies/?type=subject_expert']) {
      await page.goto('http://127.0.0.1:8000' + route);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), `Mobile overflow: ${route}`);
    }
    await page.screenshot({ path: path.join(out, 'composition-mobile.png'), fullPage: true });
    await page.goto('http://127.0.0.1:8000/');
    await page.screenshot({ path: path.join(out, 'overview-mobile.png'), fullPage: true });
    assert.deepEqual(failures, []);
    console.log('Browser checks passed: Hindi POST preview, back-to-edit, HTMX policy switching, desktop/mobile layout, no page errors.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
