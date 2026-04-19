import { useEffect, useState } from 'react'
import { listReferenceData } from '../api/referenceData'
import { PageLayout } from '../components/PageLayout'
import { CARD, COLOR, TABLE, TD, TH } from '../styles/theme'
import type { ReferenceData } from '../types/referenceData'

export function ReferenceDataListPage() {
  const [items, setItems] = useState<ReferenceData[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    listReferenceData()
      .then(r => setItems(r.items))
      .finally(() => setLoading(false))
  }, [])

  return (
    <PageLayout title="Reference Data (Instruments)">
      <div style={CARD}>
        {loading ? (
          <p style={{ color: COLOR.textMuted }}>Loading…</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
          <table style={TABLE}>
            <thead>
              <tr>
                <th style={TH}>Instrument ID</th>
                <th style={TH}>Description</th>
                <th style={TH}>Asset Class</th>
                <th style={TH}>Status</th>
              </tr>
            </thead>
            <tbody>
              {items.map(row => (
                <tr key={row.instrument_id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ ...TD, fontFamily: 'monospace', fontWeight: 600 }}>{row.instrument_id}</td>
                  <td style={TD}>{row.description}</td>
                  <td style={TD}>{row.asset_class}</td>
                  <td style={TD}>
                    <span style={{ padding: '2px 8px', borderRadius: 9999, fontSize: '0.75rem', background: row.is_active ? '#d1fae5' : '#fee2e2', color: row.is_active ? '#065f46' : '#991b1b' }}>
                      {row.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr><td colSpan={4} style={{ padding: '1rem', textAlign: 'center', color: COLOR.textMuted }}>No data</td></tr>
              )}
            </tbody>
          </table>
          </div>
        )}
      </div>
    </PageLayout>
  )
}
