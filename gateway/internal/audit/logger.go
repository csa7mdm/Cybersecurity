package audit

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/jmoiron/sqlx"
	"go.uber.org/zap"
)

type AuditLogger struct {
	db     *sqlx.DB
	logger *zap.Logger
}

func NewAuditLogger(db *sqlx.DB, logger *zap.Logger) *AuditLogger {
	return &AuditLogger{
		db:     db,
		logger: logger,
	}
}

type AuditLog struct {
	ID                 int64           `db:"id"`
	UserID             *string         `db:"user_id"`
	SessionID          *string         `db:"session_id"`
	Action             string          `db:"action"`
	ResourceType       *string         `db:"resource_type"`
	ResourceID         *string         `db:"resource_id"`
	Target             *string         `db:"target"`
	AuthorizationProof *string         `db:"authorization_proof"`
	Details            json.RawMessage `db:"details"`
	IPAddress          *string         `db:"ip_address"`
	UserAgent          *string         `db:"user_agent"`
	Status             string          `db:"status"`
	ErrorMessage       *string         `db:"error_message"`
	Severity           string          `db:"severity"`
	Timestamp          time.Time       `db:"timestamp"`
}

type LogParams struct {
	UserID             string
	SessionID          string
	Action             string
	ResourceType       string
	ResourceID         string
	Target             string
	AuthorizationProof string
	Details            map[string]interface{}
	IPAddress          string
	UserAgent          string
	Status             string
	ErrorMessage       string
	Severity           string
}

// Log creates an audit log entry
func (a *AuditLogger) Log(ctx context.Context, params LogParams) error {
	// Default values
	if params.Status == "" {
		params.Status = "success"
	}
	if params.Severity == "" {
		params.Severity = "info"
	}

	// Convert details to JSON
	var detailsJSON []byte
	var err error
	if params.Details != nil {
		detailsJSON, err = json.Marshal(params.Details)
		if err != nil {
			a.logger.Error("Failed to marshal audit log details", zap.Error(err))
			detailsJSON = []byte("{}")
		}
	} else {
		detailsJSON = []byte("{}")
	}

	query := `
		INSERT INTO audit_logs (
			user_id, session_id, action, resource_type, resource_id, 
			target, authorization_proof, details, ip_address, user_agent,
			status, error_message, severity, timestamp
		) VALUES (
			NULLIF($1, ''), NULLIF($2, ''), $3, NULLIF($4, ''), NULLIF($5, ''),
			NULLIF($6, ''), NULLIF($7, ''), $8, NULLIF($9, ''), NULLIF($10, ''),
			$11, NULLIF($12, ''), $13, NOW()
		)
	`

	_, err = a.db.ExecContext(ctx, query,
		params.UserID,
		params.SessionID,
		params.Action,
		params.ResourceType,
		params.ResourceID,
		params.Target,
		params.AuthorizationProof,
		detailsJSON,
		params.IPAddress,
		params.UserAgent,
		params.Status,
		params.ErrorMessage,
		params.Severity,
	)

	if err != nil {
		a.logger.Error("Failed to create audit log", zap.Error(err))
		return fmt.Errorf("failed to create audit log: %w", err)
	}

	a.logger.Debug("Audit log created",
		zap.String("action", params.Action),
		zap.String("user_id", params.UserID),
		zap.String("status", params.Status),
		zap.String("severity", params.Severity),
	)

	return nil
}

// LogAction is a helper for common logging patterns
func (a *AuditLogger) LogAction(ctx context.Context, userID, action, target string, details map[string]interface{}) error {
	return a.Log(ctx, LogParams{
		UserID:   userID,
		Action:   action,
		Target:   target,
		Details:  details,
		Status:   "success",
		Severity: "info",
	})
}

