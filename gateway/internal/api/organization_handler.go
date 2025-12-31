package api

import (
	"database/sql"
	"net/http"

	"github.com/cyper-security/gateway/internal/rbac"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
	"go.uber.org/zap"
)

type OrganizationHandler struct {
	db     *sqlx.DB
	logger *zap.Logger
}

func NewOrganizationHandler(db *sqlx.DB, logger *zap.Logger) *OrganizationHandler {
	return &OrganizationHandler{
		db:     db,
		logger: logger,
	}
}

type CreateOrganizationRequest struct {
	Name string `json:"name" binding:"required"`
	Slug string `json:"slug" binding:"required"`
	Tier string `json:"tier"`
}

type Organization struct {
	ID               string `json:"id" db:"id"`
	Name             string `json:"name" db:"name"`
	Slug             string `json:"slug" db:"slug"`
	SubscriptionTier string `json:"subscription_tier" db:"subscription_tier"`
	IsActive         bool   `json:"is_active" db:"is_active"`
	CreatedAt        string `json:"created_at" db:"created_at"`
}

// CreateOrganization handles POST /api/v1/organizations
func (h *OrganizationHandler) CreateOrganization(c *gin.Context) {
	var req CreateOrganizationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	userID := c.GetString("user_id")
	if userID == "" {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User ID required"})
		return
	}

	// Create organization
	orgID := uuid.New()
	tier := req.Tier
	if tier == "" {
		tier = "free"
	}

	_, err := h.db.Exec(`
		INSERT INTO organizations (id, name, slug, subscription_tier)
		VALUES ($1, $2, $3, $4)
	`, orgID, req.Name, req.Slug, tier)

	if err != nil {
		h.logger.Error("Failed to create organization", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create organization"})
		return
	}

	// Add creator as owner
	_, err = h.db.Exec(`
		INSERT INTO organization_memberships (user_id, organization_id, role)
		VALUES ($1, $2, 'owner')
	`, userID, orgID)

	if err != nil {
		h.logger.Error("Failed to add owner membership", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create membership"})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"id":   orgID.String(),
		"name": req.Name,
		"slug": req.Slug,
		"tier": tier,
	})
}

// ListOrganizations handles GET /api/v1/organizations
func (h *OrganizationHandler) ListOrganizations(c *gin.Context) {
	userID := c.GetString("user_id")
	if userID == "" {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User ID required"})
		return
	}

	var orgs []struct {
		Organization
		Role string `json:"role" db:"role"`
	}

	err := h.db.Select(&orgs, `
		SELECT o.id, o.name, o.slug, o.subscription_tier, o.is_active, o.created_at, om.role
		FROM organizations o
		INNER JOIN organization_memberships om ON o.id = om.organization_id
		WHERE om.user_id = $1
		ORDER BY o.created_at DESC
	`, userID)

	if err != nil {
		h.logger.Error("Failed to list organizations", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to list organizations"})
		return
	}

	c.JSON(http.StatusOK, orgs)
}

// GetOrganization handles GET /api/v1/organizations/:id
func (h *OrganizationHandler) GetOrganization(c *gin.Context) {
	orgID := c.Param("id")
	userID := c.GetString("user_id")

	// Verify user has access to this organization
	var role string
	err := h.db.Get(&role, `
		SELECT role FROM organization_memberships
		WHERE user_id = $1 AND organization_id = $2
	`, userID, orgID)

	if err == sql.ErrNoRows {
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
		return
	}

	if err != nil {
		h.logger.Error("Failed to verify membership", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to verify access"})
		return
	}

	var org Organization
	err = h.db.Get(&org, `
		SELECT id, name, slug, subscription_tier, is_active, created_at
		FROM organizations
		WHERE id = $1
	`, orgID)

	if err != nil {
		h.logger.Error("Failed to get organization", zap.Error(err))
		c.JSON(http.StatusNotFound, gin.H{"error": "Organization not found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"organization": org,
		"role":         role,
	})
}

type InviteUserRequest struct {
	Email string `json:"email" binding:"required,email"`
	Role  string `json:"role" binding:"required"`
}

// InviteUser handles POST /api/v1/organizations/:id/invite
func (h *OrganizationHandler) InviteUser(c *gin.Context) {
	orgID := c.Param("id")

	var req InviteUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Validate role
	role := rbac.Role(req.Role)
	if !role.IsValid() {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid role"})
		return
	}

	// Find user by email
	var targetUserID string
	err := h.db.Get(&targetUserID, "SELECT id FROM users WHERE email = $1", req.Email)
	if err == sql.ErrNoRows {
		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		return
	}

	if err != nil {
		h.logger.Error("Failed to find user", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to find user"})
		return
	}

	// Add membership
	_, err = h.db.Exec(`
		INSERT INTO organization_memberships (user_id, organization_id, role)
		VALUES ($1, $2, $3)
		ON CONFLICT (user_id, organization_id) DO UPDATE SET role = $3
	`, targetUserID, orgID, req.Role)

	if err != nil {
		h.logger.Error("Failed to add membership", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to invite user"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "User invited successfully",
		"user_id": targetUserID,
		"role":    req.Role,
	})
}
