import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listTrades } from '../api/trades'
import { PageLayout } from '../components/PageLayout'
import { Pagination } from '../components/Pagination'
import { BTN_PRIMARY, CARD, COLOR, INPUT, TABLE, TD, TH } from '../styles/theme'
import type { Trade } from '../types/trade'
import { TRADE_STATUS_COLORS, TRADE_STATUS_LABELS, WORKFLOW_STATUS_COLORS, WORKFLOW_STATUS_LABELS } from '../types/trade'

const LIMIT = 20

const WORKFLOW_STATUSES = [
  'Initial', 'FoCheck', 'FoAgentToCheck', 'FoUserToValidate', 'FoValidated',
  'BoCheck', 'BoAgentToCheck', 'BoUserToValidate', 'BoValidated',
  'Done', 'Cancelled', 'EventPending',
]

const STICKY_TRADE_ID_TH: React.CSSProperties = {
  ...TH,
  position: 'sticky',
  left: 0,
  zIndex: 3,
  backgroundColor: COLOR.bgWhite,
  boxShadow: `2px 0 0 ${COLOR.border}`,
}

const STICKY_TRADE_ID_TD: React.CSSProperties = {
  ...TD,
  position: 'sticky',
  left: 0,
  zIndex: 2,
  backgroundColor: COLOR.bgWhite,
  boxShadow: `2px 0 0 ${COLOR.border}`,
}

function Badge({ label, style }: { label: string; style: React.CSSProperties }) {
  return (
    <span style={{
      display: 'inline-block', padding: '2px 10px', borderRadius: 9999,
      fontSize: '0.78rem', fontWeight: 600, ...style,
    }}>{label}</span>
  )
}

export function TradeListPage() {
  const navigate = useNavigate()
  const [items, setItems] = useState<Trade[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(false)

  const [filterTradeId, setFilterTradeId] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterWorkflow, setFilterWorkflow] = useState('')
  const [filterDate, setFilterDate] = useState('')
  const [applied, setApplied] = useState({ tradeId: '', status: '', workflow: '', date: '' })

  const fetch = async (off = offset) => {
    setLoading(true)
    try {
      const res = await listTrades({
        trade_id: applied.tradeId || undefined,
        stp_status: applied.status || undefined,
        workflow_status: applied.workflow || undefined,
        trade_date: applied.date || undefined,
        limit: LIMIT,
        offset: off,
      })
      setItems(res.items)
      setTotal(res.total)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetch(0) }, [applied]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearch = () => {
    setOffset(0)
    setApplied({ tradeId: filterTradeId, status: filterStatus, workflow: filterWorkflow, date: filterDate })
  }

  const handlePageChange = (off: number) => {
    setOffset(off)
    fetch(off)
  }

  return (
    <PageLayout
      title="Trades"
      action={
        <button style={BTN_PRIMARY} onClick={() => navigate('/trades/new')}>+ New Trade</button>
      }
    >
      {/* Search bar */}
      <div style={{ ...CARD, marginBottom: '1rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div style={{ flex: '1 1 140px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: COLOR.textMuted, marginBottom: 4 }}>Trade ID</label>
          <input style={INPUT} placeholder="TRD-001" value={filterTradeId} onChange={e => setFilterTradeId(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()} />
        </div>
        <div style={{ flex: '1 1 140px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: COLOR.textMuted, marginBottom: 4 }}>STP Status</label>
          <select style={{ ...INPUT }} value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
            <option value="">All</option>
            <option value="NEW">New</option>
            <option value="STP_PASSED">STP Passed</option>
            <option value="STP_FAILED">STP Failed</option>
            <option value="SETTLED">Settled</option>
          </select>
        </div>
        <div style={{ flex: '1 1 160px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: COLOR.textMuted, marginBottom: 4 }}>Workflow Status</label>
          <select style={{ ...INPUT }} value={filterWorkflow} onChange={e => setFilterWorkflow(e.target.value)}>
            <option value="">All</option>
            {WORKFLOW_STATUSES.map(s => (
              <option key={s} value={s}>{WORKFLOW_STATUS_LABELS[s] ?? s}</option>
            ))}
          </select>
        </div>
        <div style={{ flex: '1 1 140px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: COLOR.textMuted, marginBottom: 4 }}>Trade Date</label>
          <input type="date" style={INPUT} value={filterDate} onChange={e => setFilterDate(e.target.value)} />
        </div>
        <button
          onClick={handleSearch}
          style={{ padding: '0.45rem 1.25rem', backgroundColor: COLOR.primary, color: '#fff', border: 'none', borderRadius: 6, fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap' }}
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
                  {['Trade ID', 'Ver', 'Trade Date', 'Counterparty LEI', 'Instrument', 'CCY', 'Amount', 'Value Date', 'Workflow', 'STP'].map((h, index) => (
                    <th key={h} style={index === 0 ? STICKY_TRADE_ID_TH : TH}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr><td colSpan={10} style={{ ...TD, textAlign: 'center', color: COLOR.textMuted, padding: '2rem' }}>No trades found.</td></tr>
                ) : items.map(t => (
                  <tr
                    key={t.trade_id}
                    onClick={() => navigate(`/trades/${t.trade_id}`)}
                    style={{ cursor: 'pointer' }}
                    onMouseEnter={e => (e.currentTarget.style.backgroundColor = '#f8fafc')}
                    onMouseLeave={e => (e.currentTarget.style.backgroundColor = '')}
                  >
                    <td style={{ ...STICKY_TRADE_ID_TD, fontWeight: 600, fontFamily: 'monospace' }}>{t.trade_id}</td>
                    <td style={{ ...TD, textAlign: 'center', color: COLOR.textMuted, fontSize: '0.82rem' }}>v{t.version}</td>
                    <td style={TD}>{t.trade_date}</td>
                    <td style={{ ...TD, fontFamily: 'monospace', fontSize: '0.8rem' }}>{t.counterparty_lei}</td>
                    <td style={TD}>{t.instrument_id}</td>
                    <td style={TD}>{t.currency}</td>
                    <td style={{ ...TD, textAlign: 'right', fontFamily: 'monospace' }}>
                      {Number(t.amount).toLocaleString()}
                    </td>
                    <td style={TD}>{t.value_date}</td>
                    <td style={TD}>
                      <Badge
                        label={WORKFLOW_STATUS_LABELS[t.workflow_status] ?? t.workflow_status}
                        style={WORKFLOW_STATUS_COLORS[t.workflow_status] ?? {}}
                      />
                    </td>
                    <td style={TD}>
                      <Badge
                        label={TRADE_STATUS_LABELS[t.stp_status] ?? t.stp_status}
                        style={TRADE_STATUS_COLORS[t.stp_status] ?? {}}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination total={total} limit={LIMIT} offset={offset} onChange={handlePageChange} />
      </div>
    </PageLayout>
  )
}
