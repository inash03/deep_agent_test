import { useEffect, useState } from 'react'
import { listTrades } from '../api/trades'
import { PageLayout } from '../components/PageLayout'
import { Pagination } from '../components/Pagination'
import { CARD, COLOR, INPUT, TABLE, TD, TH } from '../styles/theme'
import type { Trade } from '../types/trade'
import { TRADE_STATUS_COLORS, TRADE_STATUS_LABELS } from '../types/trade'

const LIMIT = 20

function StatusBadge({ status }: { status: string }) {
  const style = TRADE_STATUS_COLORS[status] ?? {}
  return (
    <span style={{
      display: 'inline-block', padding: '2px 10px', borderRadius: 9999,
      fontSize: '0.78rem', fontWeight: 600, ...style,
    }}>
      {TRADE_STATUS_LABELS[status] ?? status}
    </span>
  )
}

export function TradeListPage() {
  const [items, setItems] = useState<Trade[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(false)

  const [filterTradeId, setFilterTradeId] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterDate, setFilterDate] = useState('')
  const [applied, setApplied] = useState({ tradeId: '', status: '', date: '' })

  const fetch = async (off = offset) => {
    setLoading(true)
    try {
      const res = await listTrades({
        trade_id: applied.tradeId || undefined,
        stp_status: applied.status || undefined,
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
    setApplied({ tradeId: filterTradeId, status: filterStatus, date: filterDate })
  }

  const handlePageChange = (off: number) => {
    setOffset(off)
    fetch(off)
  }

  return (
    <PageLayout title="Trades">
      {/* Search bar */}
      <div style={{ ...CARD, marginBottom: '1rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div style={{ flex: '1 1 160px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: COLOR.textMuted, marginBottom: 4 }}>
            Trade ID
          </label>
          <input style={INPUT} placeholder="TRD-001" value={filterTradeId} onChange={e => setFilterTradeId(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()} />
        </div>
        <div style={{ flex: '1 1 160px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: COLOR.textMuted, marginBottom: 4 }}>
            STP Status
          </label>
          <select style={{ ...INPUT }} value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
            <option value="">All</option>
            <option value="NEW">New</option>
            <option value="STP_PASSED">STP Passed</option>
            <option value="STP_FAILED">STP Failed</option>
            <option value="SETTLED">Settled</option>
          </select>
        </div>
        <div style={{ flex: '1 1 160px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: COLOR.textMuted, marginBottom: 4 }}>
            Trade Date
          </label>
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
                  {['Trade ID', 'Trade Date', 'Counterparty LEI', 'Instrument', 'CCY', 'Amount', 'Value Date', 'STP Status'].map(h => (
                    <th key={h} style={TH}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr><td colSpan={8} style={{ ...TD, textAlign: 'center', color: COLOR.textMuted, padding: '2rem' }}>No trades found.</td></tr>
                ) : items.map(t => (
                  <tr key={t.trade_id}>
                    <td style={{ ...TD, fontWeight: 600, fontFamily: 'monospace' }}>{t.trade_id}</td>
                    <td style={TD}>{t.trade_date}</td>
                    <td style={{ ...TD, fontFamily: 'monospace', fontSize: '0.8rem' }}>{t.counterparty_lei}</td>
                    <td style={TD}>{t.instrument_id}</td>
                    <td style={TD}>{t.currency}</td>
                    <td style={{ ...TD, textAlign: 'right', fontFamily: 'monospace' }}>
                      {Number(t.amount).toLocaleString()}
                    </td>
                    <td style={TD}>{t.value_date}</td>
                    <td style={TD}><StatusBadge status={t.stp_status} /></td>
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
