import { test, expect } from '@playwright/test';

test('take screenshots and verify React tabs', async ({ page }) => {
  await page.goto('/');

  // 1. Verify KPIs in the hero section are visible right away
  await expect(page.locator('.stat-num').first()).toBeVisible({ timeout: 10000 });

  // 2. Queue (Variant A) - This is the default tab
  await expect(page.locator('#tab-panel-a')).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: 'docs/figures/Queue.png', fullPage: true });

  // 3. Map (Variant B)
  await page.locator('#tab-b').click();
  await expect(page.locator('#tab-panel-b')).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: 'docs/figures/Map.png', fullPage: true });

  // 4. Detail Split (Variant C)
  await page.locator('#tab-c').click();
  await expect(page.locator('#tab-panel-c')).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: 'docs/figures/DetailSplit.png', fullPage: true });

  // 5. Validation (Variant D)
  await page.locator('#tab-d').click();
  await expect(page.locator('#tab-panel-d')).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: 'docs/figures/Validation.png', fullPage: true });
});
