import { useState, useEffect, useRef, useCallback } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMapEvents, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// ── Tile layer definitions ──
const TILE_LAYERS = {
  osm: {
    name: 'Calles',
    icon: '🗺️',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '© <a href="https://openstreetmap.org">OpenStreetMap</a>',
    maxZoom: 19,
  },
  topo: {
    name: 'Topográfico',
    icon: '🏔️',
    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    attribution: '© <a href="https://opentopomap.org">OpenTopoMap</a> | © <a href="https://openstreetmap.org">OSM</a>',
    maxZoom: 17,
  },
  satellite: {
    name: 'Satelital',
    icon: '🛰️',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '© <a href="https://www.esri.com">Esri</a> | Maxar, Earthstar Geographics',
    maxZoom: 19,
  },
}

// Opciones geológicas del dominio
const HORIZONTES = ['Óxidos', 'Sulfuros secundarios', 'Sulfuros primarios', 'Zona de lixiviación', 'Sin definir']
const ROCAS_CAJA = ['Granodiorita', 'Tonalita', 'Pórfido cuarzo-feldespático', 'Andesita', 'Brecha', 'Skarn', 'Mármol', 'Cuarcita', 'Otro']
const ESTRUCTURAS_OPTS = ['Falla', 'Diaclasa', 'Veta', 'Vetilla', 'Brecha estructural', 'Foliación', 'Cizalle', 'Sin estructura', 'Otro']
const MINERALES_OPTS = ['Calcopirita', 'Bornita', 'Calcocita', 'Covelina', 'Malaquita', 'Azurita', 'Pirita', 'Molibdenita', 'Magnetita', 'Hematita', 'Limonita', 'Cuarzo', 'Otro']
const ALTERACIONES_OPTS = ['Potásica', 'Fílica', 'Argílica', 'Propilítica', 'Argilización avanzada', 'Silicificación', 'Cloritización', 'Sin alteración', 'Otro']
const MINERALIZACIONES_OPTS = ['Alta', 'Media', 'Baja', 'Estéril', 'Sin definir']

// Fix leaflet default icon
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

