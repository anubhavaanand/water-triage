import { test, expect } from '@playwright/test';

test('asserts displayed samples and band counts match live /api/meta', async ({ page, request }) => {
  const res = await request.get('http://127.0.0.1:8000/api/meta');
  const meta = await res.json();
  
  await page.goto('/');
  await page.waitForTimeout(2000);

  const samples = meta.corpus.samples.toLocaleString();
  const districts = meta.corpus.districts_with_samples.toString();

  await expect(page.locator(`text=${samples} samples`).first()).toBeVisible({ timeout: 10000 });
  await expect(page.locator(`text=${districts} districts`).first()).toBeVisible();

  const criticalStat = page.locator('.stat').filter({ hasText: 'Critical' }).locator('.stat-num');
  await expect(criticalStat.first()).toHaveText(String(meta.bands.Critical));
  
  const highStat = page.locator('.stat').filter({ hasText: 'High' }).locator('.stat-num');
  await expect(highStat.first()).toHaveText(String(meta.bands.High));
  
  const mediumStat = page.locator('.stat').filter({ hasText: 'Medium' }).locator('.stat-num');
  await expect(mediumStat.first()).toHaveText(String(meta.bands.Medium));
});
