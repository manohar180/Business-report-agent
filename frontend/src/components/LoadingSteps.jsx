// LoadingSteps.jsx — Animated progress indicator
// Shows the user what the agent is currently doing (so they don't think it's frozen)
// The agent takes 20-60 seconds, so good UX matters here

import { useState, useEffect } from 'react'

// These are the steps the agent ACTUALLY goes through (matches agent.py tools)
// We cycle through them with a timer so the UI feels alive
const STEPS = [
  { icon: "🔍", label: "Searching company overview..." },
  { icon: "💰", label: "Fetching financial data..." },
  { icon: "📰", label: "Scanning recent news..." },
  { icon: "⚔️",  label: "Analyzing competitors..." },
  { icon: "🧠", label: "Running SWOT analysis..." },
  { icon: "✍️",  label: "Writing executive summary..." },
  { icon: "📊", label: "Generating HTML report..." },
]

export default function LoadingSteps({ companyName }) {
  // currentStep tracks which step index we're showing (0 to STEPS.length-1)
  const [currentStep, setCurrentStep] = useState(0)

  // useEffect with a timer — runs when component mounts
  // Every 6 seconds, advance to the next step
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep(prev => {
        // If we're at the last step, stay there (don't loop back)
        if (prev >= STEPS.length - 1) return prev
        return prev + 1  // advance to next step
      })
    }, 6000)  // 6000ms = 6 seconds per step

    // Cleanup: clear the timer when component unmounts
    // (this prevents memory leaks)
    return () => clearInterval(interval)
  }, [])  // [] means this effect runs only once (on mount)

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '60px 24px',
      gap: '32px'
    }}>
      {/* Company name being researched */}
      <div style={{ textAlign: 'center' }}>
        <div style={{
          fontSize: '13px',
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '2px',
          marginBottom: '8px'
        }}>
          Researching
        </div>
        <div style={{
          fontSize: '28px',
          fontFamily: 'Syne, sans-serif',
          fontWeight: 700,
          color: 'var(--text-primary)'
        }}>
          {companyName}
        </div>
      </div>

      {/* Pulsing ring animation around the current step icon */}
      <div style={{ position: 'relative', width: '80px', height: '80px' }}>
        {/* Outer pulsing ring */}
        <div style={{
          position: 'absolute',
          inset: '-8px',
          borderRadius: '50%',
          border: '2px solid var(--accent)',
          opacity: 0.3,
          animation: 'pulse 2s ease-in-out infinite'
        }} />
        {/* Inner circle with icon */}
        <div style={{
          width: '80px', height: '80px',
          borderRadius: '50%',
          background: 'var(--surface-2)',
          border: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '28px'
        }}>
          {STEPS[currentStep].icon}
        </div>
      </div>

      {/* Current step label */}
      <div style={{
        fontSize: '15px',
        color: 'var(--text-secondary)',
        fontStyle: 'italic'
      }}>
        {STEPS[currentStep].label}
      </div>

      {/* Progress dots - one per step, filled = done */}
      <div style={{ display: 'flex', gap: '8px' }}>
        {STEPS.map((step, i) => (
          <div
            key={i}
            style={{
              width: i === currentStep ? '24px' : '8px',  // active dot is wider
              height: '8px',
              borderRadius: '99px',
              background: i <= currentStep
                ? 'var(--accent)'      // done steps = indigo
                : 'var(--surface-2)', // future steps = dark gray
              transition: 'all 0.3s ease'  // smooth width change animation
            }}
          />
        ))}
      </div>

      {/* Small disclaimer */}
      <div style={{
        fontSize: '12px',
        color: 'var(--text-muted)',
        textAlign: 'center',
        maxWidth: '300px',
        lineHeight: 1.6
      }}>
        The AI agent is browsing the web and analyzing data.
        This usually takes 30–60 seconds.
      </div>

      {/* Inline CSS animation — pulse effect for the ring */}
      <style>{`
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 0.3; }
          50% { transform: scale(1.15); opacity: 0.6; }
        }
      `}</style>
    </div>
  )
}