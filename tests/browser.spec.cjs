const { test, expect } = require('@playwright/test');

test('component catalogue, planned status, assets and responsive layout', async ({ page }) => {
  const failures = [];
  page.on('pageerror', error => failures.push(error.message));
  page.on('requestfailed', request => failures.push(`${request.url()}: ${request.failure()?.errorText}`));
  page.on('response', response => {
    if (response.status() >= 400 && response.url().startsWith('http://127.0.0.1:')) failures.push(response.url());
  });
  await page.goto('./');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Scientific knowledge.');
  await expect(page.locator('.pack')).toHaveCount(6);
  await expect(page.locator('.r-package')).toHaveCount(3);
  await expect(page.locator('.planned')).toHaveCount(2);
  await expect(page.locator('#gadget-wise')).toContainText('No installable knowledge pack');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await expect.poll(() => page.locator('img').evaluateAll(images => images.filter(img => !img.complete || img.naturalWidth === 0).map(img => ({src:img.src,complete:img.complete,width:img.naturalWidth}))), {message:JSON.stringify(failures)}).toEqual([]);
  await page.getByRole('link', { name: 'Explore the knowledge packs' }).click();
  await expect(page).toHaveURL(/#knowledge-packs$/);
  expect(await page.locator('#knowledge-packs').evaluate(el => el.getBoundingClientRect().top)).toBeGreaterThanOrEqual(0);
  await page.screenshot({ path: `test-results/hub-${test.info().project.name}.png`, fullPage: true });
  expect(failures).toEqual([]);
});

test('keyboard users reach a visible skip link and main content', async ({ page }) => {
  await page.goto('./');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused();
  const box = await page.getByRole('link', { name: 'Skip to content' }).boundingBox();
  expect(box.y).toBeGreaterThanOrEqual(0);
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/#main$/);
});
