"""AI orchestration agent"""

import os
from typing import Dict, Any, Optional, List
from openai import OpenAI

from .scan_planner import ScanPlanner, ScanPlan
from .results_analyzer import ResultsAnalyzer, AnalysisResult
from ..reporting.generator import ReportGenerator


class CyperAI:
    """Main AI orchestration engine"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY must be provided")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        self.model = os.getenv("AI_MODEL", "google/gemini-2.0-flash-exp:free")
        
        # Sub-modules
        self.scan_planner = ScanPlanner(api_key=self.api_key)
        self.results_analyzer = ResultsAnalyzer(api_key=self.api_key)
        self.report_generator = ReportGenerator()

    async def analyze_target(
        self,
        target: str,
        scan_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ScanPlan:
        """
        Analyze a target and create an intelligent scan plan.
        
        Args:
            target: The target to analyze (IP, domain, network, etc.)
            scan_type: Type of scan to perform (wifi, network, web, cloud)
            context: Additional context about the target
            
        Returns:
            ScanPlan with AI-generated recommendations
        """
        return await self.scan_planner.create_scan_plan(target, scan_type, context)

    async def interpret_results(
        self,
        scan_type: str,
        raw_results: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        Interpret scan results using AI.
        
        Args:
            scan_type: Type of scan performed
            raw_results: Raw scan output
            context: Additional context
            
        Returns:
            AnalysisResult with analyzed and interpreted results
        """
        return await self.results_analyzer.analyze_scan_results(
            scan_type,
            raw_results,
            context
        )

    async def generate_report(
        self,
        scan_results: Dict[str, Any],
        report_type: str = "technical",
        analysis: Optional[AnalysisResult] = None
    ) -> str:
        """
        Generate a security report using AI.
        
        Args:
            scan_results: Scan results to report on
            report_type: Type of report (executive, technical, compliance)
            analysis: Pre-computed analysis (optional)
            
        Returns:
            Generated report content (markdown)
        """
        
        # Get analysis if not provided
        if analysis is None:
            analysis = await self.interpret_results(
                scan_type=scan_results.get("scan_type", "unknown"),
                raw_results=scan_results
            )
        
        prompt = self._build_report_prompt(scan_results, report_type, analysis)
        
        message = self.client.chat.completions.create(
            model=self.model,
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text

    def _build_report_prompt(
        self,
        scan_results: Dict[str, Any],
        report_type: str,
        analysis: AnalysisResult
    ) -> str:
        """Build prompt for report generation"""
        
        if report_type == "executive":
            return f"""Generate an executive summary report for business stakeholders.

Analysis Summary:
{analysis.executive_summary}

Risk Score: {analysis.risk_score}/100

Key Findings:
{chr(10).join(f"- {f}" for f in analysis.key_findings)}

Critical Vulnerabilities: {len(analysis.critical_vulnerabilities)}

Create a concise, business-focused report in markdown format that:
1. Summarizes the security posture in plain language
2. Highlights business risks and impacts
3. Provides clear action items for leadership
4. Avoids technical jargon

Include sections:
# Executive Summary
## Risk Overview
## Critical Findings
## Recommended Actions
## Timeline and Resources Required
"""
        
        elif report_type == "technical":
            vulns_str = "\n".join(
                 f"- {v['description']} ({v['severity']})"
                for v in analysis.critical_vulnerabilities[:20]
            )
            
            return f"""Generate a detailed technical security report.

Executive Summary:
{analysis.executive_summary}

Risk Score: {analysis.risk_score}/100

Severity Breakdown:
- Critical: {analysis.severity_breakdown.get('critical', 0)}
- High: {analysis.severity_breakdown.get('high', 0)}
- Medium: {analysis.severity_breakdown.get('medium', 0)}
- Low: {analysis.severity_breakdown.get('low', 0)}

Critical Vulnerabilities:
{vulns_str}

Recommendations:
{chr(10).join(f"{i+1}. {r}" for i, r in enumerate(analysis.recommendations))}

Create a comprehensive technical report in markdown format that includes:

# Technical Security Assessment Report

## 1. Executive Summary
## 2. Scope and Methodology
## 3. Findings
### 3.1 Critical Vulnerabilities
### 3.2 High Severity Issues
### 3.3 Medium and Low Findings
## 4. Risk Analysis
## 5. Detailed Recommendations
## 6. Remediation Roadmap
## 7. Technical Appendices

Include specific technical details, exploitation scenarios, and remediation steps.
"""
        
        else:  # compliance
            return f"""Generate a compliance-focused security report.

Analysis: {analysis.executive_summary}
Risk Score: {analysis.risk_score}/100

Create a compliance report covering:
1. Regulatory requirements (GDPR, PCI-DSS, etc.)
2. Compliance gaps identified
3. Remediation required for compliance
4. Evidence and documentation
"""

    async def answer_question(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Answer security-related questions using AI.
        
        Args:
            question: User's question
            context: Relevant context (scan results, etc.)
            
        Returns:
            AI-generated answer
        """
        
        context_str = f"\nContext: {context}" if context else ""
        
        message = self.client.chat.completions.create(
            model=self.model,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": f"""You are a cybersecurity expert assistant.

Question: {question}{context_str}

Provide a clear, accurate answer with relevant security best practices."""
            }]
        )
        
        return message.content[0].text

    def generate_formatted_report(
        self,
        analysis: AnalysisResult,
        scan_metadata: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Generate a professional PDF report from analysis results.
        
        Args:
            analysis: The AI analysis result
            scan_metadata: Context info (target_ip, scan_id, etc.)
            output_path: Where to save the PDF
            
        Returns:
            Path to the generated PDF
        """
        # Convert AnalysisResult using vars() or dict comprehension since it's a dataclass
        # note: asdict needs dataclasses import
        from dataclasses import asdict
        
        data = asdict(analysis)
        
        # Merge with metadata
        data.update(scan_metadata)
        
        # Ensure 'findings' is populated for the template
        # The template expects 'findings' list with 'name', 'severity', 'description'
        if "findings" not in data:
            # Re-map from critical_vulnerabilities if needed
            findings = []
            for vuln in data.get("critical_vulnerabilities", []):
                findings.append({
                    "name": vuln.get("description", "Unknown Vulnerability"),
                    "severity": vuln.get("severity", "High"),
                    "description": vuln.get("description"),
                    "details": "Detected during automated scan.",
                    "remediation": "Please patch immediately." # Placeholder - AI should provide this
                })
            data["findings"] = findings

        return self.report_generator.generate_pdf(data, output_path)
