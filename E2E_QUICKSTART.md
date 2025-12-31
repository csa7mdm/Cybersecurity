# 🎯 Quick Start: E2E Testing

## ✅ Already Done!

Playwright is installed and browser is downloading automatically.

## 🚀 How to Run E2E Tests (3 Simple Steps)

### **Step 1: Start Your Platform**

You need your platform running first!

**Terminal 1 - Backend:**
```bash
cd /Users/ahmedmustafa/Desktop/Workspace/Cypersecurity/brain
source ../.venv/bin/activate
python -m uvicorn cyper_brain.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd /Users/ahmedmustafa/Desktop/Workspace/Cypersecurity/dashboard
npm start
```

### **Step 2: Run Tests**

**Easy Way (Use the script):**
```bash
cd /Users/ahmedmustafa/Desktop/Workspace/Cypersecurity
./run_e2e_tests.sh
```

**Manual Way:**
```bash
cd /Users/ahmedmustafa/Desktop/Workspace/Cypersecurity
source .venv/bin/activate
pytest e2e_tests/ -v
```

**Watch tests run (see the browser):**
```bash
pytest e2e_tests/ --headed
```

### **Step 3: Check Results**

You'll see output like:
```
✓ test_signup_and_verification PASSED
✓ test_onboarding_wizard PASSED  
✓ test_create_and_run_nmap_scan PASSED
✓ test_generate_pdf_report PASSED

========== 10 passed in 45.2s ==========
```

---

## 📖 What Tests Do

Your E2E tests automatically:

1. **🔐 User Onboarding**
   - Sign up new user
   - Verify email
   - Complete wizard
   - Activate trial

2. **🔍 Scanning**
   - Create Nmap scan
   - Wait for completion
   - View results

3. **📄 Reports**
   - Generate PDF
   - Download report

4. **💳 Billing**
   - Upgrade to Pro
   - Enter payment
   - Activate subscription

5. **🔗 Integrations**
   - Set up Slack
   - Create webhooks

6. **👥 Team**
   - Invite members

---

## 🐛 Debugging

**See what's happening:**
```bash
pytest e2e_tests/ --headed --slowmo 1000
```

**Stop on failure:**
```bash
pytest e2e_tests/ --headed --pause-on-failure
```

**Run one test:**
```bash
pytest e2e_tests/test_platform.py::TestUserOnboarding::test_signup -v
```

---

## 📚 Full Documentation

See `docs/E2E_TESTING_GUIDE.md` for complete guide with:
- All Playwright commands
- How to write new tests
- Troubleshooting tips
- Best practices

---

## ✨ That's It!

**You're ready to test your platform like a real user!** 🎉

```bash
./run_e2e_tests.sh
```
