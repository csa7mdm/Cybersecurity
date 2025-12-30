"""AI-driven results analysis and interpretation"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import os
import json
from openai import OpenAI


@dataclass
class AnalysisResult:
    """Results of AI analysis"""
    executive_summary: str
    key_findings: List[str]
    critical_vulnerabilities: List[Dict[str, Any]]
    risk_score: int  # 0-100
    severity_breakdown: Dict[str, int]
    recommendations: List[str]
    next_steps: List[str]


class ResultsAnalyzer:
    """AI-powered scan results analysis"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY required")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        self.model = os.getenv("AI_MODEL", "google/gemini-2.0-flash-exp:free")

    async def analyze_scan_results(
        self,
        scan_type: str,
        raw_results: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        Analyze scan results using AI.
        
        Args:
            scan_type: Type of scan performed
            raw_results: Raw scan output
            context: Additional context
            
        Returns:
            AnalysisResult with AI interpretation
        """
        
        prompt = self._build_analysis_prompt(scan_type, raw_results, context or {})
        
        message = self.client.chat.completions.create(
            model=self.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        analysis = self._parse_analysis_response(message.choices[0].message.content)
        
        return analysis

    def _build_analysis_prompt(
        self,
        scan_type: str,
        raw_results: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for results analysis"""
        
        # Truncate large results for prompt
        results_str = json.dumps(raw_results, indent=2)
        if len(results_str) > 10000:
            results_str = results_str[:10000] + "\n... (truncated)"
        
        return f"""You are a senior cybersecurity analyst reviewing scan results.

Scan Type: {scan_type}
Context: {context}

Raw Results:
{results_str}

Please provide a comprehensive analysis including:

1. EXECUTIVE SUMMARY: 2-3 sentence high-level overview
2. KEY FINDINGS: Top 5-10 most important discoveries
3. CRITICAL VULNERABILITIES: List vulnerabilities with severity
4. RISK SCORE: Overall risk rating (0-100)
5. SEVERITY BREAKDOWN: Count of critical/high/medium/low findings
6. RECOMMENDATIONS: Prioritized action items
7. NEXT STEPS: What to do immediately

Format as:
EXECUTIVE_SUMMARY: [text]
KEY_FINDINGS:
- [finding 1]
- [finding 2]
CRITICAL_VULNERABILITIES:
- [vuln 1] (severity: critical)
- [vuln 2] (severity: high)
RISK_SCORE: [0-100]
SEVERITY_BREAKDOWN: critical:X, high:Y, medium:Z, low:W
RECOMMENDATIONS:
1. [recommendation 1]
2. [recommendation 2]
NEXT_STEPS:
1. [step 1]
2. [step 2]
"""

    def _parse_analysis_response(self, response: str) -> AnalysisResult:
        """Parse AI analysis response"""
        
        # Default values
        executive_summary = ""
        key_findings = []
        critical_vulnerabilities = []
        risk_score = 50
        severity_breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        recommendations = []
        next_steps = []
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("EXECUTIVE_SUMMARY:"):
                executive_summary = line.replace("EXECUTIVE_SUMMARY:", "").strip()
            
            elif line.startswith("KEY_FINDINGS:"):
                current_section = "findings"
            
            elif line.startswith("CRITICAL_VULNERABILITIES:"):
                current_section = "vulnerabilities"
            
            elif line.startswith("RISK_SCORE:"):
                try:
                    risk_score = int(line.replace("RISK_SCORE:", "").strip())
                except:
                    pass
            
            elif line.startswith("SEVERITY_BREAKDOWN:"):
                breakdown_str = line.replace("SEVERITY_BREAKDOWN:", "").strip()
                for part in breakdown_str.split(','):
                    if ':' in part:
                        sev, count = part.split(':')
                        try:
                            severity_breakdown[sev.strip()] = int(count.strip())
                        except:
                            pass
            
            elif line.startswith("RECOMMENDATIONS:"):
                current_section = "recommendations"
            
            elif line.startswith("NEXT_STEPS:"):
                current_section = "next_steps"
            
            elif line.startswith("-") or line.startswith("•"):
                item = line[1:].strip()
                
                if current_section == "findings":
                    key_findings.append(item)
                
                elif current_section == "vulnerabilities":
                    # Parse vulnerability
                    severity = "medium"
                    if "(severity:" in item:
                        try:
                            severity = item.split("(severity:")[1].split(")")[0].strip()
                        except:
                            pass
                    
                    critical_vulnerabilities.append({
                        "description": item.split("(severity:")[0].strip(),
                        "severity": severity
                    })
            
            elif line and line[0].isdigit() and '.' in line:
                item = line.split('.', 1)[1].strip()
                
                if current_section == "recommendations":
                    recommendations.append(item)
                elif current_section == "next_steps":
                    next_steps.append(item)
        
        return AnalysisResult(
            executive_summary=executive_summary,
            key_findings=key_findings,
            critical_vulnerabilities=critical_vulnerabilities,
            risk_score=risk_score,
            severity_breakdown=severity_breakdown,
            recommendations=recommendations,
            next_steps=next_steps
        )

    async def compare_scans(
        self,
        previous_results: Dict[str, Any],
        current_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare two scan results to identify changes"""
        
        prompt = f"""Compare these two security scans and identify:

1. New vulnerabilities discovered
2. Fixed vulnerabilities
3. Changes in risk level
4. Security posture trend (improving/degrading)

Previous Scan:
{json.dumps(previous_results, indent=2)[:5000]}

Current Scan:
{json.dumps(current_results, indent=2)[:5000]}

Provide analysis of changes and trends."""

        message = self.client.chat.completions.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            "comparison_analysis": message.choices[0].message.content,
            "trend": "stable"  # TODO: Parse from response
        }

    def calculate_risk_score(
        self,
        vulnerabilities: List[Dict[str, Any]]
    ) -> int:
        """Calculate overall risk score from vulnerabilities"""
        
        if not vulnerabilities:
            return 0
        
        # Weight by severity
        weights = {
            "critical": 25,
            "high": 15,
            "medium": 5,
            "low": 1,
            "info": 0
        }
        
        total_score = 0
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "medium").lower()
            total_score += weights.get(severity, 5)
        
        # Cap at 100
        return min(100, total_score)

    def prioritize_vulnerabilities(
        self,
        vulnerabilities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Sort vulnerabilities by priority"""
        
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        
        return sorted(
            vulnerabilities,
            key=lambda v: severity_order.get(v.get("severity", "medium").lower(), 2)
        )
