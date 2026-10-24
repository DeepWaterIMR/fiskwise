const { test, expect } = require('@playwright/test');
const packages = require('../packages.json');

test('component catalogue, planned status, assets and responsive layout', async ({ page }) => {
  const failures = [];
  page.on('pageerror', error => failures.push(error.message));
  page.on('requestfailed', request => failures.push(`${request.url()}: ${request.failure()?.errorText}`));
  page.on('response', response => {
    if (response.status() >= 400 && response.url().startsWith('http://127.0.0.1:')) failures.push(response.url());
  });
  await page.goto('./');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Scientific knowledge.');
  await expect(page.locator('.pack')).toHaveCount(packages.filter(packageInfo => packageInfo.kind === 'knowledge').length);
  await expect(page.locator('.r-package')).toHaveCount(packages.filter(packageInfo => packageInfo.kind === 'r').length);
  await expect(page.locator('.planned')).toHaveCount(packages.filter(packageInfo => packageInfo.status === 'planned').length);
  await expect(page.locator('#gadget-wise')).toContainText('No installable knowledge pack');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await expect.poll(() => page.locator('img').evaluateAll(images => images.filter(img => !img.complete || img.naturalWidth === 0).map(img => ({src:img.src,complete:img.complete,width:img.naturalWidth}))), {message:JSON.stringify(failures)}).toEqual([]);
  await page.getByRole('link', { name: 'Explore the knowledge packs' }).click();
  await expect(page).toHaveURL(/#knowledge-packs$/);
  expect(await page.locator('#knowledge-packs').evaluate(el => el.getBoundingClientRect().top)).toBeGreaterThanOrEqual(0);
  await page.screenshot({ path: `test-results/hub-${test.info().project.name}.png`, fullPage: true });
  expect(failures).toEqual([]);
});

test('getting-started guide keeps lifecycle prompts accessible and responsive', async ({ page, context }) => {
  const failures = [];
  page.on('pageerror', error => failures.push(error.message));
  page.on('requestfailed', request => failures.push(`${request.url()}: ${request.failure()?.errorText}`));
  page.on('response', response => {
    if (response.status() >= 400 && response.url().startsWith('http://127.0.0.1:')) failures.push(response.url());
  });
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.goto('./getting-started.html');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Install only what your research needs.');
  await expect(page.locator('#prompt-install')).toHaveText('install https://github.com/DeepWaterIMR/fiskwise');
  await expect(page.locator('#prompt-update')).toHaveText('update Fiskwise');
  await expect(page.locator('#prompt-uninstall')).toHaveText('uninstall Fiskwise');
  await expect(page.getByRole('button', { name: 'Copy prompt' })).toHaveCount(3);
  await expect(page.getByText('Quarto CLI is a separate application')).toBeVisible();
  await expect(page.getByText(/gadget-wise.*planned/i)).toBeVisible();
  await expect(page.getByRole('link', { name: /BAIT privacy guidance/ })).toHaveAttribute('href', 'https://deepwaterimr.github.io/BAIT/privacy.html');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);

  const copyButtons = page.getByRole('button', { name: 'Copy prompt' });
  const expectedPrompts = [
    'install https://github.com/DeepWaterIMR/fiskwise',
    'update Fiskwise',
    'uninstall Fiskwise'
  ];
  const copyButton = copyButtons.first();
  for (let index = 0; index < 30 && !(await copyButton.evaluate(button => button === document.activeElement)); index += 1) {
    await page.keyboard.press('Tab');
  }
  await expect(copyButton).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('#status-install')).toHaveText('Prompt copied.');
  for (let index = 0; index < expectedPrompts.length; index += 1) {
    await copyButtons.nth(index).click();
    expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(expectedPrompts[index]);
  }
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
