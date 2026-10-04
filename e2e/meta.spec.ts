import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test('asserts displayed samples and band counts match meta.json', async ({ page }) => {
  const meta = JSON.parse(fs.readFileSync(path.join(__dirname, '../frontend/public/meta.json'), 'utf8'));
  
  await page.goto('/');
  await page.waitForTimeout(2000);

  await expect(page.locator(`text=1,741 samples`).first()).toBeVisible();
  await expect(page.locator(`text=${meta.corpus.districts_with_samples} districts`).first()).toBeVisible();

  const criticalStat = page.locator('.stat').filter({ hasText: 'Critical' }).locator('.stat-num');
  await expect(criticalStat.first()).toHaveText(String(meta.bands.Critical));
  
  const highStat = page.locator('.stat').filter({ hasText: 'High' }).locator('.stat-num');
  await expect(highStat.first()).toHaveText(String(meta.bands.High));
  
  const mediumStat = page.locator('.stat').filter({ hasText: 'Medium' }).locator('.stat-num');
  await expect(mediumStat.first()).toHaveText(String(meta.bands.Medium));
});
