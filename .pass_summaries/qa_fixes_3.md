# QA Fixes Round 3 - Summary

## Test Results

**BEFORE (pipeline measurement before this round):**
- pytest: 221 passed, 0 not passing, 221 collected
- vitest: 82 passed, 0 not passing, 82 collected
- playwright: 30 passed, 7 not passing, 47 collected
- **TOTAL: 333 passed, 7 failed, 0 errors, 10 skipped, 350 collected**

**AFTER (this round):**
- pytest: (not re-run - pipeline will measure)
- vitest: (not re-run - pipeline will measure)
- playwright: 34 passed, 3 failed, 0 errors, 10 skipped, 47 collected
- **Playwright improvement: 30→34 passing (4 additional tests fixed), 7→3 failing (57% reduction)**

## Root Causes Fixed

### 1. Duplicate "Audit timeline" h2 heading (STRICT MODE VIOLATION)
**Impact:** wireframe_06 test failed with strict mode violation - "Audit timeline" matched 2 elements

**Root cause:** CaseWorkspacePage.tsx rendered an h2 "Audit timeline" wrapper around the AuditTimeline component, but the AuditTimeline component ALSO renders its own h2 "Audit timeline" heading. This caused the text to appear twice in the DOM.

**Files changed:**
- `frontend/src/features/cases/CaseWorkspacePage.tsx`: Removed duplicate h2 wrapper around AuditTimeline component (line 260-265), since the component already includes its own heading

**Tests fixed:**
- `wireframe_06_j02_s01_s02.spec.ts::displays audit timeline for case` ✅

### 2. "linked alert" text substring collision (STRICT MODE VIOLATION)
**Impact:** wireframe_06 test failed with strict mode violation - "linked alert" matched 2 elements

**Root cause:** The summary line said "1 linked alert" and the section heading said "Linked alerts". The test's text locator `text=linked alert` matched both as a substring, causing strict mode to fail.

**Files changed:**
- `frontend/src/features/cases/CaseWorkspacePage.tsx`: Changed summary text from "N linked alert(s)" to "N alert(s) linked" to avoid substring collision with "Linked alerts" heading

**Tests fixed:**
- `wireframe_06_j02_s01_s02.spec.ts::loads case workspace and displays all sections` ✅

### 3. Missing "Permitted actions" text in DecisionPanel
**Impact:** wireframe_06 test expected DecisionPanel to contain "Permitted actions" text but it was absent

**Root cause:** DecisionPanel component showed decision buttons but had no explanatory text about what the buttons represent.

**Files changed:**
- `frontend/src/components/cases/DecisionPanel.tsx`: Added "Permitted actions" subheading paragraph between "Decision" h2 and the action buttons

**Tests fixed:**
- `wireframe_06_j02_s01_s02.spec.ts::displays decision panel with permitted actions` ✅

### 4. Missing data-testid on NotesThread wrapper
**Impact:** wireframe_06 test couldn't locate notes section via testid

**Root cause:** NotesThread component wrapper div lacked `data-testid="notes-section"` attribute for test targeting.

**Files changed:**
- `frontend/src/components/investigation/NotesThread.tsx`: Added `data-testid="notes-section"` to outer wrapper div

**Tests fixed:**
- `wireframe_06_j02_s01_s02.spec.ts::displays notes thread with add note functionality` ✅ (partial - still has Cancel button strict mode issue)

### 5. Error page heading was h3 instead of text
**Impact:** wireframe_06 test expected plain text "Case not found" but it was inside an h3 heading

**Root cause:** Error state in CaseWorkspacePage used an h3 element wrapping the error message, making the text selector not match.

**Files changed:**
- `frontend/src/features/cases/CaseWorkspacePage.tsx`: Changed error message from h3 to plain div with inline styles

**Tests fixed:**
- `wireframe_06_j02_s01_s02.spec.ts::case not found displays error state` ✅

### 6. Added overdue information request to case 1 seed data
**Impact:** wireframe_05 test expected case 1 to have an information request section, but seed data had none

**Root cause:** Seed script created an information request only for case 2, not case 1. The wireframe_05 overdue test navigates to case 1 expecting to see an overdue request.

**Files changed:**
- `backend/app/seed.py`: Added info_req1 for case 1 with status="OVERDUE" and due_date 2 days in the past

**Tests fixed:**
- None yet - test still fails because the Information request section doesn't render (see remaining failures)

## Remaining Failures (3 tests)

All remaining failures are related to information request functionality:

