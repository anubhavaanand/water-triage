import { test, expect } from '@playwright/test';

test('take screenshots and verify React tabs', async ({ page }) => {
  await page.goto('/');

  // 1. Verify we are on Overview (default) and wait for loading to finish
  await expect(page.locator('text=Loading WaterTriage Dashboard...')).toBeHidden({ timeout: 10000 });
  await expect(page.locator('h2', { hasText: 'Dashboard Overview' })).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: 'docs/figures/Overview.png', fullPage: true });

  // 2. Queue
  await page.locator('button', { hasText: /^Queue$/ }).click();
  await expect(page.locator('h2', { hasText: 'Priority Intervention Queue' })).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: 'docs/figures/Queue.png', fullPage: true });

  // Click on a sample in the queue to open the drawer/detail view
  await page.locator('table tbody tr').first().click();
  await expect(page.locator('h3', { hasText: 'Sample Details' })).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: 'docs/figures/QueueDetail.png', fullPage: true });

  // 3. Methodology
  await page.locator('button', { hasText: /^Methodology$/ }).click();
  await expect(page.locator('h2', { hasText: 'Data Provenance & Limitations' })).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: 'docs/figures/Methodology.png', fullPage: true });
});
