"""Initial schema - users, clinics, audit logs

Revision ID: 001_initial
Revises: 
Create Date: 2026-01-14 12:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""
    
    # Create clinics table
    op.create_table(
        'clinics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('npi', sa.String(length=10), nullable=True),
        sa.Column('tax_id', sa.String(length=20), nullable=True),
        sa.Column('address', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('fax', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Enum('active', 'inactive', 'trial', 'suspended', name='clinicstatus'), nullable=False, server_default='trial'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('settings', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('subscription_tier', sa.String(length=50), nullable=True, server_default='trial'),
        sa.Column('subscription_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_users', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('max_pas_per_month', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('features_enabled', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('billing_contact', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('technical_contact', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata_', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Clinic indexes
    op.create_index('idx_clinic_name_active', 'clinics', ['name', 'is_active'])
    op.create_index('idx_clinic_npi', 'clinics', ['npi'])
    op.create_index('idx_clinic_status', 'clinics', ['status'])
    op.create_index(op.f('ix_clinics_npi'), 'clinics', ['npi'], unique=True)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('role', sa.Enum('admin', 'clinician', 'staff', 'viewer', name='userrole'), nullable=False, server_default='staff'),
        sa.Column('status', sa.Enum('active', 'inactive', 'suspended', 'pending', name='userstatus'), nullable=False, server_default='pending'),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clinics.id'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('mfa_secret', sa.String(length=255), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('email_verification_token', sa.String(length=255), nullable=True),
        sa.Column('password_reset_token', sa.String(length=255), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('preferences', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('metadata_', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # User indexes
    op.create_index('idx_user_email_active', 'users', ['email', 'is_active'])
    op.create_index('idx_user_clinic_role', 'users', ['clinic_id', 'role'])
    op.create_index('idx_user_status', 'users', ['status'])
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('action', sa.Enum(
            'login', 'logout', 'login_failed', 'password_reset',
            'user_created', 'user_updated', 'user_deleted', 'user_activated', 'user_deactivated',
            'patient_viewed', 'patient_created', 'patient_updated', 'patient_deleted',
            'pa_created', 'pa_viewed', 'pa_updated', 'pa_submitted', 'pa_approved', 'pa_denied', 'pa_deleted',
            'document_uploaded', 'document_viewed', 'document_downloaded', 'document_deleted',
            'clinic_created', 'clinic_updated', 'setting_changed',
            'agent_workflow_started', 'agent_workflow_completed', 'agent_workflow_failed',
            'api_call', 'export', 'bulk_action',
            name='auditaction'
        ), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('clinic_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('details', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('request_id', sa.String(length=255), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Audit log indexes
    op.create_index('idx_audit_action_time', 'audit_logs', ['action', 'created_at'])
    op.create_index('idx_audit_user_time', 'audit_logs', ['user_id', 'created_at'])
    op.create_index('idx_audit_clinic_time', 'audit_logs', ['clinic_id', 'created_at'])
    op.create_index('idx_audit_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_request', 'audit_logs', ['request_id'])
    
    # Create trigger for updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Apply trigger to all tables
    for table in ['clinics', 'users', 'audit_logs']:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    """Drop all tables and triggers."""
    
    # Drop triggers
    for table in ['clinics', 'users', 'audit_logs']:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")
    
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop tables
    op.drop_table('audit_logs')
    op.drop_table('users')
    op.drop_table('clinics')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS auditaction")
    op.execute("DROP TYPE IF EXISTS userstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS clinicstatus")