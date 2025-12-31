package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	// HTTP metrics
	HTTPRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "cypersecurity_http_requests_total",
			Help: "Total number of HTTP requests",
		},
		[]string{"method", "endpoint", "status"},
	)

	HTTPRequestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "cypersecurity_http_request_duration_seconds",
			Help:    "HTTP request duration in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"method", "endpoint"},
	)

	// Business metrics
	ScansTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "cypersecurity_scans_total",
			Help: "Total number of scans created",
		},
		[]string{"scan_type", "organization_id"},
	)

	ScansActive = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "cypersecurity_scans_active",
			Help: "Number of currently active scans",
		},
	)

	ReportsGenerated = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "cypersecurity_reports_generated_total",
			Help: "Total number of reports generated",
		},
	)

	// Auth metrics
	AuthAttempts = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "cypersecurity_auth_attempts_total",
			Help: "Total authentication attempts",
		},
		[]string{"status"}, // success, failure
	)

	ActiveSessions = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "cypersecurity_active_sessions",
			Help: "Number of active user sessions",
		},
	)

	// Emergency stop
	EmergencyStopActive = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "cypersecurity_emergency_stop_active",
			Help: "Whether emergency stop is currently active (1=active, 0=inactive)",
		},
	)

	// Audit logs
	AuditLogsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "cypersecurity_audit_logs_total",
			Help: "Total audit logs created",
		},
		[]string{"severity", "action"},
	)

	AuditLogsSignedTotal = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "cypersecurity_audit_logs_signed_total",
			Help: "Total audit logs successfully signed",
		},
	)
)
