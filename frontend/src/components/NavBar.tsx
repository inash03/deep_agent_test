import { NavLink } from 'react-router-dom'
import { refreshData } from '../api/admin'
import { useState } from 'react'

const LINKS = [
  { to: '/', label: 'Triage', end: true },
  { to: '/history', label: 'History', end: false },
  { to: '/trades', label: 'Trades', end: false },
  { to: '/stp-exceptions', label: 'STP Exceptions', end: false },
  { to: '/counterparties', label: 'Counterparties', end: false },
  { to: '/ssis', label: 'SSIs', end: false },
  { to: '/reference-data', label: 'Ref Data', end: false },
]

export function NavBar() {
  const [refreshing, setRefreshing] = useState(false)

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
    <nav style={{
      backgroundColor: '#1e293b',
      display: 'flex',
      alignItems: 'center',
      height: 52,
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      zIndex: 100,
    }}>
      <span style={{ color: '#fff', fontWeight: 700, fontSize: '0.95rem', whiteSpace: 'nowrap', padding: '0 1rem 0 1.5rem', flexShrink: 0 }}>
        STP Triage
      </span>
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '1.5rem', overflowX: 'auto', padding: '0 0.5rem' }}>
        {LINKS.map(({ to, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            style={({ isActive }) => ({
              color: isActive ? '#60a5fa' : '#94a3b8',
              textDecoration: 'none',
              fontWeight: isActive ? 600 : 400,
              fontSize: '0.875rem',
              whiteSpace: 'nowrap',
            })}
          >
            {label}
          </NavLink>
        ))}
      </div>
      <div style={{ flexShrink: 0, padding: '0 1.5rem 0 0.5rem' }}>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          style={{
            backgroundColor: 'transparent',
            border: '1px solid #475569',
            color: '#94a3b8',
            borderRadius: 6,
            padding: '0.3rem 0.75rem',
            fontSize: '0.8rem',
            cursor: refreshing ? 'not-allowed' : 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          {refreshing ? 'Resetting…' : '↺ Reset Data'}
        </button>
      </div>
    </nav>
  )
}
