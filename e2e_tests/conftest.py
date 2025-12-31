"""
E2E Test Configuration and Fixtures

Automatically handles:
- Starting backend and frontend
- Waiting for services to be ready
- Seeding test data
- Cleaning up after tests
"""

import pytest
import subprocess
import time
import requests
import os
import signal
import sys
from pathlib import Path

# Test configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
BACKEND_HEALTH_URL = f"{BACKEND_URL}/health"
FRONTEND_READY_TIMEOUT = 60  # seconds
BACKEND_READY_TIMEOUT = 30  # seconds


class ServiceManager:
    """Manages backend and frontend processes"""
    
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.project_root = Path(__file__).parent.parent
    
    def start_backend(self):
        """Start the Python backend"""
        print("\n🚀 Starting backend...")
        
        brain_dir = self.project_root / "brain"
        venv_python = self.project_root / ".venv" / "bin" / "python3"
        
        # Start backend process
        self.backend_process = subprocess.Popen(
            [str(venv_python), "-m", "uvicorn", "cyper_brain.main:app", "--reload", "--port", "8000"],
            cwd=str(brain_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group
        )
        
        # Wait for backend to be ready
        ready = self._wait_for_service(BACKEND_HEALTH_URL, BACKEND_READY_TIMEOUT)
        if not ready:
            self.stop_backend()
            raise RuntimeError("Backend failed to start")
        
        print("✅ Backend ready!")
    
    def start_frontend(self):
        """Start the React frontend"""
        print("\n🚀 Starting frontend...")
        
        dashboard_dir = self.project_root / "dashboard"
        
        # Check if node_modules exists
        if not (dashboard_dir / "node_modules").exists():
            print("📦 Installing npm dependencies...")
            subprocess.run(["npm", "install"], cwd=str(dashboard_dir), check=True)
        
        # Start frontend process
        self.frontend_process = subprocess.Popen(
            ["npm", "start"],
            cwd=str(dashboard_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
            env={**os.environ, "BROWSER": "none"}  # Don't auto-open browser
        )
        
        # Wait for frontend to be ready
        ready = self._wait_for_service(FRONTEND_URL, FRONTEND_READY_TIMEOUT)
        if not ready:
            self.stop_frontend()
            raise RuntimeError("Frontend failed to start")
        
        print("✅ Frontend ready!")
    
    def stop_backend(self):
        """Stop the backend process"""
        if self.backend_process:
            print("\n🛑 Stopping backend...")
            try:
                # First, try graceful shutdown
                os.killpg(os.getpgid(self.backend_process.pid), signal.SIGTERM)
                try:
                    self.backend_process.wait(timeout=5)
                    print("✅ Backend stopped gracefully")
                except subprocess.TimeoutExpired:
                    print("⚠️  Backend didn't stop gracefully, forcing...")
                    # Force kill if graceful shutdown failed
                    os.killpg(os.getpgid(self.backend_process.pid), signal.SIGKILL)
                    self.backend_process.wait(timeout=2)
                    print("✅ Backend force-stopped")
            except ProcessLookupError:
                print("ℹ️  Backend process already terminated")
            except Exception as e:
                print(f"⚠️  Error stopping backend: {e}")
                try:
                    # Last resort: force kill
                    os.killpg(os.getpgid(self.backend_process.pid), signal.SIGKILL)
                except:
                    pass
            finally:
                self.backend_process = None
    
    def stop_frontend(self):
        """Stop the frontend process"""
        if self.frontend_process:
            print("\n🛑 Stopping frontend...")
            try:
                # First, try graceful shutdown
                os.killpg(os.getpgid(self.frontend_process.pid), signal.SIGTERM)
                try:
                    self.frontend_process.wait(timeout=5)
                    print("✅ Frontend stopped gracefully")
                except subprocess.TimeoutExpired:
                    print("⚠️  Frontend didn't stop gracefully, forcing...")
                    # Force kill if graceful shutdown failed
                    os.killpg(os.getpgid(self.frontend_process.pid), signal.SIGKILL)
                    self.frontend_process.wait(timeout=2)
                    print("✅ Frontend force-stopped")
            except ProcessLookupError:
                print("ℹ️  Frontend process already terminated")
            except Exception as e:
                print(f"⚠️  Error stopping frontend: {e}")
                try:
                    # Last resort: force kill
                    os.killpg(os.getpgid(self.frontend_process.pid), signal.SIGKILL)
                except:
                    pass
            finally:
                self.frontend_process = None
    
    def stop_all(self):
        """Stop all services - guaranteed cleanup"""
        print("\n" + "="*80)
        print("🧹 Cleaning up all services...")
        print("="*80)
        
        # Stop in reverse order of startup
        self.stop_frontend()
        self.stop_backend()
        
        # Double-check: kill any remaining child processes
        self._kill_orphaned_processes()
        
        print("✅ All services stopped!")
    
    def _kill_orphaned_processes(self):
        """Kill any orphaned Node.js or Python processes on our ports"""
        try:
            import psutil
            
            # Kill processes on our ports
            for port in [3000, 8000]:
                for proc in psutil.process_iter(['pid', 'name', 'connections']):
                    try:
                        for conn in proc.connections():
                            if conn.laddr.port == port:
                                print(f"🔪 Killing orphaned process {proc.name()} (PID: {proc.pid}) on port {port}")
                                proc.kill()
                                proc.wait(timeout=2)
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                        pass
        except ImportError:
            # psutil not available, try lsof instead
            try:
                for port in [3000, 8000]:
                    result = subprocess.run(
                        ["lsof", "-ti", f":{port}"],
                        capture_output=True,
                        text=True
                    )
                    if result.stdout.strip():
                        pids = result.stdout.strip().split('\n')
                        for pid in pids:
                            try:
                                subprocess.run(["kill", "-9", pid])
                                print(f"🔪 Killed orphaned process PID {pid} on port {port}")
                            except:
                                pass
            except FileNotFoundError:
                pass  # lsof not available
    
    def _wait_for_service(self, url: str, timeout: int) -> bool:
        """Wait for a service to be ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
            print(".", end="", flush=True)
        return False


# Global service manager instance
_service_manager = None


def _emergency_cleanup(signum=None, frame=None):
    """Emergency cleanup handler for signals (Ctrl+C, kill, etc.)"""
    global _service_manager
    
    if signum:
        print(f"\n\n⚠️  Received signal {signum} - Emergency cleanup!")
    
    if _service_manager:
        try:
            _service_manager.stop_all()
        except Exception as e:
            print(f"Error during emergency cleanup: {e}")
    
    if signum:
        sys.exit(1)


def _register_cleanup_handlers():
    """Register handlers to ensure cleanup on any exit"""
    import atexit
    
    # Register atexit handler (runs on normal exit)
    atexit.register(_emergency_cleanup)
    
    # Register signal handlers (runs on Ctrl+C, kill, etc.)
    signal.signal(signal.SIGINT, _emergency_cleanup)   # Ctrl+C
    signal.signal(signal.SIGTERM, _emergency_cleanup)  # kill command


def pytest_configure(config):
    """
    Called once before all tests
    Start backend and frontend services
    
    Guaranteed cleanup on:
    - Normal completion
    - Test failure
    - KeyboardInterrupt (Ctrl+C)
    - Process termination (kill)
    - Python exit
    """
    global _service_manager
    
    print("\n" + "="*80)
    print("🧪 E2E Test Suite - Environment Setup")
    print("="*80)
    
    # Register cleanup handlers FIRST
    _register_cleanup_handlers()
    
    _service_manager = ServiceManager()
    
    try:
        # Start services
        _service_manager.start_backend()
        _service_manager.start_frontend()
        
        print("\n" + "="*80)
        print("✅ All services ready! Starting tests...")
        print("="*80 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Startup interrupted by user!")
        if _service_manager:
            _service_manager.stop_all()
        raise
    except Exception as e:
        print(f"\n❌ Failed to start services: {e}")
        if _service_manager:
            _service_manager.stop_all()
        raise


def pytest_unconfigure(config):
    """
    Called once after all tests
    Stop backend and frontend services
    
    This is the primary cleanup - but we have backups:
    - atexit handler (if this fails)
    - signal handlers (if interrupted)
    """
    global _service_manager
    
    if _service_manager:
        print("\n" + "="*80)
        print("🧹 Test Cleanup - Stopping Services")
        print("="*80)
        try:
            _service_manager.stop_all()
            print("✅ Cleanup complete!")
        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}")
            # Try emergency cleanup as fallback
            try:
                _emergency_cleanup()
            except:
                pass


@pytest.fixture(scope="session")
def api_base_url():
    """Backend API base URL"""
    return BACKEND_URL


@pytest.fixture(scope="session")
def frontend_base_url():
    """Frontend base URL"""
    return FRONTEND_URL


@pytest.fixture(scope="session")
def test_user_data():
    """Test user credentials"""
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "name": "Test User"
    }


@pytest.fixture(scope="session", autouse=True)
def seed_test_data(api_base_url, test_user_data):
    """
    Seed database with test data
    Runs once before all tests
    """
    print("\n📊 Seeding test data...")
    
    try:
        # Create test user
        response = requests.post(
            f"{api_base_url}/api/auth/signup",
            json=test_user_data
        )
        
        if response.status_code in [200, 201]:
            print("✅ Test user created")
        elif response.status_code == 409:
            print("ℹ️  Test user already exists")
        else:
            print(f"⚠️  User creation returned: {response.status_code}")
        
        # Create test organization
        # Login first to get token
        login_response = requests.post(
            f"{api_base_url}/api/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Create organization
            org_response = requests.post(
                f"{api_base_url}/api/organizations",
                json={
                    "name": "Test Security Corp",
                    "industry": "technology",
                    "size": "11-50"
                },
                headers=headers
            )
            
            if org_response.status_code in [200, 201]:
                print("✅ Test organization created")
            elif org_response.status_code == 409:
                print("ℹ️  Test organization already exists")
        
        print("✅ Test data seeding complete")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not seed all test data: {e}")
        print("   Tests will attempt to create data as needed")
    
    yield  # Tests run here
    
    # Cleanup after all tests
    print("\n🧹 Cleaning up test data...")
    try:
        # Delete test user, org, etc.
        # (Implementation depends on your API)
        pass
    except:
        pass


@pytest.fixture
def authenticated_page(page, frontend_base_url, test_user_data):
    """
    Returns an authenticated page session
    Logs in the test user before each test
    """
    # Navigate to login
    page.goto(f"{frontend_base_url}/login")
    
    # Fill login form
    page.fill('input[name="email"]', test_user_data["email"])
    page.fill('input[name="password"]', test_user_data["password"])
    
    # Submit
    page.click('button[type="submit"]')
    
    # Wait for redirect to dashboard
    page.wait_for_url(f"{frontend_base_url}/dashboard", timeout=10000)
    
    return page
