import { test, expect } from '@playwright/test';

test('take screenshots and verify KPI', async ({ page }) => {
  await page.goto('/');
  await page.waitForTimeout(2000);

  // 1. Overview
  await page.click('button:has-text("Variant E")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'docs/figures/Overview.png', fullPage: true });

  // 2. Queue
  await page.click('button:has-text("Variant A")');
  await page.waitForSelector('.queue-item', { timeout: 10000 });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'docs/figures/Queue.png', fullPage: true });

  // Drawer inside Queue
  const firstRow = page.locator('.queue-item').first();
  await firstRow.click();
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'docs/figures/Drawer.png', fullPage: true });
  // Close drawer
  await page.click('button[aria-label="Close drawer"]');
  await page.waitForTimeout(500);

  // 3. Map
  await page.click('button:has-text("Variant B")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'docs/figures/Map.png', fullPage: true });

  // 4. Methodology
  await page.click('button:has-text("Variant F")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'docs/figures/Methodology.png', fullPage: true });

  // 5. Validation
  await page.click('button:has-text("Variant D")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'docs/figures/Validation.png', fullPage: true });

  await expect(page.locator('p').filter({ hasText: '1,741 samples' })).toBeVisible();
});
