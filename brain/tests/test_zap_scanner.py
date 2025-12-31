"""
TDD Tests for OWASP ZAP Web Scanner Integration

Testing web application vulnerability scanning:
- Spider/crawl functionality
- Active scanning
- Vulnerability detection (OWASP Top 10)
- Report parsing
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from cyper_brain.scanners.zap_scanner import (
    ZAPScanner,
    ZAPScanResult,
    Vulnerability,
    OWASPCategory
)


class TestZAPScannerInitialization:
    """Test ZAP scanner setup"""
    
    def test_scanner_initialization(self):
        """Should initialize with ZAP API client"""
        scanner = ZAPScanner(api_key="test_key", zap_url="http://localhost:8080")
        assert scanner is not None
        assert scanner.zap_url == "http://localhost:8080"
    
    def test_default_zap_url(self):
        """Should use default ZAP URL if not specified"""
        scanner = ZAPScanner()
        assert "localhost" in scanner.zap_url or "127.0.0.1" in scanner.zap_url


class TestSpiderScan:
    """Test website crawling/spidering"""
    
    @patch('zapv2.ZAPv2')
    def test_spider_target_url(self, mock_zap):
        """Should spider target URL to discover pages"""
        mock_spider = Mock()
        mock_zap.return_value.spider = mock_spider
        mock_spider.scan.return_value = "scan_id_123"
        mock_spider.status.return_value = "100"  # Complete
        
        scanner = ZAPScanner(api_key="test_key")
        spider_id = scanner.spider("https://example.com")
        
        assert spider_id == "scan_id_123"
        mock_spider.scan.assert_called_once_with("https://example.com")
    
    @patch('zapv2.ZAPv2')
    def test_wait_for_spider_completion(self, mock_zap):
        """Should wait for spider to complete"""
        mock_spider = Mock()
        mock_zap.return_value.spider = mock_spider
        mock_spider.status.side_effect = ["0", "50", "100"]  # Progress
        
        scanner = ZAPScanner()
        scanner.wait_for_spider("scan_id", max_wait=5)
        
        assert mock_spider.status.call_count >= 1


class TestActiveScan:
    """Test active vulnerability scanning"""
    
    @patch('zapv2.ZAPv2')
    def test_active_scan_target(self, mock_zap):
        """Should perform active scan on target"""
        mock_ascan = Mock()
        mock_zap.return_value.ascan = mock_ascan
        mock_ascan.scan.return_value = "ascan_id_456"
        mock_ascan.status.return_value = "100"
        
        scanner = ZAPScanner()
        scan_id = scanner.active_scan("https://example.com")
        
        assert scan_id == "ascan_id_456"
        mock_ascan.scan.assert_called_once()
    
    @patch('zapv2.ZAPv2')
    def test_active_scan_with_context(self, mock_zap):
        """Should support scanning with authentication context"""
        mock_ascan = Mock()
        mock_zap.return_value.ascan = mock_ascan
        
        scanner = ZAPScanner()
        scanner.active_scan(
            "https://example.com",
            context_name="auth_context"
        )
        
        # Verify context was used
        call_args = mock_ascan.scan.call_args
        assert call_args is not None


class TestVulnerabilityDetection:
    """Test vulnerability finding and classification"""
    
    @patch('zapv2.ZAPv2')
    def test_get_alerts(self, mock_zap):
        """Should retrieve vulnerability alerts"""
        mock_core = Mock()
        mock_zap.return_value.core = mock_core
        mock_core.alerts.return_value = [
            {
                "alert": "SQL Injection",
                "risk": "High",
                "confidence": "Medium",
                "url": "https://example.com/api/users",
                "param": "id",
                "attack": "' OR '1'='1",
                "evidence": "SQL error message"
            }
        ]
        
        scanner = ZAPScanner()
        vulnerabilities = scanner.get_vulnerabilities()
        
        assert len(vulnerabilities) == 1
        assert vulnerabilities[0].title == "SQL Injection"
        assert vulnerabilities[0].severity == "high"
    
    @patch('zapv2.ZAPv2')
    def test_filter_by_severity(self, mock_zap):
        """Should filter vulnerabilities by severity"""
        mock_core = Mock()
        mock_zap.return_value.core = mock_core
        mock_core.alerts.return_value = [
            {"alert": "Critical Issue", "risk": "High", "confidence": "High"},
            {"alert": "Minor Issue", "risk": "Low", "confidence": "Medium"}
        ]
        
        scanner = ZAPScanner()
        high_vulns = scanner.get_vulnerabilities(min_risk="High")
        
        assert len(high_vulns) == 1
        assert high_vulns[0].title == "Critical Issue"


class TestOWASPMapping:
    """Test mapping to OWASP Top 10 categories"""
    
    def test_map_sql_injection_to_owasp(self):
        """Should map SQL injection to A03:2021 Injection"""
        vuln = Vulnerability(
            title="SQL Injection",
            severity="high",
            description="SQL injection vulnerability",
            url="https://example.com/api"
        )
        
        category = vuln.get_owasp_category()
        assert category == OWASPCategory.A03_INJECTION
    
    def test_map_xss_to_owasp(self):
        """Should map XSS to A03:2021 Injection"""
        vuln = Vulnerability(
            title="Cross Site Scripting (Reflected)",
            severity="medium",
            description="XSS vulnerability",
            url="https://example.com"
        )
        
        category = vuln.get_owasp_category()
        assert category == OWASPCategory.A03_INJECTION
    
    def test_map_auth_bypass_to_owasp(self):
        """Should map auth issues to A07:2021"""
        vuln = Vulnerability(
            title="Broken Authentication",
            severity="high",
            description="Authentication bypass",
            url="https://example.com/login"
        )
        
        category = vuln.get_owasp_category()
        assert category == OWASPCategory.A07_AUTH_FAILURES


class TestScanWorkflow:
    """Test complete scan workflow"""
    
    @patch('zapv2.ZAPv2')
    def test_full_scan_workflow(self, mock_zap):
        """Should execute complete spider + active scan"""
        # Mock ZAP responses
        mock_spider = Mock()
        mock_ascan = Mock()
        mock_core = Mock()
        
        mock_zap.return_value.spider = mock_spider
        mock_zap.return_value.ascan = mock_ascan
        mock_zap.return_value.core = mock_core
        
        mock_spider.scan.return_value = "spider_123"
        mock_spider.status.return_value = "100"
        mock_ascan.scan.return_value = "ascan_456"
        mock_ascan.status.return_value = "100"
        mock_core.alerts.return_value = []
        
        scanner = ZAPScanner()
        result = scanner.scan("https://example.com")
        
        assert isinstance(result, ZAPScanResult)
        assert result.target == "https://example.com"
        mock_spider.scan.assert_called_once()
        mock_ascan.scan.assert_called_once()


class TestReportGeneration:
    """Test vulnerability report generation"""
    
    @patch('zapv2.ZAPv2')
    def test_generate_html_report(self, mock_zap):
        """Should generate HTML vulnerability report"""
        mock_core = Mock()
        mock_zap.return_value.core = mock_core
        mock_core.htmlreport.return_value = "<html>Report</html>"
        
        scanner = ZAPScanner()
        html = scanner.generate_html_report()
        
        assert "<html>" in html
        assert "Report" in html
    
    @patch('zapv2.ZAPv2')
    def test_export_json_results(self, mock_zap):
        """Should export results as JSON"""
        scanner = ZAPScanner()
        
        result = ZAPScanResult(
            target="https://example.com",
            vulnerabilities=[
                Vulnerability(
                    title="XSS",
                    severity="medium",
                    description="Cross-site scripting",
                    url="https://example.com/search"
                )
            ]
        )
        
        json_data = result.to_dict()
        
        assert json_data["target"] == "https://example.com"
        assert len(json_data["vulnerabilities"]) == 1
        assert json_data["vulnerabilities"][0]["title"] == "XSS"


class TestErrorHandling:
    """Test error scenarios"""
    
    @patch('zapv2.ZAPv2')
    def test_handle_zap_not_running(self, mock_zap):
        """Should raise error if ZAP is not accessible"""
        mock_zap.side_effect = ConnectionError("ZAP not running")
        
        with pytest.raises(ConnectionError):
            scanner = ZAPScanner()
            scanner.spider("https://example.com")
    
    def test_invalid_target_url(self):
        """Should validate target URL format"""
        scanner = ZAPScanner()
        
        with pytest.raises(ValueError, match="Invalid URL"):
            scanner.scan("not-a-valid-url")
    
    @patch('zapv2.ZAPv2')
    def test_scan_timeout(self, mock_zap):
        """Should handle scan timeout gracefully"""
        mock_ascan = Mock()
        mock_zap.return_value.ascan = mock_ascan
        mock_ascan.status.return_value = "50"  # Never completes
        
        scanner = ZAPScanner(scan_timeout=1)
        
        with pytest.raises(TimeoutError):
            scanner.active_scan("https://example.com")


# Fixtures
@pytest.fixture
def sample_vulnerabilities():
    """Sample vulnerabilities for testing"""
    return [
        Vulnerability(
            title="SQL Injection",
            severity="high",
            description="SQL injection in user parameter",
            url="https://example.com/api/users?id=1",
            parameter="id",
            evidence="SQL syntax error",
            solution="Use prepared statements"
        ),
        Vulnerability(
            title="Cross Site Scripting",
            severity="medium",
            description="Reflected XSS in search",
            url="https://example.com/search?q=test",
            parameter="q",
            evidence="<script> tag reflected"
        )
    ]


@pytest.fixture
def mock_zap_alerts():
    """Mock ZAP alert responses"""
    return [
        {
            "alert": "SQL Injection",
            "risk": "High",
            "confidence": "High",
            "url": "https://example.com/api",
            "param": "id",
            "attack": "' OR '1'='1",
            "evidence": "SQL error",
            "solution": "Use prepared statements",
            "cweid": "89",
            "wascid": "19"
        }
    ]
