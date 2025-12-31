# E2E Testing Guide - Step-by-Step

## What You'll Learn
- How to install Playwright
- How to run E2E tests
- How to view test results
- How to debug failing tests
- How to add new tests

---

## Prerequisites

You need:
- ✅ Python 3.11+ installed
- ✅ Virtual environment activated
- ✅ Platform running locally (frontend + backend)

---

## Installation

### Step 1: Install Playwright and pytest-playwright

```bash
cd /Users/ahmedmustafa/Desktop/Workspace/Cypersecurity
source .venv/bin/activate
pip install playwright pytest-playwright
```

### Step 2: Install Browser Binaries

```bash
playwright install chromium
```

This downloads the Chromium browser that Playwright will control.

**Optional:** Install other browsers too:
```bash
playwright install firefox
playwright install webkit  # Safari
```

---

## Running Tests

### Basic Usage

**Run all E2E tests:**
```bash
cd /Users/ahmedmustafa/Desktop/Workspace/Cypersecurity
source .venv/bin/activate
pytest e2e_tests/ -v
```

**Output will look like:**
```
e2e_tests/test_platform.py::TestUserOnboarding::test_signup_and_verification PASSED
e2e_tests/test_platform.py::TestUserOnboarding::test_onboarding_wizard PASSED
e2e_tests/test_platform.py::TestScanWorkflow::test_create_and_run_nmap_scan PASSED
...
========== 10 passed in 45.2s ==========
```

### Run Specific Tests

**Single test class:**
```bash
pytest e2e_tests/test_platform.py::TestUserOnboarding -v
```

**Single test method:**
```bash
pytest e2e_tests/test_platform.py::TestUserOnboarding::test_signup_and_verification -v
```

### Useful Options

**See browser window (headed mode):**
```bash
pytest e2e_tests/ --headed
```
Watch the browser automation in real-time!

**Slow down execution:**
```bash
pytest e2e_tests/ --headed --slowmo 1000
```
Slows down by 1000ms (1 second) per action.

**Keep browser open on failure:**
```bash
pytest e2e_tests/ --headed --pause-on-failure
```

**Run with screenshots:**
```bash
pytest e2e_tests/ --screenshot=only-on-failure
```
Screenshots saved to `e2e_tests/screenshots/`

**Run with video recording:**
```bash
pytest e2e_tests/ --video=retain-on-failure
```

**Parallel execution (faster):**
```bash
pytest e2e_tests/ -n 4  # Run 4 tests in parallel
```

---

## Understanding Test Results

### ✅ Successful Test
```
e2e_tests/test_platform.py::TestScanWorkflow::test_create_and_run_nmap_scan PASSED [50%]
```

**Meaning:** The test completed successfully. Real user workflow works!

### ❌ Failed Test
```
e2e_tests/test_platform.py::TestBillingWorkflow::test_upgrade_to_pro_plan FAILED [80%]

=== FAILURES ===
AssertionError: Expected element 'text=Subscription active' to be visible
Timeout 5000ms exceeded
```

**Meaning:** The test failed. The expected text didn't appear. There's a bug!

### 📊 Test Summary
```
========== 8 passed, 2 failed in 120.5s ==========
```

---

## Debugging Failed Tests

### Method 1: Watch the Test Run

```bash
pytest e2e_tests/test_platform.py::TestName::test_method --headed --slowmo 500
```

Watch exactly what the browser is doing.

### Method 2: Check Screenshots

Failed tests automatically save screenshots:
```
e2e_tests/screenshots/test_upgrade_to_pro_plan.png
```

Open the image to see what the browser showed when the test failed.

### Method 3: Enable Debug Logging

```bash
PWDEBUG=1 pytest e2e_tests/test_platform.py::TestName::test_method
```

Opens Playwright Inspector for step-by-step debugging.

### Method 4: Add Print Statements

In your test:
```python
def test_upgrade_to_pro_plan(self, page: Page):
    page.goto("http://localhost:3000/settings/billing")
    print(f"Current URL: {page.url}")  # Debug
    page.click('button:has-text("Upgrade to Pro")')
    print("Clicked upgrade button")  # Debug
```

---

## Before Running Tests

**⚠️ IMPORTANT:** Your platform must be running!

### Start Your Platform

**Terminal 1 - Backend:**
```bash
cd /Users/ahmedmustafa/Desktop/Workspace/Cypersecurity/brain
source ../.venv/bin/activate
python -m uvicorn cyper_brain.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd /Users/ahmedmustafa/Desktop/Workspace/Cypersecurity/dashboard
npm start
# Runs on localhost:3000
```

**Terminal 3 - Run Tests:**
```bash
cd /Users/ahmedmustafa/Desktop/Workspace/Cypersecurity
source .venv/bin/activate
pytest e2e_tests/ -v
```

---

## Adding New Tests

### Example: Test Report Download

Create a new test in `e2e_tests/test_platform.py`:

```python
class TestReporting:
    """Test report features"""
    
    def test_download_executive_report(self, page: Page):
        """Test downloading executive summary report"""
        # Navigate to scan results
        page.goto("http://localhost:3000/scans/scan_123")
        
        # Click report tab
        page.click('button:has-text("Reports")')
        
        # Select executive summary
        page.click('input[value="executive"]')
        
        # Generate report
        page.click('button:has-text("Generate")')
        
        # Wait for download
        with page.expect_download() as download_info:
            page.click('button:has-text("Download PDF")')
        
        download = download_info.value
        
        # Verify it's a PDF
        assert download.suggested_filename.endswith('.pdf')
        assert 'executive' in download.suggested_filename.lower()
```

Then run:
```bash
pytest e2e_tests/test_platform.py::TestReporting -v
```

---

## Common Playwright Commands

### Navigation
```python
page.goto("http://localhost:3000/dashboard")
page.go_back()
page.go_forward()
page.reload()
```

### Clicking
```python
page.click('button')                           # CSS selector
page.click('button:has-text("Submit")')        # Text content
page.click('text=Login')                       # Shorthand
page.click('#submit-btn')                      # ID
page.click('.submit-button')                   # Class
```

### Typing
```python
page.fill('input[name="email"]', 'user@example.com')
page.type('textarea', 'Hello world', delay=100)  # Type slowly
```

### Selecting
```python
page.select_option('select[name="plan"]', 'pro')
page.check('input[type="checkbox"]')
page.uncheck('input[type="checkbox"]')
```

### Waiting
```python
page.wait_for_selector('text=Completed')
page.wait_for_url('**/dashboard')
page.wait_for_timeout(5000)  # Wait 5 seconds
page.wait_for_load_state('networkidle')
```

### Assertions
```python
expect(page.locator('h1')).to_be_visible()
expect(page.locator('text=Error')).to_be_hidden()
expect(page).to_have_url('http://localhost:3000/dashboard')
expect(page.locator('input')).to_have_value('test@example.com')
```

---

## Best Practices

### 1. Use Specific Selectors
❌ Bad: `page.click('button')`  
✅ Good: `page.click('button:has-text("Start Scan")')`

### 2. Add Waits
❌ Bad: Assume element is ready  
✅ Good: `expect(element).to_be_visible()`

### 3. Clean Up
```python
def test_example(self, page: Page):
    # Create test data
    ...
    
    # Run test
    ...
    
    # Clean up (delete test data)
    ...
```

### 4. Use Fixtures
```python
@pytest.fixture
def authenticated_page(page):
    """Pre-authenticated page"""
    page.goto("localhost:3000/login")
    page.fill('input[name="email"]', 'test@example.com')
    page.fill('input[name="password"]', 'password')
    page.click('button[type="submit"]')
    page.wait_for_url('**/dashboard')
    return page
```

---

## CI/CD Integration

Your GitHub Actions workflow already includes E2E tests:

```yaml
# .github/workflows/ci-cd.yml
- name: Run E2E tests
  run: |
    pytest e2e_tests/ -v --headed
```

Tests run automatically on every push!

---

## Troubleshooting

### Problem: "Browser not found"
**Solution:**
```bash
playwright install chromium
```

### Problem: "Connection refused"
**Solution:** Make sure your platform is running on localhost:3000 and localhost:8000

### Problem: "Element not found"
**Solution:** 
1. Use `--headed` to see what's happening
2. Check if element selector is correct
3. Add wait: `page.wait_for_selector('element')`

### Problem: "Test timeout"
**Solution:** Increase timeout:
```python
page.wait_for_selector('text=Completed', timeout=300000)  # 5 minutes
```

---

## Quick Reference

**Install:**
```bash
pip install playwright pytest-playwright
playwright install chromium
```

**Run all tests:**
```bash
pytest e2e_tests/ -v
```

**Run with browser visible:**
```bash
pytest e2e_tests/ --headed
```

**Run specific test:**
```bash
pytest e2e_tests/test_platform.py::TestName::test_method -v
```

**Debug:**
```bash
PWDEBUG=1 pytest e2e_tests/test_platform.py::test_name
```

---

## Next Steps

1. ✅ Install Playwright
2. ✅ Run existing tests
3. ✅ Watch tests in headed mode
4. ✅ Add your own test
5. ✅ Integrate with CI/CD

**You're ready to use E2E testing!** 🚀
