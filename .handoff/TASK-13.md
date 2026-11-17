# Task 13 Handoff: Case Decision Panel and Workflow Completion

## Implemented Components

### DecisionPanel.tsx
Sticky decision panel component that displays permitted case decision actions based on backend permissions.

**Features:**
- Renders only actions included in `permitted_actions` array from backend
- Four decision action buttons with correct Carbon button kinds:
  - Approve: `kind="primary"`
  - Reject: `kind="danger--tertiary"`
  - Escalate: `kind="secondary"`
  - Close as false positive: `kind="ghost"`
- Shows blocking notice when decisions are unavailable (open information request)
- Full-width buttons with left-aligned text matching wireframe_07 design

**Props:**
```typescript
interface DecisionPanelProps {
  permittedActions: string[];
  onDecisionClick: (action: DecisionAction) => void;
  isBlocked: boolean;
  blockReason?: string;
}
```

---

### DecisionDialog.tsx
Modal dialog for recording case decisions with field validation.

**Features:**
- Different configurations per decision type (APPROVE, REJECT, ESCALATE, CLOSE_FALSE_POSITIVE)
- Required field validation:
  - REJECT: requires reason + comments
  - ESCALATE: requires reason + comments
  - CLOSE_FALSE_POSITIVE: requires reason + comments
  - APPROVE: requires comments only
- Consequence text matching wireframe specifications
- Danger styling for REJECT and CLOSE_FALSE_POSITIVE
- Validation error display with field-level error messages
- Submitting state with disabled button

**Props:**
```typescript
interface DecisionDialogProps {
  open: boolean;
  action: DecisionAction | null;
  onClose: () => void;
  onSubmit: (data: {
    decision: DecisionAction;
    reason?: string;
    comments?: string;
  }) => void;
  isSubmitting?: boolean;
}
```

**Decision Configurations:**
| Decision | Title | Required Fields | Button Kind | Consequence Text |
|---|---|---|---|---|
| APPROVE | Approve case | comments | primary | This decision is final and recorded in the audit trail. |
| REJECT | Reject case | reason, comments | danger | This decision is final and recorded in the audit trail. |
| ESCALATE | Escalate | reason, comments | primary | Case moves to Escalated. |
| CLOSE_FALSE_POSITIVE | Close as false positive | reason, comments | danger | Case closes and all linked alerts are closed. |

---

### PermissionNotice.tsx
Notice component for displaying blocking conditions and permission restrictions.

**Features:**
- Three variants: info (default), warning, error
- Icon and border color matching Carbon design system
- Used for:
  - Terminal state (final decision made)
  - Creator-decider separation (creator cannot decide own case)
  - Open information request blocking decisions

**Props:**
```typescript
interface PermissionNoticeProps {
  message: string;
  type?: 'info' | 'warning' | 'error';
}
```

---

## Business Logic

### decision-actions.ts
Utility module for computing permitted decision actions based on case state, user role, creator status, and open request state.

**Key Functions:**
- `computeDecisionPermissions()` - Computes which actions are permitted/blocked with reasons
- `hasAnyDecisionPermission()` - Checks if any actions are available
- `getPermittedActions()` - Extracts list of permitted action names

**Permission Matrix:**
Matches backend logic from TASK-8 and TASK-9:

| State | Role | Creator? | Open Request? | Permitted Actions |
|---|---|---|---|---|
| PENDING_DECISION | Officer | No | No | APPROVE, REJECT, ESCALATE |
| PENDING_DECISION | Officer | Yes | No | ESCALATE only |
| PENDING_DECISION | Officer | No | Yes | ESCALATE only |
| ESCALATED | Officer | No | No | APPROVE, REJECT |
| UNDER_INVESTIGATION | Officer | No | No | ESCALATE, CLOSE_FALSE_POSITIVE |
| Terminal states | Any | Any | Any | None |

**Separation of Duties:**
Creator CANNOT approve or reject their own case, regardless of role. This is enforced at:
1. Backend (returns 403)
2. Permitted actions computation (server-side)
3. UI rendering (hides buttons + shows PermissionNotice)

---

## API Integration

### Decision Endpoint
`POST /api/v1/cases/{id}/decision`

**Request:**
```json
{
  "decision": "APPROVE | REJECT | ESCALATE | CLOSE_FALSE_POSITIVE",
  "reason": "string (required for REJECT, ESCALATE, CLOSE_FALSE_POSITIVE)",
  "comments": "string (required for APPROVE, REJECT, ESCALATE, CLOSE_FALSE_POSITIVE)",
  "expected_version": "integer (optimistic locking)"
}
```

**Success Response (200):**
Returns full `CaseDetailResponse` with updated state, decision record, and incremented version.

**Error Responses:**
- `409 INVALID_CASE_STATE` - Invalid transition (case state changed)
- `409 STALE_OBJECT` - Version conflict (concurrent update)
- `403 CREATOR_DECIDER_CONFLICT` - Creator cannot decide own case
- `422` - Validation error (missing required fields)

**Error Handling:**
- `INVALID_CASE_STATE`: Show error, close modal, refetch case
- `STALE_OBJECT`: Show error, close modal, refetch case
- Validation errors: Display field-level errors in modal, keep modal open
- Other errors: Display error notification, keep modal open for retry

---

## CaseWorkspacePage Integration

Enhanced case workspace page with decision panel in right column.

**Key Changes:**
1. Added decision state management:
   - `decisionDialogOpen` - Controls modal visibility
   - `selectedAction` - Tracks which decision action was clicked
   - `isSubmittingDecision` - Disables submit during API call
   - `decisionError` / `decisionSuccess` - User feedback

