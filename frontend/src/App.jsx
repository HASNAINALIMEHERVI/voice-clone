import React, { useState, useEffect } from 'react'
import './App.css'

function App() {
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const [text, setText] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedAudio, setGeneratedAudio] = useState(null)
  const [voices, setVoices] = useState([])
  const [selectedVoiceId, setSelectedVoiceId] = useState('')
  const [error, setError] = useState('')
  const [isSyncing, setIsSyncing] = useState(false)

  useEffect(() => {
    localStorage.removeItem('aura_api_key')
    fetchVoices()
  }, [])

  const fetchVoices = async () => {
    try {
      const resp = await fetch(`${API_BASE_URL}/voices`)
      const data = await resp.json()
      if (!resp.ok) throw new Error(data.detail || data.message || "Request failed.")
      if (!Array.isArray(data)) throw new Error("Invalid voice catalog.")
      setVoices(data)
      if (data.length > 0) setSelectedVoiceId((data.find(v => v.available !== false) || data[0]).id)
    } catch (err) {
      setError(err.message || "Cannot reach the speech server.")
    }
  }

  const syncVoices = async () => {
    setError('')
    setIsSyncing(true)
    const formData = new FormData()

    try {
      const resp = await fetch(`${API_BASE_URL}/sync-elevenlabs`, {
        method: 'POST',
        body: formData
      })
      const data = await resp.json()
      if (!resp.ok) throw new Error(data.detail || data.message || "Request failed.")
      if (data.status === 'success') {
        alert(data.message)
        fetchVoices()
      } else {
        alert("Sync Error: " + data.message)
      }
    } catch (err) {
      setError(err.message || "Request failed.")
    } finally {
      setIsSyncing(false)
    }
  }

  const handleSynthesize = async () => {
    if (!text || !selectedVoiceId) return
    setError(''); setGeneratedAudio(null)
    setIsGenerating(true)
    
    const formData = new FormData()
    formData.append('voice_id', selectedVoiceId)
    formData.append('text', text)

    try {
      const resp = await fetch(`${API_BASE_URL}/synthesize`, {
        method: 'POST',
        body: formData
      })
      const data = await resp.json()
      if (!resp.ok) throw new Error(data.detail || data.message || "Request failed.")
      if (data.status === 'success') {
        const timestamp = new Date().getTime()
        const fullAudioUrl = data.audio_url.startsWith('http') ? data.audio_url : `${API_BASE_URL}${data.audio_url}?t=${timestamp}`
        setGeneratedAudio(fullAudioUrl)
      } else {
        alert("Nexus Error: " + data.message)
      }
    } catch (err) {
      setError(err.message || "Request failed.")
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="aura-app">
      <div className="bg-blob blob-purple"></div>
      <div className="bg-blob blob-cyan"></div>

      <aside className="sidebar glass">
        <div className="logo-section">
          <div className="logo-icon">A</div>
          <h1>Aura AI</h1>
        </div>
        
        <nav className="nav-menu">
          <div className="nav-item active">
            <span className="icon">🌌</span>
            <span>Voice Nexus</span>
          </div>
        </nav>
      </aside>

      <main className="main-stage">
        <header className="stage-header">
          <div className="header-meta">
            <span className="breadcrumb">Aura / Nexus</span>
          </div>
        </header>

        <div className="content-scroller">
            <section className="nexus-view">
              {error && <p role="alert">{error}</p>}
              <div className="welcome-banner">
                <h1>Neural Voice Nexus</h1>
                <p>Choose a voice and turn text into speech.</p>
              </div>

              <div className="nexus-grid">
                <div className="voices-sidebar glass-card">
                  <div className="sidebar-header-row">
                    <h3>Available Agents ({voices.length})</h3>
                    <button className="sync-btn" onClick={syncVoices} disabled={isSyncing}>
                      {isSyncing ? "..." : "🔄"}
                    </button>
                  </div>
                  <div className="agent-list">
                    {voices.map(v => (
                      <button type="button" disabled={v.available === false}
                        key={v.id} 
                        className={`agent-selector-card glass ${selectedVoiceId === v.id ? 'active' : ''}`}
                        onClick={() => setSelectedVoiceId(v.id)}
                      >
                        <div className="agent-avatar">{v.name.charAt(0)}</div>
                        <div className="agent-meta">
                          <strong>{v.name}</strong>
                          <span className="engine-tag">{v.engine}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="synthesis-core glass-card">
                  <header className="core-header">
                    <h3>Manifest Frequency</h3>
                    {selectedVoiceId && (
                      <span className="active-agent">Agent: {voices.find(v => v.id === selectedVoiceId)?.name}</span>
                    )}
                  </header>
                  
                  <textarea 
                    aria-label="Text to speak" maxLength={5000} placeholder="Type your message here..."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                  ></textarea>

                  <div className="synthesis-controls">
                    <button 
                      className="btn-primary full-width" 
                      onClick={handleSynthesize}
                      disabled={isGenerating || !text.trim() || !selectedVoiceId}
                    >
                      {isGenerating ? "Manifesting..." : "Synthesize ⚡"}
                    </button>
                  </div>

                  {generatedAudio && (
                    <div className="result-player glass border-glow">
                      <p>Neural Output Captured:</p>
                      <audio 
                        src={generatedAudio} 
                        controls 
                        autoPlay 
                        crossOrigin="anonymous"
                        onError={() => alert("Sonic Stream Failure: The audio file couldn't be manifest. Check if the backend is still materializing.")}
                      />
                    </div>
                  )}
                </div>
              </div>
            </section>
          </div>

          <footer className="nexus-footer glass">
            <div className="footer-content">
              <span className="footer-brand">Aura AI Nexus v2.0</span>
              <div className="footer-links">
                <span>Online voice providers</span>
                <span className="pulse-dot"></span>
                <span>Text-to-speech prototype</span>
              </div>
              <span className="footer-copyright">© 2026 APNI SALTANAT</span>
            </div>
          </footer>
        </main>
      </div>
  )
}

export default App
