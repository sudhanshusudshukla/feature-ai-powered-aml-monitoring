/**
 * E2E tests for authentication and navigation through all routes
 */
import { test, expect } from './_pipeline_guard';

const BASE_URL = 'http://127.0.0.1:5200';

test.describe('Authentication and Navigation', () => {
  test('login form authenticates user and redirects to dashboard', async ({ page }) => {
    // This test MUST use the login form directly, not localStorage or API shortcuts
    await page.goto(`${BASE_URL}/login`);
    
    // Verify login page loads
    await expect(page.locator('h1, h2, [role="heading"]').filter({ hasText: /login|sign in/i }).first()).toBeVisible();
    
    // Fill login form with seed credentials
    await page.fill('input[type="email"], input[name="email"], input[name="username"]', 'analyst@example.com');
    await page.fill('input[type="password"], input[name="password"]', 'Analyst-pass-1');
    
    // Submit form
    await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")');
    
    // Wait for navigation away from login page
    await page.waitForURL(/\/(dashboard|transactions|alerts|cases)/, { timeout: 10000 });
    
    // Verify we're authenticated - dashboard or protected page should be visible
    await expect(page.locator('h1, h2, [role="heading"]').first()).toBeVisible();
    
    // Verify URL is not /login anymore
    expect(page.url()).not.toContain('/login');
  });

  test('dashboard page renders for authenticated user', async ({ page, context }) => {
    // Login via API and set token
    const loginResponse = await context.request.post(`${BASE_URL}/api/v1/auth/login`, {
      data: {
        username: 'analyst@example.com',
        password: 'Analyst-pass-1'
      }
    });
    expect(loginResponse.ok()).toBeTruthy();
    const loginData = await loginResponse.json();
    
    // Set token in sessionStorage
    await page.goto(`${BASE_URL}/dashboard`);
    await page.evaluate((token) => {
      sessionStorage.setItem('auth_token', token);
    }, loginData.access_token);
    
    // Navigate to dashboard
    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page.locator('h1, h2').filter({ hasText: /dashboard|welcome/i }).first()).toBeVisible();
  });

  test('transactions page renders', async ({ page, context }) => {
    // Login and set token
    const loginResponse = await context.request.post(`${BASE_URL}/api/v1/auth/login`, {
      data: {
        username: 'analyst@example.com',
        password: 'Analyst-pass-1'
      }
    });
    const loginData = await loginResponse.json();
    await page.goto(`${BASE_URL}/transactions`);
    await page.evaluate((token) => {
      sessionStorage.setItem('auth_token', token);
    }, loginData.access_token);
    
    await page.goto(`${BASE_URL}/transactions`);
    await expect(page.locator('h1, h2').filter({ hasText: /transaction/i }).first()).toBeVisible();
  });

  test('alerts list page renders', async ({ page, context }) => {
    // Login and set token
    const loginResponse = await context.request.post(`${BASE_URL}/api/v1/auth/login`, {
      data: {
        username: 'analyst@example.com',
        password: 'Analyst-pass-1'
      }
    });
    const loginData = await loginResponse.json();
    await page.goto(`${BASE_URL}/alerts`);
    await page.evaluate((token) => {
      sessionStorage.setItem('auth_token', token);
    }, loginData.access_token);
    
    await page.goto(`${BASE_URL}/alerts`);
    await expect(page.locator('h1, h2').filter({ hasText: /alert/i }).first()).toBeVisible();
  });

  test('cases list page renders', async ({ page, context }) => {
    // Login and set token
    const loginResponse = await context.request.post(`${BASE_URL}/api/v1/auth/login`, {
      data: {
        username: 'officer@example.com',
        password: 'Officer-pass-1'
      }
    });
    const loginData = await loginResponse.json();
    await page.goto(`${BASE_URL}/cases`);
    await page.evaluate((token) => {
      sessionStorage.setItem('auth_token', token);
    }, loginData.access_token);
    
    await page.goto(`${BASE_URL}/cases`);
    await expect(page.locator('h1, h2').filter({ hasText: /case/i }).first()).toBeVisible();
  });

  test('rules page renders', async ({ page, context }) => {
    // Login and set token
    const loginResponse = await context.request.post(`${BASE_URL}/api/v1/auth/login`, {
      data: {
        username: 'analyst@example.com',
        password: 'Analyst-pass-1'
      }
    });
    const loginData = await loginResponse.json();
    await page.goto(`${BASE_URL}/rules`);
    await page.evaluate((token) => {
      sessionStorage.setItem('auth_token', token);
    }, loginData.access_token);
    
    await page.goto(`${BASE_URL}/rules`);
    await expect(page.locator('h1, h2').filter({ hasText: /rule/i }).first()).toBeVisible();
  });

  test('admin page renders', async ({ page, context }) => {
    // Login and set token as admin
    const loginResponse = await context.request.post(`${BASE_URL}/api/v1/auth/login`, {
      data: {
        username: 'admin@example.com',
        password: 'Admin-pass-1'
      }
    });
    const loginData = await loginResponse.json();
    await page.goto(`${BASE_URL}/admin`);
    await page.evaluate((token) => {
      sessionStorage.setItem('auth_token', token);
    }, loginData.access_token);
    
    await page.goto(`${BASE_URL}/admin`);
    await expect(page.locator('h1, h2').filter({ hasText: /admin/i }).first()).toBeVisible();
  });

  test('logout clears authentication', async ({ page, context }) => {
    // Login
    const loginResponse = await context.request.post(`${BASE_URL}/api/v1/auth/login`, {
      data: {
        username: 'analyst@example.com',
        password: 'Analyst-pass-1'
      }
    });
    const loginData = await loginResponse.json();
    await page.goto(`${BASE_URL}/dashboard`);
    await page.evaluate((token) => {
      sessionStorage.setItem('auth_token', token);
    }, loginData.access_token);
    
    await page.goto(`${BASE_URL}/dashboard`);
    
    // Look for logout button and click
    const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Log out"), button:has-text("Sign out")').first();
    await logoutButton.click();
    
    // Should redirect to login
    await page.waitForURL(/\/login/, { timeout: 5000 });
    await expect(page.locator('h1, h2').filter({ hasText: /login|sign in/i }).first()).toBeVisible();
  });
});
