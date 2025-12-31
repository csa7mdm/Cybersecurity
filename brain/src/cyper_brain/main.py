import os
import logging
from aiohttp import web
from cyper_brain.ai.agent import CyperAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Agent
agent = CyperAI()

async def health_check(request):
    return web.json_response({"status": "healthy", "service": "cyper-brain"})

async def analyze_target(request):
    try:
        data = await request.json()
        target = data.get("target")
        scan_type = data.get("scan_type", "network")
        context = data.get("context", {})
        
        if not target:
            return web.json_response({"error": "Target is required"}, status=400)

        plan = await agent.analyze_target(target, scan_type, context)
        
        # Convert ScanPlan dataclass to dict
        from dataclasses import asdict
        return web.json_response(asdict(plan))
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def generate_report(request):
    try:
        data = await request.json()
        scan_results = data.get("scan_results")
        report_type = data.get("report_type", "technical")
        
        if not scan_results:
            return web.json_response({"error": "Scan results required"}, status=400)
            
        # For PDF generation, we expect 'analysis' and 'metadata'
        # But keeping it compatible with agent.generate_report (markdown) for now
        # OR exposing generate_formatted_report (PDF)
        
        if data.get("format") == "pdf":
            # PDF Generation
            # Expects 'analysis' (dict) and 'metadata' (dict)
            analysis_dict = data.get("analysis")
            metadata = data.get("metadata", {})
            output_path = data.get("output_path", "/reports/report.pdf") # Default inside container
            
            # Need to reconstruct AnalysisResult from dict if strictly typed, 
            # but generate_formatted_report takes AnalysisResult.
            # However, I modified agent.py to take AnalysisResult, but report_generator takes dict.
            # I should probably update agent.generate_formatted_report to accept dict or handle reconstruction.
            # For simplicity, let's call ReportGenerator directly or construct dummy object.
            
            # Simplest: Update agent.generate_formatted_report to accept Dict or AnalysisResult
            # But let's assume we pass the raw dict to ReportGenerator via a helper in main for now
            # as constructing the massive AnalysisResult object from JSON might be tedious.
            
            # actually better: just use agent.report_generator directly here? NO, keep logic in agent.
            # Let's trust the agent.
            
            # Reconstruct AnalysisResult
            from cyper_brain.ai.results_analyzer import AnalysisResult
            analysis = AnalysisResult(**analysis_dict)
            
            pdf_path = agent.generate_formatted_report(analysis, metadata, output_path)
            return web.json_response({"path": pdf_path, "status": "generated"})

        else:
            # Markdown Generation
            report = await agent.generate_report(scan_results, report_type)
            return web.json_response({"report": report})
            
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def ask_question(request):
    try:
        data = await request.json()
        question = data.get("question")
        context = data.get("context")
        
        if not question:
            return web.json_response({"error": "Question is required"}, status=400)
            
        answer = await agent.answer_question(question, context)
        return web.json_response({"answer": answer})
    except Exception as e:
        logger.error(f"QA failed: {e}")
        return web.json_response({"error": str(e)}, status=500)

def main():
    app = web.Application()
    app.add_routes([
        web.get('/health', health_check),
        web.post('/api/v1/analyze', analyze_target),
        web.post('/api/v1/report', generate_report),
        web.post('/api/v1/ask', ask_question),
    ])
    
    port = int(os.getenv("PORT", 50051)) # Reuse the exposed port
    logger.info(f"Starting Brain Service on port {port}")
    web.run_app(app, port=port)

if __name__ == '__main__':
    main()
