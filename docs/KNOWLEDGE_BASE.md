# Knowledge Base - Common Workflows

## Quick Start Guides

### How to Run Your First Scan

**Time: 5 minutes**

1. **Log in** to your account
2. Click **"New Scan"** button (top right)
3. Select **"Network Scan"**
4. Enter target: `scanme.nmap.org` (test server)
5. Choose **"Quick Scan"** (100 ports)
6. Enable **Service Detection**
7. Click **"Start Scan"**
8. Wait 2-3 minutes for completion
9. View results in dashboard

**What to expect**: Open ports (22, 80, 9929), service versions, no critical vulnerabilities

---

### Set Up Slack Notifications

**Time: 3 minutes**

1. In CyperSecurity: **Settings → Integrations → Slack**
2. Click **"Add to Slack"**
3. Select your Slack workspace
4. Choose notification channel (e.g., #security-alerts)
5. Authorize the app
6. Back in CyperSecurity: Select events
   - ✅ Scan Complete
   - ✅ Critical Findings
7. Click **"Save Settings"**
8. **Test**: Run a quick scan and check Slack

---

### Invite Your Team

**Time: 2 minutes**

1. **Settings → Team**
2. Click **"Invite Member"**
3. Enter email: `teammate@yourcompany.com`
4. Select role: **Member**
5. Click **"Send Invitation"**
6. They'll receive email with signup link
7. Repeat for all team members

**Tip**: Invite up to 5 members on Pro plan

---

## Security Workflows

### Weekly Vulnerability Scan

**Recommended for all users**

**Schedule**:
- Day: Every Monday, 2 AM
- Target: All production servers
- Type: Comprehensive network + web scan

**Steps**:
1. **Settings → Scheduled Scans**
2. **"New Schedule"**
3. Enter targets (one per line)
4. Select scan types:
   - ✅ Network Scan (Nmap)
   - ✅ Web Scan (ZAP)
5. Schedule: **Weekly, Monday, 2:00 AM**
6. Notifications:
   - Email: team@yourcompany.com
   - Slack: #security-alerts
7. **Save Schedule**

**Results**: Automatic report emailed every Monday morning

---

### Responding to Critical Findings

**When you receive a critical alert**:

1. ⚠️ **Alert received** (email, Slack, PagerDuty)
2. **Open finding** in dashboard
3. **Review details**:
   - CVSS score (9.0-10.0 = critical)
   - Affected system
   - CVE identifier
   - MITRE ATT&CK technique
4. **Verify finding** (test in staging if possible)
5. **Assign to team member**
6. **Follow remediation steps** in finding details
7. **Apply fix**
8. **Re-scan** to confirm fix
9. **Mark as resolved**

**SLA**: Critical findings should be resolved within 24 hours

---

### Pre-Deployment Security Check

**Before deploying new code**:

1. Deploy to **staging environment**
2. Run **comprehensive scan**:
   - Web application scan (ZAP)
   - SQL injection test (SQLMap)
   - Custom API testing
3. Review all **findings**
4. Fix **MEDIUM** or higher severity issues
5. Document **LOW** severity for backlog
6. Re-scan to verify fixes
7. **Generate compliance report**
8. Deploy to production
9. Run **post-deployment verification scan**

---

## Integration Workflows

### Slack + PagerDuty Escalation

**Use case**: Route critical findings to on-call engineer

**Setup**:

1. **Configure Slack**:
   - Channel: #security-alerts
   - Events: All findings

2. **Configure PagerDuty**:
   - Service: "Security Alerts"
   - Events: Critical findings only
   - Escalation policy: Security team on-call

**Flow**:
- **LOW/MEDIUM**: Slack notification only
- **HIGH**: Slack + email
- **CRITICAL**: Slack + email + PagerDuty incident

---

### Webhook → Jira Integration

**Auto-create Jira tickets for findings**

**Architecture**:
```
CyperSecurity Webhook → Your Server → Jira API
```

**Implementation**:

**1. Create webhook endpoint** (Node.js example):

```javascript
app.post('/webhook/cypersecurity', (req, res) => {
  const { event, data } = req.body;
  
  if (event === 'vulnerability.found' && 
      data.severity === 'critical') {
    
    // Create Jira ticket
    createJiraIssue({
      project: 'SEC',
      type: 'Bug',
      priority: 'Highest',
      summary: `[CRITICAL] ${data.title}`,
      description: `
        CVSS Score: ${data.cvss_score}
        Target: ${data.url}
        CVE: ${data.cve_id}
        
        ${data.description}
        
        Remediation:
        ${data.solution}
      `
    });
  }
  
  res.sendStatus(200);
});
```

**2. Register webhook** in CyperSecurity:
- URL: `https://your-server.com/webhook/cypersecurity`
- Events: `vulnerability.found`
- Secret: (generate and store securely)

**3. Deploy and test**

---

## Compliance Workflows

### Generating Compliance Reports

**For audits and compliance (SOC 2, ISO 27001, PCI DSS)**:

**Monthly Process**:

1. Run **comprehensive scans** on all assets
2. Wait for completion
3. **Dashboard → Compliance**
4. Select framework:
   - SOC 2
   - ISO 27001
   - PCI DSS
   - HIPAA
5. Date range: Last 30 days
6. Click **"Generate Report"**
7. Review findings mapped to controls
8. **Download PDF**
9. Submit to auditor

**Report includes**:
- Executive summary
- Scan coverage
- Findings by severity
- Remediation status
- Compliance posture score

---

### Vulnerability Disclosure Process

**When external researcher reports vulnerability**:

1. **Verify report** (run targeted scan)
2. **Acknowledge receipt** within 24 hours
3. **Triage severity** (CVSS scoring)
4. **Assign to engineer**
5. **Develop fix**
6. **Test in staging**
7. **Deploy to production**
8. **Verify fix** (re-scan)
9. **Notify researcher**
10. **Update disclosure timeline**

**Use CyperSecurity** to:
- Verify reported vulnerabilities
- Confirm fixes
- Generate proof of remediation

---

## Troubleshooting

### Scan Taking Too Long

**If scan runs >30 minutes**:

1. Check target availability
2. Reduce scan scope:
   - Use **Quick Scan** instead of Comprehensive
   - Limit port range (e.g., 1-1000 instead of all)
   - Disable OS detection
3. Schedule for off-peak hours
4. Contact support if persistent

---

### No Vulnerabilities Found

**This is often good!** But verify:

1. **Target is reachable**:
   - Can you ping it?
   - Are firewalls blocking?
2. **Scan completed successfully** (check status)
3. **Scan type appropriate** for target:
   - Network scan for servers
   - Web scan for websites
   - SQL test for database-driven apps
4. **Review informational findings**

---

### Webhook Not Receiving Events

**Debug steps**:

1. **Check webhook URL** is publicly accessible
2. **Verify HTTPS** (required)
3. **Check logs** in Settings → Integrations → Webhooks
4. **Test webhook** with curl:
```bash
curl -X POST https://your-url.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```
5. **Verify signature** validation code
6. **Check firewall** rules

---

**More questions?** Visit [docs.cypersecurity.com](https://docs.cypersecurity.com) or email support@cypersecurity.com
