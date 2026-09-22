const { chromium } = require('playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');

(async () => {
  const creds = JSON.parse(fs.readFileSync('.local/demo-access.json', 'utf8'));
  const base = 'http://127.0.0.1:8000';
  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('response', r => { if (r.status() >= 500) errors.push(r.url()); });
    async function login(user) {
      await page.goto(base + '/office/login/');
      await page.locator('[name=username]').fill(user.username);
      await page.locator('[name=password]').fill(user.password);
      await page.getByRole('button', { name: 'साइन इन', exact: true }).click();
      await page.getByRole('heading', { name: 'कार्यालय कार्यक्षेत्र' }).waitFor();
    }
    await login(creds.poc);
    await page.goto(base + '/office/allocation/demo/');
    await page.getByRole('heading', { name: 'प्रस्तावित संरचना पूरी है' }).waitFor();
    assert(await page.getByText('केवल प्रदर्शन', { exact: false }).isVisible());
    await page.locator('[name=scenario]').selectOption('fairness');
    await page.locator('[name=appointment]').selectOption('subject_expert');
    await page.getByRole('button', { name: 'उदाहरण देखें' }).click();
    await page.getByText('विषय विशेषज्ञ की संरचना अस्थायी', { exact: false }).waitFor();
    await page.screenshot({ path: 'test-results/allocation-desktop.png', fullPage: true });
    await page.locator('[name=scenario]').selectOption('shortage');
    await page.getByRole('button', { name: 'उदाहरण देखें' }).click();
    await page.getByRole('heading', { name: 'आवंटन अपूर्ण है' }).waitFor();
    await page.setViewportSize({ width: 390, height: 844 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1));
    await page.screenshot({ path: 'test-results/allocation-mobile.png', fullPage: true });
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto(base + '/office/requests/');
    const link = page.locator('a[href^="/office/requests/"]').filter({ hasNotText: 'नया' });
    const hrefs = await link.evaluateAll(nodes => nodes.map(n => n.getAttribute('href')));
    const caseUrl = hrefs.find(h => /^\/office\/requests\/[0-9a-f-]+\/$/.test(h));
    assert(caseUrl, 'Existing synthetic request needed');
    await page.goto(base + caseUrl);
    await page.getByRole('link', { name: 'विशेषज्ञ आवंटन', exact: true }).click();
    const workbench = page.url();
    await page.getByRole('button', { name: 'पात्रता और अनुशंसा जाँचें' }).click();
    await page.getByRole('heading', { name: 'आवंटन का विवरण' }).waitFor();
    assert(await page.getByText('इतिहास का पूर्ण संकलन', { exact: false }).isVisible());
    const runUrl = page.url();
    await context.clearCookies();
    await login(creds.reviewer);
    await page.goto(workbench);
    assert.equal(await page.getByRole('button', { name: 'पात्रता और अनुशंसा जाँचें' }).count(), 0);
    await page.goto(runUrl);
    await page.getByRole('heading', { name: 'आवंटन का विवरण' }).waitFor();
    assert.deepEqual(errors, []);
    console.log('Allocation browser: demonstrations, scarcity, mobile, saved request evaluation and reviewer access passed.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
