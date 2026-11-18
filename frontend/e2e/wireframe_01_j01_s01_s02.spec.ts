/**
 * E2E test for wireframe 1: Transaction submission
 * Tests transaction submission through the form and asserts 201 response
 */
import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 01 - Transaction Submission', () => {
  test.beforeEach(async ({ page }) => {
    // Login - use id selectors for Carbon components
    await page.goto('/login');
    await page.locator('#email').fill('analyst@example.com');
    await page.locator('#password').fill('Analyst-pass-1');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('submits transaction through form and displays evaluation summary', async ({ page }) => {
    // Navigate to transaction submission page
    await page.goto('/transactions');

    // Verify page loaded
    await expect(page.getByRole('heading', { name: /submit transaction/i })).toBeVisible();

    // Fill transaction form with wireframe values - use input elements within Carbon components
    await page.locator('#ref').fill(`TXN-2026-${String(Date.now()).slice(-6)}`);
    await page.locator('#acc').selectOption('1'); // Rajesh Kumar account
    await page.locator('#amt').fill('850000.00');
    await page.locator('#typ').selectOption('TRANSFER');
    await page.locator('#org').selectOption('IN');
    await page.locator('#dst').selectOption('AE');
    await page.locator('#cpn').fill('Al Noor Trading FZE');
    await page.locator('#cpa').fill('AE07 0331 2345 6789 0123 456');

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for response to appear
    await page.waitForSelector('text=HTTP 201', { timeout: 10000 });

    // Assert response panel shows success
    await expect(page.locator('text=HTTP 201')).toBeVisible();
    await expect(page.locator('text=matchedRulesCount')).toBeVisible();
    await expect(page.locator('text=alertRaised')).toBeVisible();

    // Assert evaluation results table is present with 8 rows
    const resultRows = page.locator('[data-testid^="rule-result-AML-"]');
    await expect(resultRows).toHaveCount(8);

    // Verify all 8 rule codes are displayed
    for (let i = 1; i <= 8; i++) {
      const ruleCode = `AML-${String(i).padStart(3, '0')}`;
      await expect(page.locator(`[data-testid="rule-result-${ruleCode}"]`)).toBeVisible();
    }

    // Assert correlation ID is displayed
    await expect(page.locator('[data-testid="error-correlation-id"]')).toBeVisible();

    // Assert success toast notification appears
    await expect(page.locator('text=Transaction received and screened')).toBeVisible();
  });

  test('displays validation errors for missing required fields', async ({ page }) => {
    await page.goto('/transactions');

    // Clear amount field
    await page.locator('#amt').fill('');

    // Submit form
    await page.click('button[type="submit"]');

    // Assert validation error appears
    await expect(page.locator('text=Amount is required')).toBeVisible();
  });

  test('displays link to view transaction details', async ({ page }) => {
    await page.goto('/transactions');

    // Fill and submit minimal form
    await page.locator('#amt').fill('100000.00');
    await page.click('button[type="submit"]');

    // Wait for response
    await page.waitForSelector('text=HTTP 201', { timeout: 10000 });

    // Assert "View transaction details" link is present
    await expect(page.locator('text=View transaction details')).toBeVisible();
  });
});
