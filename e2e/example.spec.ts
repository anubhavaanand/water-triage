import { test, expect } from '@playwright/test';

test.describe('WaterTriage Svelte Frontend E2E Tests', () => {

  test('loads Premium Dashboard cleanly', async ({ page }) => {
    await page.goto('/');
    
    // Check Top Nav
    await expect(page.locator('.logo')).toContainText('WaterTriage');
    
    // DB Status indicator should be visible
    await expect(page.locator('.status-pill')).toBeVisible();

    // Check main title
    await expect(page.locator('h1')).toContainText('Priority Queue & Triangulation');
    
    // Check interactive system tabs
    await expect(page.locator('text=Variant A')).toBeVisible();
    await expect(page.locator('text=Variant B')).toBeVisible();
    await expect(page.locator('text=Variant D')).toBeVisible();
  });

  test('verifies sticky notes and 4-way triangulation rendering', async ({ page }) => {
    await page.goto('/');
    
    // Check that backend items are marked as FIXED/CLOSED
    await expect(page.locator('text=✓ data.json state')).toBeVisible();
    await expect(page.locator('text=✓ DB Startup')).toBeVisible();

    // Navigate to Validation Tab
    await page.locator('text=Variant D').click();
    
    // Verify Validation content rendered
    await expect(page.locator('text=External Validation')).toBeVisible();
    await expect(page.locator('text=4-Way Triangulation Pass')).toBeVisible();
  });

});
