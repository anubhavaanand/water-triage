import { test, expect } from '@playwright/test';

test('take screenshots and verify React tabs', async ({ page }) => {
  await page.goto('/');
  // Wait for React to mount and fetch initial data
  await page.waitForTimeout(2000);

  // 1. Queue (Variant A) - This is the default tab
  await page.waitForSelector('#tab-panel-a', { timeout: 10000 });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'docs/figures/Queue.png', fullPage: true });

  // 2. Map (Variant B)
  await page.locator('#tab-b').click();
  await page.waitForSelector('#tab-panel-b', { timeout: 5000 });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'docs/figures/Map.png', fullPage: true });

  // 3. Detail Split (Variant C)
  await page.locator('#tab-c').click();
  await page.waitForSelector('#tab-panel-c', { timeout: 5000 });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'docs/figures/DetailSplit.png', fullPage: true });

  // 4. Validation (Variant D)
  await page.locator('#tab-d').click();
  await page.waitForSelector('#tab-panel-d', { timeout: 5000 });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'docs/figures/Validation.png', fullPage: true });

  // Verify KPIs in the hero section are visible
  await expect(page.locator('.stat-num').first()).toBeVisible();
});
