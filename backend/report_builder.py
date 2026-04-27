"""
report_builder.py — Turns Raw Research Into a Structured HTML Report
======================================================================
After the agent finishes research, we have a big chunk of text.
This file sends that text to Claude AGAIN with a very specific prompt
that tells it: "Format this as a JSON report structure".

Then we take that JSON and render it into a beautiful HTML page.

Flow:
  agent research text → Claude (format as JSON) → JSON → HTML string → return to frontend
"""

from groq import Groq      # Anthropic's official SDK (direct, not via LangChain)
import json            # Python's built-in JSON parser
import os
from dotenv import load_dotenv
from datetime import datetime   # to add "Report generated on: <date>" 

load_dotenv()

# Direct Anthropic client - we use this for the report formatting step
# (not LangGraph, just a simple one-shot Claude call)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def extract_report_structure(research_text: str, company_name: str) -> dict:
    """
    Sends raw research text to Claude and asks it to return structured JSON.
    
    Args:
        research_text: The big string from the agent (all research combined)
        company_name: Company name for labeling
    
    Returns:
        A Python dict with all report sections
    """

    # This prompt is very precise - we tell Claude EXACTLY what JSON shape to return
    # The more specific the prompt, the more reliable the JSON output
    prompt = f"""Based on the following research about {company_name}, create a comprehensive 
business intelligence report. Return ONLY valid JSON with this exact structure (no extra text):

{{
  "company_name": "...",
  "tagline": "one sentence description of what they do",
  "report_date": "today's date",
  "overview": {{
    "founded": "year",
    "headquarters": "city, country",
    "ceo": "name",
    "employees": "approximate number or range",
    "business_model": "B2B/B2C/Marketplace/SaaS etc",
    "description": "2-3 sentence company description"
  }},
  "financials": {{
    "revenue": "latest annual revenue or ARR",
    "valuation": "latest valuation",
    "funding_total": "total funding raised",
    "last_round": "e.g. Series C - $100M - 2024",
    "investors": ["investor1", "investor2", "investor3"],
    "growth_rate": "YoY growth if available",
    "profitability": "profitable / not profitable / unknown"
  }},
  "recent_news": [
    {{"title": "...", "summary": "...", "date": "...", "sentiment": "positive/negative/neutral"}},
    {{"title": "...", "summary": "...", "date": "...", "sentiment": "positive/negative/neutral"}},
    {{"title": "...", "summary": "...", "date": "...", "sentiment": "positive/negative/neutral"}}
  ],
  "competitors": [
    {{"name": "...", "description": "...", "differentiator": "how they differ from {company_name}"}},
    {{"name": "...", "description": "...", "differentiator": "..."}},
    {{"name": "...", "description": "...", "differentiator": "..."}}
  ],
  "swot": {{
    "strengths": ["...", "...", "..."],
    "weaknesses": ["...", "...", "..."],
    "opportunities": ["...", "...", "..."],
    "threats": ["...", "...", "..."]
  }},
  "investment_signals": {{
    "score": 75,
    "verdict": "Promising / Cautious / Strong Buy / Avoid",
    "bull_case": "...",
    "bear_case": "...",
    "key_risks": ["...", "...", "..."]
  }},
  "executive_summary": "3-4 sentence overall summary for a busy executive"
}}

Here is the research data:
{research_text}

Return ONLY the JSON. No markdown, no explanation, no code blocks."""

    # One-shot Claude call (not agent, just direct API)
    response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    max_tokens=4000,
    messages=[{"role": "user", "content": prompt}]
    )
    raw_json=response.choices[0].message.content.strip()


    # Parse the JSON string into a Python dictionary
    # If Claude accidentally adds ``` code fences, remove them first
    # Remove markdown code fences if present
    if "```" in raw_json:
        raw_json = raw_json.split("```")[1]
        if raw_json.startswith("json"):
            raw_json = raw_json[4:]

    # Find the first { and last } and extract only that part
    # This strips any text before or after the JSON object
    start = raw_json.find("{")
    end = raw_json.rfind("}") + 1
    raw_json = raw_json[start:end]

    return json.loads(raw_json)


