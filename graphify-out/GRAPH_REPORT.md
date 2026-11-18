# Graph Report - feature-ai-powered-aml-monitoring  (2026-11-17)

## Corpus Check
- 182 files · ~93,046 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 19 file(s) not represented in the graph (top: (none) 8, .example 2, .tsbuildinfo 2)

## Summary
- 1713 nodes · 3981 edges · 101 communities (56 shown, 45 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 286 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8065f6cc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AML Transaction Monitoring Platform
- ScreeningContext
- conftest.py
- AlertDetailPage.tsx
- sqlalchemy_orm
- Customer
- test_transaction_service.py
- User
- @carbon/react
- CaseWorkspacePage.tsx
- get_current_user
- CaseManagementService
- RulesRepository
- TASK-5 Handoff: Rule Evaluation Engine and Alert Service
- Task 9 Handoff: Case State Machine and Investigation Workflow
- aml-monitoring-backend
- package.json
- App.tsx
- compilerOptions
- Transaction
- RuleVersion
- steps
- health_check
- compilerOptions
- UserRole
- get_alert_detail
- test_auth_integration.py
- TestClient
- rules/service.py
- Task 6 Handoff: Audit Service Implementation
- BaseModel
- tsconfig.json
- Task 8 Handoff: Case API and State Transitions
- TASK-4 Handoff: Transaction Screening Service and Account Context
- environment
- test_audit_service.py
- AccountRepository
- Settings
- AlertRepository
- TransactionSubmitPage.tsx
- .get_transaction_detail
- AlertRepository
- TASK-3 Handoff: Transaction Ingestion and API Transport
- pagination.py
- TestClient
- CaseStateMachine
- CustomerService
- list_audit_events
- create_transaction
- test_alert_api_simple.py
- seed.py
- CaseWorkspacePage.tsx
- CaseRepository
- Task 13 Handoff: Case Decision Panel and Workflow Completion
- UserResponse
- sample_alert
- set_sqlite_pragma
- start.sh
- investigation/service.py
- DomainValidationError
- get_correlation_id
- transaction/service.py
- rules/schemas.py
- CustomerRepository
- test_foreign_key_relationship
- @playwright/test
- .get_customer
- HighRiskGeographyEvaluator
- test_transaction_service.py
- TransactionService Integration
- customer
- errors.py
- Alert
- seed.py
- StructuringEvaluator
- stop.sh
- RoundAmountPatternEvaluator
- test_account_endpoint_not_found

## God Nodes (most connected - your core abstractions)
1. `Customer` - 88 edges
2. `Transaction` - 77 edges
3. `Account` - 59 edges
4. `User` - 59 edges
5. `CustomerRiskProfile` - 57 edges
6. `AMLCase` - 49 edges
7. `ScreeningContext` - 41 edges
8. `RuleVersion` - 38 edges
9. `Alert` - 36 edges
10. `RuleEvaluationDraft` - 35 edges

## Surprising Connections (you probably didn't know these)
- `POST /api/v1/cases/{id}/decision` --references--> `CaseDetailResponse`  [INFERRED]
  .handoff/TASK-9.md → backend/app/case_management/schemas.py
- `Optimistic Locking (Mutable Entities)` --references--> `OptimisticLockConflictError`  [INFERRED]
  .handoff/TASK-7.md → backend/app/common/errors.py
- `State Machine Support` --references--> `CaseState`  [INFERRED]
  .handoff/TASK-7.md → backend/app/common/enums.py
- `Continuous Integration` --references--> `main()`  [INFERRED]
  README.md → backend/app/seed.py
- `Repository Methods` --references--> `ScreeningContext`  [INFERRED]
  .handoff/TASK-4.md → backend/app/customer/schemas.py

## Import Cycles
- None detected.

## Communities (101 total, 45 thin omitted)

### Community 0 - "AML Transaction Monitoring Platform"
Cohesion: 0.04
Nodes (46): Access Points, Access the Application, AML Transaction Monitoring Platform, API Documentation, Apply Migrations, Architecture, Authentication Issues, Backend Development (+38 more)

### Community 1 - "ScreeningContext"
Cohesion: 0.11
Nodes (7): AlertService, Transaction, test_alert_created_for_matches(), test_no_alert_for_zero_matches(), test_pep_priority_floor_enforcement(), test_priority_bands(), test_risk_score_aggregates_multiple_matches()

### Community 2 - "conftest.py"
Cohesion: 0.09
Nodes (20): configure_logging(), CorrelationFilter, _alembic(), _annotation_kind(), _column_kind(), _env_py_text(), _foreign_key(), _has_alembic_version() (+12 more)

### Community 3 - "AlertDetailPage.tsx"
Cohesion: 0.13
Nodes (19): AlertSummary(), AlertSummaryProps, CustomerSnapshot(), CustomerSnapshotProps, ExplanationCallout(), ExplanationCalloutProps, ScoreBreakdown(), ScoreBreakdownProps (+11 more)

### Community 4 - "sqlalchemy_orm"
Cohesion: 0.08
Nodes (7): get_url(), run_migrations_offline(), run_migrations_online(), downgrade(), upgrade(), upgrade(), test_health_check()

### Community 5 - "Customer"
Cohesion: 0.06
Nodes (26): Account, Customer, CustomerRiskProfile, CountryRisk, seed_customers_and_accounts(), test_account(), sample_customer_with_account(), sample_customer() (+18 more)

### Community 6 - "test_transaction_service.py"
Cohesion: 0.19
Nodes (8): TransactionIngestRequest, TransactionService, test_context_loading_isolates_accounts(), test_screening_context_includes_transaction_history(), test_transaction_ingestion_fails_missing_account(), test_transaction_ingestion_fails_missing_risk_profile(), test_transaction_ingestion_loads_account_context(), test_ingest_transaction_success()

### Community 7 - "User"
Cohesion: 0.06
Nodes (24): AMLCase, CaseAlertLink, CaseDecision, User, test_case_alert_link_unique_constraints(), test_case_decisions_append_only(), test_case_foreign_key_constraints(), test_case_notes_append_only() (+16 more)

### Community 8 - "@carbon/react"
Cohesion: 0.17
Nodes (18): RuleResultList(), RuleResultListProps, RuleResultRow(), RuleResultRowProps, RuleResultTag(), RuleResultTagProps, TransactionOutcomeTag(), TransactionOutcomeTagProps (+10 more)

### Community 9 - "CaseWorkspacePage.tsx"
Cohesion: 0.15
Nodes (17): headers, LinkedAlertsPanelProps, calculateOverdue(), formatDueDate(), InformationRequestCard(), InformationRequestCardProps, formatTimestamp(), NotesThread() (+9 more)

### Community 10 - "get_current_user"
Cohesion: 0.11
Nodes (8): assign_case(), create_case(), get_case_detail(), record_decision(), add_note(), record_response(), request_information(), get_current_user()

### Community 11 - "CaseManagementService"
Cohesion: 0.13
Nodes (6): CaseManagementService, test_create_case_fails_if_alert_not_found(), test_creator_cannot_decide_own_case(), test_different_officer_can_decide_case(), test_get_case_detail_includes_permitted_actions(), test_invalid_state_transition_raises_error()

### Community 13 - "TASK-5 Handoff: Rule Evaluation Engine and Alert Service"
Cohesion: 0.08
Nodes (23): Alert Priority Bands, API Integration, Completed Implementation, Country Risk, Customers and Accounts, Database Tables Updated, Detection Rules, Example Explanations (+15 more)

### Community 14 - "Task 9 Handoff: Case State Machine and Investigation Workflow"
Cohesion: 0.06
Nodes (34): Adding Notes, APPROVE, Audit Events, By Role and State, Case Notes, CLOSE_FALSE_POSITIVE, Creator-Decider Conflict (HTTP 403), Decision Types and Required Fields (+26 more)

### Community 28 - "package.json"
Cohesion: 0.05
Nodes (51): dependencies, @carbon/charts-react@^1.20.0, @carbon/colors@^11.33.0, @carbon/icons-react@^11.51.0, @carbon/react@^1.70.0, @carbon/styles@^1.70.0, react@^18.3.1, react-dom@^18.3.1 (+43 more)

### Community 29 - "App.tsx"
Cohesion: 0.14
Nodes (16): App(), DashboardPage(), LoginPage(), RequireAuth(), RequireAuthProps, Header(), Layout(), LayoutProps (+8 more)

### Community 30 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 31 - "Transaction"
Cohesion: 0.14
Nodes (11): HistoricalMetrics, ScreeningContext, RulesService, all_rules_setup(), test_all_eight_rules_evaluated(), test_high_value_transaction_match(), test_high_value_transaction_pass(), test_sanctioned_or_pep_match() (+3 more)

### Community 32 - "RuleVersion"
Cohesion: 0.11
Nodes (7): AMLRuleEvaluator, HighValueTransactionEvaluator, SanctionedOrPepEvaluator, VelocityAmountEvaluator, VelocityCountEvaluator, RuleVersion, RuleEvaluationDraft

### Community 33 - "steps"
Cohesion: 0.06
Nodes (39): name, runs-on, services, steps, CORS_ORIGINS, DATABASE_URL, JWT_ALGORITHM, JWT_EXPIRY_MINUTES (+31 more)

### Community 35 - "compilerOptions"
Cohesion: 0.18
Nodes (10): compilerOptions, allowSyntheticDefaultImports, lib, module, moduleResolution, noEmit, skipLibCheck, strict (+2 more)

### Community 36 - "UserRole"
Cohesion: 0.22
Nodes (7): User, UserRole, ADMINISTRATOR, AML_ANALYST, AML_MANAGER, AML_OFFICER, AUDITOR

### Community 37 - "get_alert_detail"
Cohesion: 0.14
Nodes (6): get_alert_detail(), AlertDetailResponse, CustomerSnapshotData, RiskScoreResult, RuleEvaluationSummary, TransactionSummary

### Community 38 - "test_auth_integration.py"
Cohesion: 0.09
Nodes (9): UserSession, login(), SecurityService, test_login_creates_session(), test_login_inactive_user(), test_login_invalid_email(), test_login_invalid_password(), test_login_success() (+1 more)

### Community 39 - "TestClient"
Cohesion: 0.07
Nodes (19): test_alert_generation_creates_audit_event(), test_audit_api_pagination(), test_audit_api_requires_authentication(), test_audit_api_retrieval_by_correlation_id(), test_audit_api_retrieval_by_entity(), test_audit_events_not_editable_via_api(), test_audit_events_share_correlation_id(), test_failed_transaction_no_orphaned_audit() (+11 more)

### Community 40 - "rules/service.py"
Cohesion: 0.16
Nodes (4): RuleOutcome, RuleEvaluationFailureError, DormancySpikeEvaluator, RuleEvaluationResult

### Community 41 - "Task 6 Handoff: Audit Service Implementation"
Cohesion: 0.10
Nodes (19): API Endpoints, Atomic Behavior Guarantees, Audit Event Action Types, Correlation ID Usage, Failure Case, Future Case Workflow Events (Supported Structure), Future Enhancements (Out of Current Scope), GET /api/v1/audit (+11 more)

### Community 42 - "BaseModel"
Cohesion: 0.10
Nodes (13): AuditEventCreate, AlertSummary, CaseAssignRequest, CaseCreateRequest, CaseDecisionRequest, CaseDetailResponse, DecisionSummary, InformationRequestSummary (+5 more)

### Community 45 - "Task 8 Handoff: Case API and State Transitions"
Cohesion: 0.08
Nodes (24): Analyst Role, API Base URL, Case States, Create and Decide Case Flow, Creator-Decider Rejection Flow, GET /api/v1/cases/{id}, Implemented Endpoints, Integration Points (+16 more)

### Community 48 - "TASK-4 Handoff: Transaction Screening Service and Account Context"
Cohesion: 0.11
Nodes (17): Account Context Data Structure, Backend Endpoints Added, Completed Work, Customer Endpoints, Failed Ingestion, Files Modified, Historical Metrics Computation, HistoricalMetrics (+9 more)

### Community 49 - "environment"
Cohesion: 0.08
Nodes (31): BACKEND_HOST, build, driver, environment, expose, healthcheck, volumes, args (+23 more)

### Community 50 - "test_audit_service.py"
Cohesion: 0.09
Nodes (15): AuditEvent, AuditRepository, AuditService, sample_transaction(), test_audit_events_are_immutable(), test_list_events_combined_filters(), test_list_events_filters_by_actor_id(), test_list_events_filters_by_correlation_id() (+7 more)

### Community 51 - "AccountRepository"
Cohesion: 0.27
Nodes (3): AccountRepository, test_get_screening_context_account_not_found(), test_get_screening_context_missing_risk_profile()

### Community 53 - "AlertRepository"
Cohesion: 0.07
Nodes (26): Acceptance Criteria Status, Alert Linking: `case_alert_links`, Append-Only Entities (No Updates), Case Decisions: `case_decisions`, Case Detail Response Structure, Case Workflow Table Structures, Completion Summary, Concurrency Patterns (+18 more)

### Community 54 - "TransactionSubmitPage.tsx"
Cohesion: 0.20
Nodes (10): ACCOUNTS, TransactionForm(), TransactionFormProps, mockGetTransactionDetail, mockTransaction, mockSubmitTransaction, renderPage(), TransactionSubmitPage() (+2 more)

### Community 57 - "TASK-3 Handoff: Transaction Ingestion and API Transport"
Cohesion: 0.20
Nodes (9): Authentication, Endpoints Mounted, Error Responses, GET /api/v1/transactions/{id}, Implementation Status, POST /api/v1/transactions/, Request/Response Shapes, Seed Data for Testing (+1 more)

### Community 59 - "TestClient"
Cohesion: 0.12
Nodes (10): test_assign_case_updates_assignment(), test_create_case_returns_201_with_case_detail(), test_create_case_with_already_linked_alert_returns_409(), test_create_case_with_nonexistent_alert_returns_404(), test_creator_attempting_decision_returns_403(), test_get_case_detail_returns_200_with_complete_info(), test_get_nonexistent_case_returns_404(), test_invalid_state_transition_returns_409() (+2 more)

### Community 60 - "CaseStateMachine"
Cohesion: 0.07
Nodes (25): CaseStateMachine, test_state_machine_computes_analyst_permissions(), test_state_machine_enforces_creator_decider_separation(), test_state_machine_validates_transitions(), test_permitted_actions_administrator_has_all_actions(), test_permitted_actions_analyst_open_state(), test_permitted_actions_invalid_role_returns_empty(), test_permitted_actions_manager_has_broad_access() (+17 more)

### Community 66 - "seed.py"
Cohesion: 0.13
Nodes (12): AccountStatus, AlertPriority, AlertStatus, CaseDecision, CaseState, CountryRiskRating, InformationRequestStatus, RiskLevel (+4 more)

### Community 67 - "CaseWorkspacePage.tsx"
Cohesion: 0.10
Nodes (20): AuditTimeline(), AuditTimelineProps, DECISION_CONFIGS, DecisionConfig, DecisionDialog(), DecisionDialogProps, DecisionPanel(), DecisionPanelProps (+12 more)

### Community 69 - "Task 13 Handoff: Case Decision Panel and Workflow Completion"
Cohesion: 0.11
Nodes (17): Acceptance Criteria Met, API Integration, Business Logic, CaseWorkspacePage Integration, decision-actions.ts, Decision Endpoint, DecisionDialog.tsx, DecisionPanel.tsx (+9 more)

### Community 70 - "UserResponse"
Cohesion: 0.28
Nodes (4): get_account(), get_customer(), UserResponse, Config

### Community 71 - "sample_alert"
Cohesion: 0.18
Nodes (5): auth_client(), client(), db_session(), _fresh_schema(), test_user()

### Community 74 - "start.sh"
Cohesion: 0.48
Nodes (6): check_prerequisites(), DATABASE_URL, find_available_port(), native_path(), port_in_use(), start.sh script

### Community 75 - "investigation/service.py"
Cohesion: 0.07
Nodes (10): CaseNote, OptimisticLockConflictError, InformationRequest, InformationResponse, InvestigationRepository, CaseNoteResponse, InformationRequestResponse, InformationResponseResponse (+2 more)

### Community 76 - "DomainValidationError"
Cohesion: 0.25
Nodes (3): AuthorizationError, DomainError, DomainValidationError

### Community 77 - "get_correlation_id"
Cohesion: 0.27
Nodes (3): generate_correlation_id(), get_correlation_id(), set_correlation_id()

### Community 78 - "transaction/service.py"
Cohesion: 0.23
Nodes (4): RuleEvaluationItem, TransactionDetailResponse, TransactionIngestResponse, Placeholder Notes

### Community 79 - "rules/schemas.py"
Cohesion: 0.28
Nodes (3): EvaluationBatchResult, RuleParameters, RuleVersionResponse

### Community 81 - "test_foreign_key_relationship"
Cohesion: 0.29
Nodes (3): test_country_risk_insert(), test_database_connection(), test_foreign_key_relationship()

### Community 87 - "test_transaction_service.py"
Cohesion: 0.17
Nodes (6): account(), customer(), test_get_transaction_detail_not_found(), test_ingest_transaction_account_not_found(), test_ingest_transaction_with_optional_fields(), test_transaction_preserves_original_values()

### Community 88 - "TransactionService Integration"
Cohesion: 0.67
Nodes (3): Repository Methods, Service Integration, TransactionService Integration

### Community 91 - "customer"
Cohesion: 0.29
Nodes (3): account(), auth_token(), customer()

### Community 92 - "errors.py"
Cohesion: 0.06
Nodes (10): AuditEventListResponse, AuditEventResponse, AuthenticationError, NotFoundError, AccountResponse, CustomerResponse, get_db(), lifespan() (+2 more)

### Community 93 - "Alert"
Cohesion: 0.11
Nodes (8): Alert, sample_alert(), test_get_alert_detail_not_found(), test_get_alert_detail_requires_auth(), test_get_alert_detail_success(), test_create_case_fails_if_alert_already_linked(), test_create_case_from_multiple_alerts_uses_highest_priority(), test_create_case_from_single_alert()

### Community 94 - "seed.py"
Cohesion: 0.11
Nodes (12): DetectionRule, hash_password(), main(), seed_audit_events(), seed_cases(), seed_country_risk(), seed_detection_rules(), seed_sample_alerts() (+4 more)

## Knowledge Gaps
- **7 isolated node(s):** `aml-monitoring-backend`, `ADMINISTRATOR`, `AML_ANALYST`, `AML_MANAGER`, `AML_OFFICER` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 836 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **45 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Customer` connect `Customer` to `ScreeningContext`, `sqlalchemy_orm`, `test_transaction_service.py`, `User`, `CaseManagementService`, `Transaction`, `get_alert_detail`, `TestClient`, `test_audit_service.py`, `AccountRepository`, `TestClient`, `seed.py`, `CustomerRepository`, `test_foreign_key_relationship`, `.get_customer`, `test_transaction_service.py`, `customer`, `Alert`, `seed.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Customer` (e.g. with `get_alert_detail()` and `AccountRepository`) actually correct?**
  _`Customer` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aml-monitoring-backend`, `ADMINISTRATOR`, `AML_ANALYST` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `AML Transaction Monitoring Platform` be split into smaller, more focused modules?**
  _Cohesion score 0.0425531914893617 - nodes in this community are weakly interconnected._
- **Why does `Transaction` connect `ScreeningContext` to `RuleVersion`, `RoundAmountPatternEvaluator`, `seed.py`, `sqlalchemy_orm`, `get_alert_detail`, `test_transaction_service.py`, `User`, `rules/service.py`, `Customer`, `transaction/service.py`, `test_audit_service.py`, `HighRiskGeographyEvaluator`, `.get_transaction_detail`, `TestClient`, `Transaction`, `Alert`, `seed.py`, `StructuringEvaluator`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `Transaction` (e.g. with `get_alert_detail()` and `AlertService`) actually correct?**
  _`Transaction` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Should `ScreeningContext` be split into smaller, more focused modules?**
  _Cohesion score 0.11397849462365592 - nodes in this community are weakly interconnected._