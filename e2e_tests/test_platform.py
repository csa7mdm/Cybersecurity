"""
End-to-End Tests for CyperSecurity Platform

Tests complete user workflows using Playwright.
"""

import pytest
from playwright.sync_api import Page, expect
import time


class TestUserOnboarding:
    """Test complete user onboarding flow"""
    
    def test_signup_and_verification(self, page: Page):
        """Test user can sign up and verify email"""
        # Navigate to signup page
        page.goto("http://localhost:3000/signup")
        
        # Fill signup form
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "SecurePass123!")
        page.fill('input[name="confirm_password"]', "SecurePass123!")
        
        # Submit
        page.click('button[type="submit"]')
        
        # Should see verification message
        expect(page.locator('text=Check your email')).to_be_visible()
        
        # In real test, would check email inbox via API
        # For now, simulate direct verification link
        # verification_url = get_verification_link_from_email()
        # page.goto(verification_url)
    
    def test_onboarding_wizard(self, page: Page):
        """Test 4-step onboarding wizard"""
        # Assume user is logged in
        page.goto("http://localhost:3000/onboarding")
        
        # Step 1: Welcome
        expect(page.locator('h1:has-text("Welcome")')).to_be_visible()
        page.click('button:has-text("Get Started")')
        
        # Step 2: Organization setup
        expect(page.locator('h2:has-text("Organization")')).to_be_visible()
        page.fill('input[name="org_name"]', "Test Security Corp")
        page.select_option('select[name="industry"]', "technology")
        page.select_option('select[name="size"]', "11-50")
        page.click('button:has-text("Continue")')
        
        # Step 3: Team invitation (skip)
        page.click('button:has-text("Skip")')
        
        # Step 4: Trial activation
        page.check('input[name="accept_terms"]')
        page.click('button:has-text("Activate Trial")')
        
        # Should redirect to dashboard
        expect(page).to_have_url(/.*dashboard/)
        expect(page.locator('text=14-day trial')).to_be_visible()


class TestScanWorkflow:
    """Test complete scan workflow"""
    
    def test_create_and_run_nmap_scan(self, page: Page):
        """Test creating and running Nmap scan"""
        # Navigate to dashboard
        page.goto("http://localhost:3000/dashboard")
        
        # Click New Scan
        page.click('button:has-text("New Scan")')
        
        # Select Network Scan
        page.click('text=Network Scan')
        
        # Fill scan form
        page.fill('input[name="target"]', "scanme.nmap.org")
        page.select_option('select[name="scan_type"]', "quick")
        page.check('input[name="service_detection"]')
        
        # Start scan
        page.click('button:has-text("Start Scan")')
        
        # Should see scan in progress
        expect(page.locator('text=Scanning')).to_be_visible()
        
        # Wait for completion (with timeout)
        page.wait_for_selector('text=Completed', timeout=180000)  # 3 min
        
        # Should see results
        expect(page.locator('text=Open Ports')).to_be_visible()
        expect(page.locator('text=Services')).to_be_visible()
    
    def test_generate_pdf_report(self, page: Page):
        """Test PDF report generation"""
        # Navigate to completed scan
        page.goto("http://localhost:3000/scans/scan_12345")
        
        # Click generate report
        page.click('button:has-text("Generate Report")')
        
        # Select report type
        page.click('text=Technical Report')
        
        # Generate
        page.click('button:has-text("Generate PDF")')
        
        # Wait for generation
        expect(page.locator('text=Generating')).to_be_visible()
        
        with page.expect_download() as download_info:
            page.wait_for_selector('button:has-text("Download")', timeout=60000)
            page.click('button:has-text("Download")')
        
        download = download_info.value
        assert download.suggested_filename.endswith('.pdf')


class TestIntegrations:
    """Test integration setup"""
    
    def test_slack_integration_setup(self, page: Page):
        """Test Slack integration setup"""
        # Navigate to integrations
        page.goto("http://localhost:3000/settings/integrations")
        
        # Find Slack card
        slack_card = page.locator('div:has-text("Slack")').first
        expect(slack_card).to_be_visible()
        
        # Click configure
        slack_card.locator('button:has-text("Configure")').click()
        
        # Should see OAuth flow (would redirect to Slack in real scenario)
        # For testing, might use mock OAuth
        expect(page.locator('text=Connect to Slack')).to_be_visible()
    
    def test_webhook_creation(self, page: Page):
        """Test webhook creation"""
        page.goto("http://localhost:3000/settings/integrations")
        
        # Click Add Webhook
        page.click('button:has-text("Add Webhook")')
        
        # Fill form
        page.fill('input[name="url"]', "https://example.com/webhook")
        page.check('input[value="scan.completed"]')
        page.check('input[value="critical.finding"]')
        
        # Save
        page.click('button:has-text("Save")')
        
        # Should see webhook in list
        expect(page.locator('text=https://example.com/webhook')).to_be_visible()


class TestBillingWorkflow:
    """Test billing and subscription"""
    
    def test_upgrade_to_pro_plan(self, page: Page):
        """Test upgrading to Pro plan"""
        page.goto("http://localhost:3000/settings/billing")
        
        # Click upgrade
        page.click('button:has-text("Upgrade to Pro")')
        
        # Should see pricing
        expect(page.locator('text=$99/month')).to_be_visible()
        
        # Fill payment details (use Stripe test card)
        iframe = page.frame_locator('iframe[name*="stripe"]')
        iframe.locator('input[name="cardnumber"]').fill('4242424242424242')
        iframe.locator('input[name="exp-date"]').fill('12/25')
        iframe.locator('input[name="cvc"]').fill('123')
        iframe.locator('input[name="postal"]').fill('12345')
        
        # Submit
        page.click('button:has-text("Subscribe")')
        
        # Should see success
        expect(page.locator('text=Subscription active')).to_be_visible()


class TestTeamCollaboration:
    """Test team features"""
    
    def test_invite_team_member(self, page: Page):
        """Test inviting team member"""
        page.goto("http://localhost:3000/settings/team")
        
        # Click invite
        page.click('button:has-text("Invite Member")')
        
        # Fill form
        page.fill('input[name="email"]', "teammate@example.com")
        page.select_option('select[name="role"]', "member")
        
        # Send invitation
        page.click('button:has-text("Send Invitation")')
        
        # Should see in pending invitations
        expect(page.locator('text=teammate@example.com')).to_be_visible()
        expect(page.locator('text=Pending')).to_be_visible()


@pytest.fixture
def page(browser):
    """Create page with authenticated user"""
    context = browser.new_context()
    page = context.new_page()
    
    # Login (or set auth token)
    page.goto("http://localhost:3000/login")
    page.fill('input[name="email"]', "test@example.com")
    page.fill('input[name="password"]', "SecurePass123!")
    page.click('button[type="submit"]')
    
    # Wait for redirect to dashboard
    page.wait_for_url("**/dashboard")
    
    yield page
    
    context.close()


# Pytest configuration
@pytest.fixture(scope="session")
def browser():
    """Create browser instance"""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()