// Custom geological station icon — color según horizonte
const createStationIcon = (horizonte) => {
  const colors = {
    'Óxidos': '#F59E0B',
    'Sulfuros secundarios': '#3B82F6',
    'Sulfuros primarios': '#8B5CF6',
    'Zona de lixiviación': '#22C55E',
  }
  const color = colors[horizonte] || '#B91C1C'
  return L.divIcon({
    className: '',
    html: `<div style="
      width:28px;height:28px;border-radius:50% 50% 50% 0;
      background:${color};border:2.5px solid #D4AF37;
      transform:rotate(-45deg);box-shadow:0 2px 8px rgba(0,0,0,0.4);
    "></div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 28],
  })
}

// GPS position icon
const gpsIcon = L.divIcon({
  className: '',
  html: `<div style="
    width:16px;height:16px;border-radius:50%;
    background:#3B82F6;border:3px solid #fff;
    box-shadow:0 0 0 4px rgba(59,130,246,0.3);
  "></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
})

// ── GPS Tracker component ──
function GPSTracker({ onPosition }) {
  useMapEvents({
    locationfound(e) { onPosition(e.latlng) },
    locationerror() { console.warn('GPS no disponible') }
  })
  return null
}

// ── Layer Switcher ──
function LayerSwitcher({ activeLayer, onChange }) {
  const [open, setOpen] = useState(false)
  const layer = TILE_LAYERS[activeLayer]
  return (
    <div style={{ position: 'fixed', bottom: 96, left: 12, zIndex: 999 }}>
      {open && (
        <div className="fade-in" style={{
          position: 'absolute', bottom: 52, left: 0,
          background: 'rgba(10,10,11,0.95)', backdropFilter: 'blur(16px)',
          border: '1px solid rgba(212,175,55,0.3)', borderRadius: 14,
          overflow: 'hidden', minWidth: 160,
        }}>
          {Object.entries(TILE_LAYERS).map(([key, l]) => (
            <button key={key} onClick={() => { onChange(key); setOpen(false) }}
              style={{
                display: 'flex', alignItems: 'center', gap: 10,
                width: '100%', padding: '11px 16px',
                border: 'none', cursor: 'pointer', textAlign: 'left',
                color: activeLayer === key ? '#D4AF37' : '#fff',
                fontFamily: 'Inter, sans-serif', fontSize: 13, fontWeight: activeLayer === key ? 700 : 400,
                borderBottom: '1px solid rgba(255,255,255,0.06)',
                background: activeLayer === key ? 'rgba(212,175,55,0.08)' : 'transparent',
              }}>
              <span style={{ fontSize: 18 }}>{l.icon}</span>
              {l.name}
              {activeLayer === key && <span style={{ marginLeft: 'auto', color: '#D4AF37' }}>✓</span>}
            </button>
          ))}
        </div>
      )}
      <button onClick={() => setOpen(o => !o)} style={{
        width: 44, height: 44, borderRadius: 12,
        background: open ? 'rgba(212,175,55,0.15)' : 'rgba(10,10,11,0.9)',
        border: `1px solid ${open ? '#D4AF37' : 'rgba(212,175,55,0.3)'}`,
        color: open ? '#D4AF37' : '#fff', fontSize: 20, cursor: 'pointer',
        backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center',
        transition: 'all 0.2s',
      }} title={`Capa: ${layer.name}`}>
        {layer.icon}
      </button>
    </div>
  )
}

// ── Recenter map button ──
function RecenterButton({ position }) {
  const map = useMap()
  if (!position) return null
  return (
    <button
      onClick={() => map.flyTo(position, 16)}
      style={{
        position: 'absolute', bottom: 100, right: 12, zIndex: 999,
        background: 'rgba(10,10,11,0.9)', border: '1px solid rgba(212,175,55,0.3)',
        color: '#fff', borderRadius: '50%', width: 44, height: 44,
        cursor: 'pointer', fontSize: 18, backdropFilter: 'blur(8px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center'
      }}
      title="Ir a mi posición"
    >📍</button>
  )
}

// ── Multi-select chip button ──
function ChipSelect({ options, value, onChange, color = '#B91C1C' }) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 16 }}>
      {options.map(opt => {
        const isArr = Array.isArray(value)
        const selected = isArr ? value.includes(opt) : value === opt
        return (
          <button key={opt} onClick={() => {
            if (isArr) {
              onChange(selected ? value.filter(v => v !== opt) : [...value, opt])
            } else {
              onChange(selected ? '' : opt)
            }
          }} style={{
            padding: '6px 12px', borderRadius: 8, fontSize: 12,
            border: `1.5px solid ${selected ? color : 'rgba(255,255,255,0.12)'}`,
            background: selected ? `${color}22` : '#1A1A1C',
            color: selected ? '#fff' : '#8E8E93',
            cursor: 'pointer', fontFamily: 'Inter, sans-serif',
            fontWeight: selected ? 600 : 400, transition: 'all 0.15s',
          }}>
            {opt}
          </button>
        )
      })}
    </div>
  )
}