// LogSuccess logs a successful action
func (a *AuditLogger) LogSuccess(ctx context.Context, userID, action, resourceType, resourceID string, details map[string]interface{}) error {
	return a.Log(ctx, LogParams{
		UserID:       userID,
		Action:       action,
		ResourceType: resourceType,
		ResourceID:   resourceID,
		Details:      details,
		Status:       "success",
		Severity:     "info",
	})
}

// LogFailure logs a failed action
func (a *AuditLogger) LogFailure(ctx context.Context, userID, action, errorMsg string, details map[string]interface{}) error {
	return a.Log(ctx, LogParams{
		UserID:       userID,
		Action:       action,
		Details:      details,
		Status:       "failure",
		ErrorMessage: errorMsg,
		Severity:     "medium",
	})
}

// LogSecurityEvent logs a security-related event
func (a *AuditLogger) LogSecurityEvent(ctx context.Context, userID, action, target string, severity string, details map[string]interface{}) error {
	return a.Log(ctx, LogParams{
		UserID:   userID,
		Action:   action,
		Target:   target,
		Details:  details,
		Status:   "success",
		Severity: severity,
	})
}

// LogScanStart logs the start of a scan
func (a *AuditLogger) LogScanStart(ctx context.Context, userID, scanID, scanType, target, authProof string) error {
	return a.Log(ctx, LogParams{
		UserID:             userID,
		Action:             fmt.Sprintf("scan_%s_initiated", scanType),
		ResourceType:       "scan_job",
		ResourceID:         scanID,
		Target:             target,
		AuthorizationProof: authProof,
		Details: map[string]interface{}{
			"scan_id":   scanID,
			"scan_type": scanType,
			"target":    target,
		},
		Status:   "success",
		Severity: "info",
	})
}

// LogUnauthorizedAccess logs an unauthorized access attempt
func (a *AuditLogger) LogUnauthorizedAccess(ctx context.Context, ipAddress, action, target string) error {
	return a.Log(ctx, LogParams{
		Action:    action,
		Target:    target,
		IPAddress: ipAddress,
		Details: map[string]interface{}{
			"reason": "unauthorized_access_attempt",
		},
		Status:   "failure",
		Severity: "high",
	})
}

// GetRecentLogs retrieves recent audit logs
func (a *AuditLogger) GetRecentLogs(ctx context.Context, limit int) ([]AuditLog, error) {
	var logs []AuditLog
	query := `
		SELECT * FROM audit_logs
		ORDER BY timestamp DESC
		LIMIT $1
	`
	err := a.db.SelectContext(ctx, &logs, query, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get audit logs: %w", err)
	}
	return logs, nil
}

// GetLogsByUser retrieves audit logs for a specific user
func (a *AuditLogger) GetLogsByUser(ctx context.Context, userID string, limit int) ([]AuditLog, error) {
	var logs []AuditLog
	query := `
		SELECT * FROM audit_logs
		WHERE user_id = $1
		ORDER BY timestamp DESC
		LIMIT $2
	`
	err := a.db.SelectContext(ctx, &logs, query, userID, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get user audit logs: %w", err)
	}
	return logs, nil
}

// GetLogsByAction retrieves audit logs for a specific action
func (a *AuditLogger) GetLogsByAction(ctx context.Context, action string, limit int) ([]AuditLog, error) {
	var logs []AuditLog
	query := `
		SELECT * FROM audit_logs
		WHERE action = $1
		ORDER BY timestamp DESC
		LIMIT $2
	`
	err := a.db.SelectContext(ctx, &logs, query, action, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get action audit logs: %w", err)
	}
	return logs, nil
}

// GetHighSeverityLogs retrieves high and critical severity logs
func (a *AuditLogger) GetHighSeverityLogs(ctx context.Context, limit int) ([]AuditLog, error) {
	var logs []AuditLog
	query := `
		SELECT * FROM audit_logs
		WHERE severity IN ('high', 'critical')
		ORDER BY timestamp DESC
		LIMIT $1
	`
	err := a.db.SelectContext(ctx, &logs, query, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get high severity logs: %w", err)
	}
	return logs, nil
}
