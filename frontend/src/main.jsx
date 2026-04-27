// main.jsx — React entry point
// This file mounts the React app into the DOM
// It's the equivalent of ReactDOM.render() in older React

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// createRoot() is React 18's way of mounting the app
// document.getElementById('root') finds the <div id="root"> in index.html
createRoot(document.getElementById('root')).render(
  <StrictMode>
    {/* StrictMode helps catch bugs in development — has no effect in production */}
    <App />
  </StrictMode>
)