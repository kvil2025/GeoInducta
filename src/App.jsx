import { useState, useEffect, useRef, useCallback } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMapEvents, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import localforage from 'localforage'
import imageCompression from 'browser-image-compression'
import { useGoogleLogin } from '@react-oauth/google'
import { kml } from '@tmcw/togeojson'
import parseGeoraster from 'georaster'
import GeoRasterLayer from 'georaster-layer-for-leaflet'
import { GeoJSON } from 'react-leaflet'

// ─── CONSTANTS ───────────────────────────────────────────────────────────────
const TILE_LAYERS = {
  osm: {
    name: 'Calles', icon: '🗺️',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '© OpenStreetMap', maxZoom: 19,
  },
  topo: {
    name: 'Topográfico', icon: '🏔️',
    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    attribution: '© OpenTopoMap', maxZoom: 17,
  },
  satellite: {
    name: 'Satelital', icon: '🛰️',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '© Esri', maxZoom: 19,
  },
}

const HORIZONTES = [
  'Pedolito Superior', 'Pedolito Inferior', 'Pedolito Sup / Inf',
  'Saprolito Superior', 'Saprolito Inferior', 'Saprolito Sup / Inf',
  'Pedolito / Saprolito', 'Roca Fresca', 'Sin definir',
]

const ROCAS_CAJA = [
  'Granodiorita', 'Tonalita', 'Pórfido Q-Fsp', 'Andesita',
  'Brecha', 'Skarn', 'Mármol', 'Cuarcita', 'Otro',
]

const ESTRUCTURAS = [
  'Falla', 'Diaclasa', 'Veta', 'Vetilla',
  'Brecha estructural', 'Foliación', 'Cizalle', 'Sin estructura', 'Otro',
]

const MINERALOGIA_OPTS = [
  'Calcopirita', 'Bornita', 'Calcocita', 'Covelina',
  'Malaquita', 'Azurita', 'Pirita', 'Molibdenita',
  'Magnetita', 'Hematita', 'Limonita', 'Cuarzo', 'Otro',
]

const MINERALIZACION_OPTS = ['Alta', 'Media', 'Baja', 'Estéril', 'Sin definir']

const ALT_MINERALES = ['Kaolín', 'FeOx', 'Qz', 'Biotita', 'Muscovita']
const GRADOS        = ['--', '-', '+-', '+', '++']
const GRADO_COLOR   = { '--': '#6B7280', '-': '#60A5FA', '+-': '#FBBF24', '+': '#F97316', '++': '#EF4444' }
const GRADO_LABEL   = { '--': 'Muy débil', '-': 'Débil', '+-': 'Moderado', '+': 'Fuerte', '++': 'Muy fuerte' }

