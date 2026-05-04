import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  getTrade, runBoCheck, runFoCheck,
  resumeBoTriage, resumeFoTriage,
  startBoTriage, startFoTriage,
} from '../api/trades'
import {
  boApproveEvent, createTradeEvent,
  foApproveEvent, listTradeEvents,
} from '../api/tradeEvents'
import { PageLayout } from '../components/PageLayout'
import { BTN_DANGER, BTN_PRIMARY, BTN_SECONDARY, CARD, COLOR, INPUT, LABEL, TABLE, TD, TH } from '../styles/theme'
import type { CheckResult, Trade } from '../types/trade'
import { WORKFLOW_STATUS_COLORS, WORKFLOW_STATUS_LABELS } from '../types/trade'
import type { TradeEvent } from '../types/tradeEvent'
import { EVENT_STATUS_COLORS, EVENT_STATUS_LABELS } from '../types/tradeEvent'
import type { TriageResponse } from '../types/triage'

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function WorkflowBadge({ status }: { status: string }) {
  const style = WORKFLOW_STATUS_COLORS[status] ?? { backgroundColor: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db' }
  return (
    <span style={{ display: 'inline-block', padding: '3px 12px', borderRadius: 9999, fontSize: '0.8rem', fontWeight: 600, ...style }}>
      {WORKFLOW_STATUS_LABELS[status] ?? status}
    </span>
  )
}

function EventBadge({ status }: { status: string }) {
  const style = EVENT_STATUS_COLORS[status] ?? {}
  return (
    <span style={{ display: 'inline-block', padding: '2px 10px', borderRadius: 9999, fontSize: '0.78rem', fontWeight: 600, ...style }}>
      {EVENT_STATUS_LABELS[status] ?? status}
    </span>
  )
}

function CheckResultsTable({ results }: { results: CheckResult[] }) {
  if (!results.length) return <p style={{ color: COLOR.textMuted, fontSize: '0.875rem' }}>No results.</p>
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={TABLE}>
        <thead>
          <tr>
            {['Rule', 'Status', 'Severity', 'Message'].map(h => <th key={h} style={TH}>{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {results.map(r => (
            <tr key={r.rule_name}>
              <td style={{ ...TD, fontFamily: 'monospace', fontSize: '0.82rem' }}>{r.rule_name}</td>
              <td style={TD}>
                {r.passed
                  ? <span style={{ color: '#15803d', fontWeight: 700 }}>✓ Pass</span>
                  : <span style={{ color: r.severity === 'warning' ? '#d97706' : '#dc2626', fontWeight: 700 }}>✗ {r.severity === 'warning' ? 'Warn' : 'Fail'}</span>
                }
              </td>
              <td style={{ ...TD, fontSize: '0.82rem', color: r.severity === 'warning' ? '#d97706' : COLOR.textMuted }}>
                {r.severity}
              </td>
              <td style={{ ...TD, fontSize: '0.82rem', color: COLOR.textMuted }}>{r.message}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function TriagePanel({
  label,
  result,
  onApprove,
  onReject,
  running,
}: {
  label: string
  result: TriageResponse
  onApprove: () => void
  onReject: () => void
  running: boolean
}) {
  if (result.status === 'PENDING_APPROVAL') {
    return (
      <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#fff7ed', border: '1px solid #fed7aa', borderRadius: 8 }}>
        <p style={{ fontWeight: 700, color: '#9a3412', marginBottom: '0.5rem' }}>{label} — Awaiting Approval</p>
        <p style={{ fontSize: '0.875rem', color: '#92400e', marginBottom: '0.75rem' }}>
          <strong>Action:</strong> {result.pending_action_type}<br />
          {result.pending_action_description}
        </p>
        <div style={{ display: 'flex', gap: 8 }}>
          <button style={{ ...BTN_PRIMARY, backgroundColor: '#16a34a' }} disabled={running} onClick={onApprove}>
            {running ? 'Processing…' : 'Approve'}
          </button>
          <button style={BTN_DANGER} disabled={running} onClick={onReject}>
            {running ? 'Processing…' : 'Reject'}
          </button>
        </div>
      </div>
    )
  }
  return (
    <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#f0fdf4', border: '1px solid #86efac', borderRadius: 8 }}>
      <p style={{ fontWeight: 700, color: '#15803d', marginBottom: '0.5rem' }}>{label} — Completed</p>
      {result.diagnosis && <p style={{ fontSize: '0.875rem', color: COLOR.text, marginBottom: '0.5rem' }}><strong>Diagnosis:</strong> {result.diagnosis}</p>}
      {result.root_cause && <p style={{ fontSize: '0.875rem' }}><strong>Root cause:</strong> {result.root_cause}</p>}
      {result.recommended_action && <p style={{ fontSize: '0.875rem' }}><strong>Next steps:</strong> {result.recommended_action}</p>}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

type Tab = 'fo-check' | 'bo-check' | 'events'

const TABS: { id: Tab; label: string }[] = [
  { id: 'fo-check', label: 'FoCheck' },
  { id: 'bo-check', label: 'BoCheck' },
  { id: 'events', label: 'Events' },
]

export function TradeDetailPage() {
  const { trade_id } = useParams<{ trade_id: string }>()
  const navigate = useNavigate()

  const [trade, setTrade] = useState<Trade | null>(null)
  const [events, setEvents] = useState<TradeEvent[]>([])
  const [activeTab, setActiveTab] = useState<Tab>('fo-check')
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState<string | null>(null)
  const [error, setError] = useState('')

  // Triage state
  const [foTriage, setFoTriage] = useState<TriageResponse | null>(null)
  const [boTriage, setBoTriage] = useState<TriageResponse | null>(null)
  const [foTriageMsg, setFoTriageMsg] = useState('')
  const [boTriageMsg, setBoTriageMsg] = useState('')

  // Event creation form
  const [showEventForm, setShowEventForm] = useState(false)
  const [evtType, setEvtType] = useState<'AMEND' | 'CANCEL'>('AMEND')
  const [evtReason, setEvtReason] = useState('')
  const [evtRequester, setEvtRequester] = useState('fo_user_01')
  const [evtFields, setEvtFields] = useState('{"value_date": "2026-05-01"}')

  const reload = async () => {
    if (!trade_id) return
    const [t, evts] = await Promise.all([getTrade(trade_id), listTradeEvents(trade_id)])
    setTrade(t)
    setEvents(evts.items)
  }

  useEffect(() => {
    reload().catch(() => setError('Failed to load trade.')).finally(() => setLoading(false))
  }, [trade_id]) // eslint-disable-line react-hooks/exhaustive-deps

  const wrap = async (key: string, fn: () => Promise<void>) => {
    setRunning(key)
    setError('')
    try {
      await fn()
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
      if (typeof detail === 'string') {
        setError(detail)
      } else if (Array.isArray(detail)) {
        setError(detail.map((d: unknown) => (d as { msg?: string })?.msg ?? JSON.stringify(d)).join('; '))
      } else {
        setError(String(e))
      }
    } finally {
      setRunning(null)
    }
  }

  const handleRunFoCheck = () => wrap('fo-check', async () => {
    await runFoCheck(trade_id!)
    await reload()
  })

  const handleRunBoCheck = () => wrap('bo-check', async () => {
    await runBoCheck(trade_id!)
    await reload()
  })

  const handleStartFoTriage = () => wrap('fo-triage', async () => {
    const failures = (trade?.fo_check_results ?? []).filter(r => !r.passed)
    const lines = failures.map(r => `[${r.rule_name}] ${r.message}`)
    const errorMsg = foTriageMsg
      ? `${lines.join('\n')}\nAdditional context: ${foTriageMsg}`
      : lines.join('\n')
    const res = await startFoTriage(trade_id!, errorMsg)
    setFoTriage(res)
    if (res.status === 'COMPLETED' && res.root_cause !== null && res.root_cause !== 'UNKNOWN') {
      await runFoCheck(trade_id!)
    }
    await reload()
  })

  const handleFoHitl = (approved: boolean) => wrap(`fo-hitl-${approved}`, async () => {
    if (!foTriage?.run_id) return
    const res = await resumeFoTriage(trade_id!, foTriage.run_id, approved)
    setFoTriage(res)
    if (res.status === 'COMPLETED' && res.root_cause !== null && res.root_cause !== 'UNKNOWN') {
      await runFoCheck(trade_id!)
    }
    await reload()
  })

  const handleStartBoTriage = () => wrap('bo-triage', async () => {
    const failures = (trade?.bo_check_results ?? []).filter(r => !r.passed)
    const lines = failures.map(r => `[${r.rule_name}] ${r.message}`)
    const errorMsg = boTriageMsg
      ? `${lines.join('\n')}\nAdditional context: ${boTriageMsg}`
      : lines.join('\n')
    const res = await startBoTriage(trade_id!, errorMsg)
    setBoTriage(res)
    if (res.status === 'COMPLETED' && res.root_cause !== null && res.root_cause !== 'UNKNOWN') {
      await runBoCheck(trade_id!)
    }
    await reload()
  })

  const handleBoHitl = (approved: boolean) => wrap(`bo-hitl-${approved}`, async () => {
    if (!boTriage?.run_id) return
    const res = await resumeBoTriage(trade_id!, boTriage.run_id, approved)
    setBoTriage(res)
    if (res.status === 'COMPLETED' && res.root_cause !== null && res.root_cause !== 'UNKNOWN') {
      await runBoCheck(trade_id!)
    }
    await reload()
  })

  const handleCreateEvent = () => wrap('event-create', async () => {
    let fields: Record<string, unknown> | undefined
    if (evtType === 'AMEND') {
      try { fields = JSON.parse(evtFields) } catch { throw new Error('amended_fields is not valid JSON.') }
    }
    await createTradeEvent(trade_id!, {
      event_type: evtType,
      reason: evtReason,
      requested_by: evtRequester,
      amended_fields: fields,
    })
    setShowEventForm(false)
    setEvtReason('')
    setEvtFields('{"value_date": "2026-05-01"}')
    await reload()
  })

  const handleFoApprove = (eventId: string, approved: boolean) =>
    wrap(`fo-approve-${eventId}`, async () => {
      await foApproveEvent(eventId, approved)
      await reload()
    })

  const handleBoApprove = (eventId: string, approved: boolean) =>
    wrap(`bo-approve-${eventId}`, async () => {
      await boApproveEvent(eventId, approved)
      await reload()
    })

  if (loading) return <PageLayout title="Trade Detail"><p style={{ color: COLOR.textMuted }}>Loading…</p></PageLayout>
  if (!trade) return <PageLayout title="Trade Detail"><p style={{ color: COLOR.danger }}>Trade not found.</p></PageLayout>

  const tabStyle = (id: Tab): React.CSSProperties => ({
    padding: '0.5rem 1.25rem',
    border: 'none',
    borderBottom: activeTab === id ? `3px solid ${COLOR.primary}` : '3px solid transparent',
    backgroundColor: 'transparent',
    color: activeTab === id ? COLOR.primary : COLOR.textMuted,
    fontWeight: activeTab === id ? 700 : 400,
    fontSize: '0.9rem',
    cursor: 'pointer',
  })

  return (
    <PageLayout title={`Trade ${trade.trade_id}`}>
      {/* Breadcrumb */}
      <button onClick={() => navigate('/trades')} style={{ ...BTN_SECONDARY, marginBottom: '1rem', fontSize: '0.82rem' }}>
        ← Back to Trades
      </button>

      {error && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: '#fee2e2', borderRadius: 6, color: '#991b1b', fontSize: '0.875rem' }}>
          {error}
        </div>
      )}

      {/* Trade header */}
      <div style={{ ...CARD, marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          <span style={{ fontWeight: 700, fontSize: '1.1rem', fontFamily: 'monospace' }}>{trade.trade_id}</span>
          <span style={{ fontSize: '0.82rem', color: COLOR.textMuted }}>v{trade.version}</span>
          <WorkflowBadge status={trade.workflow_status} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.5rem 1.5rem', fontSize: '0.875rem' }}>
          {[
            ['Counterparty LEI', trade.counterparty_lei],
            ['Instrument', trade.instrument_id],
            ['Currency', trade.currency],
            ['Settlement CCY', trade.settlement_currency],
            ['Amount', Number(trade.amount).toLocaleString()],
            ['Trade Date', trade.trade_date],
            ['Value Date', trade.value_date],
          ].map(([label, val]) => (
            <div key={label}>
              <span style={{ color: COLOR.textMuted, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>{label}</span>
              <div style={{ fontFamily: 'monospace', marginTop: 2 }}>{val}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ borderBottom: `1px solid ${COLOR.border}`, display: 'flex', marginBottom: '1rem', overflowX: 'auto' }}>
        {TABS.map(t => (
          <button key={t.id} style={tabStyle(t.id)} onClick={() => setActiveTab(t.id)}>{t.label}</button>
        ))}
      </div>

      {/* ─── FoCheck tab ─── */}
      {activeTab === 'fo-check' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={CARD}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: 8 }}>
              <h3 style={{ margin: 0, fontSize: '1rem' }}>FoCheck Results</h3>
              <button style={BTN_PRIMARY} disabled={running === 'fo-check'} onClick={handleRunFoCheck}>
                {running === 'fo-check' ? 'Running…' : 'Run FoCheck'}
              </button>
            </div>
            {trade.fo_check_results?.length
              ? <CheckResultsTable results={trade.fo_check_results} />
              : <p style={{ color: COLOR.textMuted, fontSize: '0.875rem' }}>FoCheck has not been run yet. Click "Run FoCheck" to execute.</p>
            }
          </div>

          {/* FO Triage */}
          <div style={CARD}>
            <h3 style={{ margin: '0 0 0.75rem', fontSize: '1rem', color: '#1d4ed8' }}>FO Triage</h3>
            {!foTriage ? (() => {
              const foCheckRun = (trade.fo_check_results?.length ?? 0) > 0
              const foFails = (trade.fo_check_results ?? []).filter(r => !r.passed)
              return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {foFails.length > 0 ? (
                    <p style={{ margin: 0, fontSize: '0.82rem', color: '#4b5563' }}>
                      Found <strong>{foFails.length} failed rule(s)</strong>. The triage agent will investigate:{' '}
                      <span style={{ fontFamily: 'monospace' }}>{foFails.map(r => r.rule_name).join(', ')}</span>
                    </p>
                  ) : foCheckRun ? (
                    <p style={{ margin: 0, fontSize: '0.82rem', color: '#15803d' }}>
                      All FoCheck rules passed. No triage required.
                    </p>
                  ) : (
                    <p style={{ margin: 0, fontSize: '0.82rem', color: COLOR.textMuted }}>
                      FoCheck has not been run yet. Click "Run FoCheck" above first.
                    </p>
                  )}
                  <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                    <div style={{ flex: '1 1 300px' }}>
                      <label style={LABEL}>Additional context (optional)</label>
                      <input style={INPUT} value={foTriageMsg} onChange={e => setFoTriageMsg(e.target.value)} placeholder="Extra context for the agent" />
                    </div>
                    {(() => {
                      const disabled = running === 'fo-triage' || foFails.length === 0
                      return (
                        <button
                          style={{ ...BTN_PRIMARY, ...(disabled ? { opacity: 0.45, cursor: 'not-allowed' } : {}) }}
                          disabled={disabled}
                          onClick={handleStartFoTriage}
                        >
                          {running === 'fo-triage' ? 'Investigating…' : 'Start FO Triage'}
                        </button>
                      )
                    })()}
                  </div>
                </div>
              )
            })() : null}
            {foTriage && (
              <TriagePanel
                label="FO Triage"
                result={foTriage}
                onApprove={() => handleFoHitl(true)}
                onReject={() => handleFoHitl(false)}
                running={running?.startsWith('fo-hitl') ?? false}
              />
            )}
          </div>
        </div>
      )}

      {/* ─── BoCheck tab ─── */}
      {activeTab === 'bo-check' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={CARD}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: 8 }}>
              <h3 style={{ margin: 0, fontSize: '1rem' }}>BoCheck Results</h3>
              <button style={{ ...BTN_PRIMARY, backgroundColor: '#15803d' }} disabled={running === 'bo-check'} onClick={handleRunBoCheck}>
                {running === 'bo-check' ? 'Running…' : 'Run BoCheck'}
              </button>
            </div>
            {trade.bo_check_results?.length
              ? <CheckResultsTable results={trade.bo_check_results} />
              : <p style={{ color: COLOR.textMuted, fontSize: '0.875rem' }}>BoCheck has not been run yet. Click "Run BoCheck" to execute.</p>
            }
          </div>

          {/* BO Triage */}
          <div style={CARD}>
            <h3 style={{ margin: '0 0 0.75rem', fontSize: '1rem', color: '#065f46' }}>BO Triage</h3>
            {!boTriage ? (() => {
              const boCheckRun = (trade.bo_check_results?.length ?? 0) > 0
              const boFails = (trade.bo_check_results ?? []).filter(r => !r.passed)
              return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {boFails.length > 0 ? (
                    <p style={{ margin: 0, fontSize: '0.82rem', color: '#4b5563' }}>
                      Found <strong>{boFails.length} failed rule(s)</strong>. The triage agent will investigate:{' '}
                      <span style={{ fontFamily: 'monospace' }}>{boFails.map(r => r.rule_name).join(', ')}</span>
                    </p>
                  ) : boCheckRun ? (
                    <p style={{ margin: 0, fontSize: '0.82rem', color: '#15803d' }}>
                      All BoCheck rules passed. No triage required.
                    </p>
                  ) : (
                    <p style={{ margin: 0, fontSize: '0.82rem', color: COLOR.textMuted }}>
                      BoCheck has not been run yet. Click "Run BoCheck" above first.
                    </p>
                  )}
                  <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                    <div style={{ flex: '1 1 300px' }}>
                      <label style={LABEL}>Additional context (optional)</label>
                      <input style={INPUT} value={boTriageMsg} onChange={e => setBoTriageMsg(e.target.value)} placeholder="Extra context for the agent" />
                    </div>
                    {(() => {
                      const disabled = running === 'bo-triage' || boFails.length === 0
                      return (
                        <button
                          style={{ ...BTN_PRIMARY, backgroundColor: '#15803d', ...(disabled ? { opacity: 0.45, cursor: 'not-allowed' } : {}) }}
                          disabled={disabled}
                          onClick={handleStartBoTriage}
                        >
                          {running === 'bo-triage' ? 'Investigating…' : 'Start BO Triage'}
                        </button>
                      )
                    })()}
                  </div>
                </div>
              )
            })() : null}
            {boTriage && (
              <TriagePanel
                label="BO Triage"
                result={boTriage}
                onApprove={() => handleBoHitl(true)}
                onReject={() => handleBoHitl(false)}
                running={running?.startsWith('bo-hitl') ?? false}
              />
            )}
          </div>
        </div>
      )}

      {/* ─── Events tab ─── */}
      {activeTab === 'events' && (
        <div>
          <div style={CARD}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: 8 }}>
              <h3 style={{ margin: 0, fontSize: '1rem' }}>Trade Events</h3>
              <button style={BTN_PRIMARY} onClick={() => { setShowEventForm(v => !v); setError('') }}>
                {showEventForm ? 'Cancel' : '+ Create Event'}
              </button>
            </div>

            {/* Create event form */}
            {showEventForm && (
              <div style={{ padding: '1rem', backgroundColor: '#f8fafc', border: `1px solid ${COLOR.border}`, borderRadius: 8, marginBottom: '1rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <div>
                    <label style={LABEL}>Event Type</label>
                    <div style={{ display: 'flex', gap: 8 }}>
                      {(['AMEND', 'CANCEL'] as const).map(t => (
                        <button key={t} onClick={() => setEvtType(t)} style={{
                          ...BTN_SECONDARY,
                          ...(evtType === t ? { backgroundColor: COLOR.primary, color: '#fff', borderColor: COLOR.primary } : {}),
                        }}>{t}</button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label style={LABEL}>
                      Reason <span style={{ color: '#dc2626', fontWeight: 700 }}>*</span>
                    </label>
                    <input style={INPUT} value={evtReason} onChange={e => setEvtReason(e.target.value)} placeholder="Reason for amendment/cancellation (required)" />
                  </div>
                  <div>
                    <label style={LABEL}>Requested By</label>
                    <input style={INPUT} value={evtRequester} onChange={e => setEvtRequester(e.target.value)} />
                  </div>
                  {evtType === 'AMEND' && (
                    <div>
                      <label style={LABEL}>Amended Fields (JSON)</label>
                      <textarea
                        style={{ ...INPUT, height: 80, fontFamily: 'monospace', resize: 'vertical' }}
                        value={evtFields}
                        onChange={e => setEvtFields(e.target.value)}
                        placeholder='{"value_date": "2026-05-01"}'
                      />
                    </div>
                  )}
                  {error && (
                    <div style={{ padding: '0.5rem 0.75rem', backgroundColor: '#fee2e2', borderRadius: 4, color: '#991b1b', fontSize: '0.82rem' }}>
                      ⚠ {error}
                    </div>
                  )}
                  <button
                    style={BTN_PRIMARY}
                    disabled={running === 'event-create' || !evtReason}
                    onClick={handleCreateEvent}
                  >
                    {running === 'event-create' ? 'Creating…' : 'Create Event'}
                  </button>
                </div>
              </div>
            )}

            {/* Events table */}
            {events.length === 0 ? (
              <p style={{ color: COLOR.textMuted, fontSize: '0.875rem' }}>No events for this trade.</p>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={TABLE}>
                  <thead>
                    <tr>
                      {['Type', 'Status', 'Versions', 'Requested By', 'Reason', 'Actions'].map(h => (
                        <th key={h} style={TH}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {events.map(ev => (
                      <tr key={ev.id}>
                        <td style={{ ...TD, fontWeight: 600 }}>{ev.event_type}</td>
                        <td style={TD}><EventBadge status={ev.workflow_status} /></td>
                        <td style={{ ...TD, fontFamily: 'monospace', fontSize: '0.82rem' }}>
                          v{ev.from_version} → v{ev.to_version}
                        </td>
                        <td style={{ ...TD, fontSize: '0.82rem' }}>{ev.requested_by}</td>
                        <td style={{ ...TD, fontSize: '0.82rem', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {ev.reason ?? '—'}
                        </td>
                        <td style={TD}>
                          {ev.workflow_status === 'FoUserToValidate' && (
                            <div style={{ display: 'flex', gap: 6 }}>
                              <button style={{ ...BTN_PRIMARY, fontSize: '0.78rem', padding: '0.25rem 0.6rem' }}
                                disabled={!!running} onClick={() => handleFoApprove(ev.id, true)}>FO Approve</button>
                              <button style={{ ...BTN_DANGER, fontSize: '0.78rem', padding: '0.25rem 0.6rem' }}
                                disabled={!!running} onClick={() => handleFoApprove(ev.id, false)}>FO Reject</button>
                            </div>
                          )}
                          {ev.workflow_status === 'FoValidated' && (
                            <div style={{ display: 'flex', gap: 6 }}>
                              <button style={{ ...BTN_PRIMARY, backgroundColor: '#15803d', fontSize: '0.78rem', padding: '0.25rem 0.6rem' }}
                                disabled={!!running} onClick={() => handleBoApprove(ev.id, true)}>BO Approve</button>
                              <button style={{ ...BTN_DANGER, fontSize: '0.78rem', padding: '0.25rem 0.6rem' }}
                                disabled={!!running} onClick={() => handleBoApprove(ev.id, false)}>BO Reject</button>
                            </div>
                          )}
                          {(ev.workflow_status === 'Done' || ev.workflow_status === 'Cancelled') && (
                            <span style={{ fontSize: '0.82rem', color: COLOR.textMuted }}>—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

    </PageLayout>
  )
}
