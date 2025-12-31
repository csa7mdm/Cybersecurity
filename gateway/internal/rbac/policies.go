package rbac

// Policy helpers for common permission checks

// CanCreateScan checks if a role can create scans
func CanCreateScan(role Role) bool {
	return role.HasPermission(PermCreateScan)
}

// CanViewScan checks if a role can view scans
func CanViewScan(role Role) bool {
	return role.HasPermission(PermViewScan)
}

// CanDeleteScan checks if a role can delete scans
func CanDeleteScan(role Role) bool {
	return role.HasPermission(PermDeleteScan)
}

// CanGenerateReport checks if a role can generate reports
func CanGenerateReport(role Role) bool {
	return role.HasPermission(PermGenerateReport)
}

// CanManageOrganization checks if a role can manage the organization
func CanManageOrganization(role Role) bool {
	return role.HasPermission(PermManageOrganization)
}

// CanInviteUsers checks if a role can invite users
func CanInviteUsers(role Role) bool {
	return role.HasPermission(PermInviteUsers)
}

// Can RemoveUsers checks if a role can remove users
func CanRemoveUsers(role Role) bool {
	return role.HasPermission(PermRemoveUsers)
}

// CanManageTeams checks if a role can manage teams
func CanManageTeams(role Role) bool {
	return role.HasPermission(PermManageTeams)
}
