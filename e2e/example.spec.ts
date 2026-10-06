import { test, expect } from '@playwright/test';

test.describe('WaterTriage React Frontend E2E Tests', () => {

  test('loads Dashboard cleanly', async ({ page }) => {
    await page.goto('/');
    
    // Check main title
    await expect(page.locator('h1')).toContainText('WaterTriage');
    
    // DB Status indicator should be visible
    await expect(page.locator('text=DB LIVE')).toBeVisible();
    
    // Check interactive system tabs
    await expect(page.locator('button', { hasText: /^Overview$/ })).toBeVisible();
    await expect(page.locator('button', { hasText: /^Queue$/ })).toBeVisible();
    await expect(page.locator('button', { hasText: /^Methodology$/ })).toBeVisible();
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