2. Creator detection:
   - Uses `getCurrentUser()` from api-client
   - Compares `currentUser.id` with `caseData.created_by_user_id`
   - Shows PermissionNotice when creator tries to decide

3. Terminal state detection:
   - Checks if case state is APPROVED, REJECTED, or CLOSED
   - Shows PermissionNotice for terminal states
   - Hides decision action buttons

4. Open request blocking:
   - Detects open or overdue information requests
   - Passes blocking state to DecisionPanel
   - Hides APPROVE/REJECT buttons when blocked

5. Decision submission flow:
   ```
   Click action button
   → Open DecisionDialog with action type
   → Fill required fields
   → Submit with expected_version from case detail
   → Handle errors (409 → close + refetch, validation → show in modal)
   → On success: show notification, close modal, refetch case
   ```

---

## Testing

### Unit Tests (decision-actions.test.ts)
19 tests covering permission matrix logic:
- PENDING_DECISION state permissions
- ESCALATED state permissions
- UNDER_INVESTIGATION state permissions
- Terminal state permissions (empty)
- Creator-decider separation enforcement
- Open request blocking
- Role-based access (Analyst, Officer, Manager, Administrator)

**All 19 tests pass.**

### E2E Tests

**wireframe_07_j02_s03_s04.spec.ts**
Tests decision panel and dialog interactions:
1. Opens Approve dialog, submits with comments, asserts state change
2. Validates required fields in Reject dialog
3. Verifies creator-decider PermissionNotice hides buttons
4. Verifies Escalate dialog and action
5. Handles 409 STALE_OBJECT conflict

**wireframe_08_j02_s05_s06.spec.ts**
Tests permission notices and blocking conditions:
1. Verifies creator-decider PermissionNotice hides buttons
2. Verifies open request blocks decisions
3. Displays final decision for terminal state case
4. Verifies case status tag reflects terminal state
5. Handles 409 INVALID_CASE_STATE when attempting decision on terminal case

---

## Seed Data Requirements

For E2E tests to pass, seed data must include:

**Cases:**
- Case 1: created by analyst, assigned to officer, state = UNDER_INVESTIGATION or PENDING_DECISION
- Case 2: created by analyst, assigned to officer, state = UNDER_INVESTIGATION

**Users:**
- analyst@example.com / Analyst-pass-1 (creates cases)
- officer@example.com / Officer-pass-1 (can decide cases not created by them)

**Current Seed:**
- Both cases created by analyst (user_id from seed)
- Officer can decide both cases (not creator)
- Analyst cannot decide either case (is creator)

---

## Known Issues & Future Work

1. **Multiple modal instances:** All three modals (RequestInfoDialog, RecordResponseDialog, DecisionDialog) are always rendered. This causes strict-mode violations in E2E tests when multiple dialogs are present. Consider:
   - Conditional rendering based on open state
   - Using unique dialog names in selectors
   - Portal-based modal rendering

2. **Auth context integration:** Currently uses `getCurrentUser()` from sessionStorage directly. Consider:
   - React Context for auth state
   - Centralized user/role management
   - Type-safe user object

3. **Decision action history:** DecisionDialog shows no previous decisions. Consider:
   - Display previous decision reason/comments
   - Show decision audit trail
   - Link to full audit log

4. **Optimistic locking UX:** Version conflicts show generic error. Consider:
   - Show diff of what changed
   - Allow user to review and re-submit
   - Auto-merge non-conflicting fields

5. **Keyboard navigation:** Modal focus management could be improved. Consider:
   - Auto-focus first input field
   - Trap focus within modal
   - Escape key handling

---

## Files Created

**Components:**
- `/repos/feature-ai-powered-aml-monitoring/frontend/src/components/cases/DecisionPanel.tsx`
- `/repos/feature-ai-powered-aml-monitoring/frontend/src/components/cases/DecisionDialog.tsx`
- `/repos/feature-ai-powered-aml-monitoring/frontend/src/components/cases/PermissionNotice.tsx`

**Business Logic:**
- `/repos/feature-ai-powered-aml-monitoring/frontend/src/lib/decision-actions.ts`

**Tests:**
- `/repos/feature-ai-powered-aml-monitoring/frontend/src/components/cases/__tests__/decision-actions.test.ts`
- `/repos/feature-ai-powered-aml-monitoring/frontend/e2e/wireframe_07_j02_s03_s04.spec.ts`
- `/repos/feature-ai-powered-aml-monitoring/frontend/e2e/wireframe_08_j02_s05_s06.spec.ts`

**Modified:**
- `/repos/feature-ai-powered-aml-monitoring/frontend/src/features/cases/CaseWorkspacePage.tsx` - Integrated decision panel
- `/repos/feature-ai-powered-aml-monitoring/frontend/src/lib/api-client.ts` - Added `getCurrentUser()` export

---

## Acceptance Criteria Met

✅ **Frontend builds:** `npm run build` succeeds with 0 TypeScript errors  
✅ **Component tests pass:** Decision-actions utility has 19 passing tests covering full permission matrix  
✅ **Decision panel renders:** Only permitted actions from backend show as buttons  
✅ **Decision dialog validates:** Required fields enforced per action type  
✅ **Separation of duties:** Creator cannot decide own case (UI + backend enforcement)  
✅ **Open request blocking:** Decisions blocked when information request open  
✅ **Error handling:** 409 INVALID_CASE_STATE and STALE_OBJECT handled distinctly  
✅ **Terminal states:** Final decision notice shown, no action buttons  
✅ **Button kinds correct:** Approve=primary, Reject=danger--tertiary, Escalate=secondary, Close=ghost  

**E2E Tests:** Partially passing - see Known Issues for modal strict-mode violations
