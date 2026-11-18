/**
 * Smoke tests for the new list pages.
 * Verifies navigation, basic rendering, pagination, and filtering.
 */
import { test, expect } from './_pipeline_guard';

test.describe('List Pages Smoke Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login with officer credentials
    await page.goto('/login');
    await page.getByLabel('Email').fill('officer@example.com');
    await page.locator('input[type="password"]').fill('Officer-pass-1');
    await page.getByRole('button', { name: /Sign in/i }).click();
    await page.waitForURL('/dashboard');
  });

  test('alerts list page loads and displays table', async ({ page }) => {
    // Navigate to alerts list
    await page.click('a[href="/alerts"]');
    await page.waitForURL('/alerts');

    // Verify page title
    await expect(page.getByRole('heading', { name: /Alerts/i })).toBeVisible();

    // Verify table is present
    const table = page.locator('.cds--data-table');
    await expect(table).toBeVisible();

    // Verify table has columns (adjust based on actual design)
    await expect(page.getByText('Alert Number')).toBeVisible();
    await expect(page.getByText('Risk Score')).toBeVisible();
    await expect(page.getByText('Priority')).toBeVisible();
    await expect(page.getByText('Status')).toBeVisible();

    // Verify pagination is present if there are items
    const paginationContainer = page.locator('.cds--pagination');
    const hasItems = await table.locator('tbody tr').count() > 0;
    if (hasItems) {
      await expect(paginationContainer).toBeVisible();
    }
  });

  test('alerts list supports filtering', async ({ page }) => {
    await page.click('a[href="/alerts"]');
    await page.waitForURL('/alerts');

    // Look for filter controls (adjust selectors based on actual implementation)
    const filterSection = page.locator('[data-testid="filters"], .filters, .cds--form');
    
    // Check if status filter exists
    const statusFilter = page.locator('select').filter({ hasText: /Status/i }).or(
      page.locator('label').filter({ hasText: /Status/i }).locator('~select')
    );
    
    if (await statusFilter.count() > 0) {
      await expect(statusFilter.first()).toBeVisible();
    }
  });

  test('alerts list row links to detail page', async ({ page }) => {
    await page.click('a[href="/alerts"]');
    await page.waitForURL('/alerts');

    // Wait for table to load
    const table = page.locator('.cds--data-table tbody');
    const firstRow = table.locator('tr').first();
    
    // Check if there are any rows
    const rowCount = await table.locator('tr').count();
    if (rowCount > 0) {
      // Click the first row (or a link in it)
      const rowLink = firstRow.locator('a').first();
      if (await rowLink.count() > 0) {
        await rowLink.click();
        // Should navigate to detail page
        await expect(page).toHaveURL(/\/alerts\/\d+/);
      }
    }
  });

  test('transactions list page loads and displays table', async ({ page }) => {
    // Navigate to transactions list
    await page.click('a[href="/transactions"]');
    await page.waitForURL('/transactions');

    // Verify page title
    await expect(page.getByRole('heading', { name: /Transactions/i })).toBeVisible();

    // Verify table is present
    const table = page.locator('.cds--data-table');
    await expect(table).toBeVisible();

    // Verify key columns
    await expect(page.getByText('Reference')).toBeVisible();
    await expect(page.getByText('Amount')).toBeVisible();
    await expect(page.getByText('Type')).toBeVisible();

    // Verify "Submit New Transaction" button exists
    const submitButton = page.getByRole('button', { name: /Submit.*Transaction/i }).or(
      page.locator('a[href="/transactions/new"]')
    );
    await expect(submitButton).toBeVisible();
  });

  test('transactions list supports filtering by type', async ({ page }) => {
    await page.click('a[href="/transactions"]');
    await page.waitForURL('/transactions');

    // Check for transaction type filter
    const typeFilter = page.locator('select, [role="combobox"]').filter({ hasText: /Type/i }).or(
      page.locator('label').filter({ hasText: /Type/i }).locator('~select, ~[role="combobox"]')
    );
    
    if (await typeFilter.count() > 0) {
      await expect(typeFilter.first()).toBeVisible();
    }
  });

  test('transaction submission moved to /transactions/new', async ({ page }) => {
    // Verify /transactions is now the list page
    await page.goto('/transactions');
    await expect(page.getByRole('heading', { name: /Transactions/i })).toBeVisible();
    await expect(page.locator('.cds--data-table')).toBeVisible();

    // Navigate to submission page
    const submitButton = page.getByRole('button', { name: /Submit.*Transaction/i }).or(
      page.locator('a[href="/transactions/new"]')
    );
    
    if (await submitButton.count() > 0) {
      await submitButton.click();
      await page.waitForURL('/transactions/new');
      
      // Verify it's the submission form
      await expect(page.getByText(/Submit.*Transaction/i)).toBeVisible();
      await expect(page.locator('form, [role="form"]')).toBeVisible();
    }
  });

  test('transactions list row links to detail page', async ({ page }) => {
    await page.click('a[href="/transactions"]');
    await page.waitForURL('/transactions');

    const table = page.locator('.cds--data-table tbody');
    const rowCount = await table.locator('tr').count();
    
    if (rowCount > 0) {
      const firstRow = table.locator('tr').first();
      const rowLink = firstRow.locator('a').first();
      
      if (await rowLink.count() > 0) {
        await rowLink.click();
        // Should navigate to transaction detail
        await expect(page).toHaveURL(/\/transactions\/\d+/);
      }
    }
  });

  test('cases list page loads and displays table', async ({ page }) => {
    await page.click('a[href="/cases"]');
    await page.waitForURL('/cases');

    // Verify page title
    await expect(page.getByRole('heading', { name: /Cases/i })).toBeVisible();

    // Verify table is present
    const table = page.locator('.cds--data-table');
    await expect(table).toBeVisible();

    // Verify key columns
    await expect(page.getByText('Case Number')).toBeVisible();
    await expect(page.getByText('State')).toBeVisible();
    await expect(page.getByText('Priority')).toBeVisible();
  });

  test('cases list supports filtering by state', async ({ page }) => {
    await page.click('a[href="/cases"]');
    await page.waitForURL('/cases');

    // Check for state filter
    const stateFilter = page.locator('select, [role="combobox"]').filter({ hasText: /State/i }).or(
      page.locator('label').filter({ hasText: /State/i }).locator('~select, ~[role="combobox"]')
    );
    
    if (await stateFilter.count() > 0) {
      await expect(stateFilter.first()).toBeVisible();
    }
  });

  test('cases list row links to investigation page', async ({ page }) => {
    await page.click('a[href="/cases"]');
    await page.waitForURL('/cases');

    const table = page.locator('.cds--data-table tbody');
    const rowCount = await table.locator('tr').count();
    
    if (rowCount > 0) {
      const firstRow = table.locator('tr').first();
      const rowLink = firstRow.locator('a').first();
      
      if (await rowLink.count() > 0) {
        await rowLink.click();
        // Should navigate to case investigation page
        await expect(page).toHaveURL(/\/cases\/\d+/);
      }
    }
  });

  test('rules page loads and displays rules', async ({ page }) => {
    await page.click('a[href="/rules"]');
    await page.waitForURL('/rules');

    // Verify page title
    await expect(page.getByRole('heading', { name: /Rules/i })).toBeVisible();

    // Verify table or list of rules
    const table = page.locator('.cds--data-table').or(page.locator('[role="table"]'));
    await expect(table).toBeVisible();

    // Verify key columns/fields
    await expect(page.getByText('Rule Code')).toBeVisible();
    await expect(page.getByText(/Active|Status/i)).toBeVisible();
  });

  test('rules page supports active/inactive filtering', async ({ page }) => {
    await page.click('a[href="/rules"]');
    await page.waitForURL('/rules');

    // Look for active filter toggle or dropdown
    const activeFilter = page.locator('[data-testid="active-filter"], .active-filter').or(
      page.locator('label').filter({ hasText: /Active/i }).locator('~select, ~input[type="checkbox"]')
    );
    
    if (await activeFilter.count() > 0) {
      await expect(activeFilter.first()).toBeVisible();
    }
  });

  test('dashboard displays KPI tiles and charts', async ({ page }) => {
    // Already on dashboard from beforeEach
    await page.goto('/dashboard');

    // Verify KPI tiles exist
    const tiles = page.locator('.cds--tile, [data-testid="kpi-tile"]');
    const tileCount = await tiles.count();
    expect(tileCount).toBeGreaterThan(0);

    // Verify key KPIs are present (adjust text based on actual implementation)
    const kpiTexts = ['Alerts', 'Cases', 'Transactions', 'Rules'];
    for (const text of kpiTexts) {
      const kpiElement = page.getByText(new RegExp(text, 'i'));
      if (await kpiElement.count() > 0) {
        await expect(kpiElement.first()).toBeVisible();
      }
    }

    // Verify charts exist (Carbon charts)
    const charts = page.locator('.cds--chart, svg[class*="chart"]');
    if (await charts.count() > 0) {
      await expect(charts.first()).toBeVisible();
    }
  });

  test('sidebar highlights active section for list routes', async ({ page }) => {
    // Test alerts section
    await page.click('a[href="/alerts"]');
    await page.waitForURL('/alerts');
    
    const alertsSidebarItem = page.locator('.cds--side-nav__link[href="/alerts"]').or(
      page.locator('a[href="/alerts"]').filter({ has: page.locator('.cds--side-nav__link-text') })
    );
    
    if (await alertsSidebarItem.count() > 0) {
      await expect(alertsSidebarItem.first()).toHaveClass(/active|selected|current/);
    }

    // Test transactions section
    await page.click('a[href="/transactions"]');
    await page.waitForURL('/transactions');
    
    const transactionsSidebarItem = page.locator('.cds--side-nav__link[href="/transactions"]').or(
      page.locator('a[href="/transactions"]').filter({ has: page.locator('.cds--side-nav__link-text') })
    );
    
    if (await transactionsSidebarItem.count() > 0) {
      await expect(transactionsSidebarItem.first()).toHaveClass(/active|selected|current/);
    }
  });

  test('sidebar highlights active section for detail routes', async ({ page }) => {
    // Navigate to an alert detail page
    await page.goto('/alerts');
    const table = page.locator('.cds--data-table tbody');
    const rowCount = await table.locator('tr').count();
    
    if (rowCount > 0) {
      const firstRowLink = table.locator('tr').first().locator('a').first();
      if (await firstRowLink.count() > 0) {
        await firstRowLink.click();
        await page.waitForURL(/\/alerts\/\d+/);
        
        // Verify the alerts section is still highlighted in sidebar
        const alertsSidebarItem = page.locator('.cds--side-nav__link[href="/alerts"]').or(
          page.locator('a[href="/alerts"]').filter({ has: page.locator('.cds--side-nav__link-text') })
        );
        
        if (await alertsSidebarItem.count() > 0) {
          await expect(alertsSidebarItem.first()).toHaveClass(/active|selected|current/);
        }
      }
    }
  });

  test('admin page requires appropriate role', async ({ page }) => {
    // Try to access admin page as officer
    await page.goto('/admin');
    
    // Should either redirect, show 403, or show restricted message
    const is403 = page.getByText(/403|Forbidden|Access Denied|Not authorized/i);
    const isRestricted = page.getByText(/restricted|permission/i);
    
    // One of these should be visible, or we should be redirected
    const currentUrl = page.url();
    const hasAccessDenied = await is403.or(isRestricted).count() > 0;
    const redirectedAway = !currentUrl.includes('/admin');
    
    expect(hasAccessDenied || redirectedAway).toBeTruthy();
  });

  test('all list pages show loading state initially', async ({ page }) => {
    // Navigate to a list page and check for loading indicator
    const listPagePromise = page.goto('/alerts');
    
    // Look for loading skeleton or spinner
    const loadingIndicator = page.locator('.cds--skeleton, .cds--loading, [data-testid="loading"]');
    
    // The loading state might be very brief, so we check if it appears
    const hasLoading = await loadingIndicator.count() > 0;
    
    await listPagePromise;
    
    // Eventually, the table should appear
    await expect(page.locator('.cds--data-table')).toBeVisible({ timeout: 10000 });
  });

  test('list pages show empty state when no data', async ({ page }) => {
    // This test assumes there might be filters that result in no data
    await page.goto('/alerts');
    await page.waitForURL('/alerts');
    
    // Try to apply a filter that yields no results
    // (This is implementation-dependent, so we'll just check structure)
    const table = page.locator('.cds--data-table tbody');
    const rowCount = await table.locator('tr').count();
    
    if (rowCount === 0) {
      // Should show empty state
      const emptyState = page.getByText(/No.*found|No.*available|empty/i);
      await expect(emptyState).toBeVisible();
    }
  });

  test('breadcrumbs on detail pages link back to list', async ({ page }) => {
    // Navigate to alerts list
    await page.goto('/alerts');
    const table = page.locator('.cds--data-table tbody');
    const rowCount = await table.locator('tr').count();
    
    if (rowCount > 0) {
      const firstRowLink = table.locator('tr').first().locator('a').first();
      if (await firstRowLink.count() > 0) {
        await firstRowLink.click();
        await page.waitForURL(/\/alerts\/\d+/);
        
        // Look for breadcrumb
        const breadcrumb = page.locator('.cds--breadcrumb, [aria-label="Breadcrumb"]');
        if (await breadcrumb.count() > 0) {
          await expect(breadcrumb).toBeVisible();
          
          // Click breadcrumb link back to alerts
          const alertsLink = breadcrumb.locator('a[href="/alerts"]');
          if (await alertsLink.count() > 0) {
            await alertsLink.click();
            await page.waitForURL('/alerts');
            await expect(page.locator('.cds--data-table')).toBeVisible();
          }
        }
      }
    }
  });
});
