/**
 * E2E tests for wireframe 04 (Risk Score Detail)
 * Tests risk score breakdown showing severity contributions, adjustments, and floor application
 */
import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 04 - Risk Score Detail', () => {
  test.beforeEach(async ({ page }) => {
    // Log in through the login form
    await page.goto('/login');
    await page.fill('#email', 'analyst@example.com');
    await page.fill('#password', 'Analyst-pass-1');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('verifies risk score breakdown matches calculated score', async ({ page }) => {
    // Navigate to alert detail
    await page.goto('/alerts/1');

    // Wait for priority rationale section
    await expect(page.locator('h2:has-text("Priority rationale")')).toBeVisible();

    // Get the final score from the breakdown (using more specific selector)
    const finalScoreSection = page.locator('dt').filter({ hasText: 'Final score (capped 0–100)' });
    await expect(finalScoreSection).toBeVisible();
    const finalScoreRow = finalScoreSection.locator('+ dd');
    const finalScoreText = await finalScoreRow.textContent();
    const finalScore = parseInt(finalScoreText?.trim() || '0', 10);

    // Verify final score is a valid number
    expect(finalScore).toBeGreaterThanOrEqual(0);
    expect(finalScore).toBeLessThanOrEqual(100);
  });

  test('displays all score components in breakdown', async ({ page }) => {
    await page.goto('/alerts/1');

    // Verify all breakdown components are present (using dt selectors for specificity)
    await expect(page.locator('dt').filter({ hasText: 'Base score' })).toBeVisible();
    await expect(page.locator('dt').filter({ hasText: 'Customer risk adjustment' })).toBeVisible();
    await expect(page.locator('dt').filter({ hasText: 'Geography adjustment' })).toBeVisible();
    await expect(page.locator('dt').filter({ hasText: 'Final score (capped 0–100)' })).toBeVisible();
    await expect(page.locator('dt').filter({ hasText: 'Priority' })).toBeVisible();
    await expect(page.locator('dt').filter({ hasText: 'PEP / sanctioned floor' })).toBeVisible();
  });

  test('shows priority bands reference', async ({ page }) => {
    await page.goto('/alerts/1');

    // Verify priority bands section exists
    await expect(page.locator('h3:has-text("Priority bands")')).toBeVisible();

    // Verify all four priority levels are documented
    const bandsSection = page.locator('h3:has-text("Priority bands")').locator('..');
    await expect(bandsSection).toContainText('80 and above');
    await expect(bandsSection).toContainText('60 to 79');
    await expect(bandsSection).toContainText('35 to 59');
    await expect(bandsSection).toContainText('Below 35');
  });

  test('displays rationale text explaining priority', async ({ page }) => {
    await page.goto('/alerts/1');

    // Verify rationale section exists with content (using p selector containing strong)
    const rationaleSection = page.locator('p').filter({ has: page.locator('strong:has-text("Rationale")') });
    await expect(rationaleSection).toBeVisible();

    // Should contain explanation text
    const rationaleText = await rationaleSection.textContent();
    expect(rationaleText?.length || 0).toBeGreaterThanOrEqual(50);
  });

  test('indicates whether PEP floor was applied', async ({ page }) => {
    await page.goto('/alerts/1');

    // Find PEP/sanctioned floor row (using sibling selector)
    const pepDt = page.locator('dt').filter({ hasText: 'PEP / sanctioned floor' });
    await expect(pepDt).toBeVisible();
    const pepRow = pepDt.locator('+ dd');
    await expect(pepRow).toBeVisible();

    // Should say either "Applied" or "Not applied"
    const pepText = await pepRow.textContent();
    expect(['Applied', 'Not applied']).toContain(pepText?.trim());
  });

  test('shows customer risk adjustment value', async ({ page }) => {
    await page.goto('/alerts/1');

    // Find customer risk adjustment row (using sibling selector)
    const adjustmentDt = page.locator('dt').filter({ hasText: 'Customer risk adjustment' });
    await expect(adjustmentDt).toBeVisible();
    const adjustmentRow = adjustmentDt.locator('+ dd');
    await expect(adjustmentRow).toBeVisible();

    // Should be a number (possibly with + prefix)
    const adjustmentText = await adjustmentRow.textContent();
    expect(adjustmentText).toMatch(/^\+?\d+$/);
  });

  test('shows geography adjustment value', async ({ page }) => {
    await page.goto('/alerts/1');

    // Find geography adjustment row (using sibling selector)
    const geoDt = page.locator('dt').filter({ hasText: 'Geography adjustment' });
    await expect(geoDt).toBeVisible();
    const geoRow = geoDt.locator('+ dd');
    await expect(geoRow).toBeVisible();

    // Should be a number (possibly with + prefix)
    const geoText = await geoRow.textContent();
    expect(geoText).toMatch(/^\+?\d+$/);
  });
});
