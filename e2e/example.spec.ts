import { test, expect } from '@playwright/test';

test.describe('WaterTriage React Frontend E2E Tests', () => {

  test('loads Dashboard cleanly', async ({ page }) => {
    await page.goto('/');

    // The h1 is the coverage headline; the product name moved to the header
    // wordmark after the 6-tab redesign.
    await expect(page.locator('h1')).toContainText('Every District Scored');
    await expect(page.locator('header')).toContainText('WaterTriage');

    // DB status pill renders "API Live · 113 Dist." or
    // "Verified Snapshot · 113 Dist." — there is no "DB LIVE" string.
    await expect(page.locator('.status-pill')).toBeVisible();
    await expect(page.locator('.status-pill')).toContainText(/Live|Snapshot/);

    // The top nav renders tabs as <a> elements, and the queue tab is
    // labelled "Priority Queue".
    await expect(page.locator('nav a', { hasText: /^Overview$/ })).toBeVisible();
    await expect(page.locator('nav a', { hasText: /^Priority Queue$/ })).toBeVisible();
    await expect(page.locator('nav a', { hasText: /^Methodology$/ })).toBeVisible();
  });

  test('verifies tab navigation and data loading', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('h2', { hasText: 'Four Coordinated Views' })).toBeVisible({ timeout: 10000 });

    // Queue tab is the default workspace view.
    await expect(page.getByRole('tab', { name: /Variant A — Priority Queue/ })).toBeVisible();

    // Methodology tab swaps the workspace body for the limitations panel.
    await page.getByRole('tab', { name: /Methodology & Limitations/ }).click();
    await expect(page.locator('h2', { hasText: 'Why Multi-Tier Triage' })).toBeVisible();

    // Overview tab renders the band breakdown and sensitivity content.
    await page.getByRole('tab', { name: /Overview & Sensitivity/ }).click();
    await expect(page.locator('h2', { hasText: 'Risk Band Breakdown' })).toBeVisible();
  });

});