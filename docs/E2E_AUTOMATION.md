# 🚀 Fully Automated E2E Testing

## ✨ What's New: Zero Manual Setup!

The E2E tests are now **fully automated**. No need to manually start services, seed data, or clean up!

---

## 🎯 Quick Start (One Command!)

```bash
cd /Users/ahmedmustafa/Desktop/Workspace/Cypersecurity
./run_e2e_tests.sh
```

**That's it!** The system handles everything automatically.

---

## 🔄 What Happens Automatically

### **1. Environment Initialization** (conftest.py)

**Before ANY tests run:**
- ✅ Starts Python backend (uvicorn on port 8000)
- ✅ Starts React frontend (npm start on port 3000)
- ✅ Waits for health checks (services ready)
- ✅ Seeds test database with required data

**After ALL tests complete:**
- ✅ Stops backend process
- ✅ Stops frontend process
- ✅ Cleans up temporary data

### **2. Test Data Seeding** (seed_data.py)

**Creates:**
- Test user: `test@example.com` / `SecurePass123!`
- Test organization: "Test Security Corp"
- Sample scan with results (for report tests)

**Smart Handling:**
- Checks if data already exists (409 status)
- Graceful error handling
- Can run standalone: `python e2e_tests/seed_data.py`

### **3. Test Execution** (test_platform.py)

**Each test gets:**
- `authenticated_page` fixture → Pre-logged in user session
- `frontend_base_url` fixture → Configurable URLs
- `api_base_url` fixture → Backend API access
- `test_user_data` fixture → Test credentials

**No hardcoded URLs, no manual login!**

---

## 📁 New Files

### **conftest.py** (310 lines)
**Purpose:** Test environment orchestration

**Key Components:**
- `ServiceManager` class - Manages backend/frontend processes
- `pytest_configure()` - Starts services before tests
- `pytest_unconfigure()` - Stops services after tests
- `seed_test_data()` - Populates database
- `authenticated_page()` - Pre-authenticated browser session

**Features:**
- Process management with proper cleanup
- Health check polling (waits until ready)
- Automatic npm install if needed
- Browser suppression (no popup windows)
- Session-scoped fixtures (run once)

### **seed_data.py** (150 lines)
**Purpose:** Database seeding

**Can be used:**
1. Automatically (via conftest.py)
2. Standalone: `python e2e_tests/seed_data.py --api-url http://localhost:8000`

**Creates:**
- Test user account
- Test organization
- Sample scan data

### **Updated test_platform.py**
**Changes:**
- Uses `authenticated_page` instead of `page`
- Uses `frontend_base_url` instead of hardcoded URLs
- Tests start with user already logged in
- Cleaner, more focused tests

---

## 🎬 Example Test Run

```bash
$ ./run_e2e_tests.sh

🧪 CyperSecurity Platform - Fully Automated E2E Tests
=====================================================

This will automatically:
  1. ✅ Start backend (Python/FastAPI)
  2. ✅ Start frontend (React)
  3. ✅ Wait for services to be ready
  4. ✅ Seed test data
  5. ✅ Run all E2E tests
  6. ✅ Clean up and stop services

================================================================================
🧪 E2E Test Suite - Environment Setup
================================================================================

🚀 Starting backend...
...........
✅ Backend ready!

🚀 Starting frontend...
📦 Installing npm dependencies... (if needed)
.........................
✅ Frontend ready!

📊 Seeding test data...
✅ Test user created
✅ Logged in as test user
✅ Test organization created
✅ Test scan created
✅ Test data seeding complete

================================================================================
✅ All services ready! Starting tests...
================================================================================

test_signup_and_verification ✓ PASSED
test_onboarding_wizard ✓ PASSED
test_create_and_run_nmap_scan ✓ PASSED
test_generate_pdf_report ✓ PASSED
test_slack_integration_setup ✓ PASSED
test_webhook_creation ✓ PASSED
test_upgrade_to_pro_plan ✓ PASSED
test_invite_team_member ✓ PASSED

================================================================================
8 passed in 52.3s
================================================================================

================================================================================
🧹 Cleaning up test environment
================================================================================
🛑 Stopping backend...
🛑 Stopping frontend...
✅ Cleanup complete!

✅ Tests complete! Services have been stopped.
```

---

## 🛠️ How It Works

### **Fixture Scopes**

```python
@pytest.fixture(scope="session")  # Runs ONCE for all tests
def seed_test_data():
    # Seed database
    yield
    # Cleanup after all tests

@pytest.fixture  # Runs BEFORE EACH test
def authenticated_page(page):
    # Login user
    return page
```

### **Process Management**

```python
# Start backend
self.backend_process = subprocess.Popen(
    [python, "-m", "uvicorn", "cyper_brain.main:app"],
    preexec_fn=os.setsid  # Create process group
)

# Stop backend
os.killpg(os.getpgid(pid), signal.SIGTERM)  # Kill entire group
```

### **Health Checking**

```python
def _wait_for_service(url, timeout):
    for _ in range(timeout):
        try:
            if requests.get(url).status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False
```

---

## 🎯 CI/CD Integration

### **GitHub Actions**

```yaml
- name: Run E2E Tests
  run: |
    chmod +x run_e2e_tests.sh
    ./run_e2e_tests.sh
```

**That's it!** No manual service setup in CI.

---

## 🐛 Debugging

### **See browser actions:**
```bash
pytest e2e_tests/ --headed
```

### **Run single test:**
```bash
pytest e2e_tests/test_platform.py::TestUserOnboarding::test_signup -v
```

### **Manual seed (without running tests):**
```bash
python e2e_tests/seed_data.py
```

### **Check what tests will run:**
```bash
pytest e2e_tests/ --collect-only
```

---

## ⚡ Performance

**Timing:**
- Service startup: ~15-30 seconds
- Data seeding: ~2-5 seconds
- Test execution: ~30-60 seconds
- Cleanup: ~2-3 seconds
- **Total: ~50-100 seconds**

**Optimization:**
- Services start once (not per test)
- Data seeds once (reused across tests)
- Parallel test execution possible: `pytest -n 4`

---

## 🔒 Test Isolation

**Each test gets:**
- Fresh browser context
- Clean session
- Independent from other tests

**Shared across all tests:**
- Backend service
- Frontend service
- Database with seed data

---

## 📊 Benefits

### **Before (Manual Setup):**
❌ Start backend manually  
❌ Start frontend manually  
❌ Create test user manually  
❌ Remember to stop services  
❌ Different setup per developer  

### **After (Automated):**
✅ One command: `./run_e2e_tests.sh`  
✅ Consistent across all developers  
✅ Works in CI/CD out of the box  
✅ Auto cleanup (no orphan processes)  
✅ Reproducible test environment  

---

## 🎉 Summary

**You now have fully automated E2E testing!**

**Just run:**
```bash
./run_e2e_tests.sh
```

**Everything else is automatic:**
- ✅ Service orchestration
- ✅ Data seeding
- ✅ Test execution
- ✅ Cleanup

**Perfect for:**
- Local development
- CI/CD pipelines
- Team collaboration
- Continuous testing

🚀 **Your platform has enterprise-grade automated testing!**
