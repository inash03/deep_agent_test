import { useEffect, useState } from 'react'
import { getTriageHistory } from '../api/triage'
import { PageLayout } from '../components/PageLayout'
import { StatusBadge } from '../components/StatusBadge'
import { CARD, COLOR, TABLE, TD, TH } from '../styles/theme'
import type { TriageResponse } from '../types/triage'

export function TriageHistoryPage() {
  const [items, setItems] = useState<TriageResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    getTriageHistory(50).then(r => setItems(r.items)).finally(() => setLoading(false))
  }, [])

  return (
    <PageLayout title="Triage History">
      <div style={CARD}>
        {loading ? (
          <p style={{ color: COLOR.textMuted }}>Loading…</p>
        ) : (
          <table style={TABLE}>
            <thead>
              <tr>
                <th style={TH}>Trade ID</th>
                <th style={TH}>Status</th>
                <th style={TH}>Root Cause</th>
                <th style={TH}>Action Taken</th>
                <th style={TH}>Diagnosis</th>
              </tr>
            </thead>
            <tbody>
              {items.map(row => (
                <>
                  <tr
                    key={row.run_id}
                    style={{ borderBottom: '1px solid #f3f4f6', cursor: 'pointer' }}
                    onClick={() => setExpanded(expanded === row.run_id ? null : (row.run_id ?? null))}
                  >
                    <td style={{ ...TD, fontWeight: 600 }}>{row.trade_id}</td>
                    <td style={TD}><StatusBadge status={row.status} /></td>
                    <td style={{ ...TD, fontFamily: 'monospace', fontSize: '0.8rem', color: '#b45309' }}>
                      {row.root_cause ?? '—'}
                    </td>
                    <td style={TD}>
                      <span style={{ color: row.action_taken ? '#065f46' : COLOR.textMuted }}>
                        {row.action_taken ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td style={{ ...TD, fontSize: '0.85rem', color: COLOR.textMuted, maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {row.diagnosis ?? '—'}
                    </td>
                  </tr>
                  {expanded === row.run_id && (
                    <tr key={`${row.run_id}-detail`} style={{ backgroundColor: '#f9fafb' }}>
                      <td colSpan={5} style={{ padding: '1rem 1.5rem' }}>
                        <p style={{ fontWeight: 600, marginBottom: '0.25rem', fontSize: '0.875rem' }}>Diagnosis</p>
                        <p style={{ fontSize: '0.875rem', marginBottom: '0.75rem', color: '#374151' }}>{row.diagnosis ?? '—'}</p>
                        <p style={{ fontWeight: 600, marginBottom: '0.25rem', fontSize: '0.875rem' }}>Recommended Action</p>
                        <p style={{ fontSize: '0.875rem', color: '#374151' }}>{row.recommended_action ?? '—'}</p>
                        {row.run_id && (
                          <p style={{ fontSize: '0.75rem', color: COLOR.textMuted, marginTop: '0.5rem' }}>Run ID: {row.run_id}</p>
                        )}
                      </td>
                    </tr>
                  )}
                </>
              ))}
              {items.length === 0 && (
                <tr><td colSpan={5} style={{ padding: '1rem', textAlign: 'center', color: COLOR.textMuted }}>No triage history yet</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </PageLayout>
  )
}
