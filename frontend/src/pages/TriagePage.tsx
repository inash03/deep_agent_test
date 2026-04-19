import { useState } from 'react'
import { startTriage, resumeTriage } from '../api/triage'
import { PageLayout } from '../components/PageLayout'
import { StatusBadge } from '../components/StatusBadge'
import { StepList } from '../components/StepList'
import { BTN_BASE, CARD, COLOR } from '../styles/theme'
import type { PendingActionType, TriageResponse } from '../types/triage'

type UIState =
  | { phase: 'input' }
  | { phase: 'loading'; message: string }
  | { phase: 'pending'; result: TriageResponse }
  | { phase: 'completed'; result: TriageResponse }
  | { phase: 'error'; message: string }

const HITL_CONFIG: Record<
  PendingActionType,
  { title: string; color: string; bg: string; border: string; approveLabel: string; rejectLabel: string | null; warning?: string }
> = {
  register_ssi: {
    title: 'SSI Registration Approval',
    color: '#9a3412', bg: '#fff7ed', border: '#fed7aa',
    approveLabel: 'Approve Registration',
    rejectLabel: 'Reject',
  },
  reactivate_counterparty: {
    title: 'Counterparty Reactivation Approval',
    color: '#1e40af', bg: '#eff6ff', border: '#bfdbfe',
    approveLabel: 'Approve Reactivation',
    rejectLabel: 'Reject',
    warning: 'Reactivating a counterparty allows them to trade again. Ensure compliance review is complete before approving.',
  },
  update_ssi: {
    title: 'SSI Update Approval',
    color: '#6b21a8', bg: '#faf5ff', border: '#e9d5ff',
    approveLabel: 'Approve Update',
    rejectLabel: 'Reject',
  },
  escalate: {
    title: 'Escalation to Senior Operator',
    color: '#991b1b', bg: '#fef2f2', border: '#fecaca',
    approveLabel: 'Acknowledge & Escalate',
    rejectLabel: 'Override — Resolve Automatically',
    warning: 'The agent could not determine a resolution. Acknowledging will escalate this case to a senior operator.',
  },
}

