-- Cyper Security Agent - Database Schema
-- PostgreSQL 15+

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- Organizations
-- ============================================================================

CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'basic',
    max_users INTEGER DEFAULT 5,
    features JSONB NOT NULL DEFAULT '[]',
    contact_email VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_organizations_name ON organizations(name);

-- ============================================================================
-- Users & Authentication
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    organization_id UUID REFERENCES organizations(id),
    role VARCHAR(50) NOT NULL DEFAULT 'analyst',
    features JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    terms_accepted_at TIMESTAMP,
    terms_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_organization ON users(organization_id);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;

-- Sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET NOT NULL,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_session CHECK (expires_at > created_at)
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(token_hash);
CREATE INDEX idx_sessions_active ON sessions(user_id, expires_at) WHERE revoked_at IS NULL;

-- Authorization pulses
CREATE TABLE authorization_pulses (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    features_granted JSONB,
    central_server_response TEXT,
    next_check_at TIMESTAMP,
    
    CONSTRAINT valid_status CHECK (status IN ('authorized', 'revoked', 'expired', 'error'))
);

CREATE INDEX idx_pulses_session ON authorization_pulses(session_id, checked_at DESC);
CREATE INDEX idx_pulses_next_check ON authorization_pulses(next_check_at) WHERE status = 'authorized';

-- Authorized targets
CREATE TABLE authorized_targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    target_type VARCHAR(50) NOT NULL,
    target_value TEXT NOT NULL,
    authorization_document_url TEXT,
    authorization_hash VARCHAR(64),
    authorized_by VARCHAR(255) NOT NULL,
    valid_from TIMESTAMP NOT NULL,
    valid_until TIMESTAMP NOT NULL,
    scope_limitations JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_authorization_period CHECK (valid_until > valid_from)
);

CREATE INDEX idx_authorized_targets_org ON authorized_targets(organization_id);
CREATE INDEX idx_authorized_targets_type ON authorized_targets(target_type, target_value);
CREATE INDEX idx_authorized_targets_valid ON authorized_targets(valid_from, valid_until);

-- ============================================================================
-- Scan Management
-- ============================================================================

CREATE TABLE scan_targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_type VARCHAR(50) NOT NULL,
    target_value TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scan_targets_type ON scan_targets(target_type);
CREATE INDEX idx_scan_targets_value ON scan_targets USING hash(target_value);

CREATE TABLE scan_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    target_id UUID NOT NULL REFERENCES scan_targets(id),
    authorization_target_id UUID REFERENCES authorized_targets(id),
    
    scan_type VARCHAR(50) NOT NULL,
    scan_mode VARCHAR(20) NOT NULL,
    
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    
    configuration JSONB,
    
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    progress_percentage INTEGER DEFAULT 0,
    current_phase VARCHAR(100),
    
    error_message TEXT,
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'stopped')),
    CONSTRAINT valid_priority CHECK (priority BETWEEN 1 AND 10),
    CONSTRAINT valid_progress CHECK (progress_percentage BETWEEN 0 AND 100)
);

CREATE INDEX idx_scan_jobs_user ON scan_jobs(user_id, created_at DESC);
CREATE INDEX idx_scan_jobs_status ON scan_jobs(status, priority);
CREATE INDEX idx_scan_jobs_target ON scan_jobs(target_id);
CREATE INDEX idx_scan_jobs_type ON scan_jobs(scan_type);

CREATE TABLE scan_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_job_id UUID NOT NULL REFERENCES scan_jobs(id) ON DELETE CASCADE,
    
    result_type VARCHAR(50) NOT NULL,
    
    summary JSONB,
    risk_score INTEGER,
    severity_counts JSONB,
    
    raw_data JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_risk_score CHECK (risk_score BETWEEN 0 AND 100)
);

CREATE INDEX idx_scan_results_job ON scan_results(scan_job_id);
CREATE INDEX idx_scan_results_type ON scan_results(result_type);

-- ============================================================================
-- Vulnerabilities
-- ============================================================================