// ─── LEAFLET ICON FIX ────────────────────────────────────────────────────────
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const createStationIcon = (muestras) => {
  const h = muestras[0]?.horizonte || ''
  const color = h.includes('Pedolito') ? '#F59E0B'
    : h.includes('Saprolito') ? '#8B5CF6'
    : h === 'Roca Fresca' ? '#3B82F6'
    : '#B91C1C'
  const count = muestras.length
  return L.divIcon({
    className: '',
    html: `<div style="position:relative;width:32px;height:32px;">
      <div style="width:28px;height:28px;border-radius:50% 50% 50% 0;
        background:${color};border:2.5px solid #D4AF37;transform:rotate(-45deg);
        box-shadow:0 2px 8px rgba(0,0,0,0.5);"></div>
      ${count > 1 ? `<div style="position:absolute;top:-5px;right:-5px;
        width:17px;height:17px;border-radius:50%;background:#D4AF37;color:#000;
        font-size:9px;font-weight:800;display:flex;align-items:center;
        justify-content:center;font-family:Inter,sans-serif;">${count}</div>` : ''}
    </div>`,
    iconSize: [32, 32],
    iconAnchor: [14, 28],
  })
}

const gpsIcon = L.divIcon({
  className: '',
  html: `<div style="width:16px;height:16px;border-radius:50%;background:#3B82F6;
    border:3px solid #fff;box-shadow:0 0 0 4px rgba(59,130,246,0.3);"></div>`,
  iconSize: [16, 16], iconAnchor: [8, 8],
})

// ─── HELPERS ─────────────────────────────────────────────────────────────────
const generateId = () => Math.random().toString(36).substr(2, 9)

const newMuestra = () => ({
  _id: generateId(),
  cp: '', idSample: '', elevation: '', xm: '', ym: '', from: '', to: '',
  horizonte: '', rocaCaja: '', estructura: '', rumbo: '', manteo: '',
  mineralogia: [],
  alteracion: { Kaolín: null, FeOx: null, Qz: null, Biotita: null, Muscovita: null },
  mineralizacion: '', comentario: '', takenBy: '', semana: '',
  fotos: [],
  audioBlob: null,
})

const inputSt = {
  width: '100%', padding: '8px 10px', borderRadius: 8,
  background: '#111113', border: '1px solid rgba(255,255,255,0.1)',
  color: '#fff', fontSize: 13, fontFamily: 'Inter, sans-serif',
  outline: 'none', boxSizing: 'border-box',
}

const labelSt = {
  display: 'block', fontSize: 10, color: '#8E8E93',
  fontWeight: 600, letterSpacing: '0.08em', marginBottom: 4,
  fontFamily: 'Inter, sans-serif',
}

// ─── COMPONENTS ──────────────────────────────────────────────────────────────
function GeoTiffLayer({ georaster }) {
  const map = useMap()
  useEffect(() => {
    if (!georaster) return
    let layer
    try {
      layer = new GeoRasterLayer({
        georaster,
        opacity: 0.7,
        resolution: 256
      })
      layer.addTo(map)
      map.fitBounds(layer.getBounds())
    } catch (err) {
      console.error('Error renderizando GeoTIFF', err)
    }
    return () => {
      if (layer) map.removeLayer(layer)
    }
  }, [georaster, map])
  return null
}

function GPSTracker({ onPosition }) {
  const map = useMap()
  
  useEffect(() => {
    map.locate({ setView: true, maxZoom: 16 })
  }, [map])

  useMapEvents({
    locationfound(e) { onPosition(e.latlng) },
    locationerror() { console.warn('GPS no disponible') },
  })
  return null
}

function RecenterButton({ position }) {
  const map = useMap()
  if (!position) return null
  return (
    <button onClick={() => map.flyTo(position, 16)} style={{
      position: 'absolute', bottom: 100, right: 12, zIndex: 999,
      background: 'rgba(10,10,11,0.9)', border: '1px solid rgba(212,175,55,0.3)',
      color: '#fff', borderRadius: '50%', width: 44, height: 44,
      cursor: 'pointer', fontSize: 18, backdropFilter: 'blur(8px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }} title="Ir a mi posición">📍</button>
  )
}

function ChipSelect({ options, value, onChange, multi = false, color = '#B91C1C' }) {
  const toggle = (opt) => {
    if (multi) {
      const arr = value || []
      onChange(arr.includes(opt) ? arr.filter(v => v !== opt) : [...arr, opt])
    } else {
      onChange(value === opt ? '' : opt)
    }
  }
  const sel = (opt) => multi ? (value || []).includes(opt) : value === opt
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
      {options.map(opt => (
        <button key={opt} onClick={() => toggle(opt)} style={{
          padding: '5px 11px', borderRadius: 8, fontSize: 12,
          border: `1.5px solid ${sel(opt) ? color : 'rgba(255,255,255,0.12)'}`,
          background: sel(opt) ? `${color}22` : '#1A1A1C',
          color: sel(opt) ? '#fff' : '#8E8E93',
          cursor: 'pointer', fontFamily: 'Inter, sans-serif',
          fontWeight: sel(opt) ? 600 : 400, transition: 'all 0.15s',
        }}>{opt}</button>
      ))}
    </div>
  )
}

function AlteracionSelector({ value, onChange }) {
  const toggle = (mineral, grado) =>
    onChange({ ...value, [mineral]: value[mineral] === grado ? null : grado })

  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', gap: 6, marginBottom: 10, flexWrap: 'wrap' }}>
        {GRADOS.map(g => (
          <span key={g} style={{
            fontSize: 10, color: GRADO_COLOR[g], fontFamily: 'monospace',
            background: `${GRADO_COLOR[g]}18`, border: `1px solid ${GRADO_COLOR[g]}44`,
            borderRadius: 6, padding: '2px 7px',
          }}>{g} {GRADO_LABEL[g]}</span>
        ))}
      </div>
      {ALT_MINERALES.map(mineral => (
        <div key={mineral} style={{
          display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8,
          padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.05)',
        }}>
          <span style={{
            width: 68, fontSize: 12, flexShrink: 0, fontFamily: 'Inter, sans-serif',
            color: value[mineral] ? '#fff' : '#8E8E93', fontWeight: value[mineral] ? 600 : 400,
          }}>{mineral}</span>
          <div style={{ display: 'flex', gap: 5, flex: 1 }}>
            {GRADOS.map(g => {
              const active = value[mineral] === g
              return (
                <button key={g} onClick={() => toggle(mineral, g)} title={GRADO_LABEL[g]} style={{
                  flex: 1, height: 30, borderRadius: 7, fontSize: 11, fontWeight: 700,
                  border: `1.5px solid ${active ? GRADO_COLOR[g] : 'rgba(255,255,255,0.1)'}`,
                  background: active ? `${GRADO_COLOR[g]}30` : '#111113',
                  color: active ? GRADO_COLOR[g] : '#555',
                  cursor: 'pointer', fontFamily: 'monospace', transition: 'all 0.15s',
                  minWidth: 32,
                }}>{g}</button>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}

function FotoGaleria({ fotos, onChange }) {
  const inputRef = useRef(null)
  const [lightbox, setLightbox] = useState(null)
  const [isCompressing, setIsCompressing] = useState(false)

  const handleFiles = async (e) => {
    const files = Array.from(e.target.files)
    if (!files.length) return
    setIsCompressing(true)
    
    const options = { maxSizeMB: 1, maxWidthOrHeight: 1280, useWebWorker: true, initialQuality: 0.8 }

    const compressed = await Promise.all(
      files.map(async (f) => {
        try {
          const compressedFile = await imageCompression(f, options)
          return { file: compressedFile, url: URL.createObjectURL(compressedFile), name: f.name }
        } catch (error) {
          console.error('Error al comprimir foto:', error)
          return { file: f, url: URL.createObjectURL(f), name: f.name }
        }
      })
    )
    
    onChange([...fotos, ...compressed])
    e.target.value = ''
    setIsCompressing(false)
  }

  const remove = (idx) => {
    URL.revokeObjectURL(fotos[idx].url)
    onChange(fotos.filter((_, i) => i !== idx))
  }

  return (
    <>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
        {fotos.map((f, i) => (
          <div key={i} style={{ position: 'relative', width: 76, height: 76, flexShrink: 0 }}>
            <img src={f.url} alt={`foto ${i + 1}`} onClick={() => setLightbox(f.url)} style={{
              width: '100%', height: '100%', objectFit: 'cover', borderRadius: 10, cursor: 'zoom-in',
              border: '1.5px solid rgba(212,175,55,0.3)',
            }} />
            <button onClick={() => remove(i)} style={{
              position: 'absolute', top: -7, right: -7, width: 20, height: 20, borderRadius: '50%',
              background: '#B91C1C', border: '2px solid #0a0a0b', color: '#fff', fontSize: 9, cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800,
            }}>✕</button>
          </div>
        ))}
        
        <button onClick={() => inputRef.current.click()} disabled={isCompressing} style={{
          width: 76, height: 76, borderRadius: 10, flexShrink: 0, border: '1.5px dashed rgba(212,175,55,0.4)',
          background: 'rgba(212,175,55,0.04)', color: isCompressing ? '#888' : '#D4AF37', cursor: isCompressing ? 'wait' : 'pointer',
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          gap: 4, fontFamily: 'Inter, sans-serif', fontSize: 10, transition: 'background 0.2s', opacity: isCompressing ? 0.6 : 1
        }}>
          {isCompressing ? '⏳' : <><span style={{ fontSize: 22 }}>📸</span>Foto</>}
        </button>
      </div>
      <input ref={inputRef} type="file" accept="image/*" capture="environment" multiple onChange={handleFiles} style={{ display: 'none' }} />
      {lightbox && (
        <div onClick={() => setLightbox(null)} style={{
          position: 'fixed', inset: 0, zIndex: 9999, background: 'rgba(0,0,0,0.93)', backdropFilter: 'blur(10px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'zoom-out',
        }}>
          <img src={lightbox} alt="ampliada" style={{ maxWidth: '96vw', maxHeight: '90vh', borderRadius: 14, objectFit: 'contain' }} />
        </div>
      )}
    </>
  )
}

function SectionLabel({ icon, text }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 7, margin: '16px 0 9px', paddingBottom: 6,
      borderBottom: '1px solid rgba(212,175,55,0.12)',
    }}>
      <span style={{ fontSize: 13 }}>{icon}</span>
      <span style={{ color: '#D4AF37', fontSize: 10, fontWeight: 700, letterSpacing: '0.1em', fontFamily: 'Inter, sans-serif' }}>{text}</span>
    </div>
  )
}

function DestructiveModal({ isOpen, title, message, onConfirm, onCancel, keyword }) {
  const [input, setInput] = useState('')
  if (!isOpen) return null
  const isMatch = !keyword || input === keyword
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9999, background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(8px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20
    }}>
      <div className="slide-up" style={{
        background: '#111113', borderRadius: 16, padding: 24, border: '1px solid rgba(185,28,28,0.5)', maxWidth: 400, width: '100%'
      }}>
        <h3 style={{ color: '#EF4444', marginTop: 0, fontFamily: 'Inter, sans-serif' }}>⚠️ {title}</h3>
        <p style={{ color: '#ccc', fontSize: 13, lineHeight: 1.5, fontFamily: 'Inter, sans-serif' }}>{message}</p>
        {keyword && (
          <div style={{ margin: '20px 0' }}>
            <label style={labelSt}>Escribe <strong>{keyword}</strong> para confirmar:</label>
            <input style={{...inputSt, border: '1px solid rgba(185,28,28,0.5)'}} value={input} onChange={e => setInput(e.target.value)} placeholder={keyword} />
          </div>
        )}
        <div style={{ display: 'flex', gap: 10, marginTop: 24 }}>
          <button onClick={onCancel} style={{
            flex: 1, padding: 12, borderRadius: 8, background: '#222', border: 'none', color: '#fff', cursor: 'pointer', fontFamily: 'Inter, sans-serif', fontWeight: 600
          }}>Cancelar</button>
          <button disabled={!isMatch} onClick={onConfirm} style={{
            flex: 1, padding: 12, borderRadius: 8, background: isMatch ? '#B91C1C' : '#552222', border: 'none', color: isMatch ? '#fff' : '#888', cursor: isMatch ? 'pointer' : 'not-allowed', fontFamily: 'Inter, sans-serif', fontWeight: 600, transition: 'all 0.2s'
          }}>Confirmar</button>
        </div>
      </div>
    </div>
  )
}

function MuestraForm({ muestra, index, onChange, onRemove, canRemove }) {
  const [expanded, setExpanded] = useState(index === 0)
  const [isRecording, setIsRecording] = useState(false)
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

  const set = (field, val) => onChange({ ...muestra, [field]: val })

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
          set('audioBlob', new Blob(chunks, { type: 'audio/webm' }))
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

  const summary = [muestra.cp, muestra.idSample, muestra.horizonte].filter(Boolean).join(' · ') || 'Sin datos'
  const fotosCount = muestra.fotos?.length || 0

  return (
    <div style={{
      borderRadius: 14, marginBottom: 10, overflow: 'hidden',
      border: `1px solid ${expanded ? 'rgba(212,175,55,0.35)' : 'rgba(255,255,255,0.07)'}`,
      background: expanded ? 'rgba(12,12,14,0.9)' : '#0F0F11', transition: 'border-color 0.2s',
    }}>
      <div onClick={() => setExpanded(e => !e)} style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 14px', cursor: 'pointer', userSelect: 'none',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{
            width: 24, height: 24, borderRadius: '50%', flexShrink: 0, background: 'rgba(212,175,55,0.12)', border: '1px solid rgba(212,175,55,0.4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 800, color: '#D4AF37', fontFamily: 'Inter, sans-serif',
          }}>{index + 1}</span>
          <span style={{ fontSize: 12, color: expanded ? '#ddd' : '#8E8E93', fontFamily: 'Inter, sans-serif' }}>
            {expanded ? 'MUESTRA' : summary}
          </span>
          {fotosCount > 0 && <span style={{ fontSize: 10, color: '#D4AF37' }}>📸 {fotosCount}</span>}
          {muestra.audioBlob && <span style={{ fontSize: 10, color: '#22C55E' }}>🎙️</span>}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {canRemove && (
            <button onClick={e => { e.stopPropagation(); onRemove() }} style={{
              background: 'none', border: 'none', color: '#7f1d1d', cursor: 'pointer', fontSize: 15, padding: '2px 4px', lineHeight: 1,
            }} title="Eliminar muestra">🗑️</button>
          )}
          <span style={{ color: '#555', fontSize: 12 }}>{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      {expanded && (
        <div style={{ padding: '0 14px 18px' }}>
          <SectionLabel icon="🏷️" text="IDENTIFICACIÓN" />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 10 }}>
            <div><label style={labelSt}>CP *</label><input style={inputSt} placeholder="ej: CP-01" value={muestra.cp} onChange={e => set('cp', e.target.value)} /></div>
            <div><label style={labelSt}>IDSAMPLE *</label><input style={inputSt} placeholder="ej: S-001" value={muestra.idSample} onChange={e => set('idSample', e.target.value)} /></div>
          </div>

          <SectionLabel icon="📐" text="POSICIÓN & PROFUNDIDAD" />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginBottom: 8 }}>
            <div><label style={labelSt}>ELEV (m)</label><input style={inputSt} type="number" placeholder="msnm" value={muestra.elevation} onChange={e => set('elevation', e.target.value)} /></div>
            <div><label style={labelSt}>Xm (E)</label><input style={inputSt} type="number" placeholder="Este" value={muestra.xm} onChange={e => set('xm', e.target.value)} /></div>
            <div><label style={labelSt}>Ym (N)</label><input style={inputSt} type="number" placeholder="Norte" value={muestra.ym} onChange={e => set('ym', e.target.value)} /></div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 10 }}>
            <div><label style={labelSt}>FROM (m)</label><input style={inputSt} type="number" step="0.1" placeholder="desde" value={muestra.from} onChange={e => set('from', e.target.value)} /></div>
            <div><label style={labelSt}>TO (m)</label><input style={inputSt} type="number" step="0.1" placeholder="hasta" value={muestra.to} onChange={e => set('to', e.target.value)} /></div>
          </div>

          <SectionLabel icon="🪨" text="GEOLOGÍA" />
          <label style={labelSt}>HORIZONTE</label><ChipSelect options={HORIZONTES} value={muestra.horizonte} onChange={v => set('horizonte', v)} color="#F59E0B" />
          <label style={labelSt}>ROCA CAJA</label><ChipSelect options={ROCAS_CAJA} value={muestra.rocaCaja} onChange={v => set('rocaCaja', v)} color="#8B5CF6" />
          <label style={labelSt}>ESTRUCTURA</label><ChipSelect options={ESTRUCTURAS} value={muestra.estructura} onChange={v => set('estructura', v)} color="#3B82F6" />
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 10 }}>
            <div><label style={labelSt}>RUMBO °</label><input style={inputSt} type="number" placeholder="0–360" value={muestra.rumbo} onChange={e => set('rumbo', e.target.value)} /></div>
            <div><label style={labelSt}>MANTEO °</label><input style={inputSt} type="number" placeholder="0–90" value={muestra.manteo} onChange={e => set('manteo', e.target.value)} /></div>
          </div>

          <SectionLabel icon="💎" text="MINERALOGÍA" />
          <ChipSelect options={MINERALOGIA_OPTS} value={muestra.mineralogia} onChange={v => set('mineralogia', v)} multi color="#22C55E" />

          <SectionLabel icon="🧪" text="ALTERACION" />
          <AlteracionSelector value={muestra.alteracion} onChange={v => set('alteracion', v)} />

          <SectionLabel icon="📊" text="MINERALIZACIÓN" />
          <ChipSelect options={MINERALIZACION_OPTS} value={muestra.mineralizacion} onChange={v => set('mineralizacion', v)} color="#B91C1C" />

          <SectionLabel icon="📝" text="COMENTARIO" />
          <textarea value={muestra.comentario} onChange={e => set('comentario', e.target.value)}
            placeholder="Observaciones de campo..."
            style={{ ...inputSt, height: 72, resize: 'none', marginBottom: 10 }}
          />

          <SectionLabel icon="👤" text="RESPONSABLE" />
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 8, marginBottom: 10 }}>
            <div><label style={labelSt}>TAKEN BY</label><input style={inputSt} placeholder="Nombre" value={muestra.takenBy} onChange={e => set('takenBy', e.target.value)} /></div>
            <div><label style={labelSt}>SEMANA</label><input style={inputSt} type="number" placeholder="ej: 22" value={muestra.semana} onChange={e => set('semana', e.target.value)} /></div>
          </div>

          <SectionLabel icon="📸" text="FOTOGRAFÍAS" />
          <FotoGaleria fotos={muestra.fotos} onChange={v => set('fotos', v)} />

          <SectionLabel icon="🎙️" text="AUDIO DE CAMPO" />
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button onClick={toggleRecording} style={{
              width: 48, height: 48, borderRadius: '50%', flexShrink: 0,
              background: isRecording ? (blink ? '#B91C1C' : 'rgba(185,28,28,0.5)') : '#1A1A1C',
              border: `2px solid ${isRecording ? '#D4AF37' : 'rgba(255,255,255,0.15)'}`,
              color: '#fff', fontSize: 20, cursor: 'pointer', transition: 'all 0.3s',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              {isRecording ? '⏹️' : '🎙️'}
            </button>
            {muestra.audioBlob
              ? <>
                  <span style={{ color: '#22C55E', fontSize: 12 }}>✅ Audio grabado</span>
                  <button onClick={() => set('audioBlob', null)} style={{
                    background: 'none', border: 'none', color: '#B91C1C', cursor: 'pointer', fontSize: 12,
                  }}>Eliminar</button>
                </>
              : <span style={{ color: '#444', fontSize: 12 }}>Sin audio</span>
            }
          </div>
        </div>
      )}
    </div>
  )
}

