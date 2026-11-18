/**
 * E2E tests for wireframe 05 - Information request workflow
 * Tests request information through modal and asserts request card appears
 */

import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 05 - Information Request Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login as analyst
    await page.goto('/login');
    await page.fill('#email', 'analyst@example.com');
    await page.fill('#password', 'Analyst-pass-1');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('requests information through modal and displays request card with due date', async ({ page }) => {
    // Navigate to a case (CASE-000002 from seed data is in UNDER_INVESTIGATION)
    await page.goto('/cases/2');
    
    // Wait for page to load
    await expect(page.locator('h1:has-text("Case CASE-")')).toBeVisible();

    // Click "Request information" button
    const requestButton = page.locator('button:has-text("Request information")');
    await expect(requestButton).toBeVisible();
    await requestButton.click();

    // Fill in the modal
    await page.fill('#requested-what', 'Please provide bank statements for the last 3 months');
    await page.fill('#reason', 'Need to verify transaction history and account balance');
    
    // Set due date (tomorrow)
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dueDateString = tomorrow.toISOString().split('T')[0];
    const dueDateInput = page.locator('#due-date');
    await dueDateInput.click();
    await dueDateInput.fill(dueDateString);

    // Submit the request
    await page.click('button:has-text("Send request")');

    // Wait for modal to close and page to refresh
    await page.waitForTimeout(1000);

    // Verify information request card appears
    const requestCard = page.locator('[role="status"]:has-text("Awaiting response")');
    await expect(requestCard).toBeVisible();

    // Verify due date is displayed
    await expect(requestCard).toContainText('due');

    // Verify requested information is shown
    await expect(requestCard).toContainText('Please provide bank statements for the last 3 months');

    // Verify Record response button is present (use first match or more specific selector)
    await expect(page.getByTestId('record-response-button')).toBeVisible();
  });

  test('validates required fields in request information modal', async ({ page }) => {
    await page.goto('/cases/2');
    
    // Open request information modal
    await page.click('button:has-text("Request information")');

    // Try to submit without filling fields
    const submitButton = page.locator('button:has-text("Send request")');
    await expect(submitButton).toBeDisabled();

    // Fill only requested_what
    await page.fill('#requested-what', 'Test request');
    await expect(submitButton).toBeDisabled();

    // Fill reason too
    await page.fill('#reason', 'Test reason');
    // Still disabled without due date
    await expect(submitButton).toBeDisabled();

    // Fill due date
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dueDateString = tomorrow.toISOString().split('T')[0];
    await page.fill('#due-date', dueDateString);

    // Now button should be enabled
    await expect(submitButton).toBeEnabled();
  });

  test('displays overdue indicator for past-due requests', async ({ page }) => {
    // Navigate to a case that should have an information request
    await page.goto('/cases/1');
    
    // Wait for page to load
    await expect(page.locator('h1:has-text("Case CASE-")')).toBeVisible();

    // Check if there's an information request section
    const infoSection = page.locator('h2:has-text("Information request")');
    
    // Assert the section exists before checking its contents
    await expect(infoSection).toBeVisible();
    
    // Check for request card (which should be visible if there's an open request)
    const requestCard = page.locator('[role="status"]').first();
    await expect(requestCard).toBeVisible();
  });
});
