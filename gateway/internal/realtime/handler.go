package realtime

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
	"go.uber.org/zap"
)

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		// TODO: Implement proper origin checking
		return true
	},
}

// Handler handles WebSocket connections
type Handler struct {
	hub    *Hub
	logger *zap.Logger
}

// NewHandler creates a new WebSocket handler
func NewHandler(hub *Hub, logger *zap.Logger) *Handler {
	return &Handler{
		hub:    hub,
		logger: logger,
	}
}

// HandleWebSocket handles WebSocket upgrade requests
func (h *Handler) HandleWebSocket(c *gin.Context) {
	// Get user ID from context (set by auth middleware)
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
		return
	}

	// Upgrade connection to WebSocket
	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		h.logger.Error("Failed to upgrade connection", zap.Error(err))
		return
	}

	// Register client
	client := h.hub.RegisterClient(userID.(string), conn)

	// Start read and write pumps
	go client.WritePump()
	go client.ReadPump()

	h.logger.Info("WebSocket connection established",
		zap.String("user_id", userID.(string)),
		zap.String("client_id", client.ID),
	)
}

// BroadcastScanProgress broadcasts scan progress update
func (h *Handler) BroadcastScanProgress(userID, scanID string, progress int, currentPhase string) {
	h.hub.BroadcastToUser(userID, "scan_progress", map[string]interface{}{
		"scan_id":       scanID,
		"progress":      progress,
		"current_phase": currentPhase,
	})
}

// BroadcastScanComplete broadcasts scan completion
func (h *Handler) BroadcastScanComplete(userID, scanID string, results map[string]interface{}) {
	h.hub.BroadcastToUser(userID, "scan_complete", map[string]interface{}{
		"scan_id": scanID,
		"results": results,
	})
}

// BroadcastVulnerability broadcasts new vulnerability found
func (h *Handler) BroadcastVulnerability(userID, scanID string, vulnerability map[string]interface{}) {
	h.hub.BroadcastToUser(userID, "vulnerability_found", map[string]interface{}{
		"scan_id":       scanID,
		"vulnerability": vulnerability,
	})
}

// BroadcastAlert broadcasts security alert
func (h *Handler) BroadcastAlert(userID string, alert map[string]interface{}) {
	h.hub.BroadcastToUser(userID, "alert", alert)
}

// BroadcastSystemStatus broadcasts system status
func (h *Handler) BroadcastSystemStatus(status map[string]interface{}) {
	h.hub.Broadcast("system_status", status)
}
