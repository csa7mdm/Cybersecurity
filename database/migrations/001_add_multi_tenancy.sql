-- Migration: Add Multi-tenancy Support (Teams & Memberships)
-- Date: 2025-12-31
-- Description: Extends the existing schema with teams and role-based memberships for SaaS multi-tenancy

-- ============================================================================
-- Teams within Organizations
-- ============================================================================

CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(organization_id, name)
);

CREATE INDEX idx_teams_org ON teams(organization_id);

-- ============================================================================
-- Organization Memberships (RBAC)
-- ============================================================================

CREATE TABLE organization_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_role CHECK (role IN ('owner', 'admin', 'scanner', 'viewer')),
    UNIQUE(user_id, organization_id)
);

CREATE INDEX idx_memberships_user ON organization_memberships(user_id);
CREATE INDEX idx_memberships_org ON organization_memberships(organization_id);
CREATE INDEX idx_memberships_role ON organization_memberships(organization_id, role);

-- ============================================================================
-- Team Memberships
-- ============================================================================

CREATE TABLE team_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, team_id)
);

CREATE INDEX idx_team_memberships_user ON team_memberships(user_id);
CREATE INDEX idx_team_memberships_team ON team_memberships(team_id);

-- ============================================================================
-- Add organization_id to remaining tables
-- ============================================================================

-- Add to scan_results if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='scan_results' AND column_name='organization_id') THEN
        ALTER TABLE scan_results ADD COLUMN organization_id UUID REFERENCES organizations(id);
        
        -- Backfill from scan_jobs
        UPDATE scan_results sr
        SET organization_id = sj.organization_id
        FROM scan_jobs sj
        WHERE sr.scan_job_id = sj.id;
    END IF;
END $$;

-- Add to vulnerabilities if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='vulnerabilities' AND column_name='organization_id') THEN
        ALTER TABLE vulnerabilities ADD COLUMN organization_id UUID REFERENCES organizations(id);
        
        -- Backfill from scan_jobs
        UPDATE vulnerabilities v
        SET organization_id = sj.organization_id
        FROM scan_jobs sj
        WHERE v.scan_job_id = sj.id;
    END IF;
END $$;

-- Add to reports if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='reports' AND column_name='organization_id') THEN
        ALTER TABLE reports ADD COLUMN organization_id UUID REFERENCES organizations(id);
        
        -- Backfill from scan_jobs
        UPDATE reports r
        SET organization_id = sj.organization_id
        FROM scan_jobs sj
        WHERE r.scan_job_id = sj.id;
    END IF;
END $$;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_scan_results_org ON scan_results(organization_id);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_org ON vulnerabilities(organization_id);
CREATE INDEX IF NOT EXISTS idx_reports_org ON reports(organization_id);

-- ============================================================================
-- Row-Level Security Policies
-- ============================================================================

-- Enable RLS on multi-tenant tables
ALTER TABLE scan_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scan_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE vulnerabilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_memberships ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see data from their organization
CREATE POLICY org_isolation_scan_jobs ON scan_jobs
    FOR ALL
    USING (organization_id = current_setting('app.current_org_id', true)::UUID);

CREATE POLICY org_isolation_scan_results ON scan_results
    FOR ALL
    USING (organization_id = current_setting('app.current_org_id', true)::UUID);

CREATE POLICY org_isolation_vulnerabilities ON vulnerabilities
    FOR ALL
    USING (organization_id = current_setting('app.current_org_id', true)::UUID);

CREATE POLICY org_isolation_reports ON reports
    FOR ALL
    USING (organization_id = current_setting('app.current_org_id', true)::UUID);

CREATE POLICY org_isolation_teams ON teams
    FOR ALL
    USING (organization_id = current_setting('app.current_org_id', true)::UUID);

CREATE POLICY org_isolation_memberships ON organization_memberships
    FOR ALL
    USING (organization_id = current_setting('app.current_org_id', true)::UUID);

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function to set current organization context
CREATE OR REPLACE FUNCTION set_current_org(org_id UUID)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_org_id', org_id::TEXT, false);
END;
$$ LANGUAGE plpgsql;

-- Function to get user's role in current organization
CREATE OR REPLACE FUNCTION get_user_role(p_user_id UUID, p_org_id UUID)
RETURNS VARCHAR AS $$
DECLARE
    user_role VARCHAR;
BEGIN
    SELECT role INTO user_role
    FROM organization_memberships
    WHERE user_id = p_user_id AND organization_id = p_org_id;
    
    RETURN COALESCE(user_role, 'none');
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Update Triggers
-- ============================================================================

CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memberships_updated_at BEFORE UPDATE ON organization_memberships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Migrate Existing Data
-- ============================================================================

-- Create default "owner" membership for existing users
INSERT INTO organization_memberships (user_id, organization_id, role)
SELECT u.id, u.organization_id, 
    CASE 
        WHEN u.role = 'admin' THEN 'owner'
        WHEN u.role = 'analyst' THEN 'scanner'
        ELSE 'viewer'
    END
FROM users u
WHERE u.organization_id IS NOT NULL
ON CONFLICT (user_id, organization_id) DO NOTHING;
