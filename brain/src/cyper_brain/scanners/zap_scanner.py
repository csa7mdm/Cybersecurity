"""
OWASP ZAP Web Scanner Integration

Implements web application vulnerability scanning.
Following TDD - tests in test_zap_scanner.py
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ZAP Python API
try:
    from zapv2 import ZAPv2
except ImportError:
    ZAPv2 = None
    logger.warning("python-owasp-zap-v2.4 not installed - ZAP scanning disabled")


class OWASPCategory(Enum):
    """OWASP Top 10 2021 Categories"""
    A01_BROKEN_ACCESS = "A01:2021 - Broken Access Control"
    A02_CRYPTO_FAILURES = "A02:2021 - Cryptographic Failures"
    A03_INJECTION = "A03:2021 - Injection"
    A04_INSECURE_DESIGN = "A04:2021 - Insecure Design"
    A05_SECURITY_MISCONFIG = "A05:2021 - Security Misconfiguration"
    A06_VULNERABLE_COMPONENTS = "A06:2021 - Vulnerable and Outdated Components"
    A07_AUTH_FAILURES = "A07:2021 - Identification and Authentication Failures"
    A08_DATA_INTEGRITY = "A08:2021 - Software and Data Integrity Failures"
    A09_LOGGING_FAILURES = "A09:2021 - Security Logging and Monitoring Failures"
    A10_SSRF = "A10:2021 - Server-Side Request Forgery"
    UNKNOWN = "Unknown Category"


@dataclass
class Vulnerability:
    """Represents a web vulnerability"""
    title: str
    severity: str  # high, medium, low, informational
    description: str
    url: str
    parameter: Optional[str] = None
    attack: Optional[str] = None
    evidence: Optional[str] = None
    solution: Optional[str] = None
    cwe_id: Optional[str] = None
    wasc_id: Optional[str] = None
    confidence: str = "medium"
    
    def get_owasp_category(self) -> OWASPCategory:
        """Map vulnerability to OWASP Top 10 category"""
        title_lower = self.title.lower()
        
        # Injection vulnerabilities
        if any(term in title_lower for term in ["sql injection", "xss", "cross site scripting", 
                                                  "command injection", "ldap injection"]):
            return OWASPCategory.A03_INJECTION
        
        # Authentication/Authorization
        if any(term in title_lower for term in ["authentication", "authorization", "session",
                                                 "access control"]):
            if "broken access" in title_lower:
                return OWASPCategory.A01_BROKEN_ACCESS
            return OWASPCategory.A07_AUTH_FAILURES
        
        # Cryptography
        if any(term in title_lower for term in ["crypto", "encryption", "ssl", "tls", "weak"]):
            return OWASPCategory.A02_CRYPTO_FAILURES
        
        # Misconfiguration
        if any(term in title_lower for term in ["misconfiguration", "default", "directory listing"]):
            return OWASPCategory.A05_SECURITY_MISCONFIG
        
        # SSRF
        if "ssrf" in title_lower or "server side request" in title_lower:
            return OWASPCategory.A10_SSRF
        
        return OWASPCategory.UNKNOWN
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "severity": self.severity,
            "description": self.description,
            "url": self.url,
            "parameter": self.parameter,
            "attack": self.attack,
            "evidence": self.evidence,
            "solution": self.solution,
            "owasp_category": self.get_owasp_category().value
        }


@dataclass
class ZAPScanResult:
    """Results from a ZAP scan"""
    target: str
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    scan_duration: float = 0.0
    pages_crawled: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for AI analysis"""
        return {
            "target": self.target,
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "vulnerability_count": len(self.vulnerabilities),
            "high_severity_count": sum(1 for v in self.vulnerabilities if v.severity == "high"),
            "scan_duration": self.scan_duration,
            "pages_crawled": self.pages_crawled
        }


