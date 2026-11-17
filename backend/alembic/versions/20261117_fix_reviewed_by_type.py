"""Fix reviewed_by field type from integer FK to string

Revision ID: 002_fix_reviewed_by
Revises: 001_initial
Create Date: 2026-11-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_fix_reviewed_by'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Change reviewed_by from INTEGER FK to VARCHAR(64) and remove FK constraint."""
    # For SQLite, manually recreate the table without the FK constraint
    # Step 1: Create temporary table with new schema
    op.create_table(
        'customer_risk_profiles_new',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('base_score', sa.Integer(), nullable=False),
        sa.Column('last_reviewed_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_by', sa.String(64), nullable=True),  # Changed to String
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        # No FK constraint to users.id
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id')
    )
    
    # Step 2: Copy data from old table to new table
    # Use CAST to convert INTEGER to TEXT
    op.execute("""
        INSERT INTO customer_risk_profiles_new 
            (id, customer_id, risk_level, base_score, last_reviewed_at, 
             reviewed_by, version, created_at, updated_at)
        SELECT 
            id, customer_id, risk_level, base_score, last_reviewed_at,
            CAST(reviewed_by AS TEXT), version, created_at, updated_at
        FROM customer_risk_profiles
    """)
    
    # Step 3: Drop old table
    op.drop_table('customer_risk_profiles')
    
    # Step 4: Rename new table to original name
    op.rename_table('customer_risk_profiles_new', 'customer_risk_profiles')
    
    # Step 5: Recreate index
    op.create_index(op.f('ix_customer_risk_profiles_risk_level'), 
                    'customer_risk_profiles', ['risk_level'], unique=False)


def downgrade() -> None:
    """Revert reviewed_by back to INTEGER FK."""
    # Create temporary table with old schema
    op.create_table(
        'customer_risk_profiles_new',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('base_score', sa.Integer(), nullable=False),
        sa.Column('last_reviewed_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),  # Changed back to Integer
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id']),  # FK constraint restored
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id')
    )
    
    # Copy data, converting TEXT back to INTEGER
    op.execute("""
        INSERT INTO customer_risk_profiles_new 
            (id, customer_id, risk_level, base_score, last_reviewed_at, 
             reviewed_by, version, created_at, updated_at)
        SELECT 
            id, customer_id, risk_level, base_score, last_reviewed_at,
            CAST(reviewed_by AS INTEGER), version, created_at, updated_at
        FROM customer_risk_profiles
    """)
    
    # Drop old and rename
    op.drop_table('customer_risk_profiles')
    op.rename_table('customer_risk_profiles_new', 'customer_risk_profiles')
    
    # Recreate index
    op.create_index(op.f('ix_customer_risk_profiles_risk_level'), 
                    'customer_risk_profiles', ['risk_level'], unique=False)
