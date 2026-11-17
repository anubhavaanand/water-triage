import { test, expect } from '@playwright/test';

test('take screenshots and verify React tabs', async ({ page }) => {
  await page.goto('/');

  // 1. Default workspace view
  await expect(page.locator('h2', { hasText: 'Four Coordinated Views' })).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: 'docs/figures/Overview.png', fullPage: true });

  // 2. Queue view. Variant A is the default tab, but the sample queue lives in
  // Variant C (Master-Detail Split). Switch dataset to the enriched lab queue
  // so there are clickable sample rows.
  await expect(page.getByRole('tab', { name: /Variant A — Priority Queue/ })).toBeVisible();
  await page.getByRole('button', { name: /Enriched Lab Queue/ }).click();
  await page.getByRole('tab', { name: /Variant C — District \+ Detail Split/ }).click();
  await expect(page.getByText('LAB SAMPLE QUEUE (TOP 60 SHOWN)')).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: 'docs/figures/Queue.png', fullPage: true });

  // Click a sample to open the per-sample breakdown. Rows are clickable
  // <div> elements, not table rows.
  await page.locator('strong').first().click();
  await expect(page.locator('text=PER-SAMPLE BIS READING BREAKDOWN')).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: 'docs/figures/QueueDetail.png', fullPage: true });

  // 3. Methodology
  await page.getByRole('tab', { name: /Methodology & Limitations/ }).click();
  await expect(page.locator('h2', { hasText: 'Why Multi-Tier Triage' })).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: 'docs/figures/Methodology.png', fullPage: true });
});