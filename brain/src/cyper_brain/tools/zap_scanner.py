"""OWASP ZAP integration for web application scanning"""

import subprocess
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path


class ZAPScanner:
    """OWASP ZAP web application scanner"""

    def __init__(self, zap_path: Optional[str] = None, api_key: Optional[str] = None):
        self.zap_path = zap_path or "zap.sh"
        self.api_key = api_key or "cyper-security-zap-key"
        self.zap_proxy = "http://127.0.0.1:8090"
        self.process = None

    def start_zap(self) -> bool:
        """Start ZAP in daemon mode"""
        try:
            cmd = [
                self.zap_path,
                "-daemon",
                "-config", f"api.key={self.api_key}",
                "-port", "8090",
            ]
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for ZAP to start
            time.sleep(10)
            return True
        except Exception as e:
            print(f"Failed to start ZAP: {e}")
            return False

    def stop_zap(self):
        """Stop ZAP daemon"""
        if self.process:
            self.process.terminate()
            self.process.wait()

    def spider_scan(self, target_url: str, max_duration: int = 300) -> Dict[str, Any]:
        """
        Perform spider scan to discover URLs
        
        Args:
            target_url: Target URL to spider
            max_duration: Maximum scan duration in seconds
            
        Returns:
            Dictionary with spider results
        """
        try:
            # Start spider via ZAP API
            cmd = [
                "curl", "-s",
                f"{self.zap_proxy}/JSON/spider/action/scan/",
                f"?apikey={self.api_key}",
                f"&url={target_url}",
                "&maxDuration=" + str(max_duration)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            response = json.loads(result.stdout)
            
            if "scan" in response:
                scan_id = response["scan"]
                
                # Wait for spider to complete
                self._wait_for_spider(scan_id)
                
                # Get results
                return self._get_spider_results(scan_id)
            
            return {"error": "Failed to start spider"}
            
        except Exception as e:
            return {"error": str(e)}

    def active_scan(self, target_url: str) -> Dict[str, Any]:
        """
        Perform active security scan
        
        Args:
            target_url: Target URL to scan
            
        Returns:
            Dictionary with scan results including vulnerabilities
        """
        try:
            # Start active scan
            cmd = [
                "curl", "-s",
                f"{self.zap_proxy}/JSON/ascan/action/scan/",
                f"?apikey={self.api_key}",
                f"&url={target_url}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            response = json.loads(result.stdout)
            
            if "scan" in response:
                scan_id = response["scan"]
                
                # Wait for scan to complete
                self._wait_for_active_scan(scan_id)
                
                # Get vulnerabilities
                return self._get_alerts()
            
            return {"error": "Failed to start active scan"}
            
        except Exception as e:
            return {"error": str(e)}

    def passive_scan(self, target_url: str) -> Dict[str, Any]:
        """
        Enable passive scanning for a target
        
        Args:
            target_url: Target URL
            
        Returns:
            Passive scan results
        """
        try:
            # Access the URL through ZAP proxy to trigger passive scanning
            cmd = [
                "curl", "-s",
                "-x", "127.0.0.1:8090",
                target_url
            ]
            
            subprocess.run(cmd, capture_output=True)
            
            # Wait a bit for passive scanning
            time.sleep(5)
            
            return self._get_alerts()
            
        except Exception as e:
            return {"error": str(e)}

    def _wait_for_spider(self, scan_id: str, timeout: int = 300):
        """Wait for spider scan to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            cmd = [
                "curl", "-s",
                f"{self.zap_proxy}/JSON/spider/view/status/",
                f"?apikey={self.api_key}",
                f"&scanId={scan_id}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            response = json.loads(result.stdout)
            
            if response.get("status") == "100":
                break
                
            time.sleep(2)

    def _wait_for_active_scan(self, scan_id: str, timeout: int = 600):
        """Wait for active scan to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            cmd = [
                "curl", "-s",
                f"{self.zap_proxy}/JSON/ascan/view/status/",
                f"?apikey={self.api_key}",
                f"&scanId={scan_id}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            response = json.loads(result.stdout)
            
            if response.get("status") == "100":
                break
                
            time.sleep(5)

    def _get_spider_results(self, scan_id: str) -> Dict[str, Any]:
        """Get spider scan results"""
        cmd = [
            "curl", "-s",
            f"{self.zap_proxy}/JSON/spider/view/results/",
            f"?apikey={self.api_key}",
            f"&scanId={scan_id}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(result.stdout)

    def _get_alerts(self) -> Dict[str, Any]:
        """Get all alerts (vulnerabilities)"""
        cmd = [
            "curl", "-s",
            f"{self.zap_proxy}/JSON/core/view/alerts/",
            f"?apikey={self.api_key}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        response = json.loads(result.stdout)
        
        if "alerts" in response:
            # Parse and categorize alerts
            vulnerabilities = []
            
            for alert in response["alerts"]:
                vuln = {
                    "name": alert.get("name", "Unknown"),
                    "risk": alert.get("risk", "Unknown"),
                    "confidence": alert.get("confidence", "Unknown"),
                    "url": alert.get("url", ""),
                    "description": alert.get("description", ""),
                    "solution": alert.get("solution", ""),
                    "reference": alert.get("reference", ""),
                    "cwe_id": alert.get("cweid", ""),
                    "wasc_id": alert.get("wascid", ""),
                }
                vulnerabilities.append(vuln)
            
            return {
                "total": len(vulnerabilities),
                "vulnerabilities": vulnerabilities,
                "by_risk": self._categorize_by_risk(vulnerabilities)
            }
        
        return {"total": 0, "vulnerabilities": [], "by_risk": {}}

    def _categorize_by_risk(self, vulnerabilities: List[Dict]) -> Dict[str, int]:
        """Categorize vulnerabilities by risk level"""
        categories = {"High": 0, "Medium": 0, "Low": 0, "Informational": 0}
        
        for vuln in vulnerabilities:
            risk = vuln.get("risk", "Informational")
            if risk in categories:
                categories[risk] += 1
        
        return categories

    def full_scan(self, target_url: str) -> Dict[str, Any]:
        """
        Perform comprehensive scan (spider + active + passive)
        
        Args:
            target_url: Target URL to scan
            
        Returns:
            Complete scan results
        """
        results = {
            "target": target_url,
            "timestamp": time.time(),
            "spider": {},
            "active_scan": {},
            "summary": {}
        }
        
        # Spider scan
        print(f"Starting spider scan on {target_url}...")
        results["spider"] = self.spider_scan(target_url)
        
        # Active scan
        print(f"Starting active scan on {target_url}...")
        results["active_scan"] = self.active_scan(target_url)
        
        # Generate summary
        if "vulnerabilities" in results["active_scan"]:
            results["summary"] = {
                "total_vulnerabilities": results["active_scan"]["total"],
                "by_risk": results["active_scan"]["by_risk"],
                "high_risk_count": results["active_scan"]["by_risk"].get("High", 0),
            }
        
        return results

    def generate_report(self, output_file: str):
        """Generate HTML report"""
        cmd = [
            "curl", "-s",
            f"{self.zap_proxy}/OTHER/core/other/htmlreport/",
            f"?apikey={self.api_key}",
            "-o", output_file
        ]
        
        subprocess.run(cmd)
        print(f"Report saved to {output_file}")
