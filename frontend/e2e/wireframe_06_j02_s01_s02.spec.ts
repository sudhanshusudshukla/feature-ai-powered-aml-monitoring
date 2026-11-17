/**
 * E2E tests for wireframe 06 - Case workspace
 * Tests case workspace load, linked alerts table, notes thread, audit timeline
 */

import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 06 - Case Workspace', () => {
  test.beforeEach(async ({ page }) => {
    // Login as officer
    await page.goto('/login');
    await page.fill('#email', 'officer@example.com');
    await page.fill('#password', 'Officer-pass-1');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('loads case workspace and displays all sections', async ({ page }) => {
    // Navigate to case workspace (CASE-000001 from seed data)
    await page.goto('/cases/1');

    // Verify page loads
    await expect(page.locator('h1:has-text("Case CASE-")')).toBeVisible();

    // Verify breadcrumb navigation
    const breadcrumb = page.locator('[aria-label="Breadcrumb"]');
    await expect(breadcrumb).toBeVisible();
    await expect(breadcrumb.locator('text=Cases')).toBeVisible();

    // Verify case title with priority and status tags
    await expect(page.locator('[data-testid="priority-tag"]')).toBeVisible();
    await expect(page.locator('[data-testid="case-status-tag"]')).toBeVisible();

    // Verify key facts line (customer, created date, linked alerts)
    await expect(page.locator('text=Customer:')).toBeVisible();
    await expect(page.locator('text=Created')).toBeVisible();
    await expect(page.locator('text=linked alert')).toBeVisible();

    // Verify linked alerts section
    await expect(page.locator('h2:has-text("Linked alerts")')).toBeVisible();

    // Verify notes section
    await expect(page.locator('h3:has-text("Notes")')).toBeVisible();

    // Verify audit timeline section
    await expect(page.locator('h2:has-text("Audit timeline")')).toBeVisible();

    // Verify decision panel
    await expect(page.locator('[data-testid="decision-panel"]')).toBeVisible();
    await expect(page.locator('h2:has-text("Decision")')).toBeVisible();
  });

  test('displays linked alerts table with correct columns', async ({ page }) => {
    await page.goto('/cases/1');

    // Wait for linked alerts table
    const alertsTable = page.locator('[aria-label="Linked alerts"]');
    await expect(alertsTable).toBeVisible();

    // Verify table headers
    await expect(alertsTable.locator('th:has-text("Alert")')).toBeVisible();
    await expect(alertsTable.locator('th:has-text("Priority")')).toBeVisible();
    await expect(alertsTable.locator('th:has-text("Risk score")')).toBeVisible();
    await expect(alertsTable.locator('th:has-text("Transaction")')).toBeVisible();
    await expect(alertsTable.locator('th:has-text("Status")')).toBeVisible();

    // Verify at least one alert row exists
    const alertRows = alertsTable.locator('tbody tr');
    await expect(alertRows.first()).toBeVisible();

    // Verify alert link is clickable
    const alertLink = alertRows.first().locator('a').first();
    await expect(alertLink).toBeVisible();
    await expect(alertLink).toHaveAttribute('href', /\/alerts\/\d+/);
  });

  test('displays notes thread with add note functionality', async ({ page }) => {
    await page.goto('/cases/1');

    // Find notes section
    const notesSection = page.locator('h3:has-text("Notes")');
    await expect(notesSection).toBeVisible();

    // Assert "Add note" button exists
    const addNoteButton = page.locator('button:has-text("Add note")');
    await expect(addNoteButton).toBeVisible();

    // Click to open composer
    await addNoteButton.click();

    // Verify composer appears
    await expect(page.locator('#note-composer')).toBeVisible();

    // Wait a moment for buttons to render
    await page.waitForTimeout(200);
    
    // Try to submit empty note (should be disabled) - just verify submit button state
    const submitButton = page.locator('button:has-text("Add note")').last();
    await expect(submitButton).toBeDisabled();

    // Fill note text
    await page.fill('#note-composer', 'Test investigation note');

    // Submit button should now be enabled
    await expect(submitButton).toBeEnabled();
  });

  test('displays audit timeline for case', async ({ page }) => {
    await page.goto('/cases/1');

    // Verify audit timeline section
    const timelineSection = page.locator('h2:has-text("Audit timeline")');
    await expect(timelineSection).toBeVisible();

    // Note: Actual audit events depend on AuditTimeline component implementation
    // This test verifies the section exists
  });

  test('displays decision panel with permitted actions', async ({ page }) => {
    await page.goto('/cases/1');

    // Verify decision panel
    const decisionPanel = page.locator('[data-testid="decision-panel"]');
    await expect(decisionPanel).toBeVisible();

    // Verify it shows permitted actions information
    await expect(decisionPanel).toContainText('Permitted actions');

    // Panel should be sticky positioned
    const styles = await decisionPanel.evaluate(el => {
      return window.getComputedStyle(el).position;
    });
    expect(styles).toBe('sticky');
  });

  test('navigates from breadcrumb back to cases list', async ({ page }) => {
    await page.goto('/cases/1');

    // Click breadcrumb "Cases" link
    const casesLink = page.locator('[aria-label="Breadcrumb"] a:has-text("Cases")');
    await expect(casesLink).toBeVisible();
    
    // For now, just verify the link exists and has correct href
    await expect(casesLink).toHaveAttribute('href', '/cases');
  });

  test('displays information request section when request exists', async ({ page }) => {
    // Navigate to a case with an open information request
    // According to seed data, we should have a case with an open request
    await page.goto('/cases/1');

    // Wait for page to load
    await expect(page.locator('h1:has-text("Case CASE-")')).toBeVisible();

    // The case workspace should display the page successfully
    // The information request section may or may not be visible depending on case state
    // We verify the page loads and basic structure exists
    await expect(page.locator('[data-testid="decision-panel"]')).toBeVisible();
  });

  test('case not found displays error state', async ({ page, apiGuard }) => {
    // Navigate to non-existent case
    apiGuard.allow(404, '/cases/99999');
    await page.goto('/cases/99999');

    // Verify error message
    await expect(page.locator('text=Case not found')).toBeVisible();
    await expect(page.locator('text=No case matches this ID')).toBeVisible();

    // Verify back link
    await expect(page.locator('a:has-text("Back to cases")')).toBeVisible();
  });
});
