"""
Test Data Seeding Script

Creates initial test data in the database for E2E tests.
Can be run standalone or used by conftest.py
"""

import requests
import sys
from typing import Dict, Any


class TestDataSeeder:
    """Seeds database with test data"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.token = None
    
    def create_test_user(self, user_data: Dict[str, str]) -> bool:
        """Create a test user"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/auth/signup",
                json=user_data,
                timeout=5
            )
            return response.status_code in [200, 201, 409]  # 409 = already exists
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def login_test_user(self, email: str, password: str) -> bool:
        """Login and get auth token"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/auth/login",
                json={"email": email, "password": password},
                timeout=5
            )
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                return True
            return False
        except Exception as e:
            print(f"Error logging in: {e}")
            return False
    
    def create_test_organization(self, org_data: Dict[str, str]) -> bool:
        """Create test organization"""
        if not self.token:
            return False
        
        try:
            response = requests.post(
                f"{self.api_base_url}/api/organizations",
                json=org_data,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5
            )
            return response.status_code in [200, 201, 409]
        except Exception as e:
            print(f"Error creating organization: {e}")
            return False
    
    def create_test_scan(self, scan_data: Dict[str, Any]) -> bool:
        """Create a completed test scan with results"""
        if not self.token:
            return False
        
        try:
            response = requests.post(
                f"{self.api_base_url}/api/scans",
                json=scan_data,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5
            )
            return response.status_code in [200, 201, 409]
        except Exception as e:
            print(f"Error creating scan: {e}")
            return False
    
    def seed_all(self) -> bool:
        """Seed all test data"""
        print("🌱 Seeding test data...")
        
        # Test user
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "name": "Test User"
        }
        
        if not self.create_test_user(user_data):
            print("❌ Failed to create test user")
            return False
        print("✅ Test user created/verified")
        
        # Login
        if not self.login_test_user(user_data["email"], user_data["password"]):
            print("❌ Failed to login test user")
            return False
        print("✅ Logged in as test user")
        
        # Organization
        org_data = {
            "name": "Test Security Corp",
            "industry": "technology",
            "size": "11-50"
        }
        
        if not self.create_test_organization(org_data):
            print("❌ Failed to create test organization")
            return False
        print("✅ Test organization created/verified")
        
        # Sample scan with results
        scan_data = {
            "target": "scanme.nmap.org",
            "scan_type": "nmap",
            "status": "completed",
            "results": {
                "ports": [
                    {"port": 22, "state": "open", "service": "ssh"},
                    {"port": 80, "state": "open", "service": "http"},
                ],
                "vulnerabilities": [
                    {
                        "title": "Outdated SSH Version",
                        "severity": "medium",
                        "cvss_score": 5.3,
                        "description": "SSH server running outdated version"
                    }
                ]
            }
        }
        
        if not self.create_test_scan(scan_data):
            print("⚠️  Could not create test scan (may not be critical)")
        else:
            print("✅ Test scan created/verified")
        
        print("✅ All test data seeded successfully!")
        return True


def main():
    """Run seeding script standalone"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed test data for E2E tests")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Backend API URL (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    seeder = TestDataSeeder(args.api_url)
    success = seeder.seed_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
