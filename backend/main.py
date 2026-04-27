"""
main.py — FastAPI Backend Server
==================================
This is the entry point of the backend.
FastAPI is like Express.js in Node.js — it handles HTTP requests.

Endpoints:
  GET  /health          → health check (used by Railway/deployment)
  POST /api/report      → main endpoint, takes company name, returns HTML report
  GET  /api/report/{id} → retrieve a cached report by ID

How it connects to the rest:
  Request comes in → main.py → runs agent (agent.py) → formats report (report_builder.py)
  → returns HTML response

Run locally: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException    # FastAPI framework
from fastapi.middleware.cors import CORSMiddleware  # allows React frontend to call us
from pydantic import BaseModel               # data validation (like Zod in TS)
import uuid                                  # generate unique IDs for reports
import asyncio                               # Python's async runtime
from agent import run_research_agent         # our LangGraph agent
from report_builder import generate_full_report  # our HTML report generator

# ── Create FastAPI app ────────────────────────────────────────────────────
# FastAPI() creates the application instance (like express() in Express.js)
app = FastAPI(
    title="Business Report Agent API",
    description="AI-powered business intelligence report generator",
    version="1.0.0"
)

# ── CORS Middleware ────────────────────────────────────────────────────────
# CORS (Cross-Origin Resource Sharing) - allows our React frontend (running on
# a different port/domain) to make requests to this backend.
# Without this, the browser blocks all cross-origin requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",         # Vite dev server (local development)
        "http://localhost:3000",         # alternative local port
        "https://*.vercel.app",          # Vercel deployment (production)
        "*"                              # fallback - in prod, restrict to your domain
    ],
    allow_credentials=True,     # allow cookies/auth headers
    allow_methods=["*"],        # allow GET, POST, PUT, DELETE etc.
    allow_headers=["*"]         # allow all headers
)

# ── In-memory cache (reports are stored here temporarily) ─────────────────
# In production, you'd use Redis or a database.
# But for a demo, a dict is fine.
# Key = report_id (UUID string), Value = HTML string
report_cache: dict[str, str] = {}


# ── Request/Response Models ────────────────────────────────────────────────
# Pydantic models define the shape of request/response bodies.
# They also auto-validate incoming data (like Zod in TypeScript).

class ReportRequest(BaseModel):
    """What the frontend sends us"""
    company_name: str   # e.g. "Stripe" or "Zepto"

    class Config:
        # Example shown in the FastAPI /docs page
        json_schema_extra = {"example": {"company_name": "Stripe"}}

class ReportResponse(BaseModel):
    """What we send back"""
    report_id: str      # unique ID to retrieve the report
    status: str         # "completed" or "error"
    message: str        # human-readable status
    html_report: str    # the full HTML report content


# ── Routes ────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    """
    Health check endpoint.
    Railway (deployment) pings this to know if the server is alive.
    Returns 200 OK if everything is running.
    """
    return {"status": "healthy", "service": "Business Report Agent"}


@app.post("/api/report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """
    Main endpoint. Frontend sends company name, we return HTML report.

    Flow:
    1. Validate request (Pydantic does this automatically)
    2. Run the LangGraph agent to research the company
    3. Generate HTML report from research
    4. Cache the report and return it

    Args:
        request: ReportRequest with company_name field

    Returns:
        ReportResponse with the HTML report
    """

    # Basic validation - don't let empty strings through
    company = request.company_name.strip()
    if not company:
        raise HTTPException(status_code=400, detail="company_name cannot be empty")

    if len(company) > 100:
        raise HTTPException(status_code=400, detail="company_name too long")

    try:
        # Step 1: Run the LangGraph research agent
        # This is the async call that takes 20-60 seconds (lots of web searching)
        # await means "pause here, let other requests run, resume when done"
        print(f"[Agent] Starting research for: {company}")
        research_text = await run_research_agent(company)
        print(f"[Agent] Research complete. Generating report...")

        # Step 2: Generate structured HTML report from the research
        html_report = await generate_full_report(company, research_text)
        print(f"[Agent] Report generated successfully.")

        # Step 3: Cache the report with a unique ID
        # uuid4() generates a random unique ID like "a4f8b2d1-..."
        report_id = str(uuid.uuid4())
        report_cache[report_id] = html_report

        # Step 4: Return the response
        return ReportResponse(
            report_id=report_id,
            status="completed",
            message=f"Report for {company} generated successfully",
            html_report=html_report
        )

    except Exception as e:
        # If anything goes wrong, log it and return a 500 error
        print(f"[Error] Report generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )


@app.get("/api/report/{report_id}")
def get_cached_report(report_id: str):
    """
    Retrieve a previously generated report by its ID.
    Useful if the user wants to re-view a report without regenerating it.

    Args:
        report_id: The UUID returned by POST /api/report

    Returns:
        The HTML report string
    """
    if report_id not in report_cache:
        raise HTTPException(status_code=404, detail="Report not found or expired")

    return {
        "report_id": report_id,
        "html_report": report_cache[report_id],
        "status": "found"
    }


# ── Entry Point (for running locally) ─────────────────────────────────────
# This only runs when you do: python main.py
# When deployed (Railway), uvicorn is started by the Procfile command
if __name__ == "__main__":
    import uvicorn
    # host="0.0.0.0" means "accept connections from any IP" (needed for deployment)
    # reload=True means server restarts when you save a file (dev only)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)