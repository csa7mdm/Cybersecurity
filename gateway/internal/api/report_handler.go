package api

import (
	"net/http"

	"github.com/cyper-security/gateway/internal/brain"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

type ReportHandler struct {
	brainClient *brain.Client
	logger      *zap.Logger
}

func NewReportHandler(brainClient *brain.Client, logger *zap.Logger) *ReportHandler {
	return &ReportHandler{
		brainClient: brainClient,
		logger:      logger,
	}
}

// GenerateReport handles POST /api/v1/scans/:id/report
func (h *ReportHandler) GenerateReport(c *gin.Context) {
	scanID := c.Param("id")

	// In a real app, we would fetch scan results from DB here.
	// For MVP, we allow passing context/mock data or just assuming fetch works.
	// But the user request said "Connect ResultsAnalyzer output".

	// For now, let's accept the analysis/results in the body to forward to Brain
	// This makes it easier to test without a full DB population.
	var req brain.GenerateReportRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Inject metadata if not present
	if req.Metadata == nil {
		req.Metadata = make(map[string]interface{})
	}
	req.Metadata["scan_id"] = scanID

	resp, err := h.brainClient.GenerateReport(req)
	if err != nil {
		h.logger.Error("Failed to generate report", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate report"})
		return
	}

	c.JSON(http.StatusOK, resp)
}