function PuntoForm({ position, onSave, onClose, initialData }) {
  const [muestras, setMuestras] = useState(initialData ? initialData.muestras : [newMuestra()])
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [muestraToDelete, setMuestraToDelete] = useState(null)

  const update = (id, data) => setMuestras(prev => prev.map(m => m._id === id ? data : m))
  
  const requestRemove = (id) => {
    setMuestraToDelete(id)
    setDeleteModalOpen(true)
  }

  const confirmRemove = () => {
    setMuestras(prev => prev.filter(m => m._id !== muestraToDelete))
    setDeleteModalOpen(false)
    setMuestraToDelete(null)
  }

  const add = () => setMuestras(prev => [...prev, newMuestra()])

  const handleSave = () => {
    const invalid = muestras.find(m => !m.cp || !m.idSample)
    if (invalid) { alert('Cada muestra requiere CP e IDSAMPLE'); return }
    onSave({
      id: initialData ? initialData.id : generateId(),
      position: initialData ? initialData.position : position,
      muestras,
      createdAt: initialData ? initialData.createdAt : new Date().toISOString()
    })
  }

  return (
    <>
      <div className="slide-up" style={{
        position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 2000,
        background: 'rgba(10,10,11,0.97)', backdropFilter: 'blur(24px)',
        borderTop: '1.5px solid rgba(212,175,55,0.3)',
        borderRadius: '24px 24px 0 0',
        maxHeight: '92vh', display: 'flex', flexDirection: 'column',
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '16px 20px 12px', borderBottom: '1px solid rgba(255,255,255,0.06)',
          flexShrink: 0,
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 18 }}>⛏️</span>
              <span style={{ color: '#D4AF37', fontWeight: 700, fontSize: 14, letterSpacing: '0.08em' }}>PUNTO DE MUESTREO</span>
            </div>
            <div style={{ fontSize: 11, color: '#8E8E93', marginTop: 3 }}>
              📍 {position ? `${position.lat.toFixed(5)}, ${position.lng.toFixed(5)}` : '—'}
              &nbsp;·&nbsp;
              <span style={{ color: '#D4AF37' }}>{muestras.length}</span> muestra{muestras.length !== 1 ? 's' : ''}
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#8E8E93', fontSize: 22, cursor: 'pointer' }}>✕</button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '14px 16px 0' }}>
          {muestras.map((m, i) => (
            <MuestraForm key={m._id} muestra={m} index={i} onChange={data => update(m._id, data)} onRemove={() => requestRemove(m._id)} canRemove={muestras.length > 1} />
          ))}
          <button onClick={add} style={{
            width: '100%', padding: '12px', borderRadius: 12, marginBottom: 16,
            border: '1.5px dashed rgba(212,175,55,0.35)', background: 'rgba(212,175,55,0.03)', color: '#D4AF37',
            cursor: 'pointer', fontSize: 13, fontFamily: 'Inter, sans-serif', fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          }}>
            ＋ Agregar muestra en este punto
          </button>
        </div>

        <div style={{ padding: '12px 16px 28px', borderTop: '1px solid rgba(255,255,255,0.06)', flexShrink: 0 }}>
          <button onClick={handleSave} style={{
            width: '100%', padding: '14px', borderRadius: 14, background: 'linear-gradient(135deg, #B91C1C, #7f1d1d)', border: '1px solid rgba(212,175,55,0.3)',
            color: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer', fontFamily: 'Inter, sans-serif', letterSpacing: '0.06em',
          }}>
            💾 GUARDAR PUNTO — {muestras.length} muestra{muestras.length !== 1 ? 's' : ''}
          </button>
        </div>
      </div>

      <DestructiveModal 
        isOpen={deleteModalOpen}
        title="Eliminar Muestra"
        message="¿Estás seguro que deseas eliminar esta muestra? Los datos ingresados no se podrán recuperar."
        onCancel={() => setDeleteModalOpen(false)}
        onConfirm={confirmRemove}
      />
    </>
  )
}

