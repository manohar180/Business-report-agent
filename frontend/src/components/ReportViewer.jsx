// ReportViewer.jsx — Displays the generated HTML report
// The report is a complete HTML page (string) returned by the backend.
// We use an <iframe> with srcDoc to safely render it inside our React app.

export default function ReportViewer({ htmlReport, companyName, onReset }) {
  // handleDownload: creates a .html file and triggers browser download
  const handleDownload = () => {
    // Create a Blob (Binary Large Object) — a file-like object in browser memory
    const blob = new Blob([htmlReport], { type: 'text/html' })

    // createObjectURL turns the Blob into a temporary URL like "blob://..."
    const url = URL.createObjectURL(blob)

    // Create an invisible <a> tag, click it, then remove it
    // This triggers the browser's file download dialog
    const a = document.createElement('a')
    a.href = url
    a.download = `${companyName.replace(/\s+/g, '-').toLowerCase()}-report.html`
    document.body.appendChild(a)
    a.click()              // programmatically click to download
    document.body.removeChild(a)
    URL.revokeObjectURL(url)  // free memory
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

      {/* Action bar above the report */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '12px 20px',
        background: 'var(--surface)',
        borderRadius: '12px',
        border: '1px solid var(--border)'
      }}>
        {/* Left: report title */}
        <div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Report Ready</div>
          <div style={{
            fontSize: '17px',
            fontFamily: 'Syne, sans-serif',
            fontWeight: 700
          }}>
            {companyName}
          </div>
        </div>

        {/* Right: action buttons */}
        <div style={{ display: 'flex', gap: '10px' }}>
          {/* Download button */}
          <button
            onClick={handleDownload}
            style={{
              background: 'var(--accent)',
              color: 'white',
              border: 'none',
              padding: '8px 20px',
              borderRadius: '8px',
              fontSize: '13px',
              cursor: 'pointer',
              fontFamily: 'DM Sans, sans-serif'
            }}
          >
            Download HTML
          </button>

          {/* New report button — calls onReset to go back to search screen */}
          <button
            onClick={onReset}
            style={{
              background: 'transparent',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border)',
              padding: '8px 20px',
              borderRadius: '8px',
              fontSize: '13px',
              cursor: 'pointer',
              fontFamily: 'DM Sans, sans-serif'
            }}
          >
            New Report
          </button>
        </div>
      </div>

      {/* The report itself - rendered in an iframe */}
      {/* srcDoc feeds HTML string directly to the iframe (no URL needed) */}
      {/* sandbox="allow-same-origin allow-popups" allows safe rendering */}
      <iframe
        srcDoc={htmlReport}
        style={{
          width: '100%',
          height: '85vh',       // 85% of viewport height
          border: '1px solid var(--border)',
          borderRadius: '16px',
          background: 'white'
        }}
        title={`${companyName} Business Report`}
        sandbox="allow-same-origin allow-popups allow-scripts"
      />
    </div>
  )
}