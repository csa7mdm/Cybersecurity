"""
TDD Tests for CVE Database Integration

Testing vulnerability intelligence enrichment via NVD API
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from cyper_brain.vulnerability.cve_service import (
    CVEService,
    CVEData,
    CVSSScore,
    VulnerabilityNotFound
)


class TestCVELookup:
    """Test CVE database lookups"""
    
    @patch('requests.get')
    def test_lookup_cve_by_id(self, mock_get):
        """Should fetch CVE data from NVD API"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "vulnerabilities": [{
                "cve": {
                    "id": "CVE-2024-1234",
                    "descriptions": [{
                        "lang": "en",
                        "value": "SQL injection vulnerability in example.com"
                    }],
                    "metrics": {
                        "cvssMetricV31": [{
                            "cvssData": {
                                "baseScore": 9.8,
                                "baseSeverity": "CRITICAL"
                            }
                        }]
                    },
                    "published": "2024-01-15T10:00:00.000"
                }
            }]
        }
        mock_get.return_value = mock_response
        
        service = CVEService(api_key="test_key")
        cve = service.lookup("CVE-2024-1234")
        
        assert cve.cve_id == "CVE-2024-1234"
        assert "SQL injection" in cve.description
        assert cve.cvss_score == 9.8
        assert cve.severity == "CRITICAL"
    
    @patch('requests.get')
    def test_cve_not_found(self, mock_get):
        """Should raise exception when CVE not found"""
        mock_response = Mock()
        mock_response.json.return_value = {"vulnerabilities": []}
        mock_get.return_value = mock_response
        
        service = CVEService()
        
        with pytest.raises(VulnerabilityNotFound):
            service.lookup("CVE-9999-0000")
    
    @patch('requests.get')
    def test_cache_cve_results(self, mock_get):
        """Should cache CVE lookups to reduce API calls"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "vulnerabilities": [{
                "cve": {
                    "id": "CVE-2024-1234",
                    "descriptions": [{"lang": "en", "value": "Test CVE"}],
                    "metrics": {"cvssMetricV31": [{"cvssData": {"baseScore": 7.5}}]}
                }
            }]
        }
        mock_get.return_value = mock_response
        
        service = CVEService()
        
        # First call
        cve1 = service.lookup("CVE-2024-1234")
        # Second call (should use cache)
        cve2 = service.lookup("CVE-2024-1234")
        
        # API should only be called once
        assert mock_get.call_count == 1
        assert cve1.cve_id == cve2.cve_id


class TestCVSSCalculation:
    """Test CVSS score handling"""
    
    def test_parse_cvss_v3_score(self):
        """Should parse CVSS v3.1 scores"""
        cvss = CVSSScore(
            version="3.1",
            base_score=9.8,
            vector_string="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
        )
        
        assert cvss.base_score == 9.8
        assert cvss.get_severity() == "CRITICAL"
    
    def test_cvss_severity_mapping(self):
        """Should correctly map scores to severity levels"""
        assert CVSSScore(base_score=0.0).get_severity() == "NONE"
        assert CVSSScore(base_score=3.5).get_severity() == "LOW"
        assert CVSSScore(base_score=6.0).get_severity() == "MEDIUM"
        assert CVSSScore(base_score=8.0).get_severity() == "HIGH"
        assert CVSSScore(base_score=9.5).get_severity() == "CRITICAL"


class TestVulnerabilityEnrichment:
    """Test enriching scan results with CVE data"""
    
    @patch.object(CVEService, 'lookup')
    def test_enrich_scan_with_cve_data(self, mock_lookup):
        """Should enrich scan findings with CVE intelligence"""
        # Mock CVE data
        mock_lookup.return_value = CVEData(
            cve_id="CVE-2024-1234",
            description="SQL injection in user parameter",
            cvss_score=9.8,
            severity="CRITICAL",
            published_date=datetime(2024, 1, 15),
            references=["https://example.com/advisory"]
        )
        
        service = CVEService()
        
        # Scan finding that references a CVE
        finding = {
            "title": "SQL Injection",
            "cve_id": "CVE-2024-1234"
        }
        
        enriched = service.enrich_finding(finding)
        
        assert enriched["cvss_score"] == 9.8
        assert enriched["severity"] == "CRITICAL"
        assert "SQL injection" in enriched["cve_description"]
        assert len(enriched["references"]) > 0
    
    @patch.object(CVEService, 'lookup')
    def test_enrich_multiple_findings(self, mock_lookup):
        """Should enrich multiple findings in batch"""
        service = CVEService()
        
        findings = [
            {"title": "XSS", "cve_id": "CVE-2024-0001"},
            {"title": "CSRF", "cve_id": "CVE-2024-0002"}
        ]
        
        enriched = service.enrich_findings(findings)
        
        assert len(enriched) == 2
        assert mock_lookup.call_count == 2


class TestCVESearching:
    """Test searching CVE database"""
    
    @patch('requests.get')
    def test_search_by_keyword(self, mock_get):
        """Should search CVEs by keyword"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2024-1111",
                        "descriptions": [{"value": "Apache vulnerability"}]
                    }
                },
                {
                    "cve": {
                        "id": "CVE-2024-2222",
                        "descriptions": [{"value": "Apache RCE"}]
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        service = CVEService()
        results = service.search(keyword="Apache")
        
        assert len(results) == 2
        assert all("Apache" in r.description for r in results)
    
    @patch('requests.get')
    def test_search_by_product(self, mock_get):
        """Should search CVEs for specific products"""
        service = CVEService()
        
        results = service.search(product="nginx", version="1.18.0")
        
        # Verify API was called with correct parameters
        call_args = mock_get.call_args
        assert "nginx" in str(call_args)


class TestThreatIntelligence:
    """Test threat intelligence matching"""
    
    def test_match_exploit_availability(self):
        """Should check if CVE has known exploits"""
        cve = CVEData(
            cve_id="CVE-2024-1234",
            description="RCE vulnerability",
            cvss_score=9.8
        )
        
        service = CVEService()
        
        # Mock exploit database check
        with patch.object(service, 'check_exploits') as mock_check:
            mock_check.return_value = True
            
            has_exploit = service.has_known_exploit(cve)
            assert has_exploit is True
    
    def test_get_cisa_known_exploited(self):
        """Should check CISA Known Exploited Vulnerabilities"""
        service = CVEService()
        
        with patch.object(service, 'get_cisa_kev') as mock_kev:
            mock_kev.return_value = ["CVE-2024-1234", "CVE-2024-5678"]
            
            is_exploited = service.is_actively_exploited("CVE-2024-1234")
            assert is_exploited is True


class TestCVEExport:
    """Test CVE data export"""
    
    def test_export_to_json(self):
        """Should export CVE data to JSON"""
        cve = CVEData(
            cve_id="CVE-2024-1234",
            description="Test vulnerability",
            cvss_score=7.5,
            severity="HIGH",
            published_date=datetime(2024, 1, 15)
        )
        
        json_data = cve.to_dict()
        
        assert json_data["cve_id"] == "CVE-2024-1234"
        assert json_data["cvss_score"] == 7.5
        assert json_data["severity"] == "HIGH"


# Fixtures
@pytest.fixture
def sample_cve_response():
    """Sample NVD API response"""
    return {
        "vulnerabilities": [{
            "cve": {
                "id": "CVE-2024-1234",
                "descriptions": [{
                    "lang": "en",
                    "value": "SQL injection vulnerability allows remote attackers to execute arbitrary SQL commands"
                }],
                "metrics": {
                    "cvssMetricV31": [{
                        "cvssData": {
                            "version": "3.1",
                            "baseScore": 9.8,
                            "baseSeverity": "CRITICAL",
                            "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
                        }
                    }]
                },
                "published": "2024-01-15T10:00:00.000",
                "references": [
                    {"url": "https://example.com/advisory"}
                ]
            }
        }]
    }


@pytest.fixture
def sample_cve_data():
    """Sample CVE data object"""
    return CVEData(
        cve_id="CVE-2024-1234",
        description="SQL injection vulnerability",
        cvss_score=9.8,
        severity="CRITICAL",
        published_date=datetime(2024, 1, 15),
        references=["https://example.com/advisory"],
        affected_products=["Example App v1.0"]
    )
