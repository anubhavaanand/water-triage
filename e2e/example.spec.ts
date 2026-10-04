import { test, expect } from '@playwright/test';

test.describe('WaterTriage React Frontend E2E Tests', () => {

  test('loads Engineering Notebook Dashboard cleanly', async ({ page }) => {
    await page.goto('/');
    
    // Check Top Nav
    await expect(page.locator('.logo')).toContainText('WaterTriage');
    
    // DB Status indicator should be visible
    await expect(page.locator('.status-pill')).toBeVisible();

    // Check main title
    await expect(page.locator('h1')).toContainText('Dashboard Layout Explorations');
    
    // Check interactive system tabs
    await expect(page.locator('#tab-a')).toContainText('Variant A');
    await expect(page.locator('#tab-b')).toContainText('Variant B');
    await expect(page.locator('#tab-c')).toContainText('Variant C');
    await expect(page.locator('#tab-d')).toContainText('Variant D');
  });

  test('verifies tab navigation and data loading', async ({ page }) => {
    await page.goto('/');
    
    // Default tab should be Variant A
    await expect(page.locator('#tab-panel-a')).toBeVisible();

    // Navigate to Map Tab (B)
    await page.locator('#tab-b').click();
    await expect(page.locator('#tab-panel-b')).toBeVisible();

    // Navigate to Detail Tab (C)
    await page.locator('#tab-c').click();
    await expect(page.locator('#tab-panel-c')).toBeVisible();

    // Navigate to Validation Tab (D)
    await page.locator('#tab-d').click();
    
    // Verify Validation content rendered and check VP-1
    await expect(page.locator('#tab-panel-d')).toBeVisible();
    await expect(page.locator('#tab-panel-d')).toContainText('VP-1');
  });

});
