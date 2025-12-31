import os
from typing import Dict, Any, List
from datetime import datetime
import jinja2
from weasyprint import HTML, CSS

class ReportGenerator:
    """Generates professional PDF reports from analysis results."""

    def __init__(self, template_dir: str = None):
        if template_dir is None:
            # Default to local templates directory
            template_dir = os.path.join(os.path.dirname(__file__), "templates")
        
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )

    def generate_pdf(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Generates a PDF report.
        
        Args:
            data: Dictionary containing report data (target, findings, summary, etc.)
            output_path: Path to save the generated PDF.
            
        Returns:
            str: Path to the generated PDF.
        """
        # 1. Prepare data context
        context = self._prepare_context(data)
        
        # 2. Render HTML
        # We start with the executive summary as the main entry point
        # In a real implementation, we might concatenate multiple rendered templates
        template = self.env.get_template("executive_summary.html")
        html_content = template.render(**context)
        
        # 3. Generate PDF
        HTML(string=html_content).write_pdf(output_path)
        
        return output_path

    def _prepare_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enriches raw data with formatting for the template."""
        return {
            "title": data.get("title", "Security Assessment Report"),
            "target": data.get("target_ip", "Unknown"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "scan_id": data.get("scan_id", "N/A"),
            "summary": data.get("summary", "No summary provided."),
            "risk_score": data.get("risk_score", 0),
            "findings": data.get("findings", []),
            "recommendations": data.get("recommendations", []),
            "year": datetime.now().year
        }

    # Helper method to combine exec summary + technical details if needed
    def generate_full_report(self, data: Dict[str, Any], output_path: str) -> str:
        """Generates a comprehensive report with both summary and technical details."""
        context = self._prepare_context(data)
        
        # Render parts
        summary_html = self.env.get_template("executive_summary.html").render(**context)
        tech_html = self.env.get_template("technical_details.html").render(**context)
        
        # Combine (simplistic approach - in production we'd merge cleanly)
        # Ideally, we create a 'master_report.html' that includes both
        combined_html = f"{summary_html}<div style='page-break-before: always;'></div>{tech_html}"
        
        HTML(string=combined_html).write_pdf(output_path)
        return output_path
