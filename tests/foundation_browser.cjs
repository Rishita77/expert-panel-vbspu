// Synthetic local demo only. Credentials are read locally and never printed.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

(async () => {
  const credentials = JSON.parse(fs.readFileSync('.local/demo-access.json', 'utf8'));
  const base = 'http://127.0.0.1:8000';
  const out = path.join(process.cwd(), 'test-results');
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ headless: true, channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome' });
  const failures = [];
  try {
    const workContext = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
    const page = await workContext.newPage();
    page.on('pageerror', e => failures.push(e.message));
    page.on('response', r => { if (r.status() >= 500) failures.push(`${r.status()} ${r.url()}`); });
    async function signIn(target, account) {
      await target.goto(base + '/office/login/');
      await target.locator('[name=username]').fill(account.username);
      await target.locator('[name=password]').fill(account.password);
      await target.getByRole('button', { name: 'साइन इन', exact: true }).click();
      await target.getByRole('heading', { name: 'कार्यालय कार्यक्षेत्र' }).waitFor();
    }
    await signIn(page, credentials.poc);
    await page.screenshot({ path: path.join(out, 'office-desktop.png'), fullPage: true });
    // Directory creation and historical edit.
    await page.goto(base + '/office/subjects/new/');
    const subjectName = `परीक्षण विषय ${Date.now()}`;
    await page.getByLabel('विषय का नाम', { exact: true }).fill(subjectName);
    await page.getByRole('button', { name: 'सहेजें', exact: true }).click();
    await page.getByRole('heading', { name: 'परिवर्तन इतिहास' }).waitFor();
    await page.getByRole('link', { name: 'बदलें', exact: true }).click();
    await page.getByLabel('आधिकारिक कोड').fill('SAMPLE');
    await page.getByLabel('परिवर्तन का कारण', { exact: true }).fill('प्रदर्शन के लिए कोड दर्ज');
    await page.getByRole('button', { name: 'सहेजें', exact: true }).click();
    assert.equal(await page.locator('.audit-event').count(), 2);
    // Minimal draft, Hindi persistence, zero count, and reopen.
    await page.goto(base + '/office/requests/new/');
    await page.getByLabel('महाविद्यालय', { exact: true }).selectOption({ label: 'परीक्षण महाविद्यालय — जौनपुर' });
    await page.getByLabel('नियुक्ति का पद', { exact: true }).selectOption('subject_expert');
    await page.getByLabel('विषय', { exact: true }).selectOption({ label: 'हिन्दी' });
    await page.getByLabel('टिप्पणी', { exact: true }).fill('क्षेत्रीय हिन्दी — संयुक्ताक्षर क्ष त्र ज्ञ और Unicode परीक्षण');
    await page.getByLabel('अभ्यर्थियों की संख्या', { exact: true }).fill('0');
    await page.getByRole('button', { name: 'प्रारूप सहेजें', exact: true }).click();
    await page.getByRole('heading', { name: 'परिवर्तन इतिहास' }).waitFor();
    const draftUrl = page.url();
    await page.reload();
    assert(await page.locator('.office-details').getByText('क्षेत्रीय हिन्दी — संयुक्ताक्षर क्ष त्र ज्ञ और Unicode परीक्षण', { exact: true }).isVisible());
    assert.equal(await page.locator('.office-details dd').filter({ hasText: /^0$/ }).count(), 1);
    await page.getByRole('link', { name: 'बदलें', exact: true }).click();
    const stale = await page.context().newPage();
    await stale.goto(page.url());
    await page.getByLabel('टिप्पणी', { exact: true }).fill('पहला अधिकारी: संशोधित हिन्दी');
    await page.getByLabel('परिवर्तन का कारण', { exact: true }).fill('महाविद्यालय से संशोधित विवरण');
    await page.getByRole('button', { name: 'प्रारूप सहेजें', exact: true }).click();
    await page.getByRole('heading', { name: 'परिवर्तन इतिहास' }).waitFor();
    await stale.getByLabel('टिप्पणी', { exact: true }).fill('दूसरे अधिकारी का अधूरा पाठ');
    await stale.getByLabel('परिवर्तन का कारण', { exact: true }).fill('समकालीन परिवर्तन');
    const conflict = stale.waitForResponse(r => r.request().method() === 'POST');
    await stale.getByRole('button', { name: 'प्रारूप सहेजें', exact: true }).click();
    assert.equal((await conflict).status(), 409);
    assert.equal(await stale.getByLabel('टिप्पणी', { exact: true }).inputValue(), 'दूसरे अधिकारी का अधूरा पाठ');
    await stale.close();
    await page.goto(draftUrl);
    assert.equal(await page.locator('.audit-event').count(), 2);
    await page.locator('.audit-event summary').first().click();
    await page.screenshot({ path: path.join(out, 'office-hindi-history.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    for (const url of [draftUrl, base + '/office/requests/', base + '/office/requests/new/']) {
      await page.goto(url);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), url);
    }
    assert(await page.evaluate(() => document.querySelector('.topbar').getBoundingClientRect().bottom <= document.querySelector('h1').getBoundingClientRect().top));
    await page.screenshot({ path: path.join(out, 'office-mobile-form.png'), fullPage: true });
    // Read-only role can inspect but cannot edit or visit account administration.
    const reviewContext = await browser.newContext();
    const reviewer = await reviewContext.newPage();
    await signIn(reviewer, credentials.reviewer);
    await reviewer.goto(draftUrl);
    assert.equal(await reviewer.getByRole('link', { name: 'बदलें', exact: true }).count(), 0);
    assert.equal((await reviewer.goto(draftUrl + 'edit/')).status(), 403);
    assert.equal((await reviewer.goto(base + '/office/staff/')).status(), 403);
    await reviewContext.close();
    // Administrator can create a named, initially inactive account.
    const adminContext = await browser.newContext();
    const admin = await adminContext.newPage();
    await signIn(admin, credentials.admin);
    assert.equal((await admin.goto(base + '/office/requests/')).status(), 403);
    await admin.goto(base + '/office/staff/new/');
    await admin.getByLabel('लॉगिन नाम', { exact: true }).fill(`sample.${Date.now()}`);
    await admin.getByLabel('पूरा नाम', { exact: true }).fill('प्रदर्शन कर्मचारी');
    await admin.getByLabel('अनुमतियाँ', { exact: true }).selectOption(['processor']);
    await admin.getByLabel('कारण / प्राधिकरण सन्दर्भ', { exact: true }).fill('स्थानीय प्रदर्शन');
    await admin.getByRole('button', { name: 'सहेजें', exact: true }).click();
    await admin.getByRole('heading', { name: 'परिवर्तन इतिहास' }).waitFor();
    await admin.getByRole('button', { name: 'साइन आउट', exact: true }).click();
    await admin.getByRole('heading', { name: 'कर्मचारी साइन इन' }).waitFor();
    assert.deepEqual(failures, []);
    console.log('Browser passed: Hindi persistence/history, directories, stale edit, mobile layout, role boundaries, staff creation and logout.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
