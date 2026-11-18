/**
 * E2E tests for transaction submission and detail viewing workflow
 */
import { test, expect } from './_pipeline_guard';

const BASE_URL = 'http://127.0.0.1:5200';

test.describe('Transaction Workflow', () => {
  let authToken: string;
  
  test.beforeEach(async ({ context }) => {
    // Login before each test
    const loginResponse = await context.request.post(`${BASE_URL}/api/v1/auth/login`, {
      data: {
        username: 'analyst@example.com',
        password: 'Analyst-pass-1'
      }
    });
    const loginData = await loginResponse.json();
    authToken = loginData.access_token;
  });

  test('submit transaction and view it in detail page', async ({ page, context }) => {
    // Set auth token
    await page.goto(`${BASE_URL}/transactions`);
    await page.evaluate((token) => {
      sessionStorage.setItem('auth_token', token);
    }, authToken);
    
    await page.goto(`${BASE_URL}/transactions`);
    
    // Fill transaction form
    const timestamp = new Date().toISOString();
    await page.fill('input[name="accountId"], input[placeholder*="account"]', 'ACC-001');
    await page.fill('input[name="amount"], input[placeholder*="amount"]', '75000');
    await page.fill('input[name="transactionType"], input[placeholder*="type"], select[name="transactionType"]', 'TRANSFER');
    await page.fill('input[name="originCountry"], input[placeholder*="origin"]', 'US');
    await page.fill('input[name="destinationCountry"], input[placeholder*="destination"]', 'CA');
    await page.fill('input[name="timestamp"], input[type="datetime-local"]', timestamp.slice(0, 16));
    
    // Submit transaction
    await page.click('button[type="submit"], button:has-text("Submit")');
    
    // Wait for success message or redirect to detail page
    await page.waitForTimeout(2000);
    
    // Verify transaction was created - look for transaction ID or success message
    const hasSuccessMessage = await page.locator('text=/success|created|submitted/i').isVisible().catch(() => false);
    const urlHasId = page.url().includes('/transactions/');
    
    // One of these should be true
    expect(hasSuccessMessage || urlHasId).toBeTruthy();
    
    // If redirected to detail page, verify content
    if (urlHasId) {
      await expect(page.locator('h1, h2').filter({ hasText: /transaction|detail/i }).first()).toBeVisible();
      // Verify transaction data is shown
      await expect(page.locator('text=/75000|ACC-001/i').first()).toBeVisible();
    }
  });

  test('view existing transaction detail page', async ({ page, context }) => {
    // First create a transaction via API
    const transactionResponse = await context.request.post(`${BASE_URL}/api/v1/transactions`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: {
        accountId: 'ACC-002',
        amount: 50000,
        transactionType: 'DEPOSIT',
        originCountry: 'GB',
        destinationCountry: 'US',
        timestamp: new Date().toISOString()
      }
    });
    expect(transactionResponse.ok()).toBeTruthy();
    const transactionData = await transactionResponse.json();
    const transactionId = transactionData.id || transactionData.transaction_id || transactionData.transactionId;
    
    // Set auth token
    await page.goto(`${BASE_URL}/transactions/${transactionId}`);
    await page.evaluate((token) => {
      sessionStorage.setItem('auth_token', token);
    }, authToken);
    
    // Navigate to transaction detail
    await page.goto(`${BASE_URL}/transactions/${transactionId}`);
    
    // Verify detail page renders
    await expect(page.locator('h1, h2').filter({ hasText: /transaction|detail/i }).first()).toBeVisible();
    
    // Verify transaction data is displayed
    await expect(page.locator('text=/50000|ACC-002|DEPOSIT/i').first()).toBeVisible();
  });

  test('transaction triggers alert when matching rules', async ({ page, context }) => {
    // Create a high-value transaction that should trigger AML-001 rule
    const transactionResponse = await context.request.post(`${BASE_URL}/api/v1/transactions`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: {
        accountId: 'ACC-001',
        amount: 150000, // Above high-value threshold
        transactionType: 'WIRE',
        originCountry: 'US',
        destinationCountry: 'KP', // High-risk country
        timestamp: new Date().toISOString()
      }
    });
    expect(transactionResponse.ok()).toBeTruthy();
    const transactionData = await transactionResponse.json();
    const transactionId = transactionData.id || transactionData.transaction_id || transactionData.transactionId;
    
    // Set auth token
    await page.goto(`${BASE_URL}/transactions/${transactionId}`);
    await page.evaluate((token) => {
      sessionStorage.setItem('auth_token', token);
    }, authToken);
    
    // Navigate to transaction detail
    await page.goto(`${BASE_URL}/transactions/${transactionId}`);
    
    // Verify alert was raised
    await expect(page.locator('text=/alert|matched|rule/i').first()).toBeVisible();
  });
});
