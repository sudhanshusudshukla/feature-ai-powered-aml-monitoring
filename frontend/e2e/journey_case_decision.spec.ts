/**
 * E2E Journey Test: Case Creation → Investigation → Information Request → Response → Decision → Audit Trail
 * 
 * This test verifies the complete case management workflow including separation of duties
 * enforcement where the case creator (analyst) cannot make the final decision, which must
 * be done by an officer.
 */
import { test, expect } from './_pipeline_guard';

test.describe('Journey 2: Case Decision with Separation of Duties', () => {
  
  // TODO: Requires case creation UI, investigation forms, and decision controls not yet implemented
  test.skip('should complete full case investigation and decision workflow', async ({ page }) => {
    // Step 1: Login as analyst
    await page.goto('/login');
    await page.fill('#email', 'analyst@example.com');
    await page.fill('#password', 'Analyst-pass-1');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/);
    
    // Step 2: Create a transaction that generates an alert
    await page.click('a[href="/transactions"]');
    await page.click('text=Submit Transaction');
    
    const txnRef = `TXN-CASE-${Date.now()}`;
    await page.fill('#amt', '175000.00');
    await page.selectOption('#type', 'TRANSFER');
    await page.fill('#acc', 'ACC-DEMO-001');
    await page.fill('#orig', 'US');
    await page.fill('#dest', 'RU');
    await page.fill('#ref', txnRef);
    
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Transaction submitted successfully')).toBeVisible({ timeout: 10000 });
    
    // Navigate to the generated alert
    const alertLink = page.locator('a[href^="/alerts/"]').first();
    await alertLink.click();
    await page.waitForURL(/\/alerts\/.+/);
    
    // Step 3: Create case from alert
    await page.click('button:has-text("Create Case")');
    
    // Fill case creation form
    await page.fill('input[name="title"]', 'Investigation of High-Value Cross-Border Transfer');
    await page.click('button:has-text("Create Case")');
    
    // Should navigate to case detail
    await page.waitForURL(/\/cases\/.+/);
    await expect(page.locator('h2:has-text("Case Detail")')).toBeVisible();
    
    // Verify case shows OPEN state
    await expect(page.locator('text=OPEN')).toBeVisible();
    
    // Step 4: Add investigation note
    await page.click('button:has-text("Add Note")');
    await page.fill('textarea[name="note_text"]', 
      'Initial review completed. Transaction is high-value to sanctioned country. Requires documentation review.');
    await page.click('button:has-text("Save Note")');
    
    // Verify note appears in case timeline
    await expect(page.locator('text=Initial review completed')).toBeVisible();
    
    // Step 5: Request information
    await page.click('button:has-text("Request Information")');
    await page.fill('input[name="requested_what"]', 'Business purpose documentation and customer identity verification');
    await page.fill('textarea[name="reason"]', 'Need to verify legitimate business purpose for large transfer to high-risk jurisdiction');
    
    // Set due date 5 days from now
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 5);
    const dueDateStr = futureDate.toISOString().split('T')[0];
    await page.fill('input[name="due_date"]', dueDateStr);
    
    await page.click('button:has-text("Submit Request")');
    
    // Verify information request appears
    await expect(page.locator('text=Business purpose documentation')).toBeVisible();
    await expect(page.locator('text=OPEN').nth(1)).toBeVisible(); // Request status
    
    // Step 6: Record information response
    await page.click('button:has-text("Record Response")');
    await page.fill('textarea[name="response_text"]', 
      'Customer provided invoice, shipping documents, and contract confirming legitimate business transaction for equipment purchase.');
    await page.click('button:has-text("Save Response")');
    
    // Verify response appears
    await expect(page.locator('text=Customer provided invoice')).toBeVisible();
    
    // Step 7: Verify analyst CANNOT make decision (separation of duties)
    // Decision buttons should be disabled or show warning for creator
    const approveButton = page.locator('button:has-text("Approve")');
    const rejectButton = page.locator('button:has-text("Reject")');
    
    // Either buttons are disabled or warning is shown
    const buttonCount = await approveButton.count();
    if (buttonCount > 0) {
      const isDisabled = await approveButton.isDisabled();
      expect(isDisabled).toBe(true);
    }
    // If no buttons, must show permission warning
    if (buttonCount === 0) {
      await expect(page.locator('text=/cannot.*decide.*own.*case/i')).toBeVisible();
    }
    
    // Step 8: Logout and login as officer
    await page.click('button:has-text("Logout")');
    await page.waitForURL(/\/login/);
    
    await page.fill('#email', 'officer@example.com');
    await page.fill('#password', 'Officer-pass-1');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/);
    
    // Step 9: Navigate back to the case (via cases list)
    await page.click('a[href="/cases"]');
    await page.waitForURL(/\/cases/);
    
    // Find and click on the case (should be recent, at top)
    await page.click(`text=Investigation of High-Value Cross-Border Transfer`);
    await page.waitForURL(/\/cases\/.+/);
    
    // Step 10: Officer makes decision
    await page.click('button:has-text("Approve")');
    
    // Fill decision form
    await page.fill('textarea[name="reason"]', 'Transaction verified as legitimate business purpose for equipment purchase');
    await page.fill('textarea[name="comments"]', 
      'Documentation reviewed: invoice, shipping docs, and contract all in order. Customer has established business relationship. No AML concerns.');
    
    await page.click('button:has-text("Confirm Approval")');
    
    // Verify case state updated
    await expect(page.locator('text=APPROVED')).toBeVisible({ timeout: 5000 });
    
    // Step 11: Verify audit trail shows complete workflow
    // Check for audit timeline or events section
    await expect(page.locator('text=CASE_CREATED')).toBeVisible();
    await expect(page.locator('text=CASE_NOTE_ADDED')).toBeVisible();
    await expect(page.locator('text=INFORMATION_REQUESTED')).toBeVisible();
    await expect(page.locator('text=INFORMATION_RESPONSE_RECORDED')).toBeVisible();
    await expect(page.locator('text=CASE_DECISION')).toBeVisible();
    
    // Verify decision was made by officer (check actor)
    const decisionEvent = page.locator('text=CASE_DECISION').locator('..');
    await expect(decisionEvent.locator('text=/officer@demo.com|Test Officer/i')).toBeVisible();
  });

  // TODO: Requires case creation UI and decision controls not yet implemented
  test.skip('should enforce separation of duties - creator cannot decide', async ({ page }) => {
    // Login as analyst
    await page.goto('/login');
    await page.fill('#email', 'analyst@example.com');
    await page.fill('#password', 'Analyst-pass-1');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/);
    
    // Create transaction and alert
    await page.click('a[href="/transactions"]');
    await page.click('text=Submit Transaction');
    
    await page.fill('#amt', '160000.00');
    await page.selectOption('#type', 'TRANSFER');
    await page.fill('#acc', 'ACC-DEMO-001');
    await page.fill('#orig', 'US');
    await page.fill('#dest', 'CN');
    await page.fill('#ref', `TXN-SEP-${Date.now()}`);
    
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Transaction submitted successfully')).toBeVisible({ timeout: 10000 });
    
    // Create case
    const alertLink = page.locator('a[href^="/alerts/"]').first();
    await alertLink.click();
    await page.click('button:has-text("Create Case")');
    await page.fill('input[name="title"]', 'Separation of Duties Test Case');
    await page.click('button:has-text("Create Case")');
    await page.waitForURL(/\/cases\/.+/);
    
    // Try to make decision as creator (should be blocked)
    const approveButton = page.locator('button:has-text("Approve")');
    const rejectButton = page.locator('button:has-text("Reject")');
    
    // Either buttons are disabled or permission notice is shown
    const approveCount = await approveButton.count();
    const rejectCount = await rejectButton.count();
    
    if (approveCount > 0) {
      expect(await approveButton.isDisabled()).toBe(true);
    }
    if (rejectCount > 0) {
      expect(await rejectButton.isDisabled()).toBe(true);
    }
    if (approveCount === 0 && rejectCount === 0) {
      await expect(page.locator('text=/cannot.*decide.*own.*case|creator.*cannot.*approve/i')).toBeVisible();
    }
  });

  // TODO: Requires case creation UI, information request forms, and decision blocking logic not yet implemented
  test.skip('should block decision when information request is open', async ({ page }) => {
    // Login as analyst
    await page.goto('/login');
    await page.fill('#email', 'analyst@demo.com');
    await page.fill('#password', 'Analyst-pass-1');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/);
    
    // Create case with open information request
    await page.click('a[href="/transactions"]');
    await page.click('text=Submit Transaction');
    
    await page.fill('#amt', '190000.00');
    await page.selectOption('#type', 'TRANSFER');
    await page.fill('#acc', 'ACC-DEMO-001');
    await page.fill('#orig', 'US');
    await page.fill('#dest', 'RU');
    await page.fill('#ref', `TXN-BLOCK-${Date.now()}`);
    
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Transaction submitted successfully')).toBeVisible({ timeout: 10000 });
    
    const alertLink = page.locator('a[href^="/alerts/"]').first();
    await alertLink.click();
    await page.click('button:has-text("Create Case")');
    await page.fill('input[name="title"]', 'Case with Open Information Request');
    await page.click('button:has-text("Create Case")');
    await page.waitForURL(/\/cases\/.+/);
    
    // Request information
    await page.click('button:has-text("Request Information")');
    await page.fill('input[name="requested_what"]', 'Customer verification documents');
    await page.fill('textarea[name="reason"]', 'Need additional verification');
    
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 3);
    await page.fill('input[name="due_date"]', futureDate.toISOString().split('T')[0]);
    
    await page.click('button:has-text("Submit Request")');
    
    // Logout and login as officer
    await page.click('button:has-text("Logout")');
    await page.waitForURL(/\/login/);
    
    await page.fill('#email', 'officer@demo.com');
    await page.fill('#password', 'Officer-pass-1');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/);
    
    // Navigate to the case
    await page.click('a[href="/cases"]');
    await page.click('text=Case with Open Information Request');
    await page.waitForURL(/\/cases\/.+/);
    
    // Verify decision buttons are disabled due to open request
    const approveButton = page.locator('button:has-text("Approve")');
    const rejectButton = page.locator('button:has-text("Reject")');
    
    const approveCount = await approveButton.count();
    const rejectCount = await rejectButton.count();
    
    if (approveCount > 0) {
      expect(await approveButton.isDisabled()).toBe(true);
    }
    if (rejectCount > 0) {
      expect(await rejectButton.isDisabled()).toBe(true);
    }
    if (approveCount === 0 && rejectCount === 0) {
      await expect(page.locator('text=/open.*information.*request|pending.*request/i')).toBeVisible();
    }
  });

  // TODO: Requires case UI and escalation controls not yet implemented
  test.skip('should support case escalation workflow', async ({ page }) => {
    // Login as officer
    await page.goto('/login');
    await page.fill('#email', 'officer@demo.com');
    await page.fill('#password', 'Officer-pass-1');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/);
    
    // Navigate to an existing case (use seed data case)
    await page.click('a[href="/cases"]');
    await page.waitForURL(/\/cases/);
    
    // Click on first available case in PENDING_DECISION state
    const caseLinks = page.locator('a[href^="/cases/"]');
    await caseLinks.first().click();
    await page.waitForURL(/\/cases\/.+/);
    
    // Click escalate button if available and enabled
    const escalateButton = page.locator('button:has-text("Escalate")');
    const escalateCount = await escalateButton.count();
    
    if (escalateCount > 0) {
      const isDisabled = await escalateButton.isDisabled();
      if (!isDisabled) {
        await escalateButton.click();
        
        // Fill escalation form
        await page.fill('textarea[name="reason"]', 'Complex case requiring senior management review');
        await page.fill('textarea[name="comments"]', 'High-value transaction with unusual pattern. Recommending escalation to compliance manager.');
        
        await page.click('button:has-text("Confirm Escalation")');
        
        // Verify case state updated
        await expect(page.locator('text=ESCALATED')).toBeVisible({ timeout: 5000 });
        
        // Verify audit trail
        await expect(page.locator('text=CASE_DECISION')).toBeVisible();
      }
    }
  });

  // TODO: Requires case UI and assignment controls not yet implemented
  test.skip('should show case assignment and reassignment', async ({ page }) => {
    // Login as manager or officer with assignment permissions
    await page.goto('/login');
    await page.fill('#email', 'officer@example.com');
    await page.fill('#password', 'Officer-pass-1');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/);
    
    // Navigate to cases
    await page.click('a[href="/cases"]');
    await page.waitForURL(/\/cases/);
    
    // Click on a case
    const caseLinks = page.locator('a[href^="/cases/"]');
    await caseLinks.first().click();
    await page.waitForURL(/\/cases\/.+/);
    
    // Look for assign/reassign button
    const assignButton = page.locator('button:has-text("Assign")');
    const assignCount = await assignButton.count();
    
    if (assignCount > 0) {
      await assignButton.click();
      
      // Select assignee from dropdown
      await page.selectOption('select[name="assigned_to_user_id"]', { index: 1 });
      await page.click('button:has-text("Confirm Assignment")');
      
      // Verify assignment updated
      await expect(page.locator('text=Assigned to')).toBeVisible();
      
      // Verify audit trail shows assignment
      await expect(page.locator('text=CASE_ASSIGNED')).toBeVisible();
    }
  });
});
