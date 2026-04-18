import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getSsi, updateSsi } from '../api/ssis'
import { PageLayout } from '../components/PageLayout'
import { BTN_PRIMARY, BTN_SECONDARY, CARD, COLOR, INPUT, LABEL } from '../styles/theme'
import type { Ssi } from '../types/ssi'

export function SsiEditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [ssi, setSsi] = useState<Ssi | null>(null)
  const [bic, setBic] = useState('')
  const [account, setAccount] = useState('')
  const [iban, setIban] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    if (!id) return
    getSsi(id).then(data => {
      setSsi(data)
      setBic(data.bic)
      setAccount(data.account)
      setIban(data.iban ?? '')
    }).catch(() => setError('SSI not found.'))
  }, [id])

  const handleSave = async () => {
    if (!id) return
    setError('')
    setSuccess(false)
    if (!/^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$/.test(bic)) {
      setError('BIC must be 8 or 11 uppercase characters (e.g. ACMEGB2L)')
      return
    }
    if (!account.trim()) {
      setError('Account number is required.')
      return
    }
    setSaving(true)
    try {
      const updated = await updateSsi(id, { bic, account, iban: iban || undefined })
      setSsi(updated)
      setSuccess(true)
    } catch {
      setError('Failed to save changes.')
    } finally {
      setSaving(false)
    }
  }

  if (!ssi && !error) {
    return <PageLayout title="Edit SSI"><p style={{ color: COLOR.textMuted }}>Loading…</p></PageLayout>
  }

  return (
    <PageLayout title={`Edit SSI — ${ssi?.lei ?? ''} / ${ssi?.currency ?? ''}`}>
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
            <input style={{ ...INPUT, backgroundColor: COLOR.bg, color: COLOR.textMuted }} value={ssi?.lei ?? ''} readOnly />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={LABEL}>Currency (read-only)</label>
            <input style={{ ...INPUT, backgroundColor: COLOR.bg, color: COLOR.textMuted }} value={ssi?.currency ?? ''} readOnly />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={LABEL}>BIC</label>
            <input style={INPUT} value={bic} onChange={e => setBic(e.target.value.toUpperCase())}
              placeholder="ACMEGB2L" maxLength={11} />
            <span style={{ fontSize: '0.75rem', color: COLOR.textLight }}>8 or 11 uppercase characters</span>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={LABEL}>Account Number</label>
            <input style={INPUT} value={account} onChange={e => setAccount(e.target.value)} placeholder="GB29NWBK60161331926819" />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={LABEL}>IBAN (optional)</label>
            <input style={INPUT} value={iban} onChange={e => setIban(e.target.value)} placeholder="GB29NWBK60161331926819" />
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button onClick={handleSave} disabled={saving} style={BTN_PRIMARY}>
              {saving ? 'Saving…' : 'Save'}
            </button>
            <button onClick={() => navigate('/ssis')} style={BTN_SECONDARY}>
              Cancel
            </button>
          </div>
        </div>
      </div>
    </PageLayout>
  )
}
