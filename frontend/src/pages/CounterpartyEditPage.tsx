import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getCounterparty, updateCounterparty } from '../api/counterparties'
import { listSsis } from '../api/ssis'
import { PageLayout } from '../components/PageLayout'
import { BTN_PRIMARY, BTN_SECONDARY, CARD, COLOR, INPUT, LABEL, TABLE, TD, TH } from '../styles/theme'
import type { Counterparty } from '../types/counterparty'
import type { Ssi } from '../types/ssi'

export function CounterpartyEditPage() {
  const { lei } = useParams<{ lei: string }>()
  const navigate = useNavigate()
  const [cp, setCp] = useState<Counterparty | null>(null)
  const [name, setName] = useState('')
  const [bic, setBic] = useState('')
  const [isActive, setIsActive] = useState(true)
  const [ssis, setSsis] = useState<Ssi[]>([])
  const [ssiLoading, setSsiLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    if (!lei) return
    setError('')
    getCounterparty(lei).then(data => {
      setCp(data)
      setName(data.name)
      setBic(data.bic)
      setIsActive(data.is_active)
    }).catch(() => setError('Counterparty not found.'))
  }, [lei])

  useEffect(() => {
    if (!lei) return
    setSsiLoading(true)
    listSsis({ lei, limit: 100, offset: 0 })
      .then((data) => setSsis(data.items))
      .catch(() => setSsis([]))
      .finally(() => setSsiLoading(false))
  }, [lei])

  const handleSave = async () => {
    if (!lei) return
    setError('')
    setSuccess(false)
    // BIC validation: 8 or 11 chars, uppercase alphanumeric
    if (!/^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$/.test(bic)) {
      setError('BIC must be 8 or 11 uppercase characters (e.g. ACMEGB2L)')
      return
    }
    setSaving(true)
    try {
      const updated = await updateCounterparty(lei, { name, bic, is_active: isActive })
      setCp(updated)
      setSuccess(true)
    } catch {
      setError('Failed to save changes.')
    } finally {
      setSaving(false)
    }
  }

  if (!cp && !error) {
    return <PageLayout title="Edit Counterparty"><p style={{ color: COLOR.textMuted }}>Loading…</p></PageLayout>
  }

  return (
    <PageLayout title={`Edit Counterparty — ${lei}`}>
      <div style={{ maxWidth: 560 }}>
        <div style={CARD}>
          {error && (
            <div style={{ backgroundColor: '#fee2e2', color: '#991b1b', padding: '0.75rem', borderRadius: 6, marginBottom: '1rem', fontSize: '0.875rem' }}>
              {error}
            </div>
          )}
          {success && (
            <div style={{ backgroundColor: '#d1fae5', color: '#065f46', padding: '0.75rem', borderRadius: 6, marginBottom: '1rem', fontSize: '0.875rem' }}>
              Saved successfully.
            </div>
          )}

          <div style={{ marginBottom: '1rem' }}>
            <label style={LABEL}>LEI (read-only)</label>
            <input style={{ ...INPUT, backgroundColor: COLOR.bg, color: COLOR.textMuted }} value={lei} readOnly />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={LABEL}>Name</label>
            <input style={INPUT} value={name} onChange={e => setName(e.target.value)} />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={LABEL}>BIC</label>
            <input style={INPUT} value={bic} onChange={e => setBic(e.target.value.toUpperCase())}
              placeholder="ACMEGB2L" maxLength={11} />
            <span style={{ fontSize: '0.75rem', color: COLOR.textLight }}>8 or 11 uppercase characters</span>
          </div>

          <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input
              type="checkbox"
              id="is_active"
              checked={isActive}
              onChange={e => setIsActive(e.target.checked)}
              style={{ width: 16, height: 16, cursor: 'pointer' }}
            />
            <label htmlFor="is_active" style={{ fontSize: '0.875rem', cursor: 'pointer' }}>Active</label>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button onClick={handleSave} disabled={saving} style={BTN_PRIMARY}>
              {saving ? 'Saving…' : 'Save'}
            </button>
            <button onClick={() => navigate('/counterparties')} style={BTN_SECONDARY}>
              Cancel
            </button>
          </div>
        </div>

        <div style={{ ...CARD, marginTop: '1rem' }}>
          <div style={{ marginBottom: '0.75rem' }}>
            <h2 style={{ margin: 0, fontSize: '1rem' }}>SSI List</h2>
            <p style={{ margin: '0.35rem 0 0', color: COLOR.textMuted, fontSize: '0.875rem' }}>
              Click a row to open the SSI details for this counterparty.
            </p>
          </div>

          {ssiLoading ? (
            <p style={{ color: COLOR.textMuted }}>Loading SSIs…</p>
          ) : ssis.length === 0 ? (
            <p style={{ color: COLOR.textMuted, margin: 0 }}>No SSIs found for this counterparty.</p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={TABLE}>
                <thead>
                  <tr>
                    <th style={TH}>Currency</th>
                    <th style={TH}>BIC</th>
                    <th style={TH}>Account</th>
                    <th style={TH}>IBAN</th>
                    <th style={TH}>Type</th>
                    <th style={TH}>Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {ssis.map((row) => (
                    <tr
                      key={row.id}
                      onClick={() => navigate(`/ssis/${row.id}`)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          navigate(`/ssis/${row.id}`)
                        }
                      }}
                      tabIndex={0}
                      style={{ cursor: 'pointer' }}
                    >
                      <td style={TD}>{row.currency}</td>
                      <td style={{ ...TD, fontFamily: 'monospace' }}>{row.bic}</td>
                      <td style={{ ...TD, fontFamily: 'monospace', fontSize: '0.8rem' }}>{row.account}</td>
                      <td style={{ ...TD, fontFamily: 'monospace', fontSize: '0.8rem', color: row.iban ? COLOR.text : COLOR.textMuted }}>
                        {row.iban ?? '—'}
                      </td>
                      <td style={TD}>
                        <span style={{ padding: '2px 8px', borderRadius: 9999, fontSize: '0.75rem', background: row.is_external ? '#dbeafe' : '#d1fae5', color: row.is_external ? '#1e40af' : '#065f46' }}>
                          {row.is_external ? 'External' : 'Internal'}
                        </span>
                      </td>
                      <td style={{ ...TD, fontSize: '0.8rem', color: COLOR.textMuted }}>{new Date(row.updated_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </PageLayout>
  )
}
