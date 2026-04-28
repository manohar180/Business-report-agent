// App.jsx — Root Component
// This is the main component that orchestrates everything.
// It holds global state and decides WHICH screen to show:
//   1. Search screen (idle)
//   2. Loading screen (while agent runs)
//   3. Report screen (report ready)
//   4. Error screen (something went wrong)

import { useState, useEffect } from 'react'
import LoadingSteps from './components/LoadingSteps.jsx'
import ReportViewer from './components/ReportViewer.jsx'

// These are sample companies the user can click to quickly try the app
const EXAMPLE_COMPANIES = [
  "Stripe", "Zepto", "OpenAI", "Rapido", "Anthropic", "Razorpay"
]

export default function App() {
  // ── State variables ────────────────────────────────────────────────────
  // input: what the user has typed in the search box
  const [input, setInput] = useState('')

  // status: controls which screen is shown
  // "idle" | "loading" | "done" | "error"
  const [status, setStatus] = useState('idle')

  // report: the HTML string returned from the backend
  const [report, setReport] = useState('')

  // companyName: the name we searched for (kept for display purposes)
  const [companyName, setCompanyName] = useState('')

  // error: error message if something goes wrong
  const [error, setError] = useState('')

  useEffect(() => {
  const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  fetch(`${apiBase}/health`).catch(() => {})
}, [])


  // ── handleSearch: called when user clicks Generate Report ─────────────
  const handleSearch = async (name) => {
    // Use provided name (from example clicks) OR the text in the input box
    const company = (name || input).trim()
    if (!company) return   // ignore empty searches

    // Update UI state
    setCompanyName(company)
    setStatus('loading')   // show the loading animation
    setError('')

    try {
      // POST request to our FastAPI backend
      // import.meta.env.VITE_API_URL reads from .env file in frontend
      // Falls back to localhost for development
      const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000'

      const response = await fetch(`${apiBase}/api/report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'  // tell server we're sending JSON
        },
        body: JSON.stringify({ company_name: company })  // send company name
      })

      // Check if the request failed (non-200 status)
      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail || 'Unknown error from server')
      }

      // Parse the JSON response body
      const data = await response.json()

      // Store the HTML report and switch to done state
      setReport(data.html_report)
      setStatus('done')

    } catch (err) {
      // Something went wrong — show error message
      console.error('Report generation failed:', err)
      setError(err.message || 'Something went wrong. Please try again.')
      setStatus('error')
    }
  }

  // ── handleReset: go back to idle/search screen ────────────────────────
  const handleReset = () => {
    setStatus('idle')
    setReport('')
    setCompanyName('')
    setInput('')
    setError('')
  }

  // ── handleKeyDown: allow pressing Enter to submit ────────────────────
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSearch()
  }


  // ─────────────────────────────────────────────────────────────────────
  // RENDER: Switch between screens based on status
  // ─────────────────────────────────────────────────────────────────────
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      fontFamily: 'DM Sans, sans-serif'
    }}>

      {/* ── Navbar ── */}
      <nav style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '16px 32px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--surface)'
      }}>
        <div style={{
          fontFamily: 'Syne, sans-serif',
          fontWeight: 800,
          fontSize: '18px',
          cursor: 'pointer'
        }} onClick={handleReset}>
          <span style={{ color: 'var(--accent)' }}>◈</span> ReportAI
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Powered by Claude + LangGraph
        </div>
      </nav>

      {/* ── Main Content ── */}
      <main style={{ flex: 1, padding: '32px' }}>

        {/* ── SCREEN 1: IDLE (search screen) ── */}
        {status === 'idle' && (
          <div style={{
            maxWidth: '600px',
            margin: '80px auto 0',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            gap: '32px'
          }}>
            {/* Hero heading */}
            <div>
              <h1 style={{
                fontFamily: 'Syne, sans-serif',
                fontSize: 'clamp(32px, 5vw, 52px)',
                fontWeight: 800,
                lineHeight: 1.15,
                marginBottom: '12px',
                background: 'linear-gradient(135deg, #f1f5f9, var(--accent))',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}>
                Business Intelligence,<br />Automated.
              </h1>
              <p style={{
                color: 'var(--text-secondary)',
                fontSize: '16px',
                lineHeight: 1.7
              }}>
                Enter any company name. Our AI agent researches the web,
                analyzes financials, and generates a full report in seconds.
              </p>
            </div>

            {/* Search input */}
            <div style={{
              display: 'flex',
              gap: '10px',
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: '14px',
              padding: '6px'
            }}>
              <input
                type="text"
                placeholder="e.g. Stripe, Zepto, OpenAI..."
                value={input}
                onChange={e => setInput(e.target.value)}  // update input state on every keystroke
                onKeyDown={handleKeyDown}                   // submit on Enter
                style={{
                  flex: 1,
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  color: 'var(--text-primary)',
                  fontSize: '15px',
                  padding: '10px 14px',
                  fontFamily: 'DM Sans, sans-serif'
                }}
              />
              <button
                onClick={() => handleSearch()}
                disabled={!input.trim()}  // disabled if input is empty
                style={{
                  background: input.trim()
                    ? 'linear-gradient(135deg, var(--accent), var(--accent-2))'
                    : 'var(--surface-2)',
                  color: input.trim() ? 'white' : 'var(--text-muted)',
                  border: 'none',
                  borderRadius: '10px',
                  padding: '10px 24px',
                  fontSize: '14px',
                  fontWeight: 500,
                  cursor: input.trim() ? 'pointer' : 'not-allowed',
                  transition: 'all 0.2s',
                  fontFamily: 'DM Sans, sans-serif'
                }}
              >
                Generate Report
              </button>
            </div>

            {/* Example company quick-selects */}
            <div>
              <div style={{
                fontSize: '12px',
                color: 'var(--text-muted)',
                marginBottom: '12px',
                textTransform: 'uppercase',
                letterSpacing: '1px'
              }}>
                Try these
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center' }}>
                {EXAMPLE_COMPANIES.map(company => (
                  <button
                    key={company}
                    onClick={() => {
                      setInput(company)       // fill the input with the example
                      handleSearch(company)   // immediately trigger search
                    }}
                    style={{
                      background: 'var(--surface-2)',
                      color: 'var(--text-secondary)',
                      border: '1px solid var(--border)',
                      borderRadius: '99px',
                      padding: '6px 16px',
                      fontSize: '13px',
                      cursor: 'pointer',
                      fontFamily: 'DM Sans, sans-serif',
                      transition: 'all 0.15s'
                    }}
                    onMouseOver={e => e.target.style.borderColor = 'var(--accent)'}
                    onMouseOut={e => e.target.style.borderColor = 'var(--border)'}
                  >
                    {company}
                  </button>
                ))}
              </div>
            </div>

            {/* Feature list */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr',
              gap: '12px',
              marginTop: '20px'
            }}>
              {[
                ["🌐", "Real-time web research"],
                ["💡", "SWOT + Financials"],
                ["📄", "Downloadable HTML report"]
              ].map(([icon, label]) => (
                <div key={label} style={{
                  background: 'var(--surface)',
                  border: '1px solid var(--border)',
                  borderRadius: '10px',
                  padding: '14px',
                  fontSize: '12px',
                  color: 'var(--text-secondary)',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '20px', marginBottom: '6px' }}>{icon}</div>
                  {label}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── SCREEN 2: LOADING ── */}
        {status === 'loading' && (
          <div style={{ maxWidth: '500px', margin: '60px auto 0' }}>
            {/* LoadingSteps handles its own animation internally */}
            <LoadingSteps companyName={companyName} />
          </div>
        )}

        {/* ── SCREEN 3: REPORT DONE ── */}
        {status === 'done' && (
          <ReportViewer
            htmlReport={report}
            companyName={companyName}
            onReset={handleReset}
          />
        )}

        {/* ── SCREEN 4: ERROR ── */}
        {status === 'error' && (
          <div style={{
            maxWidth: '500px',
            margin: '80px auto 0',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            gap: '20px',
            alignItems: 'center'
          }}>
            <div style={{ fontSize: '48px' }}>⚠️</div>
            <div>
              <h2 style={{ fontFamily: 'Syne, sans-serif', marginBottom: '8px' }}>
                Research Failed
              </h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
                {error}
              </p>
            </div>
            <button
              onClick={handleReset}
              style={{
                background: 'var(--accent)',
                color: 'white',
                border: 'none',
                padding: '10px 28px',
                borderRadius: '10px',
                cursor: 'pointer',
                fontFamily: 'DM Sans, sans-serif',
                fontSize: '14px'
              }}
            >
              Try Again
            </button>
          </div>
        )}
      </main>
    </div>
  )
}