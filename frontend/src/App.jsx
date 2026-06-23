import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

const API_BASE = '/api'

const getWeatherEmoji = (main) => {
  const map = {
    'Clear': '☀️', 'Clouds': '☁️', 'Rain': '🌧️',
    'Drizzle': '🌦️', 'Thunderstorm': '⛈️', 'Snow': '❄️',
    'Mist': '🌫️', 'Fog': '🌫️', 'Haze': '🌫️',
  }
  return map[main] || '🌤️'
}

const getWeatherGradient = (main) => {
  const map = {
    'Clear': 'linear-gradient(135deg, #FF6B35, #F7931E, #FFD23F)',
    'Clouds': 'linear-gradient(135deg, #4A5568, #7B68EE, #9B59B6)',
    'Rain': 'linear-gradient(135deg, #1565C0, #0D47A1, #1A237E)',
    'Drizzle': 'linear-gradient(135deg, #2196F3, #1565C0, #283593)',
    'Thunderstorm': 'linear-gradient(135deg, #4A148C, #880E4F, #B71C1C)',
    'Snow': 'linear-gradient(135deg, #90CAF9, #64B5F6, #BBDEFB)',
    'Mist': 'linear-gradient(135deg, #546E7A, #607D8B, #78909C)',
    'Fog': 'linear-gradient(135deg, #546E7A, #607D8B, #78909C)',
  }
  return map[main] || 'linear-gradient(135deg, #7B2FFF, #FF2D55, #FF6B35)'
}