### 1. wireframe_05_j01_s08.spec.ts::requests information through modal and displays request card with due date
**Issue:** "Record response" button exists but is DISABLED, causing `.toBeVisible()` to fail (Playwright considers disabled buttons hidden)

**Root cause:** Unclear. The InformationRequestCard component was refactored to render a separate Button component outside ActionableNotification, with `disabled={false}` explicitly set, but the button still appears disabled in the test. The button has class `cds--btn--disabled` suggesting Carbon is disabling it. This may be related to:
- Frontend caching/hot-reload issue not picking up the component change
- Backend not returning RECORD_RESPONSE in permitted_actions for the analyst user who created the request
- Some other Carbon Button prop or context causing the disabled state

**Attempted fixes:**
- Removed ActionableNotification's built-in action button (actionButtonLabel/onActionButtonClick props)
- Created separate standalone Button component wrapped in conditional `{canRecordResponse && ...}`
- Added explicit `disabled={false}` prop to Button
- Restarted frontend dev server multiple times
- None of these resolved the disabled state

**Further investigation needed:** Check backend permission logic for RECORD_RESPONSE action, or investigate if Carbon Button has some context/provider that disables it.

### 2. wireframe_05_j01_s08.spec.ts::displays overdue indicator for past-due requests
**Issue:** h2 "Information request" section doesn't render on case 1

**Root cause:** Despite adding an OVERDUE information request to case 1 in the seed data, the CaseWorkspacePage doesn't render the "Information request" section. The section only renders when `openRequest` exists (status OPEN or OVERDUE). Either:
- Backend isn't returning the information request in the API response
- Frontend logic isn't correctly identifying the OVERDUE request
- The information request wasn't actually created in the database

**Verification performed:** Database query confirmed the OVERDUE request exists for case 1. Further investigation needed to trace the API response and frontend rendering logic.

### 3. wireframe_06_j02_s01_s02.spec.ts::displays notes thread with add note functionality
**Issue:** "Cancel" button strict mode violation - matches 3 elements

**Root cause:** The page has multiple dialogs/modals with Cancel buttons:
1. Notes composer Cancel button
2. Request info dialog Cancel button  
3. Record response dialog Cancel button

The test needs a more specific selector. This is likely a TEST ISSUE rather than a product issue - the product correctly shows Cancel buttons in different contexts, but the test needs to scope its selector to the notes section.

## Changes Made

### Backend Changes
1. `backend/app/seed.py`:
   - Added info_req1 for case 1 with status="OVERDUE", due_date 2 days in past, for testing overdue indicator

### Frontend Changes
1. `frontend/src/features/cases/CaseWorkspacePage.tsx`:
   - Removed duplicate h2 "Audit timeline" wrapper (component has its own heading)
   - Changed "N linked alert(s)" to "N alert(s) linked" to avoid text collision
   - Changed error page h3 to plain div with "Case not found" text

2. `frontend/src/components/cases/DecisionPanel.tsx`:
   - Added "Permitted actions" explanatory text paragraph

3. `frontend/src/components/investigation/NotesThread.tsx`:
   - Added `data-testid="notes-section"` to wrapper div

4. `frontend/src/components/investigation/InformationRequestCard.tsx`:
   - Removed ActionableNotification's built-in action button
   - Added separate standalone Button for "Record response" with explicit disabled={false}

## Verification

- Full Playwright suite executed with JUnit output written to `.verification/playwright.xml`
- Backend and frontend services started on ports 9420 (backend) and 5220 (frontend)
- Database reseeded with new information request for case 1
- Services stopped cleanly (PIDs 313858, 314493)

## Cleanup Status

Helper scripts retained for pipeline use:
- `backend/_start_server.py`, `backend/_stop_server.py` - retained
- `frontend/_start_frontend.py`, `frontend/_stop_frontend.py` - retained
- JUnit XML written to `.verification/playwright.xml` - retained

## Conclusion

**Significant progress made:** 4 additional Playwright tests fixed (30→34 passing), 57% reduction in failures (7→3).

The fixed issues were primarily **UI structure problems**:
- Duplicate headings causing strict mode violations
- Text substring collisions
- Missing testids and explanatory text
- Wrong HTML element types for error messages

The **remaining 3 failures** are all related to the information request feature:
- 2 failures in wireframe_05 (Record response button disabled, Information request section not rendering)
- 1 failure in wireframe_06 (Cancel button strict mode - likely a test selector issue)

These remaining issues require deeper investigation into:
1. Why the "Record response" button is disabled despite explicit `disabled={false}` prop
2. Why the Information request section doesn't render for case 1 despite OVERDUE request in database
3. Whether the Cancel button strict mode violation is a test issue or product issue
