"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-11-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('permissions_json', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    
    # User sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('issued_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    op.create_index(op.f('ix_user_sessions_expires_at'), 'user_sessions', ['expires_at'], unique=False)
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)
    
    # Customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_number', sa.String(length=64), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('residency_country', sa.String(length=2), nullable=False),
        sa.Column('pep_status', sa.Boolean(), nullable=False),
        sa.Column('sanctioned_status', sa.Boolean(), nullable=False),
        sa.Column('synthetic_source', sa.String(length=64), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_number')
    )
    op.create_index(op.f('ix_customers_full_name'), 'customers', ['full_name'], unique=False)
    
    # Customer risk profiles table
    op.create_table(
        'customer_risk_profiles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('base_score', sa.Integer(), nullable=False),
        sa.Column('last_reviewed_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id')
    )
    op.create_index(op.f('ix_customer_risk_profiles_risk_level'), 'customer_risk_profiles', ['risk_level'], unique=False)
    
    # Accounts table
    op.create_table(
        'accounts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_number', sa.String(length=64), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('opened_at', sa.DateTime(), nullable=False),
        sa.Column('current_balance', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_number')
    )
    op.create_index(op.f('ix_accounts_customer_id'), 'accounts', ['customer_id'], unique=False)
    op.create_index(op.f('ix_accounts_status'), 'accounts', ['status'], unique=False)
    
    # Country risk table
    op.create_table(
        'country_risk',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('country_code', sa.String(length=2), nullable=False),
        sa.Column('country_name', sa.String(length=100), nullable=False),
        sa.Column('is_high_risk', sa.Boolean(), nullable=False),
        sa.Column('risk_rating', sa.String(length=20), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('country_code')
    )
    
    # Transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('transaction_reference', sa.String(length=100), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('transaction_type', sa.String(length=20), nullable=False),
        sa.Column('origin_country', sa.String(length=2), nullable=False),
        sa.Column('destination_country', sa.String(length=2), nullable=False),
        sa.Column('counterparty_name', sa.String(length=255), nullable=True),
        sa.Column('counterparty_account', sa.String(length=100), nullable=True),
        sa.Column('transaction_timestamp', sa.DateTime(), nullable=False),
        sa.Column('correlation_id', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_reference')
    )
    op.create_index(op.f('ix_transactions_account_id'), 'transactions', ['account_id'], unique=False)
    op.create_index(op.f('ix_transactions_correlation_id'), 'transactions', ['correlation_id'], unique=False)
    op.create_index(op.f('ix_transactions_transaction_timestamp'), 'transactions', ['transaction_timestamp'], unique=False)
    
    # Detection rules table
    op.create_table(
        'detection_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('rule_code', sa.String(length=16), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rule_code')
    )
    
    # Rule versions table
    op.create_table(
        'rule_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('parameters_json', sa.Text(), nullable=False),
        sa.Column('effective_from', sa.DateTime(), nullable=False),
        sa.Column('changed_by', sa.Integer(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['rule_id'], ['detection_rules.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rule_id', 'version_number', name='uq_rule_version')
    )
    op.create_index(op.f('ix_rule_versions_rule_id'), 'rule_versions', ['rule_id'], unique=False)
    
    # Rule evaluation results table
    op.create_table(
        'rule_evaluation_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('rule_code', sa.String(length=16), nullable=False),
        sa.Column('rule_version', sa.Integer(), nullable=False),
        sa.Column('result', sa.String(length=10), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('evidence_snapshot', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['rule_id'], ['detection_rules.id'], ),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_id', 'rule_id', name='uq_transaction_rule')
    )
    op.create_index(op.f('ix_rule_evaluation_results_rule_code'), 'rule_evaluation_results', ['rule_code'], unique=False)
    op.create_index(op.f('ix_rule_evaluation_results_transaction_id'), 'rule_evaluation_results', ['transaction_id'], unique=False)
    
    # Alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('alert_number', sa.String(length=32), nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('assigned_to_user_id', sa.Integer(), nullable=True),
        sa.Column('priority_rationale', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('alert_number'),
        sa.UniqueConstraint('transaction_id')
    )
    op.create_index(op.f('ix_alerts_assigned_to_user_id'), 'alerts', ['assigned_to_user_id'], unique=False)
    op.create_index(op.f('ix_alerts_priority'), 'alerts', ['priority'], unique=False)
    op.create_index(op.f('ix_alerts_status'), 'alerts', ['status'], unique=False)
    
    # AML cases table
    op.create_table(
        'aml_cases',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('case_number', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('state', sa.String(length=32), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('assigned_to_user_id', sa.Integer(), nullable=True),
        sa.Column('closure_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('case_number')
    )
    op.create_index(op.f('ix_aml_cases_assigned_to_user_id'), 'aml_cases', ['assigned_to_user_id'], unique=False)
    op.create_index(op.f('ix_aml_cases_customer_id'), 'aml_cases', ['customer_id'], unique=False)
    op.create_index(op.f('ix_aml_cases_state'), 'aml_cases', ['state'], unique=False)
    
    # Case alert links table
    op.create_table(
        'case_alert_links',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('linked_at', sa.DateTime(), nullable=False),
        sa.Column('linked_by_user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['alert_id'], ['alerts.id'], ),
        sa.ForeignKeyConstraint(['case_id'], ['aml_cases.id'], ),
        sa.ForeignKeyConstraint(['linked_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('alert_id', name='uq_alert_case'),
        sa.UniqueConstraint('case_id', 'alert_id', name='uq_case_alert')
    )
    op.create_index(op.f('ix_case_alert_links_case_id'), 'case_alert_links', ['case_id'], unique=False)
    
    # Case notes table
    op.create_table(
        'case_notes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('note_text', sa.Text(), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['aml_cases.id'], ),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_case_notes_case_id'), 'case_notes', ['case_id'], unique=False)
    
    # Information requests table
    op.create_table(
        'information_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('requested_what', sa.Text(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('requested_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['aml_cases.id'], ),
        sa.ForeignKeyConstraint(['requested_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_information_requests_case_id'), 'information_requests', ['case_id'], unique=False)
    op.create_index(op.f('ix_information_requests_status'), 'information_requests', ['status'], unique=False)
    
    # Information responses table
    op.create_table(
        'information_responses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('information_request_id', sa.Integer(), nullable=False),
        sa.Column('response_text', sa.Text(), nullable=False),
        sa.Column('responded_by_user_id', sa.Integer(), nullable=False),
        sa.Column('responded_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['information_request_id'], ['information_requests.id'], ),
        sa.ForeignKeyConstraint(['responded_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('information_request_id')
    )
    
    # Case decisions table
    op.create_table(
        'case_decisions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('decision', sa.String(length=32), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('decided_by_user_id', sa.Integer(), nullable=False),
        sa.Column('decided_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['aml_cases.id'], ),
        sa.ForeignKeyConstraint(['decided_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_case_decisions_case_id'), 'case_decisions', ['case_id'], unique=False)
    
    # Audit events table
    op.create_table(
        'audit_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('actor_user_id', sa.Integer(), nullable=True),
        sa.Column('actor_username', sa.String(length=100), nullable=False),
        sa.Column('actor_role', sa.String(length=32), nullable=False),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('entity_type', sa.String(length=64), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('correlation_id', sa.String(length=100), nullable=False),
        sa.Column('details_json', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_events_actor_user_id'), 'audit_events', ['actor_user_id'], unique=False)
    op.create_index(op.f('ix_audit_events_correlation_id'), 'audit_events', ['correlation_id'], unique=False)
    op.create_index(op.f('ix_audit_events_entity_id'), 'audit_events', ['entity_id'], unique=False)
    op.create_index(op.f('ix_audit_events_entity_type'), 'audit_events', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_events_timestamp'), 'audit_events', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_events')
    op.drop_table('case_decisions')
    op.drop_table('information_responses')
    op.drop_table('information_requests')
    op.drop_table('case_notes')
    op.drop_table('case_alert_links')
    op.drop_table('aml_cases')
    op.drop_table('alerts')
    op.drop_table('rule_evaluation_results')
    op.drop_table('rule_versions')
    op.drop_table('detection_rules')
    op.drop_table('transactions')
    op.drop_table('country_risk')
    op.drop_table('accounts')
    op.drop_table('customer_risk_profiles')
    op.drop_table('customers')
    op.drop_table('user_sessions')
    op.drop_table('users')
