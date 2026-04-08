import { useState } from 'react'
import { startTriage, resumeTriage } from '../api/triage'
import type { TriageResponse } from '../types/triage'
import { StatusBadge } from '../components/StatusBadge'
import { StepList } from '../components/StepList'

type UIState =
  | { phase: 'input' }
  | { phase: 'loading'; message: string }
  | { phase: 'pending'; result: TriageResponse }
  | { phase: 'completed'; result: TriageResponse }
  | { phase: 'error'; message: string }

const CARD: React.CSSProperties = {
  background: '#fff',
  border: '1px solid #e5e7eb',
  borderRadius: '8px',
  padding: '1.5rem',
  marginBottom: '1rem',
}

const BTN_BASE: React.CSSProperties = {
  padding: '0.5rem 1.25rem',
  borderRadius: '6px',
  border: 'none',
  fontWeight: 600,
  cursor: 'pointer',
  fontSize: '0.95rem',
}

export function TriagePage() {
  const [tradeId, setTradeId] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [uiState, setUiState] = useState<UIState>({ phase: 'input' })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setUiState({ phase: 'loading', message: 'Investigating STP failure...' })
    try {
      const result = await startTriage({ trade_id: tradeId, error_message: errorMessage })
      if (result.status === 'PENDING_APPROVAL') {
        setUiState({ phase: 'pending', result })
      } else {
        setUiState({ phase: 'completed', result })
      }
    } catch (err) {
      setUiState({ phase: 'error', message: String(err) })
    }
  }

  const handleResume = async (approved: boolean) => {
    if (uiState.phase !== 'pending') return
    const { run_id } = uiState.result
    if (!run_id) return
    setUiState({ phase: 'loading', message: approved ? 'Approving SSI registration...' : 'Rejecting SSI registration...' })
    try {
      const result = await resumeTriage(run_id, { approved })
      setUiState({ phase: 'completed', result })
    } catch (err) {
      setUiState({ phase: 'error', message: String(err) })
    }
  }

  const handleReset = () => {
    setTradeId('')
    setErrorMessage('')
    setUiState({ phase: 'input' })
  }

  return (
    <div style={{ maxWidth: '800px', margin: '2rem auto', padding: '0 1rem', fontFamily: 'system-ui, sans-serif' }}>
      <h1 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>STP Exception Triage Agent</h1>
      <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
        LangGraph ReAct agent investigates STP failures and diagnoses the root cause.
      </p>

      {/* Input Form */}
      {(uiState.phase === 'input' || uiState.phase === 'error') && (
        <div style={CARD}>
          <h2 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>New Triage Request</h2>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, marginBottom: '0.25rem' }}>
                Trade ID
              </label>
              <input
                type="text"
                value={tradeId}
                onChange={e => setTradeId(e.target.value)}
                placeholder="TRD-001"
                required
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '0.95rem',
                  boxSizing: 'border-box',
                }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, marginBottom: '0.25rem' }}>
                Error Message
              </label>
              <textarea
                value={errorMessage}
                onChange={e => setErrorMessage(e.target.value)}
                placeholder="SETT FAIL - SSI not found for counterparty LEI..."
                required
                rows={3}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '0.95rem',
                  resize: 'vertical',
                  boxSizing: 'border-box',
                }}
              />
            </div>
            {uiState.phase === 'error' && (
              <p style={{ color: '#dc2626', fontSize: '0.875rem' }}>Error: {uiState.message}</p>
            )}
            <button
              type="submit"
              style={{ ...BTN_BASE, backgroundColor: '#2563eb', color: '#fff', alignSelf: 'flex-start' }}
            >
              Start Triage
            </button>
          </form>
        </div>
      )}

      {/* Loading */}
      {uiState.phase === 'loading' && (
        <div style={{ ...CARD, color: '#6b7280', textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>⏳</div>
          <p>{uiState.message}</p>
          <p style={{ fontSize: '0.8rem' }}>The agent is investigating via multiple tool calls. This may take 10–30 seconds.</p>
        </div>
      )}

      {/* HITL Approval Panel */}
      {uiState.phase === 'pending' && (
        <div style={{ ...CARD, borderColor: '#fed7aa', backgroundColor: '#fff7ed' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <span style={{ fontSize: '1.5rem' }}>⚠️</span>
            <div>
              <h2 style={{ fontSize: '1.1rem', margin: 0 }}>Operator Approval Required</h2>
              <p style={{ fontSize: '0.85rem', color: '#9a3412', margin: '0.25rem 0 0' }}>
                Trade: {uiState.result.trade_id} &nbsp;|&nbsp; Run ID: {uiState.result.run_id}
              </p>
            </div>
          </div>
          <div
            style={{
              background: '#fff',
              border: '1px solid #fed7aa',
              borderRadius: '6px',
              padding: '1rem',
              marginBottom: '1rem',
              fontSize: '0.9rem',
            }}
          >
            <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Proposed Action:</p>
            <p style={{ margin: 0 }}>{uiState.result.pending_action_description}</p>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button
              onClick={() => handleResume(true)}
              style={{ ...BTN_BASE, backgroundColor: '#16a34a', color: '#fff' }}
            >
              Approve
            </button>
            <button
              onClick={() => handleResume(false)}
              style={{ ...BTN_BASE, backgroundColor: '#dc2626', color: '#fff' }}
            >
              Reject
            </button>
          </div>
          <StepList steps={uiState.result.steps} />
        </div>
      )}

      {/* Completed Result */}
      {uiState.phase === 'completed' && (
        <div style={CARD}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
                <h2 style={{ fontSize: '1.1rem', margin: 0 }}>Triage Result</h2>
                <StatusBadge status={uiState.result.status} />
              </div>
              <p style={{ fontSize: '0.85rem', color: '#6b7280', margin: 0 }}>
                Trade: {uiState.result.trade_id} &nbsp;|&nbsp; Run ID: {uiState.result.run_id}
              </p>
            </div>
            <button
              onClick={handleReset}
              style={{ ...BTN_BASE, backgroundColor: '#f3f4f6', color: '#374151', fontSize: '0.85rem' }}
            >
              New Triage
            </button>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <tbody>
              <Row label="Root Cause" value={uiState.result.root_cause ?? '—'} highlight />
              <Row label="Diagnosis" value={uiState.result.diagnosis ?? '—'} />
              <Row label="Recommended Action" value={uiState.result.recommended_action ?? '—'} />
              <Row label="Action Taken" value={uiState.result.action_taken ? 'Yes (SSI registered)' : 'No'} />
            </tbody>
          </table>

          <StepList steps={uiState.result.steps} />
        </div>
      )}
    </div>
  )
}

function Row({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <tr style={{ borderBottom: '1px solid #f3f4f6' }}>
      <td style={{ padding: '0.5rem 0.5rem 0.5rem 0', fontWeight: 500, color: '#6b7280', whiteSpace: 'nowrap', width: '180px' }}>
        {label}
      </td>
      <td style={{ padding: '0.5rem', color: highlight ? '#b45309' : '#111827', fontWeight: highlight ? 600 : 400 }}>
        {value}
      </td>
    </tr>
  )
}