def build_html_report(data: dict) -> str:
    """
    Takes the structured dict and renders it as a beautiful self-contained HTML page.
    
    Args:
        data: The structured report dict from extract_report_structure()
    
    Returns:
        A complete HTML string (one file, no external CSS needed)
    """

    # ── Helper: sentiment color ──────────────────────────────────────────────
    def sentiment_color(s: str) -> str:
        """Returns a CSS class based on news sentiment"""
        colors = {
            "positive": "#10b981",   # green
            "negative": "#ef4444",   # red
            "neutral": "#6b7280"     # gray
        }
        return colors.get(s.lower(), "#6b7280")

    # ── Pull data out of the dict ────────────────────────────────────────────
    # .get("key", "default") safely gets value, returns default if key missing
    company = data.get("company_name", "Company")
    tagline = data.get("tagline", "")
    overview = data.get("overview", {})
    financials = data.get("financials", {})
    news_items = data.get("recent_news", [])
    competitors = data.get("competitors", [])
    swot = data.get("swot", {})
    signals = data.get("investment_signals", {})
    summary = data.get("executive_summary", "")

    # ── Build SWOT section HTML ──────────────────────────────────────────────
    def swot_card(title: str, items: list, color: str, bg: str) -> str:
        items_html = "".join(f'<li>{item}</li>' for item in items)
        return f"""
        <div style="background:{bg}; border-left:4px solid {color}; 
                    border-radius:12px; padding:20px;">
            <h4 style="color:{color}; margin:0 0 12px; font-size:13px; 
                       text-transform:uppercase; letter-spacing:1px;">{title}</h4>
            <ul style="margin:0; padding-left:18px; color:#374151; 
                       font-size:14px; line-height:1.8;">{items_html}</ul>
        </div>"""

    # ── Build competitors HTML ───────────────────────────────────────────────
    competitors_html = ""
    for comp in competitors[:4]:  # max 4 competitors shown
        competitors_html += f"""
        <div style="border:1px solid #e5e7eb; border-radius:10px; padding:16px;">
            <strong style="font-size:15px; color:#111;">{comp.get('name','')}</strong>
            <p style="color:#6b7280; font-size:13px; margin:6px 0;">{comp.get('description','')}</p>
            <span style="background:#f3f4f6; color:#374151; font-size:12px; 
                         padding:3px 10px; border-radius:99px;">
                vs: {comp.get('differentiator','')}
            </span>
        </div>"""

    # ── Build news HTML ──────────────────────────────────────────────────────
    news_html = ""
    for item in news_items[:5]:  # max 5 news items
        color = sentiment_color(item.get("sentiment", "neutral"))
        news_html += f"""
        <div style="border-bottom:1px solid #f3f4f6; padding:14px 0;">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
                <span style="width:8px; height:8px; border-radius:50%; 
                             background:{color}; display:inline-block; flex-shrink:0;"></span>
                <strong style="font-size:14px; color:#111;">{item.get('title','')}</strong>
            </div>
            <p style="color:#6b7280; font-size:13px; margin:0 0 4px; padding-left:18px;">
                {item.get('summary','')}
            </p>
            <span style="color:#9ca3af; font-size:12px; padding-left:18px;">
                {item.get('date','')}
            </span>
        </div>"""

    # ── Build investors HTML ─────────────────────────────────────────────────
    investors = financials.get("investors", [])
    investors_html = " ".join(
        f'<span style="background:#eff6ff; color:#3b82f6; font-size:12px; '
        f'padding:4px 12px; border-radius:99px; display:inline-block; margin:3px;">'
        f'{inv}</span>'
        for inv in investors[:6]  # max 6 investors shown
    )

    # ── SWOT score score bar ─────────────────────────────────────────────────
    score = signals.get("score", 50)
    # Color changes based on score: red(<40) yellow(40-70) green(>70)
    score_color = "#ef4444" if score < 40 else ("#f59e0b" if score < 70 else "#10b981")

    # ── KEY RISKS ────────────────────────────────────────────────────────────
    risks_html = "".join(
        f'<li style="color:#374151; font-size:14px; margin-bottom:6px;">'
        f'{risk}</li>'
        for risk in signals.get("key_risks", [])
    )

    # ────────────────────────────────────────────────────────────────────────
    # THE FULL HTML REPORT - self-contained single file
    # Uses Google Fonts for a premium look
    # ────────────────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{company} — Business Intelligence Report</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Inter', sans-serif;
    background: #f8fafc;
    color: #111827;
    line-height: 1.6;
  }}
  .page {{ max-width: 900px; margin: 40px auto; padding: 0 20px 60px; }}
  
  /* Header */
  .header {{
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
    border-radius: 20px;
    padding: 48px;
    color: white;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
  }}
  .header::before {{
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 200px; height: 200px;
    background: rgba(255,255,255,0.05);
    border-radius: 50%;
  }}
  .header-badge {{
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 99px;
    padding: 4px 16px;
    font-size: 12px;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 16px;
    color: rgba(255,255,255,0.9);
  }}
  .header h1 {{
    font-family: 'Playfair Display', serif;
    font-size: 42px;
    color: white;
    margin-bottom: 8px;
  }}
  .header p {{
    color: rgba(255,255,255,0.7);
    font-size: 16px;
    max-width: 500px;
  }}
  .report-meta {{
    margin-top: 28px;
    padding-top: 20px;
    border-top: 1px solid rgba(255,255,255,0.15);
    display: flex;
    gap: 28px;
    font-size: 13px;
    color: rgba(255,255,255,0.6);
  }}

  /* Section card */
  .card {{
    background: white;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 20px;
    border: 1px solid #e5e7eb;
  }}
  .section-title {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #6b7280;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid #f3f4f6;
  }}

  /* Overview grid */
  .overview-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 16px;
  }}
  .overview-item label {{
    display: block;
    font-size: 11px;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
  }}
  .overview-item span {{
    font-size: 15px;
    font-weight: 500;
    color: #111;
  }}

  /* Financial metrics */
  .fin-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 14px;
  }}
  .fin-card {{
    background: #f8fafc;
    border-radius: 12px;
    padding: 16px;
    border: 1px solid #e5e7eb;
  }}
  .fin-card label {{
    font-size: 11px;
    color: #9ca3af;
    text-transform: uppercase;
    display: block;
    margin-bottom: 6px;
  }}
  .fin-card .value {{
    font-size: 18px;
    font-weight: 600;
    color: #111;
  }}

  /* Score bar */
  .score-bar-track {{
    background: #f3f4f6;
    border-radius: 99px;
    height: 10px;
    overflow: hidden;
    margin: 12px 0;
  }}
  .score-bar-fill {{
    height: 100%;
    border-radius: 99px;
    background: {score_color};
    width: {score}%;
    transition: width 1s ease;
  }}

  /* SWOT */
  .swot-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
  @media(max-width: 600px) {{ .swot-grid {{ grid-template-columns: 1fr; }} }}

  /* Print button */
  .print-btn {{
    background: #0f172a;
    color: white;
    border: none;
    padding: 12px 28px;
    border-radius: 99px;
    font-size: 14px;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
    display: block;
    margin: 0 auto 20px;
  }}
  @media print {{ .print-btn {{ display: none; }} }}
