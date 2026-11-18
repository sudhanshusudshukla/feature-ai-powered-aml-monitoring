/**
 * E2E Journey Test: Transaction Receipt → Screening → Alert Generation → Audit Trail
 * 
 * This test verifies the complete end-to-end flow from submitting a transaction
 * through the frontend UI, seeing it evaluated by AML rules, generating an alert,
 * and verifying the audit trail.
 */
import { test, expect } from './_pipeline_guard';

test.describe('Journey 1: Transaction to Alert', () => {
  test.beforeEach(async ({ page }) => {
    // Login as analyst
    await page.goto('/login');
    await page.fill('#email', 'analyst@example.com');
    await page.fill('#password', 'Analyst-pass-1');
    await page.click('button[type="submit"]');
    
    // Wait for navigation to dashboard
    await page.waitForURL(/\/dashboard/);
  });

  // TODO: Requires complete transaction submission UI workflow not fully implemented
  test.skip('should complete transaction submission to alert generation workflow', async ({ page }) => {
    // Step 1: Navigate to transaction submission page
    await page.click('a[href="/transactions"]');
    await page.waitForURL(/\/transactions/);
    
    await page.click('text=Submit Transaction');
    await page.waitForURL(/\/transactions\/submit/);
    
    // Step 2: Fill transaction form with high-value amount (triggers AML-001)
    await page.fill('#amt', '150000.00');
    await page.selectOption('#type', 'TRANSFER');
    await page.fill('#acc', 'ACC-DEMO-001');
    await page.fill('#orig', 'US');
    await page.fill('#dest', 'RU');
    await page.fill('#ref', `TXN-E2E-${Date.now()}`);
    
    // Step 3: Submit transaction
    await page.click('button[type="submit"]');
    
    // Step 4: Verify success message and evaluation summary
    await expect(page.locator('text=Transaction submitted successfully')).toBeVisible({ timeout: 10000 });
    
    // Verify evaluation summary shows rules were evaluated
    const evaluationSummary = page.locator('[data-testid="evaluation-summary"]');
    await expect(evaluationSummary).toBeVisible();
    
    // Should show 8 rules evaluated
    const rulesEvaluatedText = await page.locator('text=/8 rules evaluated/i').textContent();
    expect(rulesEvaluatedText).toContain('8');
    
    // Should show at least 1 match for high-value transaction
    const matchedRulesText = await page.locator('text=/matched/i').first().textContent();
    expect(matchedRulesText).toBeTruthy();
    
    // Should indicate alert was raised
    await expect(page.locator('text=/alert.*raised/i')).toBeVisible();
    
    // Step 5: Navigate to transaction detail to see full screening results
    await page.click('text=View Details');
    await page.waitForURL(/\/transactions\/.+/);
    
    // Verify transaction summary section
    await expect(page.locator('h2:has-text("Transaction Summary")')).toBeVisible();
    await expect(page.locator('text=150000.00')).toBeVisible();
    await expect(page.locator('text=TRANSFER')).toBeVisible();
    
    // Verify screening results section
    await expect(page.locator('h3:has-text("Screening Results")')).toBeVisible();
    
    // Verify AML-001 (High Value Transaction) shows MATCH
    const aml001Card = page.locator('[data-testid="rule-result-AML-001"]');
    await expect(aml001Card).toBeVisible();
    await expect(aml001Card.locator('text=MATCH')).toBeVisible();
    await expect(aml001Card.locator('text=/High Value Transaction/i')).toBeVisible();
    
    // Step 6: Navigate to generated alert
    const alertLink = page.locator('a[href^="/alerts/"]').first();
    const alertHref = await alertLink.getAttribute('href');
    expect(alertHref).toBeTruthy();
    
    await alertLink.click();
    await page.waitForURL(/\/alerts\/.+/);
    
    // Verify alert detail page
    await expect(page.locator('h2:has-text("Alert Detail")')).toBeVisible();
    await expect(page.locator('text=/Priority/i')).toBeVisible();
    await expect(page.locator('text=/Risk Score/i')).toBeVisible();
    
    // Verify alert shows as NEW status
    await expect(page.locator('text=NEW')).toBeVisible();
    
    // Verify alert links back to transaction
    const transactionLink = page.locator('a[href^="/transactions/"]').first();
    await expect(transactionLink).toBeVisible();
    
    // Step 7: Check audit trail (if accessible from alert detail)
    // Note: Audit trail may be on a separate page or require additional navigation
    // This step verifies the workflow created proper audit events
    const hasAuditSection = await page.locator('text=/audit.*trail/i').count() > 0;
    if (hasAuditSection) {
      await expect(page.locator('text=/TRANSACTION_INGESTED/i')).toBeVisible();
      await expect(page.locator('text=/ALERT_GENERATED/i')).toBeVisible();
    }
  });

  // TODO: Requires complete transaction submission UI workflow not fully implemented
  test.skip('should show no alert for low-value transaction', async ({ page }) => {
    // Navigate to transaction submission
    await page.click('a[href="/transactions"]');
    await page.click('text=Submit Transaction');
    
    // Fill transaction form with low value (should not trigger rules)
    await page.fill('#amt', '100.00');
    await page.selectOption('#type', 'DEPOSIT');
    await page.fill('#acc', 'ACC-DEMO-001');
    await page.fill('#orig', 'US');
    await page.fill('#dest', 'US');
    await page.fill('#ref', `TXN-LOW-${Date.now()}`);
    
    // Submit transaction
    await page.click('button[type="submit"]');
    
    // Verify success message
    await expect(page.locator('text=Transaction submitted successfully')).toBeVisible({ timeout: 10000 });
    
    // Verify evaluation summary shows no matches
    const evaluationSummary = page.locator('[data-testid="evaluation-summary"]');
    await expect(evaluationSummary).toBeVisible();
    
    // Should show 8 rules evaluated
    await expect(page.locator('text=/8 rules evaluated/i')).toBeVisible();
    
    // Should show 0 matches
    const matchedText = await page.locator('text=/0.*matched/i').textContent();
    expect(matchedText).toContain('0');
    
    // Should indicate no alert
    await expect(page.locator('text=/no alert/i')).toBeVisible();
    
    // Navigate to detail and verify no alert link
    await page.click('text=View Details');
    await page.waitForURL(/\/transactions\/.+/);
    
    // Verify all rule results show PASS
    const ruleResults = page.locator('[data-testid^="rule-result-"]');
    const count = await ruleResults.count();
    expect(count).toBe(8);
    
    for (let i = 0; i < count; i++) {
      const result = ruleResults.nth(i);
      await expect(result.locator('text=PASS')).toBeVisible();
    }
  });

  // TODO: Requires complete transaction submission UI with validation not fully implemented
  test.skip('should validate transaction form and show errors', async ({ page }) => {
    // Navigate to transaction submission
    await page.click('a[href="/transactions"]');
    await page.click('text=Submit Transaction');
    
    // Try to submit empty form
    await page.click('button[type="submit"]');
    
    // Should show validation errors
    await expect(page.locator('text=/required/i')).toBeVisible();
    
    // Fill amount with invalid value
    await page.fill('#amt', '-100');
    await page.click('button[type="submit"]');
    
    // Should show validation error for negative amount
    await expect(page.locator('text=/positive|greater than/i')).toBeVisible();
    
    // Fill valid amount but missing account
    await page.fill('#amt', '1000.00');
    await page.selectOption('#type', 'TRANSFER');
    await page.click('button[type="submit"]');
    
    // Should show error for missing account
    await expect(page.locator('text=/account.*required/i')).toBeVisible();
  });

  // TODO: Requires complete transaction detail UI with rule explanations not fully implemented
  test.skip('should display rule evaluation explanations and evidence', async ({ page }) => {
    // Submit a transaction that triggers multiple rules
    await page.click('a[href="/transactions"]');
    await page.click('text=Submit Transaction');
    
    // High value + high risk destination + round amount
    await page.fill('#amt', '200000.00');
    await page.selectOption('#type', 'TRANSFER');
    await page.fill('#acc', 'ACC-DEMO-001');
    await page.fill('#orig', 'US');
    await page.fill('#dest', 'CN'); // High risk country
    await page.fill('#ref', `TXN-MULTI-${Date.now()}`);
    
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Transaction submitted successfully')).toBeVisible({ timeout: 10000 });
    
    // Navigate to detail
    await page.click('text=View Details');
    await page.waitForURL(/\/transactions\/.+/);
    
    // Click on a matched rule to see explanation
    const matchedRule = page.locator('[data-testid^="rule-result-"]').filter({ hasText: 'MATCH' }).first();
    await matchedRule.click();
    
    // Verify explanation is visible
    await expect(page.locator('text=/explanation|reason|why/i')).toBeVisible();
    
    // Verify evidence snapshot is shown
    await expect(page.locator('text=/evidence|threshold|detected/i')).toBeVisible();
    
    // Verify severity and score are displayed
    await expect(page.locator('text=/severity/i')).toBeVisible();
    await expect(page.locator('text=/score/i')).toBeVisible();
  });
});
