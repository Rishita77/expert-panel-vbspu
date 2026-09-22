const { chromium } = require('playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const path = require('node:path');

(async () => {
  const credentials = JSON.parse(fs.readFileSync('.local/demo-access.json', 'utf8'));
  const base = 'http://127.0.0.1:8000';
  const out = 'test-results';
  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1050 } });
    const page = await context.newPage();
    const failures = [];
    page.on('pageerror', e => failures.push(e.message));
    page.on('response', r => { if (r.status() >= 500) failures.push(r.url()); });
    async function login(target, user) {
      await target.goto(base + '/office/login/');
      await target.locator('[name=username]').fill(user.username);
      await target.locator('[name=password]').fill(user.password);
      await target.getByRole('button', { name: 'साइन इन', exact: true }).click();
      await target.getByRole('heading', { name: 'कार्यालय कार्यक्षेत्र' }).waitFor();
    }
    async function save() { await page.getByRole('button', { name: 'सहेजें', exact: true }).click(); }
    await login(page, credentials.poc);
    await page.goto(base + '/office/catalog/experts/new/');
    const name = `ब्राउज़र परीक्षण विशेषज्ञ ${Date.now()}`;
    await page.getByLabel('पूरा नाम', { exact: true }).fill(name);
    await page.getByLabel('श्रेणी', { exact: true }).selectOption('sc');
    await page.getByLabel('मोबाइल', { exact: true }).fill('+919999999992');
    await page.getByLabel('ईमेल', { exact: true }).fill('browser-private@example.test');
    await page.getByLabel('विषय', { exact: true }).selectOption({ label: 'हिन्दी' });
    await save();
    await page.getByRole('heading', { name: 'परिवर्तन इतिहास', exact: true }).waitFor();
    const expertUrl = page.url();
    const expertLabel = await page.locator('h1').innerText();
    assert(await page.getByText('इतिहास अभी लोड नहीं हुआ है', { exact: true }).isVisible());
    await page.getByRole('link', { name: 'संस्था / पद जोड़ें', exact: true }).click();
    await page.getByLabel('संस्था', { exact: true }).selectOption({ label: 'प्रदर्शन अनुदानित महाविद्यालय' });
    await page.getByLabel('वर्तमान पद', { exact: true }).selectOption('principal');
    await page.getByLabel('शैक्षणिक रैंक', { exact: true }).selectOption('professor');
    await page.getByLabel('आन्तरिक / बाह्य', { exact: true }).selectOption('internal');
    await page.getByLabel('पद / रैंक / संस्था सत्यापन सन्दर्भ', { exact: true }).fill('Synthetic verified reference');
    await page.locator('[name=start_date]').fill('2020-07-01');
    await save();
    await page.getByRole('heading', { name: 'परिवर्तन इतिहास', exact: true }).waitFor();
    await page.getByLabel('अनुरोध महाविद्यालय (अपने महाविद्यालय की जाँच)', { exact: true }).selectOption({ label: 'प्रदर्शन अनुदानित महाविद्यालय' });
    await page.getByRole('button', { name: 'तिथि / महाविद्यालय के अनुसार देखें' }).click();
    assert(await page.getByText('अपने महाविद्यालय के लिए नामांकन वर्जित है।', { exact: true }).isVisible());
    await page.screenshot({ path: path.join(out, 'expert-history-desktop.png'), fullPage: true });
    // One expert's independently approved professor membership.
    await page.goto(base + '/office/catalog/pools/new/');
    const title = 'ब्राउज़र स्वीकृत सूची ' + Date.now();
    await page.getByLabel('सूची का नाम', { exact: true }).fill(title);
    await page.getByLabel('नामांकन भूमिका', { exact: true }).selectOption('professor');
    await page.getByLabel('स्वीकृति अभिलेख', { exact: true }).selectOption({ label: 'DEMO-EC-2026-NOT-OFFICIAL · प्रदर्शन कार्य परिषद्' });
    await page.locator('[name=effective_date]').fill('2026-07-01');
    await page.locator('[name=valid_through]').fill('2027-06-30');
    await save();
    await page.getByRole('heading', { name: 'सूची के विशेषज्ञ', exact: true }).waitFor();
    const poolUrl = page.url();
    await page.getByRole('link', { name: 'सीमा जोड़ें', exact: true }).click();
    await page.getByLabel('नियुक्ति प्रकार', { exact: true }).selectOption('subject_expert');
    await page.getByLabel('विषय', { exact: true }).selectOption({ label: 'हिन्दी' });
    await save();
    await page.getByRole('link', { name: 'सदस्य जोड़ें', exact: true }).click();
    await page.getByLabel('विशेषज्ञ', { exact: true }).selectOption({ label: expertLabel });
    await save();
    await page.getByLabel('कारण / स्वीकृति सन्दर्भ', { exact: true }).fill('Browser synthetic official record');
    await page.getByRole('button', { name: 'स्वीकृति दर्ज करें', exact: true }).click();
    await page.getByRole('button', { name: 'नया प्रारूप संस्करण बनाएँ', exact: true }).waitFor();
    await page.screenshot({ path: path.join(out, 'approved-list-desktop.png'), fullPage: true });
    assert.equal((await page.request.get(poolUrl + 'edit/')).status(), 409);
    await page.getByLabel('कारण / स्वीकृति सन्दर्भ', { exact: true }).fill('Approved list correction');
    await page.getByRole('button', { name: 'नया प्रारूप संस्करण बनाएँ', exact: true }).click();
    await page.getByRole('button', { name: 'स्वीकृति दर्ज करें', exact: true }).waitFor();
    assert((await page.locator('h1').innerText()).includes('v2'));
    // Read-only CSV preview is intentionally not an import commit.
    await page.goto(base + '/office/catalog/import/');
    await page.getByLabel('रिकॉर्ड का प्रकार').selectOption('experts');
    await page.locator('input[type=file]').setInputFiles({ name: 'test.csv', mimeType: 'text/csv',
      buffer: Buffer.from('source_key,name,category,mobile,email,subject_ids\nrow1,हिन्दी पूर्वावलोकन,sc,,,\n') });
    await page.getByRole('button', { name: 'केवल जाँचें', exact: true }).click();
    await page.getByRole('heading', { name: 'पंक्ति परिणाम', exact: true }).waitFor();
    assert(await page.getByText(/क्रमांक अभी आरक्षित नहीं है/).isVisible());
    const viewerContext = await browser.newContext();
    const viewer = await viewerContext.newPage();
    await login(viewer, credentials.reviewer);
    await viewer.goto(expertUrl);
    const html = await viewer.content();
    assert(!html.includes('browser-private@example.test') && !html.includes('+919999999992'));
    assert.equal((await viewer.goto(expertUrl + 'edit/')).status(), 403);
    await page.setViewportSize({ width: 390, height: 844 });
    for (const url of [expertUrl, poolUrl, base + '/office/catalog/experts/new/']) {
      await page.goto(url);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), url);
      assert(await page.evaluate(() => document.querySelector('.topbar').getBoundingClientRect().bottom <= document.querySelector('h1').getBoundingClientRect().top));
    }
    await page.screenshot({ path: path.join(out, 'expert-mobile.png'), fullPage: true });
    assert.deepEqual(failures, []);
    console.log('Expert browser passed: dual designation, own-college check, approval/versioning, CSV preview, reviewer privacy and mobile layout.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
