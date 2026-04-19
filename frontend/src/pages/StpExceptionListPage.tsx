import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listStpExceptions, updateStpExceptionStatus } from '../api/stpExceptions'
import { getTrade } from '../api/trades'
import { PageLayout } from '../components/PageLayout'
import { Pagination } from '../components/Pagination'
import { CARD, COLOR, INPUT, TABLE, TD, TH } from '../styles/theme'
import type { StpException } from '../types/stpException'
import { EXCEPTION_STATUS_COLORS, EXCEPTION_STATUS_LABELS } from '../types/stpException'
import type { Trade } from '../types/trade'

const LIMIT = 20

function StatusBadge({ status }: { status: string }) {
  const style = EXCEPTION_STATUS_COLORS[status] ?? {}
  return (
    <span style={{
      display: 'inline-block', padding: '2px 10px', borderRadius: 9999,
      fontSize: '0.78rem', fontWeight: 600, ...style,
    }}>
      {EXCEPTION_STATUS_LABELS[status] ?? status}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Violations modal
// ---------------------------------------------------------------------------

function ViolationsModal({
  ex,
  trade,
  loading,
  onClose,
}: {
  ex: StpException
  trade: Trade | null
  loading: boolean
  onClose: () => void
}) {
  const navigate = useNavigate()

  const foFailed = (trade?.fo_check_results ?? []).filter(r => !r.passed)
  const boFailed = (trade?.bo_check_results ?? []).filter(r => !r.passed)
  const hasAnyChecks =
    (trade?.fo_check_results ?? []).length > 0 ||
    (trade?.bo_check_results ?? []).length > 0

  return (
    <div
      style={{
        position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.45)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: '#fff', borderRadius: 10, padding: '1.5rem',
          width: 580, maxWidth: '90vw', maxHeight: '80vh', overflowY: 'auto',
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700 }}>Check Violations</h3>
            <span style={{ fontFamily: 'monospace', fontSize: '0.85rem', color: COLOR.textMuted }}>
              {ex.trade_id}
            </span>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', fontSize: '1.4rem', cursor: 'pointer', color: COLOR.textMuted, lineHeight: 1, padding: '0 4px' }}
          >
            ×
          </button>
        </div>

        {/* Body */}
        {loading ? (
          <p style={{ color: COLOR.textMuted, textAlign: 'center', padding: '2rem 0' }}>Loading…</p>
        ) : !hasAnyChecks ? (
          <div>
            <p style={{ fontSize: '0.875rem', color: COLOR.textMuted, marginBottom: '0.75rem' }}>
              FO/BO チェックはまだ実行されていません。
            </p>
            <p style={{ fontSize: '0.8rem', fontWeight: 700, marginBottom: 4, color: '#374151' }}>
              元の STP エラーメッセージ:
            </p>
            <pre style={{
              fontFamily: 'monospace', fontSize: '0.78rem',
              backgroundColor: '#fef2f2', padding: '0.75rem', borderRadius: 4,
              color: '#991b1b', whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0,
            }}>
              {ex.error_message}
            </pre>
          </div>
        ) : (
          <>
            {foFailed.length > 0 ? (
              <section style={{ marginBottom: '1rem' }}>
                <p style={{ fontWeight: 700, fontSize: '0.82rem', color: '#1e40af', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  FO Check Failures ({foFailed.length})
                </p>
                {foFailed.map(r => (
                  <div key={r.rule_name} style={{
                    padding: '0.5rem 0.75rem', backgroundColor: '#eff6ff',
                    borderLeft: '3px solid #3b82f6', borderRadius: '0 4px 4px 0', marginBottom: 4,
                  }}>
                    <span style={{ fontWeight: 600, fontSize: '0.8rem', color: '#1e40af' }}>{r.rule_name}</span>
                    <span style={{ fontSize: '0.8rem', color: '#374151', marginLeft: 8 }}>{r.message}</span>
                  </div>
                ))}
              </section>
            ) : (
              <p style={{ fontSize: '0.8rem', color: '#15803d', marginBottom: '0.75rem' }}>
                ✓ FO Check: violations なし
              </p>
            )}

            {boFailed.length > 0 ? (
              <section>
                <p style={{ fontWeight: 700, fontSize: '0.82rem', color: '#065f46', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  BO Check Failures ({boFailed.length})
                </p>
                {boFailed.map(r => (
                  <div key={r.rule_name} style={{
                    padding: '0.5rem 0.75rem', backgroundColor: '#f0fdf4',
                    borderLeft: '3px solid #22c55e', borderRadius: '0 4px 4px 0', marginBottom: 4,
                  }}>
                    <span style={{ fontWeight: 600, fontSize: '0.8rem', color: '#065f46' }}>{r.rule_name}</span>
                    <span style={{ fontSize: '0.8rem', color: '#374151', marginLeft: 8 }}>{r.message}</span>
                  </div>
                ))}
              </section>
            ) : (
              <p style={{ fontSize: '0.8rem', color: '#15803d' }}>
                ✓ BO Check: violations なし
              </p>
            )}
          </>
        )}

        {/* Footer */}
        <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
          <button
            onClick={onClose}
            style={{ padding: '0.4rem 0.9rem', border: `1px solid ${COLOR.border}`, borderRadius: 6, cursor: 'pointer', background: '#fff', fontSize: '0.875rem' }}
          >
            Close
          </button>
          <button
            onClick={() => { onClose(); navigate(`/trades/${ex.trade_id}`) }}
            style={{ padding: '0.4rem 1rem', backgroundColor: COLOR.primary, color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: '0.875rem', fontWeight: 600 }}
          >
            Open Trade Detail →
          </button>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export function StpExceptionListPage() {
  const navigate = useNavigate()
  const [items, setItems] = useState<StpException[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(false)
  const [toastMsg, setToastMsg] = useState('')

  const [filterTradeId, setFilterTradeId] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [applied, setApplied] = useState({ tradeId: '', status: '' })

  // Violations modal
  const [selectedEx, setSelectedEx] = useState<StpException | null>(null)
  const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null)
  const [loadingViolations, setLoadingViolations] = useState(false)

  const load = async (off = offset) => {
    setLoading(true)
    try {
      const res = await listStpExceptions({
        trade_id: applied.tradeId || undefined,
        status: applied.status || undefined,
        limit: LIMIT,
        offset: off,
      })
      setItems(res.items)
      setTotal(res.total)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(0) }, [applied]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearch = () => {
    setOffset(0)
    setApplied({ tradeId: filterTradeId, status: filterStatus })
  }

  const showToast = (msg: string) => {
    setToastMsg(msg)
    setTimeout(() => setToastMsg(''), 3500)
  }

  const handleViewViolations = async (ex: StpException) => {
    setSelectedEx(ex)
    setSelectedTrade(null)
    setLoadingViolations(true)
    try {
      const trade = await getTrade(ex.trade_id)
      setSelectedTrade(trade)
    } catch {
      // trade not found — modal will show fallback error_message
    } finally {
      setLoadingViolations(false)
    }
  }

  const handleClose = async (id: string) => {
    try {
      await updateStpExceptionStatus(id, 'CLOSED')
      load(offset)
    } catch {
      showToast('Failed to close exception.')
    }
  }

  return (
    <PageLayout
      title="STP Exceptions"
      action={
        <button
          onClick={() => navigate('/stp-exceptions/new')}
          style={{ padding: '0.45rem 1.1rem', backgroundColor: COLOR.primary, color: '#fff', border: 'none', borderRadius: 6, fontWeight: 600, cursor: 'pointer' }}
        >
          + New Exception
        </button>
      }
    >
      {toastMsg && (
        <div style={{ backgroundColor: '#d1fae5', color: '#065f46', padding: '0.75rem 1rem', borderRadius: 6, marginBottom: '1rem', fontSize: '0.875rem' }}>
          {toastMsg}
        </div>
      )}

      {/* Filters */}
      <div style={{ ...CARD, marginBottom: '1rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div style={{ flex: '1 1 180px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: COLOR.textMuted, marginBottom: 4 }}>Trade ID</label>
          <input style={INPUT} placeholder="TRD-001" value={filterTradeId} onChange={e => setFilterTradeId(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()} />
        </div>
        <div style={{ flex: '1 1 180px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: COLOR.textMuted, marginBottom: 4 }}>Status</label>
          <select style={INPUT} value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
            <option value="">All</option>
            <option value="OPEN">Open</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
          </select>
        </div>
        <button
          onClick={handleSearch}
          style={{ padding: '0.45rem 1.25rem', backgroundColor: COLOR.primary, color: '#fff', border: 'none', borderRadius: 6, fontWeight: 600, cursor: 'pointer' }}
        >
          Search
        </button>
      </div>

      {/* Table */}
      <div style={CARD}>
        {loading ? (
          <p style={{ color: COLOR.textMuted, textAlign: 'center', padding: '2rem' }}>Loading…</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={TABLE}>
              <thead>
                <tr>
                  {['Trade ID', 'Check Violations', 'Status', 'Created', 'Actions'].map(h => (
                    <th key={h} style={TH}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr><td colSpan={5} style={{ ...TD, textAlign: 'center', color: COLOR.textMuted, padding: '2rem' }}>No exceptions found.</td></tr>
                ) : items.map(ex => (
                  <tr key={ex.id}>
                    <td
                      style={{ ...TD, fontFamily: 'monospace', fontWeight: 600, cursor: 'pointer', color: COLOR.primary }}
                      onClick={() => navigate(`/trades/${ex.trade_id}`)}
                    >
                      {ex.trade_id}
                    </td>
                    <td style={TD}>
                      <button
                        onClick={() => handleViewViolations(ex)}
                        style={{
                          padding: '0.22rem 0.7rem', backgroundColor: '#f3f4f6',
                          border: `1px solid ${COLOR.border}`, borderRadius: 4,
                          fontSize: '0.78rem', cursor: 'pointer', fontWeight: 600, color: '#374151',
                        }}
                      >
                        View Violations
                      </button>
                    </td>
                    <td style={TD}><StatusBadge status={ex.status} /></td>
                    <td style={{ ...TD, fontSize: '0.8rem', color: COLOR.textMuted, whiteSpace: 'nowrap' }}>
                      {ex.created_at.slice(0, 10)}
                    </td>
                    <td style={{ ...TD, whiteSpace: 'nowrap' }}>
                      <div style={{ display: 'flex', gap: '0.4rem' }}>
                        <button
                          onClick={() => navigate(`/trades/${ex.trade_id}`)}
                          style={{ padding: '0.25rem 0.65rem', backgroundColor: COLOR.primary, color: '#fff', border: 'none', borderRadius: 4, fontSize: '0.78rem', cursor: 'pointer', fontWeight: 600 }}
                        >
                          Open Trade
                        </button>
                        {ex.status !== 'CLOSED' && (
                          <button
                            onClick={() => handleClose(ex.id)}
                            style={{ padding: '0.25rem 0.65rem', backgroundColor: '#6b7280', color: '#fff', border: 'none', borderRadius: 4, fontSize: '0.78rem', cursor: 'pointer', fontWeight: 600 }}
                          >
                            Close
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination total={total} limit={LIMIT} offset={offset} onChange={(off) => { setOffset(off); load(off) }} />
      </div>

      {/* Violations modal */}
      {selectedEx && (
        <ViolationsModal
          ex={selectedEx}
          trade={selectedTrade}
          loading={loadingViolations}
          onClose={() => setSelectedEx(null)}
        />
      )}
    </PageLayout>
  )
}
