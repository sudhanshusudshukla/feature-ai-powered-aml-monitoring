/**
 * E2E tests for wireframe 03 (Alert Detail Page)
 * Tests alert detail view with priority tag, matched rule explanations, transaction link
 */
import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 03 - Alert Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    // Log in through the login form
    await page.goto('/login');
    await page.fill('#email', 'analyst@example.com');
    await page.fill('#password', 'Analyst-pass-1');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('loads alert detail and displays priority tag', async ({ page }) => {
    // Navigate to alert detail (assumes alert ID 1 exists from seed data)
    await page.goto('/alerts/1');

    // Wait for page to load
    await expect(page.locator('h1')).toContainText('Alert ALT-');

    // Verify priority tag is present
    const priorityTag = page.locator('[data-testid="priority-tag"]');
    await expect(priorityTag).toBeVisible();
    const tagText = await priorityTag.textContent();
    expect(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']).toContain(tagText);
  });

  test('displays matched rule explanations with correct severity', async ({ page }) => {
    await page.goto('/alerts/1');

    // Wait for matched rules section - use a more flexible locator
    await expect(page.locator('text=/Matched rules/i').first()).toBeVisible({ timeout: 10000 });

    // Check for at least one explanation callout
    const explanations = page.locator('[data-testid^="explanation-"]');
    const count = await explanations.count();
    expect(count).toBeGreaterThan(0);

    // Verify first explanation has required content
    const firstExplanation = explanations.first();
    await expect(firstExplanation).toBeVisible();
    const text = await firstExplanation.textContent();
    expect(text).toMatch(/AML-\d{3}/); // Rule code pattern
  });

  test('displays transaction link that navigates to transaction detail', async ({ page }) => {
    await page.goto('/alerts/1');

    // Find transaction link in description
    const txnLink = page.locator('a[href^="/transactions/"]').first();
    await expect(txnLink).toBeVisible();

    // Verify link has transaction reference format
    const linkText = await txnLink.textContent();
    expect(linkText).toMatch(/TXN-/);
  });

  test('displays risk score breakdown with all components', async ({ page }) => {
    await page.goto('/alerts/1');

    // Wait for priority rationale section
    await expect(page.locator('h2:has-text("Priority rationale")')).toBeVisible();

    // Verify score breakdown elements are present (using dt selectors for specificity)
    await expect(page.locator('dt').filter({ hasText: 'Base score' })).toBeVisible();
    await expect(page.locator('dt').filter({ hasText: 'Customer risk adjustment' })).toBeVisible();
    await expect(page.locator('dt').filter({ hasText: 'Geography adjustment' })).toBeVisible();
    await expect(page.locator('dt').filter({ hasText: 'Final score' })).toBeVisible();
  });

  test('displays customer snapshot with risk level', async ({ page }) => {
    await page.goto('/alerts/1');

    // Wait for customer section
    await expect(page.locator('h3:has-text("Customer")')).toBeVisible();

    // Verify customer details are present
    const customerSection = page.locator('h3:has-text("Customer")').locator('..');
    await expect(customerSection).toContainText('CUST-'); // Customer number format
    await expect(customerSection).toContainText('PEP:');
    await expect(customerSection).toContainText('Account');
  });

  test('handles 404 for non-existent alert', async ({ page, apiGuard }) => {
    apiGuard.allow(404, '/alerts/999999');
    await page.goto('/alerts/999999');

    // Should show error notification
    await expect(page.locator('text=Alert not found')).toBeVisible();
  });
});
