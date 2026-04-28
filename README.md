Here's the clean copy-paste version:

---

# Business Report Agent

An AI-powered business intelligence platform. Enter any company name and the agent autonomously researches the web, analyzes financials, and generates a professional report.

**Live Demo:** https://business-report-agent.vercel.app/

---

## Tech Stack

- **Frontend:** React + Vite, deployed on Vercel
- **Backend:** FastAPI + LangGraph, deployed on Render
- **AI Model:** Groq LLaMA 3.3 70B for reasoning and synthesis
- **Search:** Tavily API for real-time web research

---

## How It Works

The agent follows a multi-step research pipeline:

1. User enters a company name on the frontend
2. Frontend sends a POST request to the FastAPI backend
3. LangGraph agent starts running and decides which tools to call
4. Agent calls search tools one by one — company overview, financials, news, competitors
5. Once enough data is gathered, the LLM synthesizes everything
6. Report builder formats the research into a structured HTML report
7. Frontend renders the report and allows download

---

## Project Structure

```
business-report-agent/
├── backend/
│   ├── main.py            → FastAPI server and API endpoints
│   ├── agent.py           → LangGraph agent and graph definition
│   ├── tools.py           → Search and scraping tools
│   ├── report_builder.py  → Converts research into HTML report
│   ├── requirements.txt
│   └── Procfile
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── components/
    │   │   ├── LoadingSteps.jsx
    │   │   └── ReportViewer.jsx
    │   ├── main.jsx
    │   └── index.css
    └── index.html
```

---

## Local Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in the backend folder:

```
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Start the server:

```bash
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

---

## Deployment

**Backend on Render:**
- Connect GitHub repo, set root directory to `backend`
- Add environment variables: `GROQ_API_KEY`, `TAVILY_API_KEY`
- Set Python version to `3.11.0` in Render settings

**Frontend on Vercel:**
- Connect GitHub repo, set root directory to `frontend`
- Add environment variable: `VITE_API_URL=https://your-render-url.onrender.com`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/report` | Generate report for a company |
| GET | `/api/report/{id}` | Retrieve a cached report |

---

## Getting API Keys

- **Groq API** (free) → console.groq.com
- **Tavily API** (free, 1000 searches/month) → app.tavily.com



---

Replace the live demo URL with your actual Vercel link and you're good. Now let's build the shopping agent — ready?
