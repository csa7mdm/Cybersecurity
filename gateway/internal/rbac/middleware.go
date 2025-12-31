package rbac

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// RequirePermission returns a middleware that checks if the user has the required permission
func RequirePermission(perm Permission, logger *zap.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Get role from context (set by auth middleware)
		roleStr, exists := c.Get("user_role")
		if !exists {
			logger.Warn("No role found in context")
			c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
			c.Abort()
			return
		}

		role := Role(roleStr.(string))

		// Check permission
		if !role.HasPermission(perm) {
			logger.Warn("Permission denied",
				zap.String("role", string(role)),
				zap.String("required_permission", string(perm)),
			)
			c.JSON(http.StatusForbidden, gin.H{
				"error": "You do not have permission to perform this action",
			})
			c.Abort()
			return
		}

		c.Next()
	}
}

// RequireRole returns a middleware that checks if the user has one of the required roles
func RequireRole(allowedRoles ...Role) gin.HandlerFunc {
	return func(c *gin.Context) {
		roleStr, exists := c.Get("user_role")
		if !exists {
			c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
			c.Abort()
			return
		}

		role := Role(roleStr.(string))

		// Check if role is in allowed list
		for _, allowedRole := range allowedRoles {
			if role == allowedRole {
				c.Next()
				return
			}
		}

		c.JSON(http.StatusForbidden, gin.H{"error": "Insufficient role"})
		c.Abort()
	}
}

// RequireOrganizationContext ensures the request has organization context
func RequireOrganizationContext(logger *zap.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		orgID, exists := c.Get("organization_id")
		if !exists || orgID == "" {
			logger.Warn("No organization context found")
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "Organization context required",
			})
			c.Abort()
			return
		}

		c.Next()
	}
}
