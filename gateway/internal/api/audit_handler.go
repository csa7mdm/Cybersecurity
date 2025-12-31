package api

import (
	"net/http"
	"time"

	"github.com/cyper-security/gateway/internal/audit"
	"github.com/gin-gonic/gin"
	"github.com/jmoiron/sqlx"
	"go.uber.org/zap"
)

type AuditHandler struct {
	db     *sqlx.DB
	logger *zap.Logger
	signer *audit.AuditSigner
}

func NewAuditHandler(db *sqlx.DB, logger *zap.Logger) (*AuditHandler, error) {
	signer, err := audit.NewAuditSigner(logger)
	if err != nil {
		return nil, err
	}

	return &AuditHandler{
		db:     db,
		logger: logger,
		signer: signer,
	}, nil
}

// ExportAuditLogs handles GET /api/v1/audit/export
func (h *AuditHandler) ExportAuditLogs(c *gin.Context) {
	// Parse time range
	startTimeStr := c.Query("start_time") // ISO 8601 format
	endTimeStr := c.Query("end_time")

	if startTimeStr == "" || endTimeStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "start_time and end_time required"})
		return
	}

	startTime, err := time.Parse(time.RFC3339, startTimeStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid start_time format"})
		return
	}

	endTime, err := time.Parse(time.RFC3339, endTimeStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid end_time format"})
		return
	}

	// Fetch audit logs
	var logs []audit.AuditLog
	err = h.db.Select(&logs, `
		SELECT * FROM audit_logs
		WHERE timestamp BETWEEN $1 AND $2
		ORDER BY timestamp DESC
	`, startTime, endTime)

	if err != nil {
		h.logger.Error("Failed to export audit logs", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to export logs"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"logs":  logs,
		"count": len(logs),
		"range": gin.H{
			"start": startTime,
			"end":   endTime,
		},
	})
}

// VerifySignature handles POST /api/v1/audit/verify
func (h *AuditHandler) VerifySignature(c *gin.Context) {
	var req struct {
		LogID int64 `json:"log_id" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Fetch log
	var log audit.AuditLog
	err := h.db.Get(&log, "SELECT * FROM audit_logs WHERE id = $1", req.LogID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Log not found"})
		return
	}

	// Check if signed
	if log.Signature == nil || log.SignerPublicKey == nil {
		c.JSON(http.StatusOK, gin.H{
			"signed":   false,
			"log_id":   req.LogID,
			"verified": false,
		})
		return
	}

	// Create signable version
	signableLog := &audit.SignableAuditLog{
		ID:           log.ID,
		UserID:       stringPtrOrEmpty(log.UserID),
		Action:       log.Action,
		ResourceType: stringPtrOrEmpty(log.ResourceType),
		ResourceID:   stringPtrOrEmpty(log.ResourceID),
		Target:       stringPtrOrEmpty(log.Target),
		Status:       log.Status,
		IPAddress:    stringPtrOrEmpty(log.IPAddress),
		Timestamp:    log.Timestamp,
	}

	// Verify signature
	valid, err := h.signer.VerifySignature(signableLog, *log.Signature, *log.SignerPublicKey)
	if err != nil {
		h.logger.Error("Failed to verify signature", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Verification failed"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"signed":     true,
		"verified":   valid,
		"log_id":     req.LogID,
		"signed_at":  log.SignedAt,
		"public_key": *log.SignerPublicKey,
	})
}

func stringPtrOrEmpty(s *string) string {
	if s == nil {
		return ""
	}
	return *s
}
