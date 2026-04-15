import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createStpException } from '../api/stpExceptions'
import { PageLayout } from '../components/PageLayout'
import { BTN_PRIMARY, BTN_SECONDARY, CARD, COLOR, INPUT, LABEL } from '../styles/theme'

export function StpExceptionCreatePage() {
  const navigate = useNavigate()
  const [tradeId, setTradeId] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleCreate = async () => {
    if (!tradeId.trim() || !errorMessage.trim()) {
      setError('Trade ID and Error Message are required.')
      return
    }
    setError('')
    setSaving(true)
    try {
      await createStpException({ trade_id: tradeId.trim(), error_message: errorMessage.trim() })
      navigate('/stp-exceptions')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(`Failed to create exception: ${msg}`)
    } finally {
      setSaving(false)
    }
  }

  return (
    <PageLayout title="New STP Exception">
      <div style={{ maxWidth: 560 }}>
        <div style={CARD}>
          {error && (
            <div style={{ backgroundColor: '#fee2e2', color: '#991b1b', padding: '0.75rem', borderRadius: 6, marginBottom: '1rem', fontSize: '0.875rem' }}>
              {error}
            </div>
          )}

          <div style={{ marginBottom: '1rem' }}>
            <label style={LABEL}>Trade ID</label>
            <input
              style={INPUT}
              value={tradeId}
              onChange={e => setTradeId(e.target.value)}
              placeholder="TRD-001"
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={LABEL}>Error Message</label>
            <textarea
              style={{ ...INPUT, resize: 'vertical', minHeight: 80 }}
              value={errorMessage}
              onChange={e => setErrorMessage(e.target.value)}
              placeholder="SETT FAIL - SSI not found for counterparty LEI..."
              rows={4}
            />
            <span style={{ fontSize: '0.75rem', color: COLOR.textLight }}>
              Describe the STP failure reason
            </span>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button onClick={handleCreate} disabled={saving} style={BTN_PRIMARY}>
              {saving ? 'Creating…' : 'Create'}
            </button>
            <button onClick={() => navigate('/stp-exceptions')} style={BTN_SECONDARY}>
              Cancel
            </button>
          </div>
        </div>
      </div>
    </PageLayout>
  )
}
