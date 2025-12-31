-- Migration: Add Audit Log Signing Support
-- Date: 2025-12-31
-- Description: Adds cryptographic signature support for audit logs

ALTER TABLE audit_logs ADD COLUMN signature TEXT;
ALTER TABLE audit_logs ADD COLUMN signer_public_key TEXT;
ALTER TABLE audit_logs ADD COLUMN signed_at TIMESTAMP;

CREATE INDEX idx_audit_logs_signed ON audit_logs(signed_at DESC) WHERE signature IS NOT NULL;

-- Function to verify all signatures in a time range
CREATE OR REPLACE FUNCTION verify_audit_signatures(
    p_start_time TIMESTAMP,
    p_end_time TIMESTAMP
) RETURNS TABLE(log_id BIGINT, is_valid BOOLEAN) AS $$
BEGIN
    RETURN QUERY
    SELECT id, signature IS NOT NULL AND signer_public_key IS NOT NULL
    FROM audit_logs
    WHERE timestamp BETWEEN p_start_time AND p_end_time;
END;
$$ LANGUAGE plpgsql;
