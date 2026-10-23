const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: './tests',
  testMatch: 'browser.spec.cjs',
  reporter: 'line',
  workers: 1,
  outputDir: 'test-results',
  use: { baseURL: process.env.FISKWISE_TEST_URL || 'http://127.0.0.1:8766/fiskwise/',
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {},
    screenshot: 'only-on-failure' },
  projects: [
    { name: 'desktop', use: { viewport: { width: 1440, height: 1000 } } },
    { name: 'mobile', use: { viewport: { width: 390, height: 844 }, isMobile: true } },
    { name: 'narrow', use: { viewport: { width: 320, height: 740 }, isMobile: true } }
  ]
});
