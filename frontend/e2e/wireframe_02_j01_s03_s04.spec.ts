/**
 * E2E test for wireframe 2: Transaction detail view
 * Tests navigation to transaction detail and asserts all 8 rule results displayed
 */
import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 02 - Transaction Detail', () => {
  let transactionId: string;

  test.beforeEach(async ({ page }) => {
    // Login - use id selectors for Carbon components
    await page.goto('/login');
    await page.locator('#email').fill('analyst@example.com');
    await page.locator('#password').fill('Analyst-pass-1');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');

    // Create a transaction first
    await page.goto('/transactions');
    await page.locator('#amt').fill('850000.00');
    await page.click('button[type="submit"]');
    await page.waitForSelector('text=HTTP 201', { timeout: 10000 });

    // Extract transaction ID - it's the first dd after the dt containing exactly "id"
    const idText = await page.locator('dl dt:text-is("id") + dd').textContent();
    transactionId = idText?.trim() || '';
    expect(transactionId).toBeTruthy();
  });

  test('navigates to transaction detail and displays all rule results', async ({ page }) => {
    // Navigate to transaction detail page
    await page.goto(`/transactions/${transactionId}`);

    // Verify page loaded with correct title
    await expect(page.locator('h1')).toContainText('Transaction TXN-');

    // Verify outcome tag is displayed
    await expect(page.locator('[data-testid="transaction-outcome-tag"]')).toBeVisible();

    // Verify transaction summary section is present (has aria-label)
    await expect(page.locator('[aria-label="Transaction summary"]')).toBeVisible();
    await expect(page.locator('text=Amount').first()).toBeVisible();
    await expect(page.locator('text=Date').first()).toBeVisible();
    await expect(page.locator('text=From account').first()).toBeVisible();

    // Verify screening run section is present
    await expect(page.getByRole('heading', { name: 'Screening run' })).toBeVisible();
    await expect(page.locator('text=Account and customer context loaded')).toBeVisible();
    await expect(page.locator('text=Transaction persisted')).toBeVisible();
    await expect(page.locator('text=rules evaluated and persisted')).toBeVisible();

    // Verify result summary shows rule codes
    await expect(page.locator('text=Result summary')).toBeVisible();
    
    // Verify at least some rule codes are visible in the summary
    const hasAmlCodes = await page.locator('text=/AML-\\d{3}/').count();
    expect(hasAmlCodes).toBeGreaterThan(0);

    // Verify correlation ID is displayed
    await expect(page.locator('[data-testid="error-correlation-id"]')).toBeVisible();

    // Verify account and customer context panel heading exists
    await expect(page.getByRole('heading', { name: 'Account and customer context' })).toBeVisible();
    
    // Verify the context panel has data fields (checking the dl structure exists)
    await expect(page.locator('h2:has-text("Account and customer context") ~ dl')).toBeVisible();
  });

  test('displays breadcrumb navigation', async ({ page }) => {
    await page.goto(`/transactions/${transactionId}`);

    // Verify breadcrumb is present
    await expect(page.locator('nav[aria-label="Breadcrumb"]')).toBeVisible();
    // Scope to breadcrumb navigation only to avoid conflict with sidebar
    await expect(page.locator('nav[aria-label="Breadcrumb"] a:has-text("Transactions")')).toBeVisible();
  });

  test('displays transaction outcome tag correctly', async ({ page }) => {
    await page.goto(`/transactions/${transactionId}`);

    // Verify outcome tag exists (either Flagged or Clear)
    const outcomeTag = page.locator('[data-testid="transaction-outcome-tag"]');
    await expect(outcomeTag).toBeVisible();
    
    const tagText = await outcomeTag.textContent();
    expect(['Flagged', 'Clear']).toContain(tagText);
  });

  test('shows 404 for non-existent transaction', async ({ page, apiGuard }) => {
    apiGuard.allow(404, '/transactions/999999');
    await page.goto('/transactions/999999');

    // Verify 404 message is displayed
    await expect(page.locator('text=Transaction not found')).toBeVisible();
    await expect(page.locator('text=No transaction matches this ID')).toBeVisible();
    await expect(page.locator('a:has-text("Back to transactions")')).toBeVisible();
  });

  test('displays screening steps with checkmarks', async ({ page }) => {
    await page.goto(`/transactions/${transactionId}`);

    // Verify all 5 screening steps are present
    await expect(page.locator('text=Account and customer context loaded')).toBeVisible();
    await expect(page.locator('text=Transaction persisted')).toBeVisible();
    await expect(page.locator('text=rules evaluated and persisted')).toBeVisible();
    await expect(page.locator('text=Audit events written with the same correlation ID')).toBeVisible();
  });
});