// ── Station Form Panel ──
function StationForm({ position, onSave, onClose }) {
  // Identificación
  const [cp, setCp] = useState('')
  const [semana, setSemana] = useState('')
  const [idSample, setIdSample] = useState('')
  // Posición
  const [elevation, setElevation] = useState('')
  const [xm, setXm] = useState(position ? position.lng.toFixed(2) : '')
  const [ym, setYm] = useState(position ? position.lat.toFixed(2) : '')
  // Profundidad
  const [fromM, setFromM] = useState('')
  const [toM, setToM] = useState('')
  // Geología
  const [horizonte, setHorizonte] = useState('')
  const [rocaCaja, setRocaCaja] = useState('')
  const [estructura, setEstructura] = useState('')
  const [rumbo, setRumbo] = useState('')
  const [manteo, setManteo] = useState('')
  // Mineralogía
  const [minerales, setMinerales] = useState([])
  const [alteracion, setAlteracion] = useState('')
  const [mineraliza, setMineraliza] = useState('')
  const [comentario, setComentario] = useState('')
  // Audio
  const [isRecording, setIsRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState(null)
  const [blink, setBlink] = useState(false)
  const mediaRef = useRef(null)
  const blinkRef = useRef(null)

  useEffect(() => {
    if (isRecording) {
      blinkRef.current = setInterval(() => setBlink(b => !b), 500)
    } else {
      clearInterval(blinkRef.current)
      setBlink(false)
    }
    return () => clearInterval(blinkRef.current)
  }, [isRecording])

  const toggleRecording = async () => {
    if (isRecording) {
      mediaRef.current?.stop()
      setIsRecording(false)
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        const recorder = new MediaRecorder(stream)
        const chunks = []
        recorder.ondataavailable = e => chunks.push(e.data)
        recorder.onstop = () => {
          setAudioBlob(new Blob(chunks, { type: 'audio/webm' }))
          stream.getTracks().forEach(t => t.stop())
        }
        recorder.start()
        mediaRef.current = recorder
        setIsRecording(true)
      } catch {
        alert('Micrófono no disponible')
      }
    }
  }

  const handleSave = () => {
    if (!cp) { alert('CP es requerido'); return }
    if (!idSample) { alert('IDSAMPLE es requerido'); return }
    onSave({
      cp, semana, idSample,
      elevation: parseFloat(elevation) || null,
      xm: parseFloat(xm) || null,
      ym: parseFloat(ym) || null,
      from: parseFloat(fromM) || null,
      to: parseFloat(toM) || null,
      horizonte, rocaCaja, estructura,
      rumbo: rumbo ? parseFloat(rumbo) : null,
      manteo: manteo ? parseFloat(manteo) : null,
      minerales: minerales.join('; '),
      alteracion, mineraliza, comentario,
      audioBlob, position,
      createdAt: new Date().toISOString()
    })
  }

  const sectionLabel = (text, icon) => (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8,
      margin: '16px 0 10px', paddingBottom: 6,
      borderBottom: '1px solid rgba(212,175,55,0.15)'
    }}>
      <span style={{ fontSize: 14 }}>{icon}</span>
      <span style={{ color: '#D4AF37', fontSize: 11, fontWeight: 700, letterSpacing: '0.1em' }}>{text}</span>
    </div>
  )

  return (
    <div className="slide-up" style={{
      position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 2000,
      background: 'rgba(10,10,11,0.96)', backdropFilter: 'blur(24px)',
      borderTop: '1.5px solid rgba(212,175,55,0.3)',
      borderRadius: '24px 24px 0 0', padding: '16px 20px 36px',
      maxHeight: '90vh', overflowY: 'auto'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 20 }}>⛏️</span>
          <span style={{ color: '#D4AF37', fontWeight: 700, fontSize: 14, letterSpacing: '0.1em' }}>NUEVA MUESTRA</span>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#8E8E93', fontSize: 20, cursor: 'pointer' }}>✕</button>
      </div>
      <div style={{ fontSize: 11, color: '#8E8E93', marginBottom: 4 }}>
        📍 {position ? `${position.lat.toFixed(5)}, ${position.lng.toFixed(5)}` : 'Centro del mapa'}
      </div>
      <div className="divider" />

      {/* ── IDENTIFICACIÓN ── */}
      {sectionLabel('IDENTIFICACIÓN', '🏷️')}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 4 }}>
        <div>
          <span className="field-label">CP *</span>
          <input className="input-field" placeholder="ej: CP-01" value={cp} onChange={e => setCp(e.target.value)} />
        </div>
        <div>
          <span className="field-label">SEMANA</span>
          <input className="input-field" placeholder="ej: 22" type="number" value={semana} onChange={e => setSemana(e.target.value)} />
        </div>
        <div>
          <span className="field-label">IDSAMPLE *</span>
          <input className="input-field" placeholder="ej: S-001" value={idSample} onChange={e => setIdSample(e.target.value)} />
        </div>
      </div>

      {/* ── POSICIÓN ── */}
      {sectionLabel('POSICIÓN & PROFUNDIDAD', '📐')}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 4 }}>
        <div>
          <span className="field-label">ELEVATION (m)</span>
          <input className="input-field" placeholder="msnm" type="number" value={elevation} onChange={e => setElevation(e.target.value)} />
        </div>
        <div>
          <span className="field-label">Xm (E)</span>
          <input className="input-field" placeholder="UTM Este" type="number" value={xm} onChange={e => setXm(e.target.value)} />
        </div>
        <div>
          <span className="field-label">Ym (N)</span>
          <input className="input-field" placeholder="UTM Norte" type="number" value={ym} onChange={e => setYm(e.target.value)} />
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 4 }}>
        <div>
          <span className="field-label">FROM (m)</span>
          <input className="input-field" placeholder="desde" type="number" step="0.1" value={fromM} onChange={e => setFromM(e.target.value)} />
        </div>
        <div>
          <span className="field-label">TO (m)</span>
          <input className="input-field" placeholder="hasta" type="number" step="0.1" value={toM} onChange={e => setToM(e.target.value)} />
        </div>
      </div>

      {/* ── GEOLOGÍA ── */}
      {sectionLabel('GEOLOGÍA', '🪨')}
      <span className="field-label">HORIZONTE</span>
      <ChipSelect options={HORIZONTES} value={horizonte} onChange={setHorizonte} color="#F59E0B" />

      <span className="field-label">ROCA CAJA</span>
      <ChipSelect options={ROCAS_CAJA} value={rocaCaja} onChange={setRocaCaja} color="#8B5CF6" />

      <span className="field-label">ESTRUCTURA</span>
      <ChipSelect options={ESTRUCTURAS_OPTS} value={estructura} onChange={setEstructura} color="#3B82F6" />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 4 }}>
        <div>
          <span className="field-label">RUMBO (STRIKE °)</span>
          <input className="input-field" type="number" placeholder="0 – 360°" value={rumbo} onChange={e => setRumbo(e.target.value)} min={0} max={360} />
        </div>
        <div>
          <span className="field-label">MANTEO (DIP °)</span>
          <input className="input-field" type="number" placeholder="0 – 90°" value={manteo} onChange={e => setManteo(e.target.value)} min={0} max={90} />
        </div>
      </div>

      {/* ── MINERALOGÍA ── */}
      {sectionLabel('MINERALOGÍA', '💎')}
      <span className="field-label">MINERALES (multi-select)</span>
      <ChipSelect options={MINERALES_OPTS} value={minerales} onChange={setMinerales} color="#22C55E" />

      <span className="field-label">ALTERACION</span>
      <ChipSelect options={ALTERACIONES_OPTS} value={alteracion} onChange={setAlteracion} color="#EC4899" />

      <span className="field-label">MINERALIZA</span>
      <ChipSelect options={MINERALIZACIONES_OPTS} value={mineraliza} onChange={setMineraliza} color="#B91C1C" />

      {/* ── COMENTARIO ── */}
      {sectionLabel('COMENTARIO', '📝')}
      <textarea className="input-field" placeholder="Observaciones de campo, descripción de la muestra..." value={comentario} onChange={e => setComentario(e.target.value)}
        style={{ height: 80, resize: 'none', marginBottom: 20 }} />

      {/* Audio + Guardar */}
      <div style={{ display: 'flex', gap: 12 }}>
        <button onClick={toggleRecording} className={isRecording ? 'pulse-red' : ''} style={{
          width: 56, height: 56, borderRadius: '50%', flexShrink: 0,
          background: isRecording ? (blink ? '#B91C1C' : 'rgba(185,28,28,0.5)') : '#1E1E20',
          border: `2px solid ${isRecording ? '#D4AF37' : 'rgba(255,255,255,0.2)'}`,
          color: '#fff', fontSize: 22, cursor: 'pointer', transition: 'all 0.3s'
        }} title={isRecording ? 'Detener grabación' : 'Grabar audio'}>
          {isRecording ? '🔴' : '🎙️'}
        </button>
        {audioBlob && <span style={{ color: '#22C55E', fontSize: 12, alignSelf: 'center' }}>✅ Audio grabado</span>}
        <button className="btn-primary" onClick={handleSave} style={{ flex: 1, justifyContent: 'center' }}>
          GUARDAR MUESTRA
        </button>
      </div>
    </div>
  )
}

