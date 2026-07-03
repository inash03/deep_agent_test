'use client'

import { useEffect, useState } from 'react'
import { listCounterparties } from '../api/counterparties'
import { BTN_PRIMARY, BTN_SECONDARY, COLOR, INPUT, TABLE, TD, TH } from '../styles/theme'
import type { Counterparty } from '../types/counterparty'

const LIMIT = 20

interface Props {
  open: boolean
  onSelect: (counterparty: Counterparty) => void
  onClose: () => void
}

/**
 * Search modal backing the trade-creation Counterparty field (Issue #61).
 *
 * Reuses GET /api/v1/counterparties: name and LEI are substring,
 * case-insensitive filters (combined with AND server-side). Only active
 * counterparties are selectable, matching the previous dropdown behavior.
 * Selecting a row hands the counterparty back to the caller and closes.
 */
export function CounterpartySearchModal({ open, onSelect, onClose }: Props) {
  const [name, setName] = useState('')
  const [lei, setLei] = useState('')
  const [items, setItems] = useState<Counterparty[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const search = async () => {
    setLoading(true)
    try {
      const res = await listCounterparties({
        name: name.trim() || undefined,
        lei: lei.trim() || undefined,
        limit: LIMIT,
      })
      setItems(res.items.filter(c => c.is_active))
      setTotal(res.total)
      setSearched(true)
    } catch {
      setItems([])
      setTotal(0)
      setSearched(true)
    } finally {
      setLoading(false)
    }
  }

  // Load the first page whenever the modal is opened; reset on close.
  useEffect(() => {
    if (open) {
      setName('')
      setLei('')
      setSearched(false)
      void search()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  // Close on Escape for keyboard users.
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.4)',
        display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
        padding: '4rem 1rem', zIndex: 50,
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Search counterparty"
        onClick={e => e.stopPropagation()}
        style={{
          backgroundColor: COLOR.bgWhite, borderRadius: 8, width: '100%', maxWidth: 640,
          boxShadow: '0 10px 25px rgba(0,0,0,0.2)', display: 'flex', flexDirection: 'column',
          maxHeight: '80vh', overflow: 'hidden',
        }}
      >
        <div style={{ padding: '1rem 1.25rem', borderBottom: `1px solid ${COLOR.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ margin: 0, fontSize: '1rem', color: COLOR.text }}>Search Counterparty</h2>
          <button aria-label="Close" onClick={onClose} style={{ ...BTN_SECONDARY, padding: '0.25rem 0.6rem' }}>✕</button>
        </div>

        <div style={{ padding: '1rem 1.25rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'flex-end', borderBottom: `1px solid ${COLOR.border}` }}>
          <div style={{ flex: '1 1 200px' }}>
            <label htmlFor="cp-search-name" style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: COLOR.textMuted, marginBottom: 4 }}>Name</label>
            <input id="cp-search-name" style={INPUT} placeholder="Acme..." value={name}
              onChange={e => setName(e.target.value)} onKeyDown={e => e.key === 'Enter' && search()} />
          </div>
          <div style={{ flex: '1 1 200px' }}>
            <label htmlFor="cp-search-lei" style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: COLOR.textMuted, marginBottom: 4 }}>LEI</label>
            <input id="cp-search-lei" style={INPUT} placeholder="213800..." value={lei}
              onChange={e => setLei(e.target.value)} onKeyDown={e => e.key === 'Enter' && search()} />
          </div>
          <button onClick={search} style={BTN_PRIMARY}>Search</button>
        </div>

        <div style={{ overflowY: 'auto', padding: '0 1.25rem 1rem' }}>
          {loading ? (
            <p style={{ color: COLOR.textMuted, textAlign: 'center', padding: '2rem' }}>Loading...</p>
          ) : (
            <table style={TABLE}>
              <thead>
                <tr>{['LEI', 'Name', 'BIC'].map(h => <th key={h} style={TH}>{h}</th>)}</tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr><td colSpan={3} style={{ ...TD, textAlign: 'center', color: COLOR.textMuted, padding: '2rem' }}>
                    {searched ? 'No counterparties found.' : ''}
                  </td></tr>
                ) : items.map(cp => (
                  <tr
                    key={cp.lei}
                    onClick={() => onSelect(cp)}
                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(cp) } }}
                    tabIndex={0}
                    style={{ cursor: 'pointer' }}
                  >
                    <td style={{ ...TD, fontFamily: 'monospace', fontSize: '0.8rem' }}>{cp.lei}</td>
                    <td style={{ ...TD, fontWeight: 500 }}>{cp.name}</td>
                    <td style={{ ...TD, fontFamily: 'monospace' }}>{cp.bic}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {!loading && total > items.length && (
            <p style={{ color: COLOR.textLight, fontSize: '0.78rem', textAlign: 'center', marginTop: '0.75rem' }}>
              Showing {items.length} of {total} matches — refine your search to narrow results.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
