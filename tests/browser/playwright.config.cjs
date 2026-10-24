const {defineConfig} = require('@playwright/test');

module.exports = defineConfig({
  testDir: '.',
  testMatch: '*.spec.cjs',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30000,
  outputDir: 'artifacts/results',
  reporter: [['list'], ['json', {outputFile: 'artifacts/report.json'}]],
  use: {browserName: 'chromium', viewport: {width: 1280, height: 900},
    screenshot: 'only-on-failure', trace: 'retain-on-failure'},
});