CREATE TABLE vulnerabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_result_id UUID NOT NULL REFERENCES scan_results(id) ON DELETE CASCADE,
    scan_job_id UUID NOT NULL REFERENCES scan_jobs(id),
    
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    
    severity VARCHAR(20) NOT NULL,
    cvss_score DECIMAL(3, 1),
    cvss_vector VARCHAR(100),
    
    category VARCHAR(100),
    owasp_category VARCHAR(50),
    
    affected_component TEXT,
    proof_of_concept TEXT,
    
    remediation TEXT,
    references JSONB,
    
    status VARCHAR(20) DEFAULT 'open',
    
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_severity CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    CONSTRAINT valid_cvss CHECK (cvss_score BETWEEN 0.0 AND 10.0),
    CONSTRAINT valid_status CHECK (status IN ('open', 'confirmed', 'false_positive', 'fixed', 'accepted'))
);

CREATE INDEX idx_vulnerabilities_scan ON vulnerabilities(scan_job_id, severity);
CREATE INDEX idx_vulnerabilities_severity ON vulnerabilities(severity, discovered_at DESC);
CREATE INDEX idx_vulnerabilities_status ON vulnerabilities(status);

-- ============================================================================
-- Audit Logging
-- ============================================================================

CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),
    
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    
    target TEXT,
    
    authorization_proof TEXT,
    
    details JSONB,
    
    ip_address INET,
    user_agent TEXT,
    
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    
    severity VARCHAR(20) DEFAULT 'info',
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_status CHECK (status IN ('success', 'failure', 'error')),
    CONSTRAINT valid_severity CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info'))
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, timestamp DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, timestamp DESC);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_severity ON audit_logs(severity, timestamp DESC) WHERE severity IN ('critical', 'high');

-- ============================================================================
-- Reports
-- ============================================================================

CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_job_id UUID NOT NULL REFERENCES scan_jobs(id),
    
    report_type VARCHAR(50) NOT NULL,
    
    title VARCHAR(500) NOT NULL,
    
    content TEXT,
    pdf_path VARCHAR(500),
    
    executive_summary TEXT,
    recommendations TEXT,
    
    metadata JSONB,
    
    generated_by UUID REFERENCES users(id),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    version INTEGER DEFAULT 1
);

CREATE INDEX idx_reports_scan ON reports(scan_job_id, generated_at DESC);
CREATE INDEX idx_reports_type ON reports(report_type);

-- ============================================================================
-- Initial Data
-- ============================================================================

-- Create default organization
INSERT INTO organizations (name, subscription_tier, features, contact_email)
VALUES (
    'Default Organization',
    'enterprise',
    '["wifi_scan", "port_scan", "web_scan", "cloud_audit", "exploitation"]',
    'admin@cyper.security'
);

-- Create admin user (password: Admin123! - CHANGE THIS IN PRODUCTION)
INSERT INTO users (email, username, password_hash, full_name, organization_id, role, features, terms_accepted_at, terms_version)
SELECT 
    'admin@cyper.security',
    'admin',
    crypt('Admin123!', gen_salt('bf')),
    'System Administrator',
    id,
    'admin',
    '["wifi_scan", "port_scan", "web_scan", "cloud_audit", "exploitation", "admin"]',
    CURRENT_TIMESTAMP,
    '1.0'
FROM organizations
WHERE name = 'Default Organization';

-- ============================================================================
-- Functions & Triggers
-- ============================================================================

-- Update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables with updated_at
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scan_jobs_updated_at BEFORE UPDATE ON scan_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vulnerabilities_updated_at BEFORE UPDATE ON vulnerabilities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Row Level Security (Optional - uncomment if needed)
-- ============================================================================

-- Enable RLS
-- ALTER TABLE scan_jobs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE vulnerabilities ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- Policies (example)
-- CREATE POLICY org_isolation_scan_jobs ON scan_jobs
--     USING (organization_id = current_setting('app.current_org_id')::uuid);
