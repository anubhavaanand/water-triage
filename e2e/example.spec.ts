import { test, expect } from '@playwright/test';

test.describe('WaterTriage Svelte Frontend E2E Tests', () => {

  test('loads Landing Page cleanly', async ({ page }) => {
    await page.goto('/');
    
    // Check main title
    await expect(page.locator('h1')).toContainText('WaterTriage');
    
    // Check buttons
    await expect(page.locator('text=LAUNCH RADAR')).toBeVisible();
    await expect(page.locator('text=Methodology')).toBeVisible();
    await expect(page.locator('text=Findings')).toBeVisible();
    
    // Check metadata
    await expect(page.locator('text=Dr. Girish Paliwal')).toBeVisible();
    await expect(page.locator('text=Anubhav Anand')).toBeVisible();
  });

  test('navigates to Methodology page', async ({ page }) => {
    await page.goto('/');
    await page.locator('text=Methodology').click();
    
    await expect(page.locator('h1')).toContainText('Methodology');
    await expect(page.locator('text=BIS IS 10500 Scoring Model')).toBeVisible();
    
    // Return to hub
    await page.locator('text=RETURN TO HUB').click();
    await expect(page.locator('h1')).toContainText('WaterTriage');
  });

  test('navigates to Findings page', async ({ page }) => {
    await page.goto('/');
    await page.locator('text=Findings').click();
    
    await expect(page.locator('h1')).toContainText('Findings');
    await expect(page.locator('text=1,741')).toBeVisible();
    
    // Return to hub
    await page.locator('text=RETURN TO HUB').click();
    await expect(page.locator('h1')).toContainText('WaterTriage');
  });

  test('navigates to Radar and renders Threat Feed', async ({ page }) => {
    await page.goto('/');
    await page.locator('text=LAUNCH RADAR').click();
    
    await expect(page.locator('h1')).toContainText('Command Center');
    
    // Threat Feed renders items
    await expect(page.locator('text=PATNA')).toBeVisible();
    await expect(page.locator('text=LUCKNOW')).toBeVisible();
    
    // Canvas is rendered
    await expect(page.locator('canvas#webgl')).toBeVisible();
  });

});
