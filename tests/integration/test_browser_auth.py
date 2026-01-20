"""
Browser-based Integration Tests for Authentication and Route Navigation

Tests the complete login flow using Playwright headless browser to verify:
1. Login form works and authenticates users
2. All protected routes are accessible after login
3. Logout clears credentials properly
4. Unauthenticated users are redirected to login
"""

import pytest
import subprocess
import time
import signal
import os
import sys
from datetime import datetime


# Check if playwright is available
try:
    from playwright.sync_api import sync_playwright, expect
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# Skip all tests in this module if playwright is not available
pytestmark = pytest.mark.skipif(
    not PLAYWRIGHT_AVAILABLE,
    reason="Playwright not installed. Run: pip install playwright && playwright install chromium"
)


class TestBrowserAuthentication:
    """Test authentication flow using headless browser"""

    BASE_URL = "http://localhost:5001"
    DEMO_EMAIL = "demo@familyoffice.com"
    DEMO_PASSWORD = "DemoPassword123!"

    @pytest.fixture(scope="class")
    def server_process(self):
        """Start Flask server for testing"""
        # Start Flask server in background
        env = os.environ.copy()
        env['FLASK_ENV'] = 'testing'

        process = subprocess.Popen(
            [sys.executable, 'run.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )

        # Wait for server to start
        time.sleep(3)

        yield process

        # Cleanup: terminate server
        process.send_signal(signal.SIGTERM)
        process.wait(timeout=5)

    @pytest.fixture(scope="class")
    def browser_context(self):
        """Create browser context for tests"""
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            yield context
            context.close()
            browser.close()

    def test_login_page_loads(self, browser_context, server_process):
        """Test that login page loads correctly"""
        page = browser_context.new_page()
        try:
            page.goto(f"{self.BASE_URL}/login", timeout=10000)
            expect(page.locator("h3")).to_contain_text("Family Office")
            expect(page.locator("#email")).to_be_visible()
            expect(page.locator("#password")).to_be_visible()
            expect(page.locator("button[type='submit']")).to_be_visible()
        finally:
            page.close()

    def test_login_with_valid_credentials(self, browser_context, server_process):
        """Test login with valid demo credentials"""
        page = browser_context.new_page()
        try:
            page.goto(f"{self.BASE_URL}/login", timeout=10000)

            # Fill in credentials
            page.fill("#email", self.DEMO_EMAIL)
            page.fill("#password", self.DEMO_PASSWORD)

            # Submit form
            page.click("button[type='submit']")

            # Wait for redirect to dashboard
            page.wait_for_url("**/dashboard", timeout=10000)

            # Verify we're on the dashboard
            assert "/dashboard" in page.url

            # Check that JWT token was stored
            access_token = page.evaluate("() => localStorage.getItem('access_token')")
            assert access_token is not None
            assert len(access_token) > 0
        finally:
            page.close()

    def test_login_with_invalid_credentials(self, browser_context, server_process):
        """Test login with invalid credentials shows error"""
        page = browser_context.new_page()
        try:
            page.goto(f"{self.BASE_URL}/login", timeout=10000)

            # Fill in invalid credentials
            page.fill("#email", "invalid@test.com")
            page.fill("#password", "wrongpassword")

            # Submit form
            page.click("button[type='submit']")

            # Wait for error message
            error_alert = page.locator("#errorAlert")
            expect(error_alert).to_be_visible(timeout=5000)

            # Verify we're still on login page
            assert "/login" in page.url
        finally:
            page.close()

    def test_unauthenticated_redirect(self, browser_context, server_process):
        """Test that unauthenticated users are redirected to login"""
        page = browser_context.new_page()
        try:
            # Clear any stored tokens
            page.goto(f"{self.BASE_URL}/login", timeout=10000)
            page.evaluate("() => { localStorage.clear(); }")

            # Try to access protected route
            page.goto(f"{self.BASE_URL}/dashboard", timeout=10000)

            # Should be redirected to login
            page.wait_for_url("**/login", timeout=10000)
            assert "/login" in page.url
        finally:
            page.close()

    def test_logout_clears_credentials(self, browser_context, server_process):
        """Test that logout clears stored credentials"""
        page = browser_context.new_page()
        try:
            # First login
            page.goto(f"{self.BASE_URL}/login", timeout=10000)
            page.fill("#email", self.DEMO_EMAIL)
            page.fill("#password", self.DEMO_PASSWORD)
            page.click("button[type='submit']")
            page.wait_for_url("**/dashboard", timeout=10000)

            # Verify token exists
            access_token = page.evaluate("() => localStorage.getItem('access_token')")
            assert access_token is not None

            # Navigate to logout
            page.goto(f"{self.BASE_URL}/logout", timeout=10000)

            # Wait for redirect to login
            page.wait_for_url("**/login", timeout=10000)

            # Verify token was cleared
            access_token = page.evaluate("() => localStorage.getItem('access_token')")
            assert access_token is None
        finally:
            page.close()


class TestProtectedRouteAccess:
    """Test that all protected routes are accessible after login"""

    BASE_URL = "http://localhost:5001"
    DEMO_EMAIL = "demo@familyoffice.com"
    DEMO_PASSWORD = "DemoPassword123!"

    PROTECTED_ROUTES = [
        "/dashboard",
        "/portfolio",
        "/analytics",
        "/agents",
        "/profile",
        "/settings",
    ]

    @pytest.fixture(scope="class")
    def server_process(self):
        """Start Flask server for testing"""
        env = os.environ.copy()
        env['FLASK_ENV'] = 'testing'

        process = subprocess.Popen(
            [sys.executable, 'run.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )

        time.sleep(3)
        yield process

        process.send_signal(signal.SIGTERM)
        process.wait(timeout=5)

    @pytest.fixture(scope="class")
    def authenticated_page(self, server_process):
        """Create authenticated browser page"""
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Login
            page.goto(f"{self.BASE_URL}/login", timeout=10000)
            page.fill("#email", self.DEMO_EMAIL)
            page.fill("#password", self.DEMO_PASSWORD)
            page.click("button[type='submit']")
            page.wait_for_url("**/dashboard", timeout=10000)

            yield page

            context.close()
            browser.close()

    @pytest.mark.parametrize("route", PROTECTED_ROUTES)
    def test_protected_route_accessible(self, authenticated_page, route):
        """Test that each protected route is accessible after login"""
        authenticated_page.goto(f"{self.BASE_URL}{route}", timeout=10000)

        # Verify we're on the expected route (not redirected to login)
        assert "/login" not in authenticated_page.url
        assert route in authenticated_page.url or authenticated_page.url.endswith(route.rstrip('/'))

        # Verify page loaded without server error
        assert "500" not in authenticated_page.content()
        assert "Internal Server Error" not in authenticated_page.content()


class TestRegistrationFlow:
    """Test user registration flow"""

    BASE_URL = "http://localhost:5001"

    @pytest.fixture(scope="class")
    def server_process(self):
        """Start Flask server for testing"""
        env = os.environ.copy()
        env['FLASK_ENV'] = 'testing'

        process = subprocess.Popen(
            [sys.executable, 'run.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )

        time.sleep(3)
        yield process

        process.send_signal(signal.SIGTERM)
        process.wait(timeout=5)

    @pytest.fixture(scope="class")
    def browser_context(self):
        """Create browser context for tests"""
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            yield context
            context.close()
            browser.close()

    def test_registration_page_loads(self, browser_context, server_process):
        """Test that registration page loads correctly"""
        page = browser_context.new_page()
        try:
            page.goto(f"{self.BASE_URL}/register", timeout=10000)
            expect(page.locator("h3")).to_contain_text("Create Account")
            expect(page.locator("#email")).to_be_visible()
            expect(page.locator("#password")).to_be_visible()
            expect(page.locator("#confirmPassword")).to_be_visible()
        finally:
            page.close()

    def test_registration_with_valid_data(self, browser_context, server_process):
        """Test registration with valid data"""
        page = browser_context.new_page()
        try:
            page.goto(f"{self.BASE_URL}/register", timeout=10000)

            # Generate unique email
            test_email = f"test_browser_{datetime.now().timestamp()}@test.com"

            # Fill in registration form
            page.fill("#firstName", "Browser")
            page.fill("#lastName", "Test")
            page.fill("#email", test_email)
            page.fill("#password", "TestPassword123!")
            page.fill("#confirmPassword", "TestPassword123!")
            page.check("#terms")

            # Submit form
            page.click("button[type='submit']")

            # Wait for redirect to dashboard
            page.wait_for_url("**/dashboard", timeout=15000)

            # Verify we're on the dashboard
            assert "/dashboard" in page.url

            # Check that JWT token was stored
            access_token = page.evaluate("() => localStorage.getItem('access_token')")
            assert access_token is not None
        finally:
            page.close()

    def test_registration_password_mismatch(self, browser_context, server_process):
        """Test registration with mismatched passwords"""
        page = browser_context.new_page()
        try:
            page.goto(f"{self.BASE_URL}/register", timeout=10000)

            page.fill("#email", "mismatch@test.com")
            page.fill("#password", "TestPassword123!")
            page.fill("#confirmPassword", "DifferentPassword123!")
            page.check("#terms")

            # Submit form
            page.click("button[type='submit']")

            # Wait for error message
            error_alert = page.locator("#errorAlert")
            expect(error_alert).to_be_visible(timeout=5000)
            expect(error_alert).to_contain_text("Passwords do not match")

            # Verify we're still on registration page
            assert "/register" in page.url
        finally:
            page.close()


class TestCompleteUserJourney:
    """Test complete user journey through the application"""

    BASE_URL = "http://localhost:5001"
    DEMO_EMAIL = "demo@familyoffice.com"
    DEMO_PASSWORD = "DemoPassword123!"

    @pytest.fixture(scope="class")
    def server_process(self):
        """Start Flask server for testing"""
        env = os.environ.copy()
        env['FLASK_ENV'] = 'testing'

        process = subprocess.Popen(
            [sys.executable, 'run.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )

        time.sleep(3)
        yield process

        process.send_signal(signal.SIGTERM)
        process.wait(timeout=5)

    def test_complete_journey(self, server_process):
        """Test complete user journey from login to logout"""
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            try:
                # 1. Visit homepage - should redirect to login
                page.goto(f"{self.BASE_URL}/", timeout=10000)
                page.wait_for_url("**/login", timeout=10000)
                assert "/login" in page.url

                # 2. Login
                page.fill("#email", self.DEMO_EMAIL)
                page.fill("#password", self.DEMO_PASSWORD)
                page.click("button[type='submit']")
                page.wait_for_url("**/dashboard", timeout=10000)
                assert "/dashboard" in page.url

                # 3. Navigate through protected routes
                routes_visited = []

                for route in ["/portfolio", "/analytics", "/agents", "/profile", "/settings"]:
                    page.goto(f"{self.BASE_URL}{route}", timeout=10000)
                    # Verify we're on the route (not redirected to login)
                    if "/login" not in page.url:
                        routes_visited.append(route)

                # At least some routes should be accessible
                assert len(routes_visited) >= 3, f"Only {len(routes_visited)} routes accessible: {routes_visited}"

                # 4. Logout
                page.goto(f"{self.BASE_URL}/logout", timeout=10000)
                page.wait_for_url("**/login", timeout=10000)
                assert "/login" in page.url

                # 5. Verify can't access protected routes after logout
                page.goto(f"{self.BASE_URL}/dashboard", timeout=10000)
                page.wait_for_url("**/login", timeout=10000)
                assert "/login" in page.url

                print("\n" + "="*60)
                print("COMPLETE USER JOURNEY TEST PASSED")
                print("="*60)
                print(f"Routes successfully accessed: {routes_visited}")
                print("="*60 + "\n")

            finally:
                context.close()
                browser.close()
