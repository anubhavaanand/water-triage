import { test, expect } from '@playwright/test';

test('asserts displayed samples and band counts match live /api/meta', async ({ page, request }) => {
  const res = await request.get('http://127.0.0.1:8000/api/meta');
  const meta = await res.json();
  
  await page.goto('/');
  await page.waitForTimeout(2000);

  const samples = meta.corpus.samples.toString();
  const historical = meta.corpus.historical_events_distinct.toString();

  await expect(page.locator(`text=${samples} Samples`).first()).toBeVisible({ timeout: 10000 });
  await expect(page.locator(`text=${historical} Historical Records`).first()).toBeVisible();

  // Find the exact text of the Critical count. We'll verify the div containing 'Critical' also contains the number.
  const criticalCount = String(meta.bands.Critical);
  await expect(page.locator(`text=Critical`).locator('xpath=..').locator(`text=${criticalCount}`).first()).toBeVisible();
  
  const highCount = String(meta.bands.High);
  await expect(page.locator(`text=High`).locator('xpath=..').locator(`text=${highCount}`).first()).toBeVisible();
  
  const mediumCount = String(meta.bands.Medium);
  await expect(page.locator(`text=Medium`).locator('xpath=..').locator(`text=${mediumCount}`).first()).toBeVisible();
});