// ── Station List Sidebar ──
function StationSidebar({ stations, onClose, onExport }) {
  const horizColors = {
    'Óxidos': '#F59E0B',
    'Sulfuros secundarios': '#3B82F6',
    'Sulfuros primarios': '#8B5CF6',
    'Zona de lixiviación': '#22C55E',
  }

  return (
    <div className="slide-in" style={{
      position: 'fixed', top: 0, left: 0, bottom: 0, width: 340, zIndex: 1500,
      background: 'rgba(10,10,11,0.97)', backdropFilter: 'blur(20px)',
      borderRight: '1px solid rgba(212,175,55,0.2)', display: 'flex', flexDirection: 'column'
    }}>
      {/* Header */}
      <div style={{ padding: '20px 16px 12px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <span style={{ color: '#D4AF37', fontWeight: 700, fontSize: 13, letterSpacing: '0.1em' }}>⛏️ MUESTRAS</span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#8E8E93', cursor: 'pointer', fontSize: 18 }}>✕</button>
        </div>
        <div style={{ color: '#8E8E93', fontSize: 12 }}>{stations.length} muestra{stations.length !== 1 ? 's' : ''} registrada{stations.length !== 1 ? 's' : ''}</div>
      </div>

      {/* List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 12px' }}>
        {stations.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#8E8E93', marginTop: 40, fontSize: 13 }}>
            <div style={{ fontSize: 32, marginBottom: 8 }}>🗺️</div>
            Aún no hay muestras.<br />Toca el mapa para crear una.
          </div>
        ) : stations.map((s, i) => (
          <div key={i} className="fade-in" style={{
            background: '#1E1E20', borderRadius: 12, padding: '12px 14px', marginBottom: 8,
            border: '1px solid rgba(212,175,55,0.15)',
            transition: 'border-color 0.2s'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                <span className="chip chip-gold">{s.cp || '—'}</span>
                <span className="chip chip-red">{s.idSample || '—'}</span>
                {s.horizonte && <span style={{
                  padding: '2px 8px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                  background: `${horizColors[s.horizonte] || '#B91C1C'}22`,
                  color: horizColors[s.horizonte] || '#B91C1C', border: `1px solid ${horizColors[s.horizonte] || '#B91C1C'}44`
                }}>{s.horizonte}</span>}
              </div>
              <span style={{ color: '#8E8E93', fontSize: 10 }}>#{i + 1}</span>
            </div>
            <div style={{ fontSize: 11, color: '#8E8E93', fontFeatureSettings: '"tnum"', marginBottom: 4 }}>
              {s.rocaCaja && <span style={{ color: '#aaa' }}>{s.rocaCaja}</span>}
              {s.estructura && <span style={{ color: '#888' }}> · {s.estructura}</span>}
            </div>
            {(s.rumbo !== null || s.manteo !== null) && (
              <div style={{ fontSize: 11, color: '#8E8E93' }}>
                Strike: <span style={{ color: '#fff' }}>{s.rumbo ?? '—'}°</span> &nbsp;|&nbsp;
                Dip: <span style={{ color: '#fff' }}>{s.manteo ?? '—'}°</span>
              </div>
            )}
            {s.minerales && <div style={{ fontSize: 11, color: '#22C55E', marginTop: 4 }}>💎 {s.minerales}</div>}
            {s.comentario && <div style={{ fontSize: 11, color: '#8E8E93', marginTop: 4, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.comentario}</div>}
            {s.audioBlob && <div style={{ marginTop: 4 }}><span className="chip chip-green">🎙️ Audio</span></div>}
            <div style={{ fontSize: 10, color: '#555', marginTop: 6 }}>
              {s.from != null && s.to != null ? `${s.from}m – ${s.to}m` : ''}
              {s.elevation ? ` · ${s.elevation}m snm` : ''}
            </div>
          </div>
        ))}
      </div>

      {/* Export button */}
      {stations.length > 0 && (
        <div style={{ padding: '12px 16px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
          <button className="btn-primary" onClick={onExport} style={{ width: '100%', justifyContent: 'center' }}>
            📦 Exportar Campaña ZIP
          </button>
        </div>
      )}
    </div>
  )
}

// ── Main App ──
export default function App() {
  const [stations, setStations] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [clickPosition, setClickPosition] = useState(null)
  const [gpsPosition, setGpsPosition] = useState(null)
  const [showSidebar, setShowSidebar] = useState(false)
  const [mapCenter] = useState([-33.45, -70.65]) // Santiago como default
  const [activeLayer, setActiveLayer] = useState('osm')

  // Map click handler
  function MapClickHandler() {
    useMapEvents({
      click(e) {
        setClickPosition(e.latlng)
        setShowForm(true)
        setShowSidebar(false)
      }
    })
    return null
  }

  const handleSaveStation = useCallback((station) => {
    setStations(prev => [...prev, station])
    setShowForm(false)
    setClickPosition(null)
  }, [])

  const handleExport = useCallback(async () => {
    const { default: JSZip } = await import('jszip')
    const zip = new JSZip()

    // GeoJSON
    const geojson = {
      type: 'FeatureCollection',
      features: stations.map((s, i) => ({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [s.position.lng, s.position.lat] },
        properties: {
          id: i + 1,
          CP: s.cp, SEMANA: s.semana, IDSAMPLE: s.idSample,
          Elevation: s.elevation, Xm: s.xm, Ym: s.ym,
          From: s.from, To: s.to,
          HORIZONTE: s.horizonte, ROCA_CAJA: s.rocaCaja,
          ESTRUCTURA: s.estructura, RUMBO: s.rumbo, MANTEO: s.manteo,
          MINERALES: s.minerales, ALTERACION: s.alteracion,
          MINERALIZA: s.mineraliza, COMENTARIO: s.comentario,
          createdAt: s.createdAt
        }
      }))
    }
    zip.file('muestras.geojson', JSON.stringify(geojson, null, 2))

    // CSV — columnas exactas de la planilla
    const headers = 'CP\tSEMANA\tIDSAMPLE\tElevation\tXm\tYm\tFrom\tTo\tHORIZONTE\tROCA CAJA\tESTRUCTURA\tRUMBO\tMANTEO\tMINERALES\tALTERACION\tMINERALIZA\tCOMENTARIO\tLat\tLng\tFecha'
    const rows = stations.map(s =>
      [s.cp, s.semana, s.idSample, s.elevation, s.xm, s.ym,
       s.from, s.to, s.horizonte, s.rocaCaja, s.estructura,
       s.rumbo, s.manteo, s.minerales, s.alteracion, s.mineraliza,
       `"${(s.comentario||'').replace(/"/g,'""')}"`,
       s.position.lat, s.position.lng, s.createdAt].join('\t')
    )
    zip.file('muestras.tsv', [headers, ...rows].join('\n'))

    // Audios
    stations.forEach((s, i) => {
      if (s.audioBlob) zip.file(`audio_${s.cp || i+1}_${s.idSample || ''}.webm`, s.audioBlob)
    })

    const blob = await zip.generateAsync({ type: 'blob' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `campana_GeoINducta_${new Date().toISOString().slice(0,10)}.zip`
    a.click()
    URL.revokeObjectURL(url)
  }, [stations])

  return (
    <div style={{ height: '100vh', width: '100vw', position: 'relative' }}>
      {/* Top Bar */}
      <div style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 1000,
        background: 'rgba(10,10,11,0.9)', backdropFilter: 'blur(16px)',
        borderBottom: '1px solid rgba(212,175,55,0.2)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '10px 16px', height: 56
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button onClick={() => { setShowSidebar(s => !s); setShowForm(false) }}
            style={{ background: 'none', border: 'none', color: showSidebar ? '#D4AF37' : '#8E8E93', fontSize: 20, cursor: 'pointer' }}>☰</button>
          <span style={{ fontWeight: 700, fontSize: 16, letterSpacing: '0.05em' }}>
            Geo<span style={{ color: '#B91C1C' }}>IN</span>ducta
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {gpsPosition && <span className="chip chip-green">📍 GPS</span>}
          <span className="chip chip-gold">{stations.length} muestras</span>
        </div>
      </div>

      {/* Map */}
      <MapContainer
        center={mapCenter}
        zoom={13}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
      >
        <TileLayer
          key={activeLayer}
          url={TILE_LAYERS[activeLayer].url}
          attribution={TILE_LAYERS[activeLayer].attribution}
          maxZoom={TILE_LAYERS[activeLayer].maxZoom}
        />
        <MapClickHandler />
        <GPSTracker onPosition={setGpsPosition} />

        {/* GPS position marker */}
        {gpsPosition && <Marker position={gpsPosition} icon={gpsIcon}><Popup>Tu posición actual</Popup></Marker>}

        {/* Station markers */}
        {stations.map((s, i) => (
          <Marker key={i} position={s.position} icon={createStationIcon(s.horizonte)}>
            <Popup>
              <div style={{ minWidth: 200, fontFamily: 'Inter, sans-serif', fontSize: 12 }}>
                <strong style={{ color: '#B91C1C', display: 'block', marginBottom: 4 }}>
                  {s.cp} — {s.idSample}
                </strong>
                {s.horizonte && <div><b>Horizonte:</b> {s.horizonte}</div>}
                {s.rocaCaja && <div><b>Roca caja:</b> {s.rocaCaja}</div>}
                {s.estructura && <div><b>Estructura:</b> {s.estructura}</div>}
                {s.rumbo != null && <div><b>Strike/Dip:</b> {s.rumbo}° / {s.manteo}°</div>}
                {s.minerales && <div><b>Minerales:</b> {s.minerales}</div>}
                {s.alteracion && <div><b>Alteración:</b> {s.alteracion}</div>}
                {s.mineraliza && <div><b>Mineralización:</b> {s.mineraliza}</div>}
                {(s.from != null || s.to != null) && <div><b>Intervalo:</b> {s.from}m – {s.to}m</div>}
                {s.comentario && <div><b>Comentario:</b> {s.comentario}</div>}
                {s.audioBlob && <div style={{ marginTop: 4 }}>🎙️ Audio registrado</div>}
              </div>
            </Popup>
          </Marker>
        ))}

        <RecenterButton position={gpsPosition} />
      </MapContainer>

      {/* Layer Switcher */}
      <LayerSwitcher activeLayer={activeLayer} onChange={setActiveLayer} />

      {/* Sidebar */}
      {showSidebar && <StationSidebar stations={stations} onClose={() => setShowSidebar(false)} onExport={handleExport} />}

      {/* Station Form */}
      {showForm && (
        <StationForm
          position={clickPosition}
          onSave={handleSaveStation}
          onClose={() => { setShowForm(false); setClickPosition(null) }}
        />
      )}

      {/* FAB hint */}
      {!showForm && !showSidebar && stations.length === 0 && (
        <div className="fade-in" style={{
          position: 'fixed', bottom: 80, left: '50%', transform: 'translateX(-50%)',
          background: 'rgba(10,10,11,0.85)', backdropFilter: 'blur(12px)',
          border: '1px solid rgba(212,175,55,0.3)', borderRadius: 99,
          padding: '10px 20px', fontSize: 13, color: '#D4AF37', zIndex: 999,
          whiteSpace: 'nowrap'
        }}>
          👆 Toca el mapa para registrar una muestra
        </div>
      )}

      {/* GPS activate button */}
      <button
        onClick={() => {
          if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
              pos => setGpsPosition({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
              () => alert('GPS no disponible')
            )
          }
        }}
        style={{
          position: 'fixed', bottom: 40, right: 12, zIndex: 999,
          background: 'rgba(10,10,11,0.9)', border: '1px solid rgba(212,175,55,0.3)',
          color: '#fff', borderRadius: '50%', width: 44, height: 44,
          cursor: 'pointer', fontSize: 20, backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}
        title="Activar GPS"
      >🛰️</button>
    </div>
  )
}
