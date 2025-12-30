package api

import (
	"net/http"

	"github.com/cyper-security/gateway/internal/auth"
	"github.com/cyper-security/gateway/internal/audit"
	"github.com/gin-gonic/gin"
)

type AuthHandler struct {
	authService *auth.AuthService
	auditLogger *audit.AuditLogger
}

func NewAuthHandler(authService *auth.AuthService, auditLogger *audit.AuditLogger) *AuthHandler {
	return &AuthHandler{
		authService: authService,
		auditLogger: auditLogger,
	}
}

// Register handler
func (h *AuthHandler) Register(c *gin.Context) {
	var req auth.RegisterRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	user, err := h.authService.Register(c.Request.Context(), req)
	if err != nil {
		h.auditLogger.LogFailure(c.Request.Context(), "", "user_registration", err.Error(), map[string]interface{}{
			"email": req.Email,
		})
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to register user"})
		return
	}

	h.auditLogger.LogSuccess(c.Request.Context(), user.ID, "user_registration", "user", user.ID, map[string]interface{}{
		"email":    user.Email,
		"username": user.Username,
	})

	c.JSON(http.StatusCreated, gin.H{
		"user_id": user.ID,
		"email":   user.Email,
		"message": "User created successfully. Please accept terms of use.",
	})
}

// Login handler
func (h *AuthHandler) Login(c *gin.Context) {
	var req auth.LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	ipAddress := c.ClientIP()
	userAgent := c.GetHeader("User-Agent")

	loginResp, err := h.authService.Login(c.Request.Context(), req, ipAddress, userAgent)
	if err != nil {
		h.auditLogger.LogFailure(c.Request.Context(), "", "login_attempt", err.Error(), map[string]interface{}{
			"email":      req.Email,
			"ip_address": ipAddress,
		})
		c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid credentials"})
		return
	}

	h.auditLogger.LogSuccess(c.Request.Context(), loginResp.User.ID, "login_success", "session", "", map[string]interface{}{
		"email":      loginResp.User.Email,
		"ip_address": ipAddress,
	})

	c.JSON(http.StatusOK, loginResp)
}

// Logout handler
func (h *AuthHandler) Logout(c *gin.Context) {
	userID := c.GetString("user_id")
	
	// TODO: Revoke session in database
	
	h.auditLogger.LogSuccess(c.Request.Context(), userID, "logout", "session", "", nil)
	
	c.JSON(http.StatusNoContent, nil)
}

// AcceptTerms handler
func (h *AuthHandler) AcceptTerms(c *gin.Context) {
	var req struct {
		UserID        string `json:"user_id" binding:"required"`
		TermsVersion  string `json:"terms_version" binding:"required"`
		AcceptanceIP  string `json:"acceptance_ip"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// TODO: Update user with terms acceptance
	
	h.auditLogger.LogSecurityEvent(c.Request.Context(), req.UserID, "terms_accepted", "", "info", map[string]interface{}{
		"terms_version": req.TermsVersion,
		"ip_address":    req.AcceptanceIP,
	})

	c.JSON(http.StatusOK, gin.H{
		"accepted_at":   "2025-12-30T15:00:00Z",
		"terms_version": req.TermsVersion,
	})
}

// AuthPulse handler
func (h *AuthHandler) AuthPulse(c *gin.Context) {
	userID := c.GetString("user_id")
	features := c.GetStringSlice("features")

	// TODO: Check with central authorization server
	
	// Log pulse check
	h.auditLogger.LogAction(c.Request.Context(), userID, "authorization_pulse", "", nil)

	c.JSON(http.StatusOK, gin.H{
		"authorized":    true,
		"features":      features,
		"expires_at":    "2025-12-30T16:00:00Z",
		"next_check_in": 300,
	})
}