function StationSidebar({ stations, onClose, onExport, isExporting, onDriveSync, isSyncing, onClearAll, driveToken, loginToDrive, onEditStation, externalLayers, onRemoveLayer }) {
  const [clearModalOpen, setClearModalOpen] = useState(false)
  const totalMuestras = stations.reduce((a, s) => a + s.muestras.length, 0)
  const totalFotos    = stations.reduce((a, s) => a + s.muestras.reduce((b, m) => b + (m.fotos?.length || 0), 0), 0)

  const isBusy = isExporting || isSyncing

  return (
    <>
      <div className="slide-in" style={{
        position: 'fixed', top: 0, left: 0, bottom: 0, width: 340, zIndex: 1500,
        background: 'rgba(10,10,11,0.97)', backdropFilter: 'blur(20px)',
        borderRight: '1px solid rgba(212,175,55,0.2)', display: 'flex', flexDirection: 'column',
      }}>
        <div style={{ padding: '20px 16px 12px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ color: '#D4AF37', fontWeight: 700, fontSize: 13, letterSpacing: '0.1em' }}>⛏️ CAMPAÑA</span>
            <button onClick={onClose} disabled={isBusy} style={{ background: 'none', border: 'none', color: '#8E8E93', cursor: 'pointer', fontSize: 18 }}>✕</button>
          </div>
          <div style={{ color: '#8E8E93', fontSize: 12 }}>
            {stations.length} punto{stations.length !== 1 ? 's' : ''}
            &nbsp;·&nbsp;{totalMuestras} muestras
            {totalFotos > 0 && <>&nbsp;·&nbsp;📸 {totalFotos}</>}
          </div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '8px 12px' }}>
          {externalLayers && externalLayers.length > 0 && (
            <div style={{ marginBottom: 16, padding: '0 4px' }}>
              <div style={{ color: '#D4AF37', fontWeight: 700, fontSize: 11, letterSpacing: '0.1em', marginBottom: 6 }}>🗺️ CAPAS EXTERNAS</div>
              {externalLayers.map(l => (
                <div key={l.id} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  background: 'rgba(255,255,255,0.03)', padding: '6px 10px', borderRadius: 6, marginBottom: 4,
                  border: '1px solid rgba(255,255,255,0.1)'
                }}>
                  <span style={{ fontSize: 11, color: '#ccc', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>{l.name}</span>
                  <button onClick={() => onRemoveLayer(l.id)} style={{ background: 'none', border: 'none', color: '#B91C1C', cursor: 'pointer', fontSize: 12 }}>✕</button>
                </div>
              ))}
            </div>
          )}

          {stations.length === 0 ? (
            <div style={{ textAlign: 'center', color: '#8E8E93', marginTop: 48, fontSize: 13 }}>
              <div style={{ fontSize: 36, marginBottom: 10 }}>🗺️</div>
              Sin puntos aún.<br />Toca el mapa para comenzar.
            </div>
          ) : stations.map((s, i) => {
            const fCnt = s.muestras.reduce((a, m) => a + (m.fotos?.length || 0), 0)
            const hasAudio = s.muestras.some(m => m.audioBlob)
            return (
              <div key={s.id || i} className="fade-in" style={{
                background: '#1A1A1C', borderRadius: 12, padding: '12px 14px',
                marginBottom: 8, border: '1px solid rgba(212,175,55,0.12)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', flex: 1 }}>
                    {s.muestras.slice(0, 2).map((m, j) => (
                      <span key={j} style={{
                        padding: '2px 8px', borderRadius: 6, fontSize: 11, background: 'rgba(212,175,55,0.1)', color: '#D4AF37',
                        border: '1px solid rgba(212,175,55,0.25)', fontFamily: 'Inter, sans-serif', fontWeight: 600,
                      }}>{m.cp} · {m.idSample}</span>
                    ))}
                    {s.muestras.length > 2 && (
                      <span style={{
                        padding: '2px 8px', borderRadius: 6, fontSize: 11, background: 'rgba(212,175,55,0.06)', color: '#8E8E93', border: '1px solid rgba(255,255,255,0.08)',
                      }}>+{s.muestras.length - 2}</span>
                    )}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                    <span style={{ color: '#555', fontSize: 10 }}>#{i + 1}</span>
                    <button onClick={() => onEditStation(s)} disabled={isBusy} style={{
                      background: 'rgba(212,175,55,0.1)', border: '1px solid rgba(212,175,55,0.3)',
                      color: '#D4AF37', borderRadius: 6, padding: '3px 8px', fontSize: 11,
                      cursor: 'pointer', fontFamily: 'Inter, sans-serif'
                    }}>✏️ Editar</button>
                  </div>
                </div>
                {s.muestras[0]?.horizonte && (
                  <div style={{ fontSize: 11, color: '#aaa', marginBottom: 3 }}>{s.muestras[0].horizonte}</div>
                )}
                <div style={{ fontSize: 10, color: '#555' }}>
                  {s.muestras.length} muestra{s.muestras.length !== 1 ? 's' : ''}
                  {fCnt > 0 && ` · 📸 ${fCnt}`}
                  {hasAudio && ' · 🎙️'}
                </div>
              </div>
            )
          })}
          
          {stations.length > 0 && (
            <div style={{ marginTop: 24, textAlign: 'center' }}>
              <button onClick={() => setClearModalOpen(true)} disabled={isBusy} style={{
                background: 'none', border: 'none', color: '#7f1d1d', textDecoration: 'underline',
                fontSize: 12, cursor: 'pointer', fontFamily: 'Inter, sans-serif'
              }}>Limpiar campaña (Eliminar todo)</button>
            </div>
          )}
        </div>

        {stations.length > 0 && (
          <div style={{ padding: '12px 16px 24px', borderTop: '1px solid rgba(255,255,255,0.08)', display: 'flex', flexDirection: 'column', gap: 10 }}>
            {!driveToken ? (
              <button onClick={loginToDrive} disabled={isBusy} style={{
                width: '100%', padding: '13px', borderRadius: 12,
                background: '#fff', color: '#000', fontSize: 13, fontWeight: 700,
                cursor: isBusy ? 'wait' : 'pointer', fontFamily: 'Inter, sans-serif',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                border: '1px solid #ccc'
              }}>
                <img src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg" width={16} alt="G" />
                Conectar Google Drive
              </button>
            ) : (
              <button onClick={onDriveSync} disabled={isBusy} style={{
                width: '100%', padding: '13px', borderRadius: 12,
                background: isBusy ? '#333' : 'linear-gradient(135deg, #10B981, #047857)',
                border: '1px solid rgba(16, 185, 129, 0.4)',
                color: isBusy ? '#888' : '#fff', fontSize: 13, fontWeight: 700,
                cursor: isBusy ? 'wait' : 'pointer', fontFamily: 'Inter, sans-serif',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                transition: 'all 0.3s'
              }}>
                {isSyncing ? '⏳ Subiendo a Drive...' : '☁️ Guardar en mi Drive'}
              </button>
            )}
            
            <button onClick={onExport} disabled={isBusy} style={{
              width: '100%', padding: '13px', borderRadius: 12,
              background: isBusy ? '#333' : 'transparent',
              border: '1px solid rgba(212,175,55,0.3)',
              color: isBusy ? '#888' : '#D4AF37', fontSize: 13, fontWeight: 600,
              cursor: isBusy ? 'wait' : 'pointer', fontFamily: 'Inter, sans-serif',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              transition: 'all 0.3s'
            }}>
              {isExporting ? '⏳ Generando ZIP...' : '📦 Guardar ZIP Localmente'}
            </button>
          </div>
        )}
      </div>

      <DestructiveModal 
        isOpen={clearModalOpen}
        title="Limpiar Campaña"
        message="ADVERTENCIA CRÍTICA: Estás a punto de borrar TODAS las muestras registradas. Esta acción no se puede deshacer y perderás el trabajo no exportado."
        onCancel={() => setClearModalOpen(false)}
        onConfirm={() => {
          onClearAll()
          setClearModalOpen(false)
        }}
        keyword="ELIMINAR"
      />
    </>
  )
}

