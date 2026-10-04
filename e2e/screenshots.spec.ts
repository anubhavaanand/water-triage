import { test, expect } from '@playwright/test';

test('take screenshots and verify KPI', async ({ page }) => {
  await page.goto('/');
  await page.waitForTimeout(2000);

  // 1. Overview
  await page.click('button:has-text("Variant E: Overview")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'docs/figures/Overview.png', fullPage: true });

  // 2. Queue
  await page.click('button:has-text("Variant A: Priority Queue")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'docs/figures/Queue.png', fullPage: true });

  // 3. Map
  await page.click('button:has-text("Variant B: Map")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'docs/figures/Map.png', fullPage: true });

  // 4. Methodology
  await page.click('button:has-text("Variant F: Methodology")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'docs/figures/Methodology.png', fullPage: true });

  // 5. Validation
  await page.click('button:has-text("Variant D: External Validation")');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'docs/figures/Validation.png', fullPage: true });

  // Check KPI == /api/meta
  await expect(page.locator('p').filter({ hasText: 'Live tracking of 1,741 sources' })).toBeVisible();
});
