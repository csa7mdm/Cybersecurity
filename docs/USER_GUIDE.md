# CyperSecurity Platform - User Guide

## 🚀 Getting Started

### What is CyperSecurity Platform?

CyperSecurity Platform is an AI-powered automated security testing platform that helps security teams discover vulnerabilities before attackers do.

**Key Features**:
- Network scanning (ports, services, OS detection)
- Web application security testing (OWASP Top 10)
- SQL injection detection
- Vulnerability intelligence (CVE/CVSS/MITRE ATT&CK)
- Professional PDF reports
- Team collaboration
- Integrations (Slack, Discord, PagerDuty)

---

## 📧 Creating Your Account

### 1. Sign Up

1. Go to `https://app.cypersecurity.com/signup`
2. Enter your email address
3. Create a strong password
4. Click "Create Account"

### 2. Verify Your Email

1. Check your inbox for verification email
2. Click "Verify Email Address" button
3. You'll be redirected to the onboarding wizard

### 3. Complete Onboarding

**Step 1: Welcome**
- Introduction to the platform

**Step 2: Organization Setup**
- Organization name (e.g., "Acme Security")
- Industry (Technology, Finance, Healthcare, etc.)
- Company size (1-10, 11-50, 51-200, 201-1000, 1000+)

**Step 3: Invite Your Team** (Optional)
- Add team member emails
- They'll receive invitation links

**Step 4: Activate Trial**
- Read and accept Terms of Service
- Activate your 14-day Pro trial
- Get 1,000 scans included

---

## 🔍 Running Your First Scan

### Network Scan with Nmap

**What it does**: Discovers open ports, services, and operating systems

**Steps**:
1. Click "New Scan" → "Network Scan"
2. Enter target (e.g., `scanme.nmap.org`)
3. Select scan type:
   - **Quick**: Top 100 ports
   - **Standard**: Top 1000 ports
   - **Comprehensive**: All 65,535 ports
4. Enable options:
   - ✅ Service Detection
   - ✅ Version Detection
   - ✅ OS Detection
5. Click "Start Scan"

**Results**: View open ports, running services, and identified vulnerabilities

### Web Application Scan with ZAP

**What it does**: Tests web applications for security vulnerabilities

**Steps**:
1. Click "New Scan" → "Web Scan"
2. Enter target URL (e.g., `https://example.com`)
3. Configure spider:
   - Max depth: 5
   - Max pages: 100
4. Enable active scan
5. Click "Start Scan"

**Results**: OWASP Top 10 vulnerabilities, severity ratings, remediation advice

### SQL Injection Test with SQLMap

**What it does**: Automatically detects SQL injection vulnerabilities

**Steps**:
1. Click "New Scan" → "SQL Injection Test"
2. Enter target URL with parameter (e.g., `https://example.com/page?id=1`)
3. Select HTTP method (GET/POST)
4. Set risk level (1-3)
5. Click "Start Scan"

**Results**: Injection points, database type, exploitability assessment

---

## 📊 Understanding Your Results

### Severity Levels

- **CRITICAL** (9.0-10.0 CVSS): Immediate action required
- **HIGH** (7.0-8.9): Fix as soon as possible
- **MEDIUM** (4.0-6.9): Schedule remediation
- **LOW** (0.1-3.9): Fix when convenient
- **INFORMATIONAL**: No immediate risk

### CVE & CVSS Scores

**CVE** (Common Vulnerabilities and Exposures): Unique identifier for vulnerabilities
- Example: CVE-2024-1234

**CVSS** (Common Vulnerability Scoring System): Severity score 0.0-10.0
- Calculated using attack vector, complexity, privileges required, user interaction, scope, and impact

### MITRE ATT&CK Mapping

Vulnerabilities are mapped to MITRE ATT&CK techniques:
- **T1190**: Exploit Public-Facing Application (SQL injection, RCE)
- **T1189**: Drive-by Compromise (XSS)
- **T1110**: Brute Force (weak authentication)

---

## 📄 Generating Reports

