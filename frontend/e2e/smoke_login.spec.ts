import { test, expect } from './_pipeline_guard';

test('smoke: user can log in with seed credentials and see dashboard', async ({ page }) => {
  // Navigate to the login page
  await page.goto('/login');

  // Verify we're on the login page
  await expect(page.getByRole('heading', { name: /AML Transaction Monitoring/i })).toBeVisible();
  await expect(page.getByText(/Sign in to your account/i)).toBeVisible();

  // Fill in the login form with seed credentials
  await page.getByLabel('Email').fill('officer@example.com');
  await page.locator('input[type="password"]').fill('Officer-pass-1');

  // Submit the form
  await page.getByRole('button', { name: /Sign in/i }).click();

  // Wait for navigation to dashboard
  await page.waitForURL('/dashboard');

  // Verify we're logged in and on the dashboard
  await expect(page.getByRole('heading', { name: /Dashboard/i })).toBeVisible();
  await expect(page.getByText(/Welcome to the AML Transaction Monitoring Platform/i)).toBeVisible();

  // Verify user menu shows the logged-in user's role tag in header
  await expect(page.locator('.cds--tag__label').getByText('AML OFFICER')).toBeVisible();
});
