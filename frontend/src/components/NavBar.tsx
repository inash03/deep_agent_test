import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { refreshData } from '../api/admin'
import { VERSION } from '../version'

const LINKS = [
  { to: '/trades', label: 'Trades', end: true },
  { to: '/stp-exceptions', label: 'STP Exceptions', end: false },
  { to: '/counterparties', label: 'Counterparties', end: false },
  { to: '/ssis', label: 'SSIs', end: false },
  { to: '/reference-data', label: 'Ref Data', end: false },
  { to: '/settings', label: 'Settings', end: false },
]

export function NavBar() {
  const [open, setOpen] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  const close = () => setOpen(false)

  const handleRefresh = async () => {
    if (!window.confirm('Reset all data to initial state? (Triage history is preserved)')) return
    setRefreshing(true)
    try {
      await refreshData()
      window.location.reload()
    } catch {
      alert('Data refresh failed.')
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <>
      {/* ── Top bar ── */}
      <nav style={{
        backgroundColor: '#1e293b',
        display: 'flex',
        alignItems: 'center',
        height: 52,
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 200,
        padding: '0 1.25rem',
        gap: '0.75rem',
      }}>
        {/* Hamburger */}
        <button
          onClick={() => setOpen(v => !v)}
          aria-label="Open menu"
          style={{
            background: 'none',
            border: 'none',
            color: '#94a3b8',
            fontSize: '1.35rem',
            cursor: 'pointer',
            padding: '0.25rem 0.4rem',
            borderRadius: 6,
            lineHeight: 1,
            flexShrink: 0,
          }}
        >
          ☰
        </button>

        {/* Logo + version */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
          <span style={{ color: '#fff', fontWeight: 700, fontSize: '1rem', letterSpacing: '-0.01em' }}>
            STP Triage
          </span>
          <span style={{ color: '#475569', fontSize: '0.72rem', fontFamily: 'monospace' }}>
            v{VERSION}
          </span>
        </div>
      </nav>

      {/* ── Backdrop ── */}
      {open && (
        <div
          onClick={close}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.45)',
            zIndex: 300,
          }}
        />
      )}

      {/* ── Side panel ── */}
      <aside style={{
        position: 'fixed',
        top: 0,
        left: 0,
        bottom: 0,
        width: 240,
        backgroundColor: '#1e293b',
        zIndex: 400,
        display: 'flex',
        flexDirection: 'column',
        transform: open ? 'translateX(0)' : 'translateX(-100%)',
        transition: 'transform 0.22s ease',
        boxShadow: open ? '4px 0 24px rgba(0,0,0,0.3)' : 'none',
      }}>
        {/* Panel header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: 52,
          padding: '0 1rem',
          borderBottom: '1px solid #334155',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
            <span style={{ color: '#fff', fontWeight: 700, fontSize: '1rem' }}>STP Triage</span>
            <span style={{ color: '#475569', fontSize: '0.72rem', fontFamily: 'monospace' }}>v{VERSION}</span>
          </div>
          <button
            onClick={close}
            aria-label="Close menu"
            style={{ background: 'none', border: 'none', color: '#64748b', fontSize: '1.2rem', cursor: 'pointer', padding: '0.2rem' }}
          >
            ✕
          </button>
        </div>

        {/* Nav links */}
        <nav style={{ flex: 1, overflowY: 'auto', padding: '0.5rem 0' }}>
          {LINKS.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={close}
              style={({ isActive }) => ({
                display: 'block',
                padding: '0.65rem 1.25rem',
                color: isActive ? '#fff' : '#94a3b8',
                backgroundColor: isActive ? '#2563eb' : 'transparent',
                textDecoration: 'none',
                fontWeight: isActive ? 600 : 400,
                fontSize: '0.9rem',
                borderRadius: '0 6px 6px 0',
                marginRight: '0.75rem',
                transition: 'background-color 0.12s, color 0.12s',
              })}
            >
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Reset data button */}
        <div style={{ padding: '1rem', borderTop: '1px solid #334155', flexShrink: 0 }}>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            style={{
              width: '100%',
              backgroundColor: 'transparent',
              border: '1px solid #475569',
              color: '#94a3b8',
              borderRadius: 6,
              padding: '0.45rem',
              fontSize: '0.82rem',
              cursor: refreshing ? 'not-allowed' : 'pointer',
            }}
          >
            {refreshing ? 'Resetting…' : '↺ Reset Data'}
          </button>
        </div>
      </aside>
    </>
  )
}
