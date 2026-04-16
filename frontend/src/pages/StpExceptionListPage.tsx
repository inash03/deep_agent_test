import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listStpExceptions, startTriageForException, updateStpExceptionStatus } from '../api/stpExceptions'
import { PageLayout } from '../components/PageLayout'
import { Pagination } from '../components/Pagination'
import { CARD, COLOR, INPUT, TABLE, TD, TH } from '../styles/theme'
import type { StpException } from '../types/stpException'
import { EXCEPTION_STATUS_COLORS, EXCEPTION_STATUS_LABELS } from '../types/stpException'

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

export function StpExceptionListPage() {
  const navigate = useNavigate()
  const [items, setItems] = useState<StpException[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(false)
  const [triagingId, setTriagingId] = useState<string | null>(null)
  const [toastMsg, setToastMsg] = useState('')

  const [filterTradeId, setFilterTradeId] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [applied, setApplied] = useState({ tradeId: '', status: '' })

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

  const handleStartTriage = async (id: string) => {
    setTriagingId(id)
    try {
      const result = await startTriageForException(id)
      if (result.status === 'PENDING_APPROVAL') {
        showToast(`Triage started for ${result.trade_id} — PENDING_APPROVAL (run_id: ${result.run_id})`)
      } else {
        showToast(`Triage completed: ${result.status} — ${result.root_cause ?? ''}`)
      }
      load(offset)
    } catch {
      showToast('Failed to start triage.')
    } finally {
      setTriagingId(null)
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
                  {['Trade ID', 'Error Message', 'Status', 'Created', 'Actions'].map(h => (
                    <th key={h} style={TH}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr><td colSpan={5} style={{ ...TD, textAlign: 'center', color: COLOR.textMuted, padding: '2rem' }}>No exceptions found.</td></tr>
                ) : items.map(ex => (
                  <tr key={ex.id}>
                    <td style={{ ...TD, fontFamily: 'monospace', fontWeight: 600 }}>{ex.trade_id}</td>
                    <td style={{ ...TD, maxWidth: 320 }}>
                      <span title={ex.error_message} style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 300 }}>
                        {ex.error_message}
                      </span>
                    </td>
                    <td style={TD}><StatusBadge status={ex.status} /></td>
                    <td style={{ ...TD, fontSize: '0.8rem', color: COLOR.textMuted, whiteSpace: 'nowrap' }}>
                      {ex.created_at.slice(0, 10)}
                    </td>
                    <td style={{ ...TD, whiteSpace: 'nowrap' }}>
                      <div style={{ display: 'flex', gap: '0.4rem' }}>
                        {(ex.status === 'OPEN' || ex.status === 'IN_PROGRESS') && (
                          <button
                            onClick={() => handleStartTriage(ex.id)}
                            disabled={triagingId === ex.id}
                            style={{ padding: '0.25rem 0.65rem', backgroundColor: '#7c3aed', color: '#fff', border: 'none', borderRadius: 4, fontSize: '0.78rem', cursor: 'pointer', fontWeight: 600 }}
                          >
                            {triagingId === ex.id ? '…' : 'Triage'}
                          </button>
                        )}
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
    </PageLayout>
  )
}
