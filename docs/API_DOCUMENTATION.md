# CyperSecurity Platform - API Documentation

## Overview

The CyperSecurity Platform API allows you to programmatically run scans, retrieve results, and manage your account.

**Base URL**: `https://api.cypersecurity.com/v1`  
**Authentication**: API Key (Header: `X-API-Key`)  
**Format**: JSON

---

## Authentication

### Getting Your API Key

1. Log in to dashboard
2. Settings → API Keys
3. Click "Generate New Key"
4. Copy and save securely (shown once)

### Using API Keys

Include in all requests:

```bash
curl -H "X-API-Key: your_api_key_here" \
  https://api.cypersecurity.com/v1/scans
```

---

## Endpoints

### Scans

#### List Scans

```http
GET /scans
```

**Query Parameters**:
- `limit` (integer): Results per page (default: 20, max: 100)
- `offset` (integer): Pagination offset
- `status` (string): Filter by status (`pending`, `running`, `completed`, `failed`)

**Response**:
```json
{
  "scans": [
    {
      "id": "scan_123abc",
      "target": "example.com",
      "type": "nmap",
      "status": "completed",
      "created_at": "2024-12-31T10:00:00Z",
      "completed_at": "2024-12-31T10:05:23Z",
      "findings_count": 5,
      "critical_count": 1
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

#### Create Scan

```http
POST /scans
```

**Request Body**:
```json
{
  "target": "scanme.nmap.org",
  "type": "nmap",
  "options": {
    "ports": "1-1000",
    "service_detection": true,
    "os_detection": true
  }
}
```

**Scan Types**:
- `nmap`: Network scan
- `zap`: Web application scan
- `sqlmap`: SQL injection test

**Response**:
```json
{
  "id": "scan_456def",
  "target": "scanme.nmap.org",
  "type": "nmap",
  "status": "pending",
  "created_at": "2024-12-31T12:00:00Z"
}
```

#### Get Scan Details

```http
GET /scans/{scan_id}
```

**Response**:
```json
{
  "id": "scan_123abc",
  "target": "example.com",
  "type": "nmap",
  "status": "completed",
  "results": {
    "services": [
      {
        "port": 80,
        "protocol": "tcp",
        "service": "http",
        "version": "Apache 2.4.41"
      }
    ],
    "vulnerabilities": [
      {
        "title": "Outdated Apache Version",
        "severity": "medium",
        "cvss_score": 5.3,
        "cve_id": "CVE-2021-1234"
      }
    ]
  }
}
```

### Reports

#### Generate Report

```http
POST /scans/{scan_id}/report
```

**Request Body**:
```json
{
  "format": "pdf",
  "type": "technical"
}
```

**Response**:
```json
{
  "report_id": "report_789xyz",
  "status": "generating",
  "download_url": null
}
```

#### Download Report

```http
GET /reports/{report_id}/download
```

Returns PDF file.

### Webhooks

#### List Webhooks

```http
GET /webhooks
```

#### Create Webhook

```http
POST /webhooks
```

**Request Body**:
```json
{
  "url": "https://your-server.com/webhook",
  "events": [
    "scan.completed",
    "vulnerability.found"
  ],
  "secret": "your_webhook_secret"
}
```

**Response**:
```json
{
  "id": "webhook_abc123",
  "url": "https://your-server.com/webhook",
  "events": ["scan.completed", "vulnerability.found"],
  "created_at": "2024-12-31T12:00:00Z"
}
```

### Organizations

#### Get Organization

```http
GET /organization
```

#### Update Organization

```http
PATCH /organization
```

**Request Body**:
```json
{
  "name": "Acme Security",
  "industry": "technology"
}
```

### Team

#### List Team Members

```http
GET /team/members
```

#### Invite Member

```http
POST /team/members
```

**Request Body**:
```json
{
  "email": "teammate@example.com",
  "role": "member"
}
```

---

## Webhook Events

### Event Types

- `scan.started`: Scan initiated
- `scan.completed`: Scan finished successfully
- `scan.failed`: Scan encountered error
- `vulnerability.found`: Vulnerability discovered
- `critical.finding`: Critical severity finding
- `payment.success`: Payment processed
- `payment.failed`: Payment failed
- `trial.expiring`: Trial ending in 3 days

### Payload Format

```json
{
  "event": "scan.completed",
  "timestamp": 1704024000,
  "data": {
    "scan_id": "scan_123abc",
    "target": "example.com",
    "findings_count": 5,
    "critical_count": 1
  }
}
```

### Signature Verification

Verify webhook authenticity using HMAC SHA-256:

**Python Example**:
```python
import hmac
import hashlib
import json

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        json.dumps(payload, sort_keys=True).encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)

# In your webhook handler
signature = request.headers.get('X-Webhook-Signature')
if verify_webhook(payload, signature, webhook_secret):
    # Process webhook
    pass
```

**Node.js Example**:
```javascript
const crypto = require('crypto');

function verifyWebhook(payload, signature, secret) {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(JSON.stringify(payload))
    .digest('hex');
    
  return crypto.timingSafeEqual(
    Buffer.from(expected),
    Buffer.from(signature)
  );
}
```

---

## Rate Limits

- **Free**: 100 requests/hour
- **Pro**: 1,000 requests/hour
- **Enterprise**: 10,000 requests/hour

**Headers**:
- `X-RateLimit-Limit`: Requests allowed per hour
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Timestamp when limit resets

**429 Too Many Requests** if exceeded.

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Target parameter is required",
    "details": {
      "field": "target"
    }
  }
}
```

### Error Codes

- `invalid_request`: Malformed request
- `authentication_failed`: Invalid API key
- `insufficient_quota`: Scan limit exceeded
- `not_found`: Resource doesn't exist
- `rate_limit_exceeded`: Too many requests
- `internal_error`: Server error

---

## Code Examples

### Python

```python
import requests

API_KEY = "your_api_key"
BASE_URL = "https://api.cypersecurity.com/v1"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Create scan
response = requests.post(
    f"{BASE_URL}/scans",
    headers=headers,
    json={
        "target": "example.com",
        "type": "nmap",
        "options": {
            "ports": "1-1000",
            "service_detection": True
        }
    }
)

scan = response.json()
scan_id = scan["id"]

# Get results
response = requests.get(
    f"{BASE_URL}/scans/{scan_id}",
    headers=headers
)

results = response.json()
print(f"Found {results['findings_count']} vulnerabilities")
```

### JavaScript

```javascript
const API_KEY = 'your_api_key';
const BASE_URL = 'https://api.cypersecurity.com/v1';

const headers = {
  'X-API-Key': API_KEY,
  'Content-Type': 'application/json'
};

// Create scan
const createScan = async () => {
  const response = await fetch(`${BASE_URL}/scans`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      target: 'example.com',
      type: 'zap',
      options: {
        spider: true,
        active_scan: true
      }
    })
  });
  
  const scan = await response.json();
  return scan.id;
};

// Get results
const getResults = async (scanId) => {
  const response = await fetch(`${BASE_URL}/scans/${scanId}`, {
    headers
  });
  
  return await response.json();
};
```

---

## Best Practices

1. **Store API keys securely** (environment variables, secret managers)
2. **Implement exponential backoff** for retries
3. **Verify webhook signatures** for security
4. **Cache results** to reduce API calls
5. **Handle rate limits** gracefully
6. **Use HTTPS only** for all requests

---

**Need help?** Contact api-support@cypersecurity.com
