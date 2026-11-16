import { test, expect } from '@playwright/test';

test.describe('WaterTriage React Frontend E2E Tests', () => {

  test('loads Dashboard cleanly', async ({ page }) => {
    await page.goto('/');
    
    // The h1 was rewritten to the coverage headline; the product name now
    // lives in the header wordmark and the footer.
    await expect(page.locator('h1')).toContainText('Every District Scored');
    await expect(page.locator('header')).toContainText('WaterTriage');
    
    // DB Status indicator should be visible. The badge renders one of
    // "API Live · 113 Dist." / "Verified Snapshot · 113 Dist." /
    // "Checking..." inside .status-pill — there is no "DB LIVE" string.
    await expect(page.locator('.status-pill')).toBeVisible();
    await expect(page.locator('.status-pill')).toContainText(/Live|Snapshot/);
    
    // Check interactive system tabs. These render as <a> elements in the
    // topnav, and the queue tab is labelled "Priority Queue".
    await expect(page.locator('nav a', { hasText: /^Overview$/ })).toBeVisible();
    await expect(page.locator('nav a', { hasText: /^Priority Queue$/ })).toBeVisible();
    await expect(page.locator('nav a', { hasText: /^Methodology$/ })).toBeVisible();
  });

  test('verifies tab navigation and data loading', async ({ page }) => {
    await page.goto('/');
    
    // Wait for data to load
    await expect(page.locator('text=Loading WaterTriage Dashboard...')).toBeHidden({ timeout: 10000 });

    // Navigate to Queue Tab
    await page.locator('button', { hasText: /^Queue$/ }).click();
    await expect(page.locator('h2', { hasText: 'Priority Intervention Queue' })).toBeVisible();

    // Navigate to Methodology Tab
    await page.locator('button', { hasText: /^Methodology$/ }).click();
    await expect(page.locator('h2', { hasText: 'Data Provenance & Limitations' })).toBeVisible();
    
    // Navigate back to Overview Tab
    await page.locator('button', { hasText: /^Overview$/ }).click();
    await expect(page.locator('h2', { hasText: 'Dashboard Overview' })).toBeVisible();
  });

});
