import { useState, useRef, useCallback } from 'react'
import './App.css'

const API_BASE = ''

function App() {
  // ── State ──────────────────────────────────────────────
  const [folderPath, setFolderPath] = useState('')
  const [indexStatus, setIndexStatus] = useState(null) // { type, message }
  const [isIndexing, setIsIndexing] = useState(false)

  const [previewUrl, setPreviewUrl] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [isSearching, setIsSearching] = useState(false)
  const [results, setResults] = useState([])
  const [queryFilename, setQueryFilename] = useState('')

  const [dragover, setDragover] = useState(false)
  const [lightbox, setLightbox] = useState(null)

  const fileInputRef = useRef(null)

  // ── Index a folder ─────────────────────────────────────
  const handleIndex = async () => {
    if (!folderPath.trim()) return
    setIsIndexing(true)
    setIndexStatus({ type: 'loading', message: 'Scanning and indexing images…' })

    try {
      const res = await fetch(`${API_BASE}/api/index`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ directory: folderPath.trim() }),
      })
      const data = await res.json()

      if (res.ok) {
        setIndexStatus({
          type: 'success',
          message: `✓ Indexed ${data.indexed_count} images in ${data.elapsed_seconds}s`,
        })
      } else {
        setIndexStatus({ type: 'error', message: data.detail || 'Indexing failed' })
      }
    } catch (err) {
      setIndexStatus({ type: 'error', message: 'Cannot connect to backend. Is it running?' })
    } finally {
      setIsIndexing(false)
    }
  }

  // ── File selection ─────────────────────────────────────
  const handleFileSelect = (file) => {
    if (!file || !file.type.startsWith('image/')) return
    setSelectedFile(file)
    setPreviewUrl(URL.createObjectURL(file))
    setResults([])
  }

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragover(false)
    const file = e.dataTransfer.files[0]
    handleFileSelect(file)
  }, [])

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setDragover(true)
  }, [])

  const handleDragLeave = useCallback(() => {
    setDragover(false)
  }, [])

  const clearSelection = () => {
    setSelectedFile(null)
    setPreviewUrl(null)
    setResults([])
    setQueryFilename('')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  // ── Search ─────────────────────────────────────────────
  const handleSearch = async () => {
    if (!selectedFile) return
    setIsSearching(true)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const res = await fetch(`${API_BASE}/api/search?top_k=20`, {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()

      if (res.ok) {
        setResults(data.results || [])
        setQueryFilename(data.query_filename || '')
      } else {
        setIndexStatus({ type: 'error', message: data.detail || 'Search failed' })
      }
    } catch (err) {
      setIndexStatus({ type: 'error', message: 'Search failed. Is the backend running?' })
    } finally {
      setIsSearching(false)
    }
  }

  // ── Similarity badge class ─────────────────────────────
  const getSimilarityClass = (score) => {
    if (score >= 80) return 'high'
    if (score >= 50) return 'medium'
    return ''
  }

  return (
    <div className="app">
      <div className="app-content">
        {/* ── Header ──────────────────────────────────── */}
        <header className="header">
          <div className="header-icon">🔍</div>
          <h1>Neptune</h1>
          <p>Search for visually similar images in your local folders</p>
        </header>

        {/* ── Controls ────────────────────────────────── */}
        <div className="controls">
          {/* Index Panel */}
          <div className="glass-card">
            <div className="card-title">
              <span>📁</span>
              <span>Index Folder</span>
            </div>
            <div className="index-form">
              <input
                type="text"
                className="path-input"
                placeholder="C:\Users\YourName\Pictures"
                value={folderPath}
                onChange={(e) => setFolderPath(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleIndex()}
                disabled={isIndexing}
              />
              <button
                className="btn-primary"
                onClick={handleIndex}
                disabled={isIndexing || !folderPath.trim()}
              >
                {isIndexing ? (
                  <><span className="spinner" /> Indexing…</>
                ) : (
                  '⚡ Index'
                )}
              </button>
            </div>
            {indexStatus && (
              <div className={`status-badge ${indexStatus.type}`}>
                {indexStatus.message}
              </div>
            )}
          </div>

          {/* Search Panel */}
          <div className="glass-card">
            <div className="card-title">
              <span>🖼️</span>
              <span>Search Image</span>
            </div>

            {!previewUrl ? (
              <div
                className={`drop-zone ${dragover ? 'dragover' : ''}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
              >
                <span className="drop-zone-icon">📷</span>
                <div className="drop-zone-text">
                  <strong>Drop an image</strong> or click to browse
                </div>
                <div className="drop-zone-hint">
                  Supports JPG, PNG, WebP, BMP
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => handleFileSelect(e.target.files[0])}
                />
              </div>
            ) : (
              <div className="preview-container">
                <img src={previewUrl} alt="Query" className="preview-image" />
                <div className="preview-actions">
                  <button
                    className="btn-search"
                    onClick={handleSearch}
                    disabled={isSearching || !indexStatus?.type === 'success'}
                  >
                    {isSearching ? (
                      <><span className="spinner" /> Searching…</>
                    ) : (
                      '🔍 Find Similar'
                    )}
                  </button>
                  <button className="btn-clear" onClick={clearSelection}>
                    ✕ Clear
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Results ─────────────────────────────────── */}
        {isSearching && (
          <div className="empty-state">
            <div className="spinner spinner-large" />
            <h3>Searching for similar images…</h3>
          </div>
        )}

        {!isSearching && results.length > 0 && (
          <section className="results-section">
            <div className="results-header">
              <h2>
                ✨ Similar Images
                <span className="results-count">({results.length} found)</span>
              </h2>
            </div>
            <div className="results-grid">
              {results.map((item, i) => (
                <div
                  className="image-card"
                  key={i}
                  style={{ animationDelay: `${i * 0.05}s` }}
                  onClick={() => setLightbox(item)}
                >
                  <div className="image-card-img-container">
                    <img
                      className="image-card-img"
                      src={`${API_BASE}/api/images?path=${encodeURIComponent(item.path)}`}
                      alt={item.filename}
                      loading="lazy"
                    />
                    <span className={`similarity-badge ${getSimilarityClass(item.similarity)}`}>
                      {item.similarity}%
                    </span>
                  </div>
                  <div className="image-card-info">
                    <div className="image-card-name" title={item.filename}>
                      {item.filename}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {!isSearching && results.length === 0 && !previewUrl && (
          <div className="empty-state">
            <div className="empty-state-icon">🌌</div>
            <h3>Ready to discover similar images</h3>
            <p>Index a folder, then upload an image to find matches</p>
          </div>
        )}

        {/* ── Lightbox ────────────────────────────────── */}
        {lightbox && (
          <div className="lightbox-overlay" onClick={() => setLightbox(null)}>
            <div>
              <img
                className="lightbox-content"
                src={`${API_BASE}/api/images?path=${encodeURIComponent(lightbox.path)}`}
                alt={lightbox.filename}
              />
              <div className="lightbox-info">
                {lightbox.filename} — {lightbox.similarity}% similar
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
