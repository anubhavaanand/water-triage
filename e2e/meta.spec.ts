import { test, expect } from '@playwright/test';

const API_URL = 'http://localhost:8000/api/meta';

async function apiAvailable(request: { get: (url: string) => Promise<{ ok: () => boolean }> }) {
  try {
    const res = await request.get(API_URL);
    return res.ok();
  } catch {
    return false;
  }
}

test('dashboard reports a valid data source', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('.status-pill')).toBeVisible({ timeout: 15000 });
  await expect(page.locator('.status-pill')).toContainText(/Live|Snapshot|Checking/);
});

test('backend /api/meta is reachable and well-formed', async ({ request }) => {
  test.skip(!(await apiAvailable(request)), 'backend not running; dashboard-only smoke test');

  const res = await request.get(API_URL);
  expect(res.ok()).toBeTruthy();

  const meta = await res.json();
  expect(meta.corpus.samples).toBeGreaterThanOrEqual(0);
  expect(Object.values(meta.bands).reduce((a, b) => a + b, 0)).toBe(meta.corpus.samples);
});

test('dashboard and backend agree on band counts when live', async ({ page, request }) => {
  test.skip(!(await apiAvailable(request)), 'backend not running; dashboard-only smoke test');

  const res = await request.get(API_URL);
  expect(res.ok()).toBeTruthy();
  const meta = await res.json();

  await page.goto('/');
  await expect(page.locator('.status-pill')).toBeVisible({ timeout: 15000 });

  const pill = await page.locator('.status-pill').innerText();
  test.skip(!pill.includes('API Live'), 'page is serving the snapshot, not the live API');

  const bodyText = await page.locator('body').innerText();
  expect(bodyText).toContain(String(meta.corpus.samples));
});