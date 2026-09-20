import { test, expect } from '@playwright/test';

test.describe('WaterTriage Dashboard E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    page.on('pageerror', error => {
      console.error('Browser uncaught error:', error);
    });
  });

  test('loads dashboard cleanly with zero unhandled exceptions', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });

    await page.goto('/');
    await expect(page).toHaveTitle(/WaterTriage/);

    // Verify main landmarks and 3D canvas exist
    await expect(page.locator('canvas#webgl')).toBeVisible();
    await expect(page.locator('#main-console')).toBeVisible();
    await expect(page.locator('#hero-overlay')).toBeVisible();

    // Verify no critical errors in console (excluding benign icon 404s if any)
    const criticalErrors = consoleErrors.filter(e => !e.includes('favicon.ico'));
    expect(criticalErrors).toHaveLength(0);
  });

  test('switches to regional mode and displays triage queue with formatted location titles', async ({ page }) => {
    await page.goto('/?mode=regional');

    // Wait for queue items to render in regional mode
    const firstCard = page.locator('.queue-card').first();
    await expect(firstCard).toBeVisible({ timeout: 10000 });

    // Verify queue count is formatted with Indian number formatting
    const queueCount = page.locator('#queue-count');
    await expect(queueCount).toHaveText(/[\d,]+ Villages/);

    // Verify card titles do NOT show unformatted "Not available"
    const villageTitle = firstCard.locator('.q-village');
    const titleText = await villageTitle.textContent();
    expect(titleText).not.toBe('Not available');
    expect(titleText && titleText.length).toBeGreaterThan(3);
  });

  test('filters queue by contaminant and synchronizes URL parameters', async ({ page }) => {
    await page.goto('/?mode=regional');

    // Wait for queue items to ensure regional mode is active and data is loaded
    await expect(page.locator('.queue-card').first()).toBeVisible({ timeout: 15000 });

    // Click 'Arsenic' filter chip
    const arsenicChip = page.locator('.filter-chip[data-filter="Arsenic"]');
    await arsenicChip.click();

    // Verify chip state
    await expect(arsenicChip).toHaveAttribute('aria-pressed', 'true');
    await expect(page).toHaveURL(/filter=Arsenic/);

    // Verify rendered cards exist
    const cards = page.locator('.queue-card');
    await expect(cards.first()).toBeVisible();
  });

  test('searches queue and displays empty state on zero matches', async ({ page }) => {
    await page.goto('/?mode=regional');
    await expect(page.locator('.queue-card').first()).toBeVisible({ timeout: 15000 });

    const searchInput = page.locator('#queue-search');
    await searchInput.fill('NonExistentVillageQueryXYZ');

    // Verify empty state box renders
    const emptyQueue = page.locator('.empty-queue');
    await expect(emptyQueue).toBeVisible();
    await expect(emptyQueue).toContainText('No Matching Water Sources Found');

    // Click clear search button
    const clearBtn = page.locator('#btn-clear-search');
    await clearBtn.click();
    await expect(searchInput).toHaveValue('');
    await expect(page.locator('.queue-card').first()).toBeVisible();
  });

  test('opens What-If Simulator, reflects risk calculation, and syncs URL', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#main-console')).toBeVisible();

    const simBtn = page.locator('#btn-toggle-sim');
    await simBtn.click();

    const simPanel = page.locator('#simulator-drawer');
    await expect(simPanel).toHaveClass(/open/);
    await expect(page).toHaveURL(/sim=open/);

    // Verify simulator recommendation has measured height (Pretext DOM-free calculation)
    const recText = page.locator('#sim-rec-text');
    await expect(recText).toBeVisible();
    const minHeight = await recText.evaluate(el => (el as HTMLElement).style.minHeight);
    expect(minHeight).toMatch(/\d+px/);

    // Close simulator
    await page.locator('#btn-close-sim').click();
    await expect(simPanel).not.toHaveClass(/open/);
    await expect(page).not.toHaveURL(/sim=open/);
  });

  test('opens village telemetry modal and restores focus on close', async ({ page }) => {
    await page.goto('/?mode=regional');

    const firstCard = page.locator('.queue-card').first();
    await expect(firstCard).toBeVisible({ timeout: 15000 });
    await firstCard.click();

    // Modal opens
    const modal = page.locator('#detail-modal');
    await expect(modal).toBeVisible();
    await expect(page).toHaveURL(/village=/);

    // Modal title should have formatted location title
    const modalTitle = page.locator('#modal-village-name');
    const modalTitleText = await modalTitle.textContent();
    expect(modalTitleText).not.toBe('Not available');

    // Close modal
    await page.locator('#btn-close-modal').click();
    await expect(modal).not.toBeVisible();
    await expect(page).not.toHaveURL(/village=/);
  });

  test('interacts with River Basin Corridor Explorer and isolates corridor telemetry', async ({ page }) => {
    await page.goto('/?mode=regional');
    await expect(page.locator('.queue-card').first()).toBeVisible({ timeout: 15000 });

    // Verify River Explorer Card is visible
    const explorer = page.locator('#river-explorer-card');
    await expect(explorer).toBeVisible();

    // Select Kosi river corridor chip
    const kosiChip = page.locator('.river-chip[data-river="Kosi"]');
    await kosiChip.click();
    await expect(kosiChip).toHaveAttribute('aria-pressed', 'true');
    await expect(page).toHaveURL(/river=Kosi/);

    // Verify corridor telemetry updates
    const riverName = page.locator('#rex-river-name');
    await expect(riverName).toContainText('Kosi Floodplain');
    const hazard = page.locator('#rex-stat-hazard');
    await expect(hazard).toContainText('Iron');

    // Reset view
    const resetBtn = page.locator('#btn-rex-reset');
    await resetBtn.click();
    const allChip = page.locator('.river-chip[data-river="all"]');
    await expect(allChip).toHaveAttribute('aria-pressed', 'true');
  });

  test('displays live FPS telemetry meter and opens academic NTCC dossier modal via button and keyboard shortcut', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#main-console')).toBeVisible();

    // Verify live FPS telemetry meter is visible and populated
    const fpsMeter = page.locator('#fps-meter');
    await expect(fpsMeter).toBeVisible();
    const fpsVal = page.locator('#fps-val');
    await expect(fpsVal).toBeVisible();

    // Open Academic Dossier modal via button click
    const btnDossier = page.locator('#btn-project-info');
    await expect(btnDossier).toBeVisible();
    await btnDossier.click();

    const dossierModal = page.locator('#dossier-modal');
    await expect(dossierModal).toBeVisible();

    // Verify NTCC minor project metadata and academic supervisor attribution
    await expect(dossierModal).toContainText('Dr. Girish Paliwal');
    await expect(dossierModal).toContainText('Anubhav Anand');
    await expect(dossierModal).toContainText('A41105223039');
    await expect(dossierModal).toContainText('BIS IS 10500:2012');

    // Close dossier via close button
    const btnClose = page.locator('#btn-close-dossier');
    await btnClose.click();
    await expect(dossierModal).not.toBeVisible();

    // Test Keyboard shortcut 'I' opens modal
    await page.keyboard.press('i');
    await expect(dossierModal).toBeVisible();

    // Test 'Escape' key closes modal
    await page.keyboard.press('Escape');
    await expect(dossierModal).not.toBeVisible();
  });

  test('navigates system using keyboard command deck shortcuts (1, 2, S, /, Esc)', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#main-console')).toBeVisible();

    // Key '2' switches to Regional mode
    await page.keyboard.press('2');
    await expect(page).toHaveURL(/mode=regional/);
    const regionalBtn = page.locator('#btn-mode-regional');
    await expect(regionalBtn).toHaveAttribute('aria-selected', 'true');

    // Key '1' switches back to Globe mode
    await page.keyboard.press('1');
    await expect(page).toHaveURL(/mode=globe/);
    const globeBtn = page.locator('#btn-mode-globe');
    await expect(globeBtn).toHaveAttribute('aria-selected', 'true');

    // Key 's' toggles What-If Simulator drawer
    await page.keyboard.press('s');
    const simDrawer = page.locator('#simulator-drawer');
    await expect(simDrawer).toHaveClass(/open/);

    // Key 'Escape' closes What-If Simulator drawer
    await page.keyboard.press('Escape');
    await expect(simDrawer).not.toHaveClass(/open/);

    // Key '/' triggers quick search focus in Regional mode
    await page.keyboard.press('/');
    const searchInput = page.locator('#queue-search');
    await expect(searchInput).toBeFocused();
  });

  test('verifies station laboratory dossier telemetry export in detail modal', async ({ page }) => {
    await page.goto('/?mode=regional');
    const firstCard = page.locator('.queue-card').first();
    await expect(firstCard).toBeVisible({ timeout: 15000 });
    await firstCard.click();

    const detailModal = page.locator('#detail-modal');
    await expect(detailModal).toBeVisible();

    // Verify export button exists in modal header
    const exportBtn = page.locator('#btn-export-station');
    await expect(exportBtn).toBeVisible();

    // Intercept client-side JSON download
    const downloadPromise = page.waitForEvent('download');
    await exportBtn.click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toMatch(/^watertriage_station_.*\.json$/);

    // Read download stream and verify JSON structure
    const stream = await download.createReadStream();
    const chunks: Buffer[] = [];
    for await (const chunk of stream) {
      chunks.push(typeof chunk === 'string' ? Buffer.from(chunk) : chunk);
    }
    const content = Buffer.concat(chunks).toString('utf-8');
    const dossierData = JSON.parse(content);

    expect(dossierData.metadata.project).toContain('WaterTriage');
    expect(dossierData.metadata.academic_supervision.guide).toBe('Dr. Girish Paliwal');
    expect(dossierData.metadata.academic_supervision.author).toContain('Anubhav Anand');
    expect(dossierData.metadata.regulatory_standard).toContain('BIS IS 10500');
    expect(dossierData.monitoring_station).toHaveProperty('risk_score');
    expect(dossierData.monitoring_station).toHaveProperty('severity_band');

    // Close detail modal
    await page.locator('#btn-close-modal').click();
    await expect(detailModal).not.toBeVisible();
  });
});