const ACTION_TAKEN_LABELS: Record<PendingActionType | string, string> = {
  register_ssi: 'Yes (SSI registered)',
  reactivate_counterparty: 'Yes (counterparty reactivated)',
  update_ssi: 'Yes (SSI updated)',
  escalate: 'Yes (escalated to senior operator)',
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
    const { run_id, pending_action_type } = uiState.result
    if (!run_id) return
    const actionLabel = pending_action_type
      ? (approved ? HITL_CONFIG[pending_action_type].approveLabel : (HITL_CONFIG[pending_action_type].rejectLabel ?? 'Reject'))
      : (approved ? 'Approving...' : 'Rejecting...')
    setUiState({ phase: 'loading', message: `${actionLabel}...` })
    try {
      const result = await resumeTriage(run_id, { approved })
      if (result.status === 'PENDING_APPROVAL') {
        setUiState({ phase: 'pending', result })
      } else {
        setUiState({ phase: 'completed', result })
      }
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
    <PageLayout title="STP Exception Triage Agent">
      <p style={{ color: COLOR.textMuted, marginBottom: '1.5rem', marginTop: '-0.5rem' }}>
        LangGraph ReAct agent investigates STP failures and diagnoses the root cause.
      </p>

      {/* Input Form */}
      {(uiState.phase === 'input' || uiState.phase === 'error') && (
        <div style={{ ...CARD, maxWidth: 600 }}>
          <h2 style={{ fontSize: '1.05rem', marginBottom: '1rem', fontWeight: 600 }}>New Triage Request</h2>
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
                style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '4px', fontSize: '0.95rem', boxSizing: 'border-box' }}
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
                style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '4px', fontSize: '0.95rem', resize: 'vertical', boxSizing: 'border-box' }}
              />
            </div>
            {uiState.phase === 'error' && (
              <p style={{ color: '#dc2626', fontSize: '0.875rem' }}>Error: {uiState.message}</p>
            )}
            <button type="submit" style={{ ...BTN_BASE, backgroundColor: COLOR.primary, color: '#fff', alignSelf: 'flex-start' }}>
              Start Triage
            </button>
          </form>
        </div>
      )}

      {/* Loading */}
      {uiState.phase === 'loading' && (
        <div style={{ ...CARD, color: COLOR.textMuted, textAlign: 'center', maxWidth: 600 }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>⏳</div>
          <p>{uiState.message}</p>
          <p style={{ fontSize: '0.8rem' }}>The agent is investigating via multiple tool calls. This may take 10–30 seconds.</p>
        </div>
      )}

      {/* HITL Approval Panel */}
      {uiState.phase === 'pending' && (
        <HitlPanel result={uiState.result} onDecide={handleResume} />
      )}

      {/* Completed Result */}
      {uiState.phase === 'completed' && (
        <div style={{ ...CARD, maxWidth: 700 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
                <h2 style={{ fontSize: '1.1rem', margin: 0 }}>Triage Result</h2>
                <StatusBadge status={uiState.result.status} />
              </div>
              <p style={{ fontSize: '0.85rem', color: COLOR.textMuted, margin: 0 }}>
                Trade: {uiState.result.trade_id} &nbsp;|&nbsp; Run ID: {uiState.result.run_id}
              </p>
            </div>
            <button onClick={handleReset} style={{ ...BTN_BASE, backgroundColor: '#f3f4f6', color: '#374151', fontSize: '0.85rem' }}>
              New Triage
            </button>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <tbody>
              <Row label="Root Cause" value={uiState.result.root_cause ?? '—'} highlight />
              <Row label="Diagnosis" value={uiState.result.diagnosis ?? '—'} />
              <Row label="Recommended Action" value={uiState.result.recommended_action ?? '—'} />
              <Row
                label="Action Taken"
                value={
                  uiState.result.action_taken
                    ? (ACTION_TAKEN_LABELS[uiState.result.root_cause ?? ''] ?? 'Yes')
                    : 'No'
                }
              />
            </tbody>
          </table>

          <StepList steps={uiState.result.steps} />
        </div>
      )}
    </PageLayout>
  )
}

function HitlPanel({ result, onDecide }: { result: TriageResponse; onDecide: (approved: boolean) => void }) {
  const actionType = result.pending_action_type
  const cfg = actionType ? HITL_CONFIG[actionType] : HITL_CONFIG.register_ssi

  return (
    <div style={{ ...CARD, borderColor: cfg.border, backgroundColor: cfg.bg, maxWidth: 700 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <span style={{ fontSize: '1.5rem' }}>⚠️</span>
        <div>
          <h2 style={{ fontSize: '1.1rem', margin: 0 }}>{cfg.title}</h2>
          <p style={{ fontSize: '0.85rem', color: cfg.color, margin: '0.25rem 0 0' }}>
            Trade: {result.trade_id} &nbsp;|&nbsp; Run ID: {result.run_id}
          </p>
        </div>
      </div>

      {cfg.warning && (
        <div style={{ background: '#fff', border: `1px solid ${cfg.border}`, borderRadius: '6px', padding: '0.75rem 1rem', marginBottom: '0.75rem', fontSize: '0.85rem', color: cfg.color }}>
          {cfg.warning}
        </div>
      )}

      <div style={{ background: '#fff', border: `1px solid ${cfg.border}`, borderRadius: '6px', padding: '1rem', marginBottom: '1rem', fontSize: '0.9rem' }}>
        <p style={{ fontWeight: 600, marginBottom: '0.25rem', color: '#374151' }}>Proposed Action:</p>
        <p style={{ margin: 0, color: '#111827' }}>{result.pending_action_description}</p>
      </div>

      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
        <button onClick={() => onDecide(true)} style={{ ...BTN_BASE, backgroundColor: '#16a34a', color: '#fff' }}>
          {cfg.approveLabel}
        </button>
        {cfg.rejectLabel && (
          <button onClick={() => onDecide(false)} style={{ ...BTN_BASE, backgroundColor: '#dc2626', color: '#fff' }}>
            {cfg.rejectLabel}
          </button>
        )}
      </div>

      <StepList steps={result.steps} />
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
