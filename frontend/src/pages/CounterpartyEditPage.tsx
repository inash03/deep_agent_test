import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getCounterparty, updateCounterparty } from '../api/counterparties'
import { PageLayout } from '../components/PageLayout'
import { BTN_PRIMARY, BTN_SECONDARY, CARD, COLOR, INPUT, LABEL } from '../styles/theme'
import type { Counterparty } from '../types/counterparty'

export function CounterpartyEditPage() {
  const { lei } = useParams<{ lei: string }>()
  const navigate = useNavigate()
  const [cp, setCp] = useState<Counterparty | null>(null)
  const [name, setName] = useState('')
  const [bic, setBic] = useState('')
  const [isActive, setIsActive] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    if (!lei) return
    getCounterparty(lei).then(data => {
      setCp(data)
      setName(data.name)
      setBic(data.bic)
      setIsActive(data.is_active)
    }).catch(() => setError('Counterparty not found.'))
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
      </div>
    </PageLayout>
  )
}