</style>
</head>
<body>
<div class="page">

  <button class="print-btn" onclick="window.print()">Download as PDF (Ctrl+P → Save as PDF)</button>

  <!-- HEADER -->
  <div class="header">
    <div class="header-badge">Business Intelligence Report</div>
    <h1>{company}</h1>
    <p>{tagline}</p>
    <div class="report-meta">
      <span>Generated: {datetime.now().strftime("%B %d, %Y")}</span>
      <span>Powered by AI Research Agent</span>
    </div>
  </div>

  <!-- EXECUTIVE SUMMARY -->
  <div class="card">
    <div class="section-title">Executive Summary</div>
    <p style="color:#374151; font-size:15px; line-height:1.8;">{summary}</p>
  </div>

  <!-- COMPANY OVERVIEW -->
  <div class="card">
    <div class="section-title">Company Overview</div>
    <p style="color:#374151; font-size:14px; margin-bottom:20px;">{overview.get('description','')}</p>
    <div class="overview-grid">
      <div class="overview-item">
        <label>Founded</label>
        <span>{overview.get('founded','—')}</span>
      </div>
      <div class="overview-item">
        <label>Headquarters</label>
        <span>{overview.get('headquarters','—')}</span>
      </div>
      <div class="overview-item">
        <label>CEO</label>
        <span>{overview.get('ceo','—')}</span>
      </div>
      <div class="overview-item">
        <label>Employees</label>
        <span>{overview.get('employees','—')}</span>
      </div>
      <div class="overview-item">
        <label>Business Model</label>
        <span>{overview.get('business_model','—')}</span>
      </div>
    </div>
  </div>

  <!-- FINANCIALS -->
  <div class="card">
    <div class="section-title">Financial Overview</div>
    <div class="fin-grid">
      <div class="fin-card">
        <label>Revenue / ARR</label>
        <div class="value">{financials.get('revenue','—')}</div>
      </div>
      <div class="fin-card">
        <label>Valuation</label>
        <div class="value">{financials.get('valuation','—')}</div>
      </div>
      <div class="fin-card">
        <label>Total Funding</label>
        <div class="value">{financials.get('funding_total','—')}</div>
      </div>
      <div class="fin-card">
        <label>Growth Rate</label>
        <div class="value">{financials.get('growth_rate','—')}</div>
      </div>
    </div>
    <div style="margin-top:16px;">
      <label style="font-size:12px; color:#9ca3af;">Last Funding Round</label>
      <p style="font-size:14px; color:#374151; margin-top:4px;">
        {financials.get('last_round','Not available')}
      </p>
    </div>
    <div style="margin-top:16px;">
      <label style="font-size:12px; color:#9ca3af; display:block; margin-bottom:8px;">
        Key Investors
      </label>
      {investors_html if investors_html else '<span style="color:#9ca3af;font-size:13px;">Not found</span>'}
    </div>
  </div>

  <!-- RECENT NEWS -->
  <div class="card">
    <div class="section-title">Recent News & Developments</div>
    {news_html if news_html else '<p style="color:#9ca3af;">No recent news found</p>'}
  </div>

  <!-- COMPETITORS -->
  <div class="card">
    <div class="section-title">Competitive Landscape</div>
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:14px;">
      {competitors_html}
    </div>
  </div>

  <!-- SWOT -->
  <div class="card">
    <div class="section-title">SWOT Analysis</div>
    <div class="swot-grid">
      {swot_card("Strengths", swot.get('strengths',[]), "#10b981", "#f0fdf4")}
      {swot_card("Weaknesses", swot.get('weaknesses',[]), "#ef4444", "#fef2f2")}
      {swot_card("Opportunities", swot.get('opportunities',[]), "#3b82f6", "#eff6ff")}
      {swot_card("Threats", swot.get('threats',[]), "#f59e0b", "#fffbeb")}
    </div>
  </div>

  <!-- INVESTMENT SIGNALS -->
  <div class="card">
    <div class="section-title">Investment Intelligence</div>
    <div style="display:flex; align-items:center; gap:16px; margin-bottom:20px;">
      <div>
        <div style="font-size:40px; font-weight:700; color:{score_color};">{score}</div>
        <div style="font-size:12px; color:#9ca3af;">out of 100</div>
      </div>
      <div style="flex:1;">
        <div style="font-size:16px; font-weight:500; color:#111; margin-bottom:4px;">
          {signals.get('verdict','—')}
        </div>
        <div class="score-bar-track">
          <div class="score-bar-fill"></div>
        </div>
      </div>
    </div>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:20px;">
      <div style="background:#f0fdf4; border-radius:10px; padding:16px;">
        <div style="font-size:11px; color:#059669; text-transform:uppercase; 
                    letter-spacing:1px; margin-bottom:8px;">Bull Case</div>
        <p style="font-size:13px; color:#374151;">{signals.get('bull_case','—')}</p>
      </div>
      <div style="background:#fef2f2; border-radius:10px; padding:16px;">
        <div style="font-size:11px; color:#dc2626; text-transform:uppercase; 
                    letter-spacing:1px; margin-bottom:8px;">Bear Case</div>
        <p style="font-size:13px; color:#374151;">{signals.get('bear_case','—')}</p>
      </div>
    </div>
    <div style="font-size:11px; color:#9ca3af; text-transform:uppercase; 
                letter-spacing:1px; margin-bottom:12px;">Key Risks</div>
    <ul style="padding-left:18px;">{risks_html}</ul>
  </div>

  <div style="text-align:center; color:#9ca3af; font-size:12px; margin-top:20px;">
    This report was auto-generated by an AI research agent. Always verify data independently.
  </div>

</div>
</body>
</html>"""

    return html


async def generate_full_report(company_name: str, research_text: str) -> str:
    """
    Main entry point called by FastAPI.
    Takes research text → returns complete HTML report.

    Args:
        company_name: e.g. "Stripe"
        research_text: output from run_research_agent()

    Returns:
        Full HTML string of the report
    """
    # Step 1: Structure the research into JSON using Claude
    structured_data = extract_report_structure(research_text, company_name)

    # Step 2: Render that JSON into HTML
    html_report = build_html_report(structured_data)

    return html_report