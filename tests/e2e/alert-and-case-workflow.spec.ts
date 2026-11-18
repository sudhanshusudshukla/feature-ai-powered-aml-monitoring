/**
 * E2E tests for alert and case management workflows
 */
import { test, expect } from './_pipeline_guard';

const BASE_URL = 'http://127.0.0.1:5200';

test.describe('Alert and Case Workflow', () => {
  let analystToken: string;
  let officerToken: string;
  
  test.beforeAll(async ({ request }) => {
    // Get analyst token
    const analystLogin = await request.post(`${BASE_URL}/api/v1/auth/login`, {
      data: {
        username: 'analyst@example.com',
        password: 'Analyst-pass-1'
      }
    });
    const analystData = await analystLogin.json();
    analystToken = analystData.access_token;
    
    // Get officer token
    const officerLogin = await request.post(`${BASE_URL}/api/v1/auth/login`, {
      data: {
        username: 'officer@example.com',
        password: 'Officer-pass-1'
      }
    });
    const officerData = await officerLogin.json();
    officerToken = officerData.access_token;
  });

  test('view alert list page', async ({ page }) => {
    await page.goto(`${BASE_URL}/alerts`);
    await page.evaluate((token) => {
      sessionStorage.setItem('auth_token', token);
    }, analystToken);
    
    await page.goto(`${BASE_URL}/alerts`);
    
    // Verify alerts page renders
    await expect(page.locator('h1, h2').filter({ hasText: /alert/i }).first()).toBeVisible();
  });

  test('view alert detail page', async ({ page, request }) => {
    // First create a transaction that generates an alert
    const transactionResponse = await request.post(`${BASE_URL}/api/v1/transactions`, {
      headers: {
        'Authorization': `Bearer ${analystToken}`,
        'Content-Type': 'application/json'
      },
      data: {
        accountId: 'ACC-001',
        amount: 200000, // High value to trigger alert
        transactionType: 'WIRE',
        originCountry: 'US',
        destinationCountry: 'IR', // High-risk
        timestamp: new Date().toISOString()
      }
    });
    expect(transactionResponse.ok()).toBeTruthy();
    const transactionData = await transactionResponse.json();
    
    // Get the alert ID from transaction data
    const alertId = transactionData.alert_id || transactionData.alertId;
    
    if (alertId) {
      await page.goto(`${BASE_URL}/alerts/${alertId}`);
      await page.evaluate((token) => {
        sessionStorage.setItem('auth_token', token);
      }, analystToken);
      
      await page.goto(`${BASE_URL}/alerts/${alertId}`);
      
      // Verify alert detail renders
      await expect(page.locator('h1, h2').filter({ hasText: /alert/i }).first()).toBeVisible();
      
      // Verify alert shows risk information
      await expect(page.locator('text=/risk|priority|severity/i').first()).toBeVisible();
    } else {
      // Get alerts list and pick the first one
      const alertsResponse = await request.get(`${BASE_URL}/api/v1/alerts`, {
        headers: {
          'Authorization': `Bearer ${analystToken}`
        }
      });
      expect(alertsResponse.ok()).toBeTruthy();
      const alertsData = await alertsResponse.json();
      const alerts = alertsData.items || alertsData.alerts || alertsData;
      
      if (alerts && alerts.length > 0) {
        const firstAlertId = alerts[0].id || alerts[0].alert_id;
        
        await page.goto(`${BASE_URL}/alerts/${firstAlertId}`);
        await page.evaluate((token) => {
          sessionStorage.setItem('auth_token', token);
        }, analystToken);
        
        await page.goto(`${BASE_URL}/alerts/${firstAlertId}`);
        
        await expect(page.locator('h1, h2').filter({ hasText: /alert/i }).first()).toBeVisible();
      }
    }
  });

  test('create case from alert', async ({ page, request }) => {
    // Create a transaction that generates an alert
    const transactionResponse = await request.post(`${BASE_URL}/api/v1/transactions`, {
      headers: {
        'Authorization': `Bearer ${officerToken}`,
        'Content-Type': 'application/json'
      },
      data: {
        accountId: 'ACC-001',
        amount: 250000,
        transactionType: 'WIRE',
        originCountry: 'US',
        destinationCountry: 'SY',
        timestamp: new Date().toISOString()
      }
    });
    expect(transactionResponse.ok()).toBeTruthy();
    const transactionData = await transactionResponse.json();
    
    // Get alerts
    const alertsResponse = await request.get(`${BASE_URL}/api/v1/alerts`, {
      headers: {
        'Authorization': `Bearer ${officerToken}`
      }
    });
    expect(alertsResponse.ok()).toBeTruthy();
    const alertsData = await alertsResponse.json();
    const alerts = alertsData.items || alertsData.alerts || alertsData;
    
    if (alerts && alerts.length > 0) {
      const alertId = alerts[0].id || alerts[0].alert_id;
      
      // Create case via API
      const caseResponse = await request.post(`${BASE_URL}/api/v1/cases`, {
        headers: {
          'Authorization': `Bearer ${officerToken}`,
          'Content-Type': 'application/json'
        },
        data: {
          alert_ids: [alertId],
          priority: 'HIGH',
          notes: 'E2E test case'
        }
      });
      expect(caseResponse.ok()).toBeTruthy();
      const caseData = await caseResponse.json();
      const caseId = caseData.id || caseData.case_id || caseData.caseId;
      
      // Navigate to case detail page
      await page.goto(`${BASE_URL}/cases/${caseId}`);
      await page.evaluate((token) => {
        sessionStorage.setItem('auth_token', token);
      }, officerToken);
      
      await page.goto(`${BASE_URL}/cases/${caseId}`);
      
      // Verify case detail page renders
      await expect(page.locator('h1, h2').filter({ hasText: /case/i }).first()).toBeVisible();
      
      // Verify case shows linked alert
      await expect(page.locator('text=/alert|linked/i').first()).toBeVisible();
    }
  });

  test('case detail page displays tabs and sections', async ({ page, request }) => {
    // Get or create a case
    const casesResponse = await request.get(`${BASE_URL}/api/v1/cases`, {
      headers: {
        'Authorization': `Bearer ${officerToken}`
      }
    });
    expect(casesResponse.ok()).toBeTruthy();
    const casesData = await casesResponse.json();
    const cases = casesData.items || casesData.cases || casesData;
    
    let caseId: string;
    
    if (cases && cases.length > 0) {
      caseId = cases[0].id || cases[0].case_id;
    } else {
      // Create a new case
      const alertsResponse = await request.get(`${BASE_URL}/api/v1/alerts`, {
        headers: {
          'Authorization': `Bearer ${officerToken}`
        }
      });
      const alertsData = await alertsResponse.json();
      const alerts = alertsData.items || alertsData.alerts || alertsData;
      
      if (alerts && alerts.length > 0) {
        const alertId = alerts[0].id || alerts[0].alert_id;
        const caseResponse = await request.post(`${BASE_URL}/api/v1/cases`, {
          headers: {
            'Authorization': `Bearer ${officerToken}`,
            'Content-Type': 'application/json'
          },
          data: {
            alert_ids: [alertId],
            priority: 'MEDIUM'
          }
        });
        const caseData = await caseResponse.json();
        caseId = caseData.id || caseData.case_id;
      }
    }
    
    if (caseId) {
      await page.goto(`${BASE_URL}/cases/${caseId}`);
      await page.evaluate((token) => {
        sessionStorage.setItem('auth_token', token);
      }, officerToken);
      
      await page.goto(`${BASE_URL}/cases/${caseId}`);
      
      // Verify case workspace renders
      await expect(page.locator('h1, h2').filter({ hasText: /case/i }).first()).toBeVisible();
      
      // Look for tabs or sections (alerts, notes, timeline, etc.)
      const hasTabs = await page.locator('[role="tab"], .tab, button:has-text("Alerts"), button:has-text("Notes"), button:has-text("Timeline")').first().isVisible().catch(() => false);
      const hasSections = await page.locator('h2, h3').filter({ hasText: /alert|note|timeline|detail/i }).first().isVisible().catch(() => false);
      
      // Either tabs or sections should be present
      expect(hasTabs || hasSections).toBeTruthy();
    }
  });
});