export default function App() {
  const [location, setLocation] = useState('')
  const [weather, setWeather] = useState(null)
  const [forecast, setForecast] = useState([])
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [dateRange, setDateRange] = useState({ start: '', end: '' })
  const [editingId, setEditingId] = useState(null)
  const [editLocation, setEditLocation] = useState('')

  useEffect(() => { fetchHistory() }, [])

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API_BASE}/searches/`)
      setHistory(res.data)
    } catch (e) { console.error('History fetch failed', e) }
  }

  const searchWeather = async (e) => {
    e.preventDefault()
    if (!location.trim()) return setError('Please enter a location')
    setLoading(true)
    setError('')
    setWeather(null)
    setForecast([])
    try {
      const [wRes, fRes] = await Promise.all([
        axios.get(`${API_BASE}/weather/current/?location=${encodeURIComponent(location)}`),
        axios.get(`${API_BASE}/weather/forecast/?location=${encodeURIComponent(location)}`)
      ])
      setWeather(wRes.data)
      setForecast(fRes.data.list || [])
    } catch (e) {
      setError(e.response?.data?.error || 'Location not found. Please check the spelling and try again.')
    } finally { setLoading(false) }
  }

  const detectLocation = () => {
    if (!navigator.geolocation) return setError('Geolocation not supported by your browser')
    setLoading(true)
    setError('')
    navigator.geolocation.getCurrentPosition(
      async ({ coords: { latitude: lat, longitude: lon } }) => {
        try {
          const [wRes, fRes] = await Promise.all([
            axios.get(`${API_BASE}/weather/current/?lat=${lat}&lon=${lon}`),
            axios.get(`${API_BASE}/weather/forecast/?lat=${lat}&lon=${lon}`)
          ])
          setWeather(wRes.data)
          setForecast(fRes.data.list || [])
          setLocation(wRes.data.name)
        } catch (e) {
          setError('Could not get weather for your location')
        } finally { setLoading(false) }
      },
      () => { setError('Location access denied. Please allow location access.'); setLoading(false) }
    )
  }

  const saveSearch = async () => {
    if (!weather) return setError('Search for a location first')
    if (!dateRange.start || !dateRange.end) return setError('Please select both start and end dates')
    if (dateRange.end < dateRange.start) return setError('End date must be after start date')
    try {
      await axios.post(`${API_BASE}/searches/`, {
        location: weather.name,
        date_range_start: dateRange.start,
        date_range_end: dateRange.end,
        weather_data: weather
      })
      setDateRange({ start: '', end: '' })
      fetchHistory()
    } catch (e) {
      setError(e.response?.data?.error || 'Failed to save search')
    }
  }

  const deleteSearch = async (id) => {
    if (!confirm('Delete this saved search?')) return
    try {
      await axios.delete(`${API_BASE}/searches/${id}/`)
      fetchHistory()
    } catch (e) { setError('Failed to delete') }
  }

  const saveEdit = async (id) => {
    if (!editLocation.trim()) return setError('Location cannot be empty')
    try {
      await axios.put(`${API_BASE}/searches/${id}/`, { location: editLocation })
      setEditingId(null)
      fetchHistory()
    } catch (e) { setError('Failed to update') }
  }

  const exportData = async (fmt) => {
    try {
      const res = await axios.get(`${API_BASE}/export/?format=${fmt}`, { responseType: 'blob' })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `weather-data.${fmt}`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) { setError('Export failed. No data to export yet.') }
  }

  const dailyForecast = forecast
    .filter(item => item.dt_txt?.includes('12:00:00'))
    .slice(0, 5)

  return (
    <div className="app">
      <div className="bg-orbs">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
      </div>

      <header className="header">
        <div className="header-inner">
          <div>
            <h1 className="logo">Aurora Weather</h1>
            <p className="logo-sub">by Kammari Ashritha · PM Accelerator</p>
          </div>
          <div className="pma-badge">Built for<br /><strong>PM Accelerator</strong></div>
        </div>
      </header>

      <main className="main">

        {/* SEARCH */}
        <section className="search-section">
          <form onSubmit={searchWeather} className="search-form">
            <div className="search-box">
              <span className="search-icon">🔍</span>
              <input
                type="text"
                value={location}
                onChange={e => setLocation(e.target.value)}
                placeholder="City name, zip code, or GPS coordinates..."
                className="search-input"
              />
              <button type="button" onClick={detectLocation} className="locate-btn" title="Use my location">📍</button>
            </div>
            <button type="submit" className="search-btn" disabled={loading}>
              {loading ? <span className="spinner"></span> : 'Get Weather'}
            </button>
          </form>
          {error && (
            <div className="error-toast">
              <span>⚠️</span> {error}
              <button onClick={() => setError('')}>×</button>
            </div>
          )}
        </section>

        {/* CURRENT WEATHER */}
        {weather && (
          <section className="weather-hero" style={{ background: getWeatherGradient(weather.weather?.[0]?.main) }}>
            <div className="hero-overlay">
              <div className="weather-hero-inner">
                <div className="weather-main">
                  <div className="weather-emoji">{getWeatherEmoji(weather.weather?.[0]?.main)}</div>
                  <div className="weather-temp">{Math.round(weather.main?.temp)}°C</div>
                  <div className="weather-city">{weather.name}, {weather.sys?.country}</div>
                  <div className="weather-desc">{weather.weather?.[0]?.description}</div>
                  <div className="weather-range">
                    H: {Math.round(weather.main?.temp_max)}° / L: {Math.round(weather.main?.temp_min)}°
                  </div>
                </div>
                <div className="weather-details">
                  {[
                    { icon: '💧', val: `${weather.main?.humidity}%`, lbl: 'Humidity' },
                    { icon: '💨', val: `${weather.wind?.speed} m/s`, lbl: 'Wind Speed' },
                    { icon: '🌡️', val: `${Math.round(weather.main?.feels_like)}°C`, lbl: 'Feels Like' },
                    { icon: '👁️', val: `${((weather.visibility||0)/1000).toFixed(1)} km`, lbl: 'Visibility' },
                    { icon: '🌅', val: new Date(weather.sys?.sunrise*1000).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}), lbl: 'Sunrise' },
                    { icon: '🌇', val: new Date(weather.sys?.sunset*1000).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}), lbl: 'Sunset' },
                    { icon: '📊', val: `${weather.main?.pressure} hPa`, lbl: 'Pressure' },
                    { icon: '🧭', val: `${weather.coord?.lat?.toFixed(2)}, ${weather.coord?.lon?.toFixed(2)}`, lbl: 'Coordinates' },
                  ].map((d, i) => (
                    <div key={i} className="detail-card">
                      <span className="detail-icon">{d.icon}</span>
                      <span className="detail-val">{d.val}</span>
                      <span className="detail-lbl">{d.lbl}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="save-search">
                <p className="save-title">💾 Save this search with a date range</p>
                <div className="date-row">
                  <input type="date" value={dateRange.start} onChange={e => setDateRange(p=>({...p,start:e.target.value}))} className="date-input" />
                  <span>→</span>
                  <input type="date" value={dateRange.end} min={dateRange.start} onChange={e => setDateRange(p=>({...p,end:e.target.value}))} className="date-input" />
                  <button onClick={saveSearch} className="save-btn">Save Search</button>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* 5-DAY FORECAST */}
        {dailyForecast.length > 0 && (
          <section className="forecast-section">
            <h2 className="section-title">📅 5-Day Forecast</h2>
            <div className="forecast-grid">
              {dailyForecast.map((day, i) => (
                <div key={i} className="forecast-card">
                  <div className="forecast-day">
                    {new Date(day.dt_txt).toLocaleDateString('en',{weekday:'long'})}
                  </div>
                  <div className="forecast-date">
                    {new Date(day.dt_txt).toLocaleDateString('en',{month:'short',day:'numeric'})}
                  </div>
                  <div className="forecast-emoji">{getWeatherEmoji(day.weather?.[0]?.main)}</div>
                  <div className="forecast-temp">{Math.round(day.main?.temp)}°C</div>
                  <div className="forecast-desc">{day.weather?.[0]?.description}</div>
                  <div className="forecast-hilo">
                    <span className="high">↑ {Math.round(day.main?.temp_max)}°</span>
                    <span className="low">↓ {Math.round(day.main?.temp_min)}°</span>
                  </div>
                  <div className="forecast-humidity">💧 {day.main?.humidity}%</div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* SEARCH HISTORY — CRUD */}
        <section className="history-section">
          <div className="section-header">
            <h2 className="section-title">🗂️ Saved Searches</h2>
            <div className="export-row">
              <span>Export:</span>
              <button onClick={() => exportData('json')} className="export-btn">JSON</button>
              <button onClick={() => exportData('csv')} className="export-btn">CSV</button>
            </div>
          </div>

          {history.length === 0 ? (
            <div className="empty-state">
              <p>No saved searches yet.</p>
              <p>Search for a city above, then save it with a date range.</p>
            </div>
          ) : (
            <div className="table-wrap">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Location</th>
                    <th>Date Range</th>
                    <th>Temp</th>
                    <th>Condition</th>
                    <th>Saved On</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((item, idx) => (
                    <tr key={item._id}>
                      <td>{idx + 1}</td>
                      <td>
                        {editingId === item._id ? (
                          <input value={editLocation} onChange={e => setEditLocation(e.target.value)} className="edit-input" />
                        ) : item.location}
                      </td>
                      <td>{item.date_range_start} → {item.date_range_end}</td>
                      <td>{item.weather_data?.main?.temp ? `${Math.round(item.weather_data.main.temp)}°C` : '—'}</td>
                      <td style={{textTransform:'capitalize'}}>{item.weather_data?.weather?.[0]?.description || '—'}</td>
                      <td>{new Date(item.created_at).toLocaleDateString()}</td>
                      <td>
                        {editingId === item._id ? (
                          <div className="action-group">
                            <button onClick={() => saveEdit(item._id)} className="action-btn save">✓ Save</button>
                            <button onClick={() => setEditingId(null)} className="action-btn cancel">✕</button>
                          </div>
                        ) : (
                          <div className="action-group">
                            <button onClick={() => { setEditingId(item._id); setEditLocation(item.location) }} className="action-btn edit">✏️ Edit</button>
                            <button onClick={() => deleteSearch(item._id)} className="action-btn delete">🗑️ Delete</button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* PM ACCELERATOR DESCRIPTION */}
        <section className="pma-section">
          <div className="pma-card">
            <h3>About PM Accelerator</h3>
            <p>
              The Product Manager Accelerator Program is designed to support PM professionals through every 
              stage of their careers. From students looking for entry-level jobs to Directors looking to take 
              on a leadership role, our program has helped over hundreds of students fulfill their career 
              aspirations.
            </p>
            <p style={{marginTop:'12px'}}>
              Our PM Accelerator community are ambitious and committed. Through our program they have learnt, 
              honed and developed new PM and leadership skills, giving them a strong foundation for their 
              future endeavors. Programs include: PMA Pro (FAANG-level PM skills), AI PM Bootcamp 
              (hands-on AI product building), PMA Power Skills, and PMA Leader for executives.
            </p>
            <div className="pma-links">
              <a href="https://www.pmaccelerator.io/" target="_blank" rel="noreferrer" className="pma-link">🌐 Website</a>
              <a href="https://www.linkedin.com/school/pmaccelerator/" target="_blank" rel="noreferrer" className="pma-link">LinkedIn →</a>
              <a href="https://www.youtube.com/c/drnancyli" target="_blank" rel="noreferrer" className="pma-link">▶ YouTube</a>
            </div>
          </div>
        </section>

      </main>

      <footer className="footer">
        <p>Aurora Weather · Built by <strong>Kammari Ashritha</strong> · PM Accelerator AI Engineer Internship 2026</p>
      </footer>
    </div>
  )
}