package rbac

// Role represents a user's role within an organization
type Role string

const (
	RoleOwner   Role = "owner"
	RoleAdmin   Role = "admin"
	RoleScanner Role = "scanner"
	RoleViewer  Role = "viewer"
)

// Permission represents an action that can be performed
type Permission string

const (
	// Organization management
	PermManageOrganization Permission = "manage:organization"
	PermViewOrganization   Permission = "view:organization"
	PermInviteUsers        Permission = "invite:users"
	PermRemoveUsers        Permission = "remove:users"

	// Scan management
	PermCreateScan Permission = "create:scan"
	PermViewScan   Permission = "view:scan"
	PermDeleteScan Permission = "delete:scan"
	PermStopScan   Permission = "stop:scan"

	// Report management
	PermGenerateReport Permission = "generate:report"
	PermViewReport     Permission = "view:report"
	PermDeleteReport   Permission = "delete:report"

	// Team management
	PermManageTeams Permission = "manage:teams"
	PermViewTeams   Permission = "view:teams"
)

// rolePermissions maps roles to their allowed permissions
var rolePermissions = map[Role][]Permission{
	RoleOwner: {
		// Full access
		PermManageOrganization,
		PermViewOrganization,
		PermInviteUsers,
		PermRemoveUsers,
		PermCreateScan,
		PermViewScan,
		PermDeleteScan,
		PermStopScan,
		PermGenerateReport,
		PermViewReport,
		PermDeleteReport,
		PermManageTeams,
		PermViewTeams,
	},
	RoleAdmin: {
		// Admin access (no org deletion, but can manage most things)
		PermViewOrganization,
		PermInviteUsers,
		PermCreateScan,
		PermViewScan,
		PermDeleteScan,
		PermStopScan,
		PermGenerateReport,
		PermViewReport,
		PermDeleteReport,
		PermManageTeams,
		PermViewTeams,
	},
	RoleScanner: {
		// Can run scans and view results
		PermViewOrganization,
		PermCreateScan,
		PermViewScan,
		PermStopScan,
		PermGenerateReport,
		PermViewReport,
		PermViewTeams,
	},
	RoleViewer: {
		// Read-only access
		PermViewOrganization,
		PermViewScan,
		PermViewReport,
		PermViewTeams,
	},
}

// HasPermission checks if a role has a specific permission
func (r Role) HasPermission(perm Permission) bool {
	perms, exists := rolePermissions[r]
	if !exists {
		return false
	}

	for _, p := range perms {
		if p == perm {
			return true
		}
	}
	return false
}

// IsValid checks if a role is valid
func (r Role) IsValid() bool {
	_, exists := rolePermissions[r]
	return exists
}

// GetPermissions returns all permissions for a role
func (r Role) GetPermissions() []Permission {
	return rolePermissions[r]
}