class ZAPScanner:
    """
    OWASP ZAP Web Vulnerability Scanner
    
    Performs automated web application security testing.
    Requires ZAP to be running (typically on localhost:8080)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        zap_url: str = "http://localhost:8080",
        scan_timeout: int = 1800  # 30 minutes
    ):
        """
        Initialize ZAP scanner
        
        Args:
            api_key: ZAP API key (or from ZAP_API_KEY env)
            zap_url: ZAP proxy URL
            scan_timeout: Maximum scan duration in seconds
        """
        import os
        self.api_key = api_key or os.getenv("ZAP_API_KEY", "")
        self.zap_url = zap_url
        self.scan_timeout = scan_timeout
        
        if ZAPv2:
            self.zap = ZAPv2(
                apikey=self.api_key,
                proxies={'http': zap_url, 'https': zap_url}
            )
        else:
            self.zap = None
            logger.error("ZAP client not available")
    
    def _validate_url(self, url: str):
        """Validate target URL"""
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise ValueError(f"Invalid URL: {url}")
        except Exception as e:
            raise ValueError(f"Invalid URL: {url}") from e
    
    def spider(self, target_url: str, max_depth: int = 5) -> str:
        """
        Spider/crawl the target website
        
        Args:
            target_url: URL to spider
            max_depth: Maximum crawl depth
        
        Returns:
            Spider scan ID
        """
        self._validate_url(target_url)
        
        if not self.zap:
            raise ConnectionError("ZAP client not initialized")
        
        logger.info(f"Starting spider on {target_url}")
        scan_id = self.zap.spider.scan(target_url, maxdepth=max_depth)
        
        return scan_id
    
    def wait_for_spider(self, scan_id: str, max_wait: int = 600):
        """Wait for spider to complete"""
        start_time = time.time()
        
        while True:
            if time.time() - start_time > max_wait:
                raise TimeoutError(f"Spider timeout after {max_wait}s")
            
            status = int(self.zap.spider.status(scan_id))
            logger.info(f"Spider progress: {status}%")
            
            if status >= 100:
                break
            
            time.sleep(2)
    
    def active_scan(
        self,
        target_url: str,
        context_name: Optional[str] = None
    ) -> str:
        """
        Perform active vulnerability scan
        
        Args:
            target_url: URL to scan
            context_name: Optional authentication context
        
        Returns:
            Active scan ID
        """
        self._validate_url(target_url)
        
        if not self.zap:
            raise ConnectionError("ZAP client not initialized")
        
        logger.info(f"Starting active scan on {target_url}")
        
        # Start scan
        if context_name:
            scan_id = self.zap.ascan.scan(target_url, contextid=context_name)
        else:
            scan_id = self.zap.ascan.scan(target_url)
        
        return scan_id
    
    def wait_for_active_scan(self, scan_id: str):
        """Wait for active scan to complete"""
        start_time = time.time()
        
        while True:
            if time.time() - start_time > self.scan_timeout:
                raise TimeoutError(f"Scan timeout after {self.scan_timeout}s")
            
            status = int(self.zap.ascan.status(scan_id))
            logger.info(f"Active scan progress: {status}%")
            
            if status >= 100:
                break
            
            time.sleep(5)
    
    def get_vulnerabilities(self, min_risk: str = "Low") -> List[Vulnerability]:
        """
        Get detected vulnerabilities
        
        Args:
            min_risk: Minimum risk level (High, Medium, Low, Informational)
        
        Returns:
            List of vulnerabilities
        """
        if not self.zap:
            return []
        
        alerts = self.zap.core.alerts()
        vulnerabilities = []
        
        risk_levels = ["Informational", "Low", "Medium", "High"]
        min_risk_index = risk_levels.index(min_risk) if min_risk in risk_levels else 0
        
        for alert in alerts:
            risk = alert.get("risk", "Low")
            
            # Filter by risk level
            if risk_levels.index(risk) < min_risk_index:
                continue
            
            vuln = Vulnerability(
                title=alert.get("alert", "Unknown"),
                severity=risk.lower(),
                description=alert.get("description", ""),
                url=alert.get("url", ""),
                parameter=alert.get("param"),
                attack=alert.get("attack"),
                evidence=alert.get("evidence"),
                solution=alert.get("solution"),
                cwe_id=alert.get("cweid"),
                wasc_id=alert.get("wascid"),
                confidence=alert.get("confidence", "Medium").lower()
            )
            
            vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def scan(self, target_url: str, spider_first: bool = True) -> ZAPScanResult:
        """
        Perform complete scan (spider + active scan)
        
        Args:
            target_url: URL to scan
            spider_first: Whether to spider before active scan
        
        Returns:
            ZAPScanResult with vulnerabilities
        """
        self._validate_url(target_url)
        start_time = time.time()
        
        logger.info(f"Starting ZAP scan of {target_url}")
        
        # Spider to discover pages
        pages_crawled = 0
        if spider_first:
            spider_id = self.spider(target_url)
            self.wait_for_spider(spider_id)
            # Get number of URLs found
            pages_crawled = len(self.zap.core.urls())
        
        # Active scan for vulnerabilities
        scan_id = self.active_scan(target_url)
        self.wait_for_active_scan(scan_id)
        
        # Collect vulnerabilities
        vulnerabilities = self.get_vulnerabilities()
        
        duration = time.time() - start_time
        
        result = ZAPScanResult(
            target=target_url,
            vulnerabilities=vulnerabilities,
            scan_duration=duration,
            pages_crawled=pages_crawled
        )
        
        logger.info(f"Scan complete: {len(vulnerabilities)} vulnerabilities found in {duration:.1f}s")
        
        return result
    
    def generate_html_report(self) -> str:
        """Generate HTML vulnerability report"""
        if not self.zap:
            return ""
        
        return self.zap.core.htmlreport()
