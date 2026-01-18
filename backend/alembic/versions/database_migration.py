"""
Add Phase 4 core business tables

Revision ID: 002_phase4_core_tables
Revises: 001_initial_users
Create Date: 2025-01-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_phase4_core_tables'
down_revision = '001_initial_users'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create payers table
    op.create_table(
        'payers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('payer_id', sa.String(10), nullable=False, unique=True),
        sa.Column('external_id', sa.String(100), unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('legal_name', sa.String(255)),
        sa.Column('payer_type', sa.String(50), nullable=False),
        sa.Column('phone', sa.String(20)),
        sa.Column('fax', sa.String(20)),
        sa.Column('email', sa.String(255)),
        sa.Column('website', sa.String(255)),
        sa.Column('pa_portal_url', sa.String(500)),
        sa.Column('address_line1', sa.String(255)),
        sa.Column('address_line2', sa.String(255)),
        sa.Column('city', sa.String(100)),
        sa.Column('state', sa.String(2)),
        sa.Column('zip_code', sa.String(10)),
        sa.Column('country', sa.String(2), nullable=False, server_default='US'),
        sa.Column('preferred_submission_method', sa.String(50), nullable=False),
        sa.Column('accepted_submission_methods', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('requires_electronic_signature', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('accepts_rush_requests', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('standard_processing_days', sa.Integer),
        sa.Column('urgent_processing_days', sa.Integer),
        sa.Column('expedited_processing_days', sa.Integer),
        sa.Column('required_documents', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('optional_documents', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('covered_services', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('medical_policies', postgresql.JSON, nullable=False, server_default='{}'),
        sa.Column('formulary_url', sa.String(500)),
        sa.Column('has_api_integration', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('api_endpoint', sa.String(500)),
        sa.Column('api_version', sa.String(20)),
        sa.Column('api_documentation_url', sa.String(500)),
        sa.Column('requires_api_authentication', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('portal_username', sa.String(255)),
        sa.Column('portal_password_hash', sa.String(255)),
        sa.Column('total_submissions', sa.Integer, nullable=False, server_default='0'),
        sa.Column('approved_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('denied_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('average_approval_time_days', sa.Float),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('accepts_new_submissions', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('submission_notes', sa.Text),
        sa.Column('appeal_notes', sa.Text),
        sa.Column('internal_notes', sa.Text),
        sa.Column('metadata', postgresql.JSON, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_verified_at', sa.DateTime),
    )
    op.create_index('ix_payers_id', 'payers', ['id'])
    op.create_index('ix_payers_payer_id', 'payers', ['payer_id'])
    op.create_index('ix_payers_name', 'payers', ['name'])
    op.create_index('ix_payers_payer_type', 'payers', ['payer_type'])
    op.create_index('ix_payers_is_active', 'payers', ['is_active'])

    # Create patients table
    op.create_table(
        'patients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('mrn', sa.String(50), unique=True),
        sa.Column('external_id', sa.String(100), unique=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('middle_name', sa.String(100)),
        sa.Column('date_of_birth', sa.Date, nullable=False),
        sa.Column('gender', sa.String(20), nullable=False),
        sa.Column('ssn', sa.String(11)),
        sa.Column('email', sa.String(255)),
        sa.Column('phone_primary', sa.String(20)),
        sa.Column('phone_secondary', sa.String(20)),
        sa.Column('address_line1', sa.String(255)),
        sa.Column('address_line2', sa.String(255)),
        sa.Column('city', sa.String(100)),
        sa.Column('state', sa.String(2)),
        sa.Column('zip_code', sa.String(10)),
        sa.Column('country', sa.String(2), nullable=False, server_default='US'),
        sa.Column('insurance_primary_member_id', sa.String(50)),
        sa.Column('insurance_primary_group_number', sa.String(50)),
        sa.Column('insurance_primary_payer_id', postgresql.UUID(as_uuid=True)),
        sa.Column('insurance_primary_payer_name', sa.String(200)),
        sa.Column('insurance_primary_plan_name', sa.String(200)),
        sa.Column('insurance_primary_effective_date', sa.Date),
        sa.Column('insurance_primary_termination_date', sa.Date),
        sa.Column('insurance_secondary_member_id', sa.String(50)),
        sa.Column('insurance_secondary_group_number', sa.String(50)),
        sa.Column('insurance_secondary_payer_name', sa.String(200)),
        sa.Column('primary_diagnosis_codes', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('allergies', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('current_medications', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('medical_history', sa.Text),
        sa.Column('emergency_contact_name', sa.String(200)),
        sa.Column('emergency_contact_phone', sa.String(20)),
        sa.Column('emergency_contact_relationship', sa.String(50)),
        sa.Column('consent_to_treat', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('consent_to_share_info', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('preferred_language', sa.String(10), nullable=False, server_default='en'),
        sa.Column('communication_preferences', postgresql.JSON, nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_deceased', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('deceased_date', sa.Date),
        sa.Column('notes', sa.Text),
        sa.Column('metadata', postgresql.JSON, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_verified_at', sa.DateTime),
    )
    op.create_index('ix_patients_id', 'patients', ['id'])
    op.create_index('ix_patients_mrn', 'patients', ['mrn'])
    op.create_index('ix_patients_last_name', 'patients', ['last_name'])
    op.create_index('ix_patients_dob', 'patients', ['date_of_birth'])
    op.create_index('ix_patients_insurance_member_id', 'patients', ['insurance_primary_member_id'])
    op.create_index('ix_patients_is_active', 'patients', ['is_active'])

    # Create providers table
    op.create_table(
        'providers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('npi', sa.String(10), nullable=False, unique=True),
        sa.Column('tax_id', sa.String(20)),
        sa.Column('license_number', sa.String(50)),
        sa.Column('license_state', sa.String(2)),
        sa.Column('dea_number', sa.String(20)),
        sa.Column('external_id', sa.String(100), unique=True),
        sa.Column('provider_type', sa.String(50), nullable=False),
        sa.Column('specialty', sa.String(50)),
        sa.Column('subspecialties', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('first_name', sa.String(100)),
        sa.Column('last_name', sa.String(100)),
        sa.Column('middle_name', sa.String(100)),
        sa.Column('credentials', sa.String(50)),
        sa.Column('organization_name', sa.String(255)),
        sa.Column('doing_business_as', sa.String(255)),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(20)),
        sa.Column('fax', sa.String(20)),
        sa.Column('website', sa.String(255)),
        sa.Column('address_line1', sa.String(255)),
        sa.Column('address_line2', sa.String(255)),
        sa.Column('city', sa.String(100)),
        sa.Column('state', sa.String(2)),
        sa.Column('zip_code', sa.String(10)),
        sa.Column('country', sa.String(2), nullable=False, server_default='US'),
        sa.Column('accepts_new_patients', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('hospital_affiliations', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('languages_spoken', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('insurance_networks', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('board_certified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('board_certification_date', sa.Date),
        sa.Column('board_certification_expiry', sa.Date),
        sa.Column('medical_school', sa.String(255)),
        sa.Column('graduation_year', sa.Integer),
        sa.Column('license_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('license_expiry_date', sa.Date),
        sa.Column('total_pa_requests', sa.Integer, nullable=False, server_default='0'),
        sa.Column('approved_pa_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('denied_pa_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('average_approval_time_days', sa.Float),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('verification_date', sa.DateTime),
        sa.Column('notes', sa.Text),
        sa.Column('metadata', postgresql.JSON, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_providers_id', 'providers', ['id'])
    op.create_index('ix_providers_npi', 'providers', ['npi'])
    op.create_index('ix_providers_last_name', 'providers', ['last_name'])
    op.create_index('ix_providers_org_name', 'providers', ['organization_name'])
    op.create_index('ix_providers_provider_type', 'providers', ['provider_type'])
    op.create_index('ix_providers_specialty', 'providers', ['specialty'])
    op.create_index('ix_providers_is_active', 'providers', ['is_active'])

    # Create prior_authorizations table (NOTE: Requires workflows table from future phase)
    op.create_table(
        'prior_authorizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('external_reference', sa.String(100)),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('urgency', sa.String(50), nullable=False),
        sa.Column('pa_type', sa.String(50), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payer_id', postgresql.UUID(as_uuid=True)),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_to_id', postgresql.UUID(as_uuid=True)),
        sa.Column('service_code', sa.String(50)),
        sa.Column('service_description', sa.Text, nullable=False),
        sa.Column('medication_name', sa.String(200)),
        sa.Column('medication_ndc', sa.String(20)),
        sa.Column('diagnosis_codes', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('clinical_rationale', sa.Text),
        sa.Column('medical_necessity', sa.Text),
        sa.Column('requested_quantity', sa.Integer),
        sa.Column('requested_duration_days', sa.Integer),
        sa.Column('treatment_start_date', sa.DateTime),
        sa.Column('treatment_end_date', sa.DateTime),
        sa.Column('submitted_at', sa.DateTime),
        sa.Column('submission_method', sa.String(50)),
        sa.Column('decision_date', sa.DateTime),
        sa.Column('approval_number', sa.String(100)),
        sa.Column('denial_reason', sa.Text),
        sa.Column('denial_code', sa.String(50)),
        sa.Column('valid_from', sa.DateTime),
        sa.Column('valid_until', sa.DateTime),
        sa.Column('ai_confidence_score', sa.Float),
        sa.Column('ai_recommendation', sa.String(50)),
        sa.Column('requires_human_review', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True)),
        sa.Column('notes', sa.Text),
        sa.Column('metadata', postgresql.JSON, nullable=False, server_default='{}'),
        sa.Column('is_appeal', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('original_pa_id', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['provider_id'], ['providers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['payer_id'], ['payers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['original_pa_id'], ['prior_authorizations.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_pa_id', 'prior_authorizations', ['id'])
    op.create_index('ix_pa_external_ref', 'prior_authorizations', ['external_reference'])
    op.create_index('ix_pa_status', 'prior_authorizations', ['status'])
    op.create_index('ix_pa_urgency', 'prior_authorizations', ['urgency'])
    op.create_index('ix_pa_type', 'prior_authorizations', ['pa_type'])
    op.create_index('ix_pa_patient_id', 'prior_authorizations', ['patient_id'])
    op.create_index('ix_pa_provider_id', 'prior_authorizations', ['provider_id'])
    op.create_index('ix_pa_payer_id', 'prior_authorizations', ['payer_id'])
    op.create_index('ix_pa_service_code', 'prior_authorizations', ['service_code'])
    op.create_index('ix_pa_submitted_at', 'prior_authorizations', ['submitted_at'])
    op.create_index('ix_pa_decision_date', 'prior_authorizations', ['decision_date'])
    op.create_index('ix_pa_is_appeal', 'prior_authorizations', ['is_appeal'])
    op.create_index('ix_pa_created_at', 'prior_authorizations', ['created_at'])

    # Create pa_status_history table
    op.create_table(
        'pa_status_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('prior_authorization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_status', sa.String(50)),
        sa.Column('to_status', sa.String(50), nullable=False),
        sa.Column('changed_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reason', sa.Text),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['prior_authorization_id'], ['prior_authorizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by_id'], ['users.id'], ondelete='RESTRICT'),
    )
    op.create_index('ix_pa_status_history_pa_id', 'pa_status_history', ['prior_authorization_id'])


def downgrade() -> None:
    op.drop_table('pa_status_history')
    op.drop_table('prior_authorizations')
    op.drop_table('providers')
    op.drop_table('patients')
    op.drop_table('payers')