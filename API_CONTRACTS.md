# API Contracts

> [!NOTE]
> This document defines the API contracts for all service interfaces in the Cybersecurity Agent platform.
> - **REST API** (Go Gateway) - Primary HTTP/JSON interface
> - **gRPC API** (Go Gateway <-> Python Brain, Rust Core)
> - **WebSocket API** (Real-time updates)

---

## 📚 Table of Contents

- [REST API](#rest-api)
- [gRPC API](#grpc-api)
- [WebSocket API](#websocket-api)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## 🌐 REST API

**Base URL**: `https://api.cyper.security/v1`

**Authentication**: Bearer token (JWT) in `Authorization` header

```
Authorization: Bearer <jwt_token>
```

### Authentication & Authorization

#### POST `/auth/register`
Register a new user account.

**Request**:
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePassword123!",
  "full_name": "John Doe",
  "organization_id": "uuid-of-organization"
}
```

**Response**: `201 Created`
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "message": "User created successfully. Please accept terms of use."
}
```

---

#### POST `/auth/accept-terms`
Accept terms of use (required before any operations).

**Request**:
```json
{
  "user_id": "uuid",
  "terms_version": "1.0",
  "acceptance_ip": "192.168.1.1"
}
```

**Response**: `200 OK`
```json
{
  "accepted_at": "2025-12-30T15:00:00Z",
  "terms_version": "1.0"
}
```

---

#### POST `/auth/login`
Authenticate and receive JWT token.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response**: `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJl...",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "johndoe",
    "role": "analyst",
    "features": ["wifi_scan", "port_scan", "web_scan"],
    "organization_id": "uuid"
  }
}
```

---

#### POST `/auth/refresh`
Refresh access token.

**Request**:
```json
{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJl..."
}
```

**Response**: `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 3600
}
```

---

#### POST `/auth/logout`
Revoke session and invalidate tokens.

**Response**: `204 No Content`

---

#### GET `/auth/pulse`
Authorization pulse check (called periodically by client).

**Response**: `200 OK`
```json
{
  "authorized": true,
  "features": ["wifi_scan", "port_scan", "web_scan", "cloud_audit"],
  "expires_at": "2025-12-30T16:00:00Z",
  "next_check_in": 300
}
```

**Response** (if revoked): `403 Forbidden`
```json
{
  "error": "authorization_revoked",
  "message": "Your authorization has been revoked. Please contact your administrator."
}
```

---

### Scan Management

#### GET `/scans`
List all scan jobs for the authenticated user.

**Query Parameters**:
- `page` (int, default: 1)
- `limit` (int, default: 20, max: 100)
- `status` (string, optional: "pending", "running", "completed", "failed")
- `scan_type` (string, optional: "wifi", "port_scan", "web_vuln", etc.)
- `sort` (string, default: "-created_at")

**Response**: `200 OK`
```json
{
  "scans": [
    {
      "id": "uuid",
      "target": {
        "type": "wifi_network",
        "value": "MyWiFi-5G"
      },
      "scan_type": "wifi",
      "status": "completed",
      "progress": 100,
      "risk_score": 65,
      "vulnerabilities_count": 3,
      "created_at": "2025-12-30T14:00:00Z",
      "completed_at": "2025-12-30T14:05:23Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "total_pages": 3
  }
}
```

---

#### POST `/scans/wifi`
Initiate WiFi security scan.

**Request**:
```json
{
  "target": {
    "type": "wifi_network",
    "ssid": "MyWiFi-5G",
    "interface": "wlan0"
  },
  "configuration": {
    "scan_mode": "passive", // passive, active, aggressive
    "test_wps": true,
    "capture_handshake": false,
    "duration_seconds": 300
  },
  "priority": 5,
  "authorization_target_id": "uuid" // Reference to authorized_targets table
}
```

**Response**: `202 Accepted`
```json
{
  "scan_id": "uuid",
  "status": "pending",
  "message": "WiFi scan initiated",
  "estimated_duration": "5 minutes",
  "websocket_channel": "scan:uuid"
}
```

---

#### POST `/scans/network`
Initiate network port scan.

**Request**:
```json
{
  "target": {
    "type": "ip_range",
    "value": "192.168.1.0/24"
  },
  "configuration": {
    "scan_type": "syn", // syn, tcp_connect, udp, comprehensive
    "port_range": "1-65535",
    "service_detection": true,
    "os_detection": true,
    "aggressive_timing": false
  },
  "priority": 7,
  "authorization_target_id": "uuid"
}
```

**Response**: `202 Accepted`
```json
{
  "scan_id": "uuid",
  "status": "pending",
  "estimated_duration": "15 minutes"
}
```

---

#### POST `/scans/web`
Initiate web application security scan.

**Request**:
```json
{
  "target": {
    "type": "web_app",
    "url": "https://example.com"
  },
  "configuration": {
    "scan_depth": "thorough", // quick, standard, thorough
    "test_categories": ["sql_injection", "xss", "csrf", "security_headers"],
    "authentication": {
      "type": "basic", // basic, form, oauth
      "credentials": {
        "username": "testuser",
        "password": "testpass"
      }
    },
    "rate_limit": 10 // requests per second
  },
  "authorization_target_id": "uuid"
}
```

**Response**: `202 Accepted`
```json
{
  "scan_id": "uuid",
  "status": "pending",
  "message": "Web application scan initiated"
}
```

---

#### POST `/scans/cloud`
Initiate cloud security audit.

**Request**:
```json
{
  "target": {
    "type": "aws_account",
    "account_id": "123456789012"
  },
  "configuration": {
    "provider": "aws", // aws, azure, gcp
    "audit_types": ["iam", "s3_buckets", "security_groups", "compliance"],
    "compliance_frameworks": ["cis", "pci_dss"],
    "credentials": {
      "access_key_id": "AKIA...",
      "secret_access_key": "encrypted_value"
    }
  },
  "authorization_target_id": "uuid"
}
```

**Response**: `202 Accepted`
```json
{
  "scan_id": "uuid",
  "status": "pending"
}
```

---

#### GET `/scans/{scan_id}`
Get detailed scan information.

**Response**: `200 OK`
```json
{
  "id": "uuid",
  "target": {
    "type": "wifi_network",
    "ssid": "MyWiFi-5G"
  },
  "scan_type": "wifi",
  "status": "running",
  "progress": 65,
  "current_phase": "Analyzing encryption strength",
  "started_at": "2025-12-30T14:00:00Z",
  "estimated_completion": "2025-12-30T14:05:00Z",
  "configuration": { /* scan config */ },
  "results_summary": {
    "risk_score": 45,
    "vulnerabilities_count": 2,
    "severity_distribution": {
      "critical": 0,
      "high": 1,
      "medium": 1,
      "low": 0,
      "info": 3
    }
  }
}
```

---

#### DELETE `/scans/{scan_id}`
Stop/cancel a running scan.

**Response**: `200 OK`
```json
{
  "message": "Scan stopped successfully",
  "status": "stopped"
}
```

---

### Results & Vulnerabilities

#### GET `/scans/{scan_id}/results`
Get scan results.

**Response**: `200 OK`
```json
{
  "scan_id": "uuid",
  "results": [
    {
      "id": "uuid",
      "type": "wifi_finding",
      "ssid": "MyWiFi-5G",
      "bssid": "AA:BB:CC:DD:EE:FF",
      "security_type": "WPA2-PSK",
      "encryption": "AES/CCMP",
      "signal_strength": -45,
      "wps_enabled": true,
      "crackability_score": 65,
      "estimated_crack_time": "3-7 days with dictionary attack",
      "vulnerabilities": [
        {
          "title": "WPS Enabled",
          "severity": "medium",
          "description": "WiFi Protected Setup is enabled, allowing potential brute force attacks"
        }
      ]
    }
  ],
  "summary": {
    "total_findings": 1,
    "risk_score": 65
  }
}
```

---

#### GET `/scans/{scan_id}/vulnerabilities`
Get discovered vulnerabilities.

**Query Parameters**:
- `severity` (string, optional: "critical", "high", "medium", "low", "info")
- `status` (string, optional: "open", "confirmed", "fixed", "false_positive")

**Response**: `200 OK`
```json
{
  "vulnerabilities": [
    {
      "id": "uuid",
      "title": "SQL Injection in login form",
      "description": "The login endpoint is vulnerable to SQL injection attacks...",
      "severity": "critical",
      "cvss_score": 9.8,
      "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
      "category": "injection",
      "owasp_category": "A03",
      "affected_component": "POST /api/login",
      "proof_of_concept": "' OR '1'='1' -- ",
      "remediation": "Use parameterized queries...",
      "cves": ["CVE-2024-12345"],
      "exploits": [
        {
          "name": "SQLMap automated exploit",
          "difficulty": "easy",
          "metasploit_module": "exploit/multi/http/sql_injection"
        }
      ],
      "status": "open",
      "discovered_at": "2025-12-30T14:02:15Z"
    }
  ],
  "count": 1
}
```

---

#### PATCH `/vulnerabilities/{vuln_id}`
Update vulnerability status.

**Request**:
```json
{
  "status": "confirmed", // open, confirmed, false_positive, fixed, accepted
  "notes": "Confirmed after manual testing"
}
```

**Response**: `200 OK`
```json
{
  "id": "uuid",
  "status": "confirmed",
  "updated_at": "2025-12-30T15:00:00Z"
}
```

---

### Reports

#### GET `/scans/{scan_id}/reports`
List all reports for a scan.

**Response**: `200 OK`
```json
{
  "reports": [
    {
      "id": "uuid",
      "type": "executive",
      "title": "WiFi Security Assessment - MyWiFi-5G",
      "generated_at": "2025-12-30T14:10:00Z",
      "version": 1
    },
    {
      "id": "uuid",
      "type": "technical",
      "title": "Detailed Technical Report - MyWiFi-5G",
      "generated_at": "2025-12-30T14:10:05Z",
      "version": 1
    }
  ]
}
```

---

#### POST `/scans/{scan_id}/reports`
Generate a new report.

**Request**:
```json
{
  "type": "executive", // executive, technical, compliance, pdf
  "include_sections": ["summary", "findings", "recommendations"],
  "format": "markdown" // markdown, pdf, json
}
```

**Response**: `202 Accepted`
```json
{
  "report_id": "uuid",
  "status": "generating",
  "estimated_time": "30 seconds"
}
```

---

#### GET `/reports/{report_id}`
Get report content.

**Response**: `200 OK`
```json
{
  "id": "uuid",
  "type": "executive",
  "title": "WiFi Security Assessment - MyWiFi-5G",
  "content": "# Executive Summary\n\n...",
  "executive_summary": "The WiFi network 'MyWiFi-5G' has a medium risk score...",
  "recommendations": "1. Disable WPS\n2. Upgrade to WPA3...",
  "generated_at": "2025-12-30T14:10:00Z"
}
```

---

#### GET `/reports/{report_id}/download`
Download report as PDF.

**Response**: `200 OK`
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="report_uuid.pdf"

[PDF binary data]
```

---

### Monitoring

#### GET `/monitors`
List all continuous monitors.

**Response**: `200 OK`
```json
{
  "monitors": [
    {
      "id": "uuid",
      "name": "Production Network Monitor",
      "target": {
        "type": "ip_range",
        "value": "10.0.0.0/16"
      },
      "monitor_type": "network",
      "schedule": "0 */6 * * *", // Every 6 hours
      "is_active": true,
      "last_run_at": "2025-12-30T12:00:00Z",
      "next_run_at": "2025-12-30T18:00:00Z"
    }
  ]
}
```

---

#### POST `/monitors`
Create a new continuous monitor.

**Request**:
```json
{
  "name": "Production Network Monitor",
  "target_id": "uuid",
  "monitor_type": "network",
  "schedule": "0 */6 * * *",
  "alert_conditions": {
    "new_open_ports": true,
    "new_vulnerabilities": true,
    "risk_score_increase": 10
  }
}
```

**Response**: `201 Created`
```json
{
  "id": "uuid",
  "message": "Monitor created successfully",
  "next_run_at": "2025-12-30T18:00:00Z"
}
```

---

#### GET `/alerts`
Get security alerts.

**Query Parameters**:
- `severity` (string, optional)
- `resolved` (boolean, optional)
- `limit` (int, default: 50)

**Response**: `200 OK`
```json
{
  "alerts": [
    {
      "id": "uuid",
      "severity": "high",
      "title": "New critical vulnerability detected",
      "message": "SQL injection found in production API endpoint",
      "created_at": "2025-12-30T14:30:00Z",
      "acknowledged": false,
      "resolved": false,
      "alert_data": {
        "vulnerability_id": "uuid",
        "affected_url": "https://api.example.com/login"
      }
    }
  ],
  "unresolved_count": 3
}
```

---

#### PATCH `/alerts/{alert_id}/acknowledge`
Acknowledge an alert.

**Response**: `200 OK`
```json
{
  "id": "uuid",
  "acknowledged": true,
  "acknowledged_at": "2025-12-30T15:00:00Z"
}
```

---

### Audit Logs

#### GET `/audit/logs`
Retrieve audit logs (admin only).

**Query Parameters**:
- `user_id` (uuid, optional)
- `action` (string, optional)
- `severity` (string, optional)
- `start_date` (ISO 8601, optional)
- `end_date` (ISO 8601, optional)
- `limit` (int, default: 100)

**Response**: `200 OK`
```json
{
  "logs": [
    {
      "id": "123456",
      "user_id": "uuid",
      "action": "wifi_scan_initiated",
      "target": "MyWiFi-5G",
      "authorization_proof": "session:uuid",
      "status": "success",
      "severity": "info",
      "timestamp": "2025-12-30T14:00:00Z",
      "ip_address": "192.168.1.100",
      "details": {
        "scan_id": "uuid",
        "configuration": { /* ... */ }
      }
    }
  ],
  "pagination": {
    "limit": 100,
    "offset": 0,
    "total": 1523
  }
}
```

---

### Emergency Controls

#### POST `/emergency/kill-switch`
Activate emergency kill switch (admin only).

**Request**:
```json
{
  "reason": "Unauthorized activity detected",
  "confirmation": "I UNDERSTAND AND AUTHORIZE"
}
```

**Response**: `200 OK`
```json
{
  "message": "Kill switch engaged",
  "stopped_scans": 3,
  "closed_connections": 15,
  "incident_report_id": "uuid",
  "system_locked": true
}
```

---

## 🔌 gRPC API

Used for internal service communication (Go Gateway ↔ Python Brain ↔ Rust Core).

### Service Definitions

#### `ScanService.proto`

```protobuf
syntax = "proto3";

package cyper.scan;

service ScanService {
  rpc InitiateWiFiScan(WiFiScanRequest) returns (ScanResponse);
  rpc InitiatePortScan(PortScanRequest) returns (ScanResponse);
  rpc GetScanStatus(ScanStatusRequest) returns (ScanStatusResponse);
  rpc StopScan(StopScanRequest) returns (StopScanResponse);
}

message WiFiScanRequest {
  string scan_id = 1;
  string interface = 2;
  string ssid = 3;
  ScanMode mode = 4;
  ScanConfiguration config = 5;
}

message ScanConfiguration {
  int32 duration_seconds = 1;
  bool test_wps = 2;
  bool capture_handshake = 3;
}

enum ScanMode {
  PASSIVE = 0;
  ACTIVE = 1;
  AGGRESSIVE = 2;
}

message ScanResponse {
  string scan_id = 1;
  ScanStatus status = 2;
  string message = 3;
}

enum ScanStatus {
  PENDING = 0;
  RUNNING = 1;
  COMPLETED = 2;
  FAILED = 3;
  STOPPED = 4;
}

message ScanStatusRequest {
  string scan_id = 1;
}

message ScanStatusResponse {
  string scan_id = 1;
  ScanStatus status = 2;
  int32 progress_percentage = 3;
  string current_phase = 4;
  repeated Finding findings = 5;
}

message Finding {
  string id = 1;
  string type = 2;
  Severity severity = 3;
  string title = 4;
  string description = 5;
  map<string, string> metadata = 6;
}

enum Severity {
  INFO = 0;
  LOW = 1;
  MEDIUM = 2;
  HIGH = 3;
  CRITICAL = 4;
}
```

#### `AIService.proto`

```protobuf
syntax = "proto3";

package cyper.ai;

service AIService {
  rpc AnalyzeTarget(AnalyzeRequest) returns (AnalysisResponse);
  rpc GenerateReport(ReportRequest) returns (ReportResponse);
  rpc InterpretResults(InterpretRequest) returns (InterpretResponse);
}

message AnalyzeRequest {
  string target = 1;
  string scan_type = 2;
  map<string, string> context = 3;
}

message AnalysisResponse {
  string scan_plan = 1;
  repeated string recommended_tools = 2;
  int32 estimated_duration_seconds = 3;
  repeated string warnings = 4;
}

message ReportRequest {
  string scan_id = 1;
  ReportType type = 2;
  repeated string include_sections = 3;
}

enum ReportType {
  EXECUTIVE = 0;
  TECHNICAL = 1;
  COMPLIANCE = 2;
}

message ReportResponse {
  string report_id = 1;
  string content = 2;
  bytes pdf_data = 3;
}
```

---

## 🔔 WebSocket API

**Endpoint**: `wss://api.cyper.security/ws`

**Authentication**: Send JWT token in first message

### Connection Flow

```javascript
const ws = new WebSocket('wss://api.cyper.security/ws');

// 1. Authenticate
ws.send(JSON.stringify({
  type: 'auth',
  token: 'jwt_token_here'
}));

// 2. Subscribe to channels
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['scan:uuid', 'alerts']
}));

// 3. Receive updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

### Message Types

#### Scan Progress Updates

```json
{
  "type": "scan_progress",
  "scan_id": "uuid",
  "progress": 45,
  "current_phase": "Service Detection",
  "findings_count": 12,
  "timestamp": "2025-12-30T14:02:30Z"
}
```

#### New Vulnerability Discovered

```json
{
  "type": "vulnerability_found",
  "scan_id": "uuid",
  "vulnerability": {
    "id": "uuid",
    "title": "SQL Injection",
    "severity": "critical",
    "cvss_score": 9.8
  },
  "timestamp": "2025-12-30T14:03:15Z"
}
```

#### Scan Completed

```json
{
  "type": "scan_completed",
  "scan_id": "uuid",
  "status": "completed",
  "duration_seconds": 312,
  "results_summary": {
    "risk_score": 72,
    "vulnerabilities_count": 8,
    "critical": 1,
    "high": 3,
    "medium": 4
  },
  "timestamp": "2025-12-30T14:05:12Z"
}
```

#### Security Alert

```json
{
  "type": "alert",
  "alert": {
    "id": "uuid",
    "severity": "high",
    "title": "New open port detected",
    "message": "Port 22 (SSH) is now open on 192.168.1.100"
  },
  "timestamp": "2025-12-30T14:10:00Z"
}
```

#### Authorization Revoked

```json
{
  "type": "auth_revoked",
  "reason": "Central authorization check failed",
  "action_required": "logout",
  "timestamp": "2025-12-30T14:15:00Z"
}
```

---

## ⚠️ Error Handling

### Standard Error Response Format

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required",
    "details": "JWT token is missing or invalid",
    "request_id": "req_uuid",
    "timestamp": "2025-12-30T15:00:00Z"
  }
}
```

### HTTP Status Codes

| Code | Name | Usage |
|------|------|-------|
| 200 | OK | Successful request |
| 201 | Created | Resource created |
| 202 | Accepted | Async operation initiated |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing/invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource conflict (duplicate) |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily down |

### Error Codes

| Code | Description |
|------|-------------|
| `UNAUTHORIZED` | Authentication failed |
| `FORBIDDEN` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `VALIDATION_ERROR` | Request validation failed |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `AUTHORIZATION_REVOKED` | User authorization revoked |
| `FEATURE_NOT_ENABLED` | Feature not available for user |
| `TARGET_NOT_AUTHORIZED` | Target not in authorized list |
| `SCAN_FAILED` | Scan execution failed |
| `INTERNAL_ERROR` | Internal server error |

### Example Error Responses

#### Validation Error (422)
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "field_errors": [
        {
          "field": "target.ssid",
          "message": "SSID is required for WiFi scans"
        },
        {
          "field": "configuration.duration_seconds",
          "message": "Duration must be between 60 and 3600 seconds"
        }
      ]
    },
    "request_id": "req_uuid"
  }
}
```

#### Authorization Error (403)
```json
{
  "error": {
    "code": "FEATURE_NOT_ENABLED",
    "message": "WiFi scanning is not enabled for your account",
    "details": "Please upgrade to Professional tier or contact your administrator",
    "request_id": "req_uuid"
  }
}
```

#### Rate Limit (429)
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "details": "Rate limit: 100 requests per hour",
    "retry_after": 1823,
    "request_id": "req_uuid"
  }
}
```

---

## 🚦 Rate Limiting

### Default Rate Limits

| Tier | Requests/Hour | Concurrent Scans | WebSocket Connections |
|------|---------------|------------------|----------------------|
| Basic | 100 | 1 | 2 |
| Professional | 1,000 | 5 | 10 |
| Enterprise | 10,000 | 20 | 50 |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1735574400
```

---

## 🔐 Security Best Practices

### 1. Always Use HTTPS
All API calls must use HTTPS in production.

### 2. Rotate Tokens
Access tokens expire in 1 hour. Use refresh tokens to obtain new access tokens.

### 3. Validate Authorization
Check authorization before every sensitive operation:
- Scan initiation
- Vulnerability exploitation
- Report generation

### 4. Audit Logging
All API calls are logged with:
- User ID
- IP address
- Action performed
- Timestamp
- Authorization proof

### 5. Input Validation
All inputs are validated and sanitized server-side.

---

**API Version**: 1.0  
**Last Updated**: 2025-12-30  
**Status**: Planning Phase