### PDF Reports

1. Open scan results
2. Click "Generate Report"
3. Select report type:
   - **Executive Summary**: High-level overview for stakeholders
   - **Technical Report**: Detailed findings for security teams
   - **Compliance Report**: Mapped to compliance frameworks
4. Customize:
   - Company logo
   - Report title
   - Include/exclude sections
5. Click "Generate PDF"

**Download**: Report is emailed and available in dashboard

---

## 🔔 Setting Up Notifications

### Email Notifications

**Enabled by default**. You'll receive emails for:
- Scan completion
- Critical findings (immediate)
- Payment confirmations
- Trial expiration (3 days before)

**Manage**: Settings → Notifications → Email Preferences

### Slack Integration

1. Go to Settings → Integrations → Slack
2. Click "Add to Slack"
3. Authorize CyperSecurity Platform
4. Select channel for notifications
5. Choose events:
   - ✅ Scan Complete
   - ✅ Critical Findings
   - ⬜ All Findings

### Discord Integration

1. Create webhook in Discord:
   - Server Settings → Integrations → Webhooks → New Webhook
2. Copy webhook URL
3. In CyperSecurity: Settings → Integrations → Discord
4. Paste webhook URL
5. Save

### PagerDuty (for Critical Alerts)

1. Get integration key from PagerDuty
2. Settings → Integrations → PagerDuty
3. Enter integration key
4. Critical findings will create incidents

### Custom Webhooks

1. Settings → Integrations → Webhooks
2. Click "Add Webhook"
3. Enter webhook URL
4. Select events to subscribe
5. Copy secret key (for signature verification)
6. Save

**Verify signatures** in your webhook handler using HMAC SHA-256

---

## 👥 Team Collaboration

### Inviting Team Members

1. Settings → Team
2. Click "Invite Member"
3. Enter email address
4. Select role:
   - **Admin**: Full access
   - **Member**: Run scans, view results
   - **Viewer**: View results only
5. Send invitation

### Managing Permissions

**Admin** can:
- Manage billing
- Invite/remove team members
- Configure integrations
- Delete scans

**Member** can:
- Run scans
- Generate reports
- View all findings

**Viewer** can:
- View scan results
- Download reports

---

## 💳 Billing & Subscriptions

### Plans

**Free** - $0/month
- 100 scans/month
- 30-day data retention
- Email support

**Pro** - $99/month
- 1,000 scans/month
- 90-day data retention
- Priority email support
- Slack/Discord integrations
- Team collaboration (5 members)

**Enterprise** - Custom pricing
- Unlimited scans
- Unlimited data retention
- Dedicated support
- SLA guarantee
- Custom integrations
- On-premise deployment option

### Upgrading Your Plan

1. Settings → Billing
2. Click "Upgrade Plan"
3. Select plan (Pro or Enterprise)
4. Enter payment details
5. Confirm subscription

### Usage Tracking

View remaining scans: Dashboard → Usage

---

## 🆘 Getting Help

**Documentation**: https://docs.cypersecurity.com  
**Knowledge Base**: https://kb.cypersecurity.com  
**Email Support**: support@cypersecurity.com  
**Status Page**: https://status.cypersecurity.com

**Response Times**:
- Free: 48 hours
- Pro: 24 hours
- Enterprise: 4 hours (SLA)

---

## 🔒 Security Best Practices

### Authorized Scanning Only

⚠️ **IMPORTANT**: Only scan systems you own or have explicit permission to test.

Unauthorized security testing is illegal and may result in:
- Criminal charges
- Account termination
- Legal liability

### Scan Responsibly

- Avoid scanning during business hours
- Use lower intensity for production systems
- Coordinate with system administrators
- Document scan authorizations

### Secure Your Account

- Use strong, unique passwords
- Enable two-factor authentication (Settings → Security)
- Review audit logs regularly
- Rotate API keys periodically

---

**Need more help?** Check our [Knowledge Base](https://kb.cypersecurity.com) or contact support@cypersecurity.com
