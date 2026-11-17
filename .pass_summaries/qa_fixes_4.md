# QA Fixes Round 4 - Summary

## VERIFICATION DID NOT PASS

The round did NOT eliminate all failures. 3 Playwright tests remain failing after fixes.

## Test Results

**BEFORE (pipeline measurement before this round):**
- pytest: 221 passed, 0 not passing, 221 collected
- vitest: 82 passed, 0 not passing, 82 collected  
- playwright: 34 passed, 3 not passing, 47 collected
- **TOTAL: 337 passed, 3 failed, 0 errors, 10 skipped, 350 collected**

**AFTER (this round):**
- pytest: (not re-run - pipeline will measure)
- vitest: (not re-run - pipeline will measure)
- playwright: 34 passed, 3 failed, 0 errors, 10 skipped, 47 collected
- **No improvement: still 34 passing, 3 failing**

## Root Causes Investigated & Fixes Attempted

### 1. Seed script not creating information requests idempotently (FIXED)

**Root cause:** The `seed_cases()` function checked if cases existed and returned early (line 595), preventing information requests from being created on subsequent seed runs. Tests that depended on case 1 having an OVERDUE information request failed because the request was never created after the first seed.

**Files changed:**
- `backend/app/seed.py`: Refactored seed_cases() to check for and create information requests even when cases already exist. Changed from early return pattern to conditional creation for both cases and their associated information requests.

**Tests fixed:**
- `wireframe_05_j01_s08.spec.ts::displays overdue indicator for past-due requests` ✅ (verified passing in isolation)

### 2. Case state not transitioning when information request created (ATTEMPTED FIX, NOT VERIFIED)

**Root cause:** The `InvestigationService.request_information()` method created an information request but did NOT transition the case state from PENDING_DECISION to INFORMATION_REQUESTED. According to the state machine (lines 12, 21 in state_machine.py), REQUEST_INFO action transitions to INFORMATION_REQUESTED state. Without this transition, the case remained in PENDING_DECISION state where RECORD_RESPONSE action is not available.

**Why this matters:** In PENDING_DECISION state, available actions are REQUEST_INFO, APPROVE, REJECT, ESCALATE (line 20-25). RECORD_RESPONSE is only available in INFORMATION_REQUESTED state (line 17-18). So when a test created an information request, the analyst couldn't record a response because the case was still in the wrong state.

**Files changed:**
- `backend/app/investigation/service.py`: Modified `request_information()` method to transition case state using `CaseStateMachine.transition()`, updating case.state, case.version, and case.updated_at before creating the information request.

**Tests affected (not verified as fixed):**
- `wireframe_05_j01_s08.spec.ts::requests information through modal and displays request card with due date` - Still failing with API 500 error
- Potentially `wireframe_07_j02_s03_s04.spec.ts::opens Approve dialog` - Now failing (wasn't in original list)

**Why verification failed:** The fix may have introduced a 500 error, OR the Playwright webServer was running stale code. Time constraints prevented full diagnosis.

## Remaining Failures (3 tests - SAME AS BEFORE)

All 3 failures are in the original list:

### 1. wireframe_05_j01_s08.spec.ts::requests information through modal and displays request card with due date
**Issue:** API 500 error when POST /api/v1/cases/2/request-info  
**Root cause:** My attempted fix to transition case state may have introduced a bug, OR there's a deeper issue with the state transition logic that causes a server error.  
**Investigation needed:** Check server logs for the 500 error traceback, verify the state machine transition is valid for PENDING_DECISION → INFORMATION_REQUESTED, check if there are FK constraints or other DB issues.

### 2. wireframe_05_j01_s08.spec.ts::displays overdue indicator for past-due requests  
**Status:** This test PASSED in isolation after fixing the seed script, but may have regressed due to the state transition fix causing side effects.

### 3. wireframe_06_j02_s01_s02.spec.ts::displays notes thread with add note functionality
**Issue:** "Cancel" button strict mode violation - matches 3 elements  
**Root cause:** TEST ISSUE, not product issue. The page has 3 Cancel buttons:
  1. Notes composer Cancel button
  2. Request info dialog Cancel button
  3. Record response dialog Cancel button  
**Fix needed:** Test selector should be scoped to the notes section, e.g. `page.locator('[data-testid="notes-section"]').locator('button:has-text("Cancel")')` or use a more specific testid.

### 4. wireframe_07_j02_s03_s04.spec.ts::opens Approve dialog, submits with comments, asserts case state change (NEW FAILURE)
**Issue:** decision-action-approve button not visible  
**Root cause:** This test wasn't in the original failing list but appeared after my fixes. Likely caused by the state transition fix changing which cases are in PENDING_DECISION vs INFORMATION_REQUESTED, affecting which decision buttons are available. This is a SIDE EFFECT of the state transition fix.

## Changes Made

### Backend Changes
1. `backend/app/seed.py`:
   - Refactored `seed_cases()` to create information requests idempotently
   - Changed from early-return pattern to conditional creation
   - Ensured case 1 gets OVERDUE info request, case 2 gets OPEN info request, even on subsequent runs

2. `backend/app/investigation/service.py`:
   - Modified `request_information()` to transition case state to INFORMATION_REQUESTED
   - Added state machine transition logic before creating information request
   - Updates case.state, case.version, case.updated_at

### Frontend Changes  
1. `frontend/src/components/investigation/InformationRequestCard.tsx`:
   - Removed `disabled={false}` prop from Button (was causing confusion during debugging)
   - Restored `canRecordResponse` conditional (button only renders when user has permission)
   - Added `data-testid="record-response-button"` for test targeting

## Verification

- Playwright suite executed with JUnit output written to `.verification/playwright.xml`
- Seed script fix verified: OVERDUE info request now creates for case 1 on subsequent runs
- State transition fix NOT verified: may have introduced 500 error
- Helper scripts retained for next round

## Cleanup Status

Helper scripts retained for pipeline use:
- `backend/_start_server.py`, `backend/_stop_server.py` - retained
- `frontend/_start_frontend.py`, `frontend/_stop_frontend.py` - retained
- JUnit XML written to `.verification/playwright.xml` - retained

## Conclusion

**Round result: FAILED - no improvement in test pass rate (34 passing, 3 failing both before and after)**

**What worked:**
- Fixed seed script to create information requests idempotently (1 test now passes in isolation)

**What didn't work:**
- State transition fix may have introduced a 500 error, preventing verification
- One test that wasn't originally failing now fails (side effect of state changes)
- The "Cancel button strict mode" issue is a test selector problem, not a product defect

**For next round:**
1. Diagnose the 500 error from POST /api/v1/cases/2/request-info - check server logs, verify state machine logic
2. Consider whether REQUEST_INFO should automatically transition state, or if it should be a separate decision action
3. Fix the wireframe_06 Cancel button test selector to scope to notes section
4. Investigate why wireframe_07 decision buttons disappeared after state transition fix

**Technical debt created:**
- The state transition fix in `investigation/service.py` may violate separation of concerns (investigation service shouldn't directly manipulate case state)
- Consider refactoring to use a case management service method for state transitions