// ─── MAIN APP ────────────────────────────────────────────────────────────────
export default function App() {
  const [stations, setStations] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [editingStation, setEditingStation] = useState(null)
  const [clickPosition, setClickPosition] = useState(null)
  const [gpsPosition, setGpsPosition] = useState(null)
  const [showSidebar, setShowSidebar] = useState(false)
  const [mapCenter] = useState([-33.45, -70.65])
  const [activeLayer, setActiveLayer] = useState('osm')
  
  const [isExporting, setIsExporting] = useState(false)
  const [isSyncing, setIsSyncing] = useState(false)
  const [isLoaded, setIsLoaded] = useState(false)
  const [driveToken, setDriveToken] = useState(null)
  
  const [externalLayers, setExternalLayers] = useState([])
  const fileInputRef = useRef(null)

  // ─── GOOGLE LOGIN ───
  const loginToDrive = useGoogleLogin({
    onSuccess: (tokenResponse) => {
      setDriveToken(tokenResponse.access_token)
    },
    onError: () => alert('Error al iniciar sesión con Google'),
    scope: 'https://www.googleapis.com/auth/drive.file'
  })

  useEffect(() => {
    async function loadData() {
      try {
        const stored = await localforage.getItem('geoinducta_stations')
        if (stored && Array.isArray(stored)) {
          const restored = stored.map(s => ({
            ...s,
            muestras: s.muestras.map(m => ({
              ...m,
              fotos: (m.fotos || []).map(f => ({
                ...f,
                url: f.file ? URL.createObjectURL(f.file) : null
              }))
            }))
          }))
          setStations(restored)
        }
      } catch (err) {
        console.error("Error loading data from localforage:", err)
      } finally {
        setIsLoaded(true)
      }
    }
    loadData()
  }, [])

  const saveStations = async (newStationsOrFn) => {
    setStations(prev => {
      const nextStations = typeof newStationsOrFn === 'function' ? newStationsOrFn(prev) : newStationsOrFn
      localforage.setItem('geoinducta_stations', nextStations).catch(e => console.error('Save error', e))
      return nextStations
    })
  }

  function MapClickHandler() {
    useMapEvents({
      click(e) {
        setClickPosition(e.latlng)
        setEditingStation(null)
        setShowForm(true)
        setShowSidebar(false)
      }
    })
    return null
  }

  const handleSavePunto = useCallback((punto) => {
    saveStations(prev => {
      const idx = prev.findIndex(p => p.id === punto.id)
      if (idx >= 0) {
        const next = [...prev]
        next[idx] = punto
        return next
      }
      return [...prev, punto]
    })
    setShowForm(false)
    setEditingStation(null)
    setClickPosition(null)
  }, [])

  const handleClearAll = useCallback(() => {
    saveStations([])
  }, [])

  const handleLayerUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const name = file.name
    const ext = name.split('.').pop().toLowerCase()
    
    try {
      if (ext === 'kmz') {
        const { default: JSZip } = await import('jszip')
        const arrayBuffer = await file.arrayBuffer()
        const zip = await JSZip.loadAsync(arrayBuffer)
        const kmlFile = Object.values(zip.files).find(f => f.name.endsWith('.kml'))
        if (kmlFile) {
          const text = await kmlFile.async('text')
          const dom = new DOMParser().parseFromString(text, 'text/xml')
          const geojson = kml(dom)
          setExternalLayers(prev => [...prev, { id: generateId(), type: 'geojson', data: geojson, name }])
        } else {
          alert('No se encontró archivo .kml dentro del KMZ')
        }
      } else if (ext === 'kml') {
        const text = await file.text()
        const dom = new DOMParser().parseFromString(text, 'text/xml')
        const geojson = kml(dom)
        setExternalLayers(prev => [...prev, { id: generateId(), type: 'geojson', data: geojson, name }])
      } else if (ext === 'geojson' || ext === 'json') {
        const text = await file.text()
        const geojson = JSON.parse(text)
        setExternalLayers(prev => [...prev, { id: generateId(), type: 'geojson', data: geojson, name }])
      } else if (ext === 'tif' || ext === 'tiff') {
        const arrayBuffer = await file.arrayBuffer()
        const raster = await parseGeoraster(arrayBuffer)
        setExternalLayers(prev => [...prev, { id: generateId(), type: 'geotiff', georaster: raster, name }])
      } else {
        alert('Formato no soportado. Usa KML, KMZ, GeoJSON o TIF.')
      }
    } catch (err) {
      console.error(err)
      alert('Error procesando el archivo.')
    }
    e.target.value = ''
  }

  // ─── CORE ZIP GENERATOR ───
  const generateZipBlob = async () => {
    const { default: JSZip } = await import('jszip')
    const zip = new JSZip()
    const fotosDir  = zip.folder('fotos')
    const audiosDir = zip.folder('audios')

    const features = stations.flatMap(s =>
      s.muestras.map(m => {
        const altStr = Object.entries(m.alteracion)
          .filter(([, v]) => v).map(([k, v]) => `${k}:${v}`).join('; ')
        return {
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [s.position.lng, s.position.lat] },
          properties: {
            CP: m.cp, IDSAMPLE: m.idSample,
            Elevation: m.elevation, Xm: m.xm, Ym: m.ym,
            From: m.from, To: m.to,
            HORIZONTE: m.horizonte, 'ROCA CAJA': m.rocaCaja,
            ESTRUCTURA: m.estructura, RUMBO: m.rumbo, MANTEO: m.manteo,
            MINERALOGÍA: (m.mineralogia || []).join('; '),
            ALTERACION: altStr,
            MINERALIZACION: m.mineralizacion,
            COMENTARIO: m.comentario,
            'TAKEN BY': m.takenBy, SEMANA: m.semana,
            Lat: s.position.lat, Lng: s.position.lng, Fecha: s.createdAt,
          }
        }
      })
    )
    zip.file('muestras.geojson', JSON.stringify({ type: 'FeatureCollection', features }, null, 2))

    const COLS = [
      'CP', 'IDSAMPLE', 'Elevation', 'Xm', 'Ym', 'From', 'To',
      'HORIZONTE', 'ROCA CAJA', 'ESTRUCTURA', 'RUMBO', 'MANTEO',
      'MINERALOGÍA', 'ALTERACION', 'MINERALIZACION', 'COMENTARIO',
      'TAKEN BY', 'SEMANA', 'Lat', 'Lng', 'Fecha',
    ]
    const rows = [COLS.join('\t')]
    stations.forEach(s => s.muestras.forEach(m => {
      const altStr = Object.entries(m.alteracion)
        .filter(([, v]) => v).map(([k, v]) => `${k}:${v}`).join('; ')
      rows.push([
        m.cp, m.idSample, m.elevation, m.xm, m.ym, m.from, m.to,
        m.horizonte, m.rocaCaja, m.estructura, m.rumbo, m.manteo,
        (m.mineralogia || []).join('; '), altStr, m.mineralizacion,
        `"${(m.comentario || '').replace(/"/g, '""')}"`,
        m.takenBy, m.semana,
        s.position.lat, s.position.lng, s.createdAt,
      ].join('\t'))
    }))
    zip.file('muestras.tsv', rows.join('\n'))

    for (const s of stations) {
      for (const m of s.muestras) {
        const prefix = `${m.cp || 'CP'}_${m.idSample || 'S'}`
        if (m.fotos?.length) {
          m.fotos.forEach((f, i) => {
            if (f.file) fotosDir.file(`${prefix}_foto_${i + 1}.jpg`, f.file)
          })
        }
        if (m.audioBlob) {
          audiosDir.file(`${prefix}_audio.webm`, m.audioBlob)
        }
      }
    }

    return await zip.generateAsync({ type: 'blob' })
  }

  // ─── LOCAL EXPORT ───
  const handleExport = useCallback(async () => {
    setIsExporting(true)
    try {
      const blob = await generateZipBlob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `campana_GeoINducta_${new Date().toISOString().slice(0, 10)}.zip`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error("Export error", err)
      alert("Error al generar el ZIP local.")
    } finally {
      setIsExporting(false)
    }
  }, [stations])

  // ─── CLOUD SYNC (Direct to Google Drive) ───
  const handleDriveSync = useCallback(async () => {
    if (!driveToken) return
    setIsSyncing(true)
    try {
      const blob = await generateZipBlob()
      
      const boundary = 'geoinducta_boundary_' + Date.now()
      const delimiter = "\r\n--" + boundary + "\r\n"
      const close_delim = "\r\n--" + boundary + "--"

      const metadata = {
        name: `GeoINducta_${new Date().toISOString().slice(0, 10)}.zip`,
        mimeType: 'application/zip'
      }

      // 1. Search if file already exists for today
      const query = encodeURIComponent(`name='${metadata.name}' and trashed=false`)
      const searchRes = await fetch(`https://www.googleapis.com/drive/v3/files?q=${query}&spaces=drive`, {
        headers: { 'Authorization': `Bearer ${driveToken}` }
      })
      const searchData = await searchRes.json()
      
      if (searchData.error) throw new Error(searchData.error.message)

      const existingFileId = searchData.files && searchData.files.length > 0 ? searchData.files[0].id : null

      // We construct the multipart/related body manually
      const multipartRequestBody = new Blob([
        delimiter,
        'Content-Type: application/json; charset=UTF-8\r\n\r\n',
        JSON.stringify(metadata),
        delimiter,
        'Content-Type: application/zip\r\n\r\n',
        blob,
        close_delim
      ])

      let uploadUrl = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart'
      let uploadMethod = 'POST'

      if (existingFileId) {
        uploadUrl = `https://www.googleapis.com/upload/drive/v3/files/${existingFileId}?uploadType=multipart`
        uploadMethod = 'PATCH'
      }

      const response = await fetch(uploadUrl, {
        method: uploadMethod,
        headers: {
          'Authorization': `Bearer ${driveToken}`,
          'Content-Type': `multipart/related; boundary=${boundary}`
        },
        body: multipartRequestBody
      })
      
      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.error?.message || 'Error en subida')
      }
      
      alert("✅ ¡Sincronización Exitosa!\n\nEl archivo ZIP ha sido guardado directamente en tu Google Drive.")
    } catch (err) {
      console.error("Drive sync error", err)
      alert(`❌ Error al subir a Drive.\n${err.message}`)
      if (err.message.includes('Invalid Credentials') || err.message.includes('Auth')) {
        setDriveToken(null) // Reset token if expired
      }
    } finally {
      setIsSyncing(false)
    }
  }, [stations, driveToken])


  const totalMuestras = stations.reduce((a, s) => a + s.muestras.length, 0)

  if (!isLoaded) return <div style={{ background: '#0a0a0b', height: '100vh' }}></div>

  return (
    <div style={{ height: '100vh', width: '100vw', position: 'relative' }}>
      <div style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 1000,
        background: 'rgba(10,10,11,0.92)', backdropFilter: 'blur(16px)',
        borderBottom: '1px solid rgba(212,175,55,0.2)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '10px 16px', height: 56,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button onClick={() => { setShowSidebar(s => !s); setShowForm(false) }}
            style={{ background: 'none', border: 'none', color: showSidebar ? '#D4AF37' : '#8E8E93', fontSize: 20, cursor: 'pointer' }}>
            ☰
          </button>
          <span style={{ fontWeight: 700, fontSize: 16, letterSpacing: '0.05em', fontFamily: 'Inter, sans-serif' }}>
            Geo<span style={{ color: '#B91C1C' }}>IN</span>ducta
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button onClick={() => fileInputRef.current?.click()} style={{
            background: 'rgba(59,130,246,0.15)', border: '1px solid rgba(59,130,246,0.4)',
            color: '#60A5FA', borderRadius: 8, padding: '4px 8px', fontSize: 11, cursor: 'pointer',
            fontFamily: 'Inter, sans-serif'
          }}>+ 🗺️ Capa</button>
          <input type="file" ref={fileInputRef} onChange={handleLayerUpload} accept=".kml,.kmz,.geojson,.json,.tif,.tiff" style={{ display: 'none' }} />
          
          {gpsPosition && (
            <span style={{ padding: '3px 8px', borderRadius: 8, fontSize: 11, background: 'rgba(34,197,94,0.12)', color: '#22C55E', border: '1px solid rgba(34,197,94,0.3)' }}>
              📍 GPS
            </span>
          )}
          {totalMuestras > 0 && (
            <span style={{ padding: '3px 8px', borderRadius: 8, fontSize: 11, background: 'rgba(212,175,55,0.1)', color: '#D4AF37', border: '1px solid rgba(212,175,55,0.3)' }}>
              {totalMuestras} muestras
            </span>
          )}
        </div>
      </div>

      <MapContainer center={mapCenter} zoom={13} style={{ height: '100%', width: '100%' }} zoomControl={false}>
        <TileLayer
          key={activeLayer}
          url={TILE_LAYERS[activeLayer].url}
          attribution={TILE_LAYERS[activeLayer].attribution}
          maxZoom={TILE_LAYERS[activeLayer].maxZoom}
        />
        <MapClickHandler />
        <GPSTracker onPosition={setGpsPosition} />

        {gpsPosition && <Marker position={gpsPosition} icon={gpsIcon}><Popup>Tu posición actual</Popup></Marker>}

        {externalLayers.map(layer => {
          if (layer.type === 'geojson') {
            return <GeoJSON key={layer.id} data={layer.data} style={{ color: '#3B82F6', weight: 2, opacity: 0.8 }} />
          } else if (layer.type === 'geotiff') {
            return <GeoTiffLayer key={layer.id} georaster={layer.georaster} />
          }
          return null
        })}

        {stations.map((s, i) => (
          <Marker key={s.id || i} position={s.position} icon={createStationIcon(s.muestras)}>
            <Popup>
              <div style={{ minWidth: 200, fontFamily: 'Inter, sans-serif', fontSize: 12 }}>
                <strong style={{ color: '#B91C1C', display: 'block', marginBottom: 6 }}>
                  Punto #{i + 1} — {s.muestras.length} muestra{s.muestras.length !== 1 ? 's' : ''}
                </strong>
                {s.muestras.map((m, j) => (
                  <div key={m._id || j} style={{
                    marginBottom: 6, paddingBottom: 6, borderBottom: j < s.muestras.length - 1 ? '1px solid #eee' : 'none',
                  }}>
                    <div><b>{m.cp}</b> — {m.idSample}</div>
                    {m.horizonte && <div>Horizonte: {m.horizonte}</div>}
                    {m.rocaCaja && <div>Roca: {m.rocaCaja}</div>}
                    {m.mineralizacion && <div>Mineralización: {m.mineralizacion}</div>}
                    {m.fotos?.length > 0 && <div>📸 {m.fotos.length} foto{m.fotos.length !== 1 ? 's' : ''}</div>}
                  </div>
                ))}
              </div>
            </Popup>
          </Marker>
        ))}

        <RecenterButton position={gpsPosition} />
      </MapContainer>

      <div style={{ position: 'fixed', bottom: 96, left: 12, zIndex: 999 }}>
        <select value={activeLayer} onChange={e => setActiveLayer(e.target.value)} style={{
          background: 'rgba(10,10,11,0.9)', color: '#fff', border: '1px solid rgba(212,175,55,0.3)',
          borderRadius: 8, padding: '8px 12px', outline: 'none', cursor: 'pointer', fontFamily: 'Inter, sans-serif'
        }}>
          {Object.entries(TILE_LAYERS).map(([k, v]) => (
            <option key={k} value={k}>{v.icon} {v.name}</option>
          ))}
        </select>
      </div>

      {showSidebar && (
        <StationSidebar
          stations={stations}
          onClose={() => setShowSidebar(false)}
          onExport={handleExport}
          isExporting={isExporting}
          onDriveSync={handleDriveSync}
          isSyncing={isSyncing}
          onClearAll={handleClearAll}
          driveToken={driveToken}
          loginToDrive={loginToDrive}
          externalLayers={externalLayers}
          onRemoveLayer={(id) => setExternalLayers(prev => prev.filter(l => l.id !== id))}
          onEditStation={(s) => {
            setEditingStation(s)
            setShowForm(true)
            setShowSidebar(false)
          }}
        />
      )}

      {showForm && (
        <PuntoForm
          position={clickPosition}
          initialData={editingStation}
          onSave={handleSavePunto}
          onClose={() => { setShowForm(false); setEditingStation(null); setClickPosition(null) }}
        />
      )}

      {!showForm && !showSidebar && stations.length === 0 && (
        <div className="fade-in" style={{
          position: 'fixed', bottom: 80, left: '50%', transform: 'translateX(-50%)',
          background: 'rgba(10,10,11,0.88)', backdropFilter: 'blur(12px)',
          border: '1px solid rgba(212,175,55,0.3)', borderRadius: 99,
          padding: '10px 20px', fontSize: 13, color: '#D4AF37', zIndex: 999, whiteSpace: 'nowrap',
          fontFamily: 'Inter, sans-serif',
        }}>
          👆 Toca el mapa para registrar un punto de muestreo
        </div>
      )}

      <button onClick={() => {
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            pos => setGpsPosition({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
            () => alert('GPS no disponible')
          )
        }
      }} style={{
        position: 'fixed', bottom: 40, right: 12, zIndex: 999,
        background: 'rgba(10,10,11,0.9)', border: '1px solid rgba(212,175,55,0.3)',
        color: '#fff', borderRadius: '50%', width: 44, height: 44,
        cursor: 'pointer', fontSize: 20, backdropFilter: 'blur(8px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }} title="Activar GPS">🛰️</button>
    </div>
  )
}
