import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listTrades } from '../api/trades'
import { PageLayout } from '../components/PageLayout'
import { Pagination } from '../components/Pagination'
import { BTN_PRIMARY, CARD, COLOR, INPUT, TABLE, TD, TH } from '../styles/theme'
import type { Trade } from '../types/trade'
import { WORKFLOW_STATUS_COLORS, WORKFLOW_STATUS_LABELS } from '../types/trade'

const LIMIT = 20

const WORKFLOW_STATUSES = [
  'Initial', 'FoCheck', 'FoAgentToCheck', 'FoUserToValidate', 'FoValidated',
  'BoCheck', 'BoAgentToCheck', 'BoUserToValidate', 'BoValidated',
  'Done', 'Cancelled', 'EventPending',
]

const WORKFLOW_STATUS_ORDER: Record<string, number> = Object.fromEntries(
  WORKFLOW_STATUSES.map((s, i) => [s, i]),
)

type SortKey = 'workflow_status' | 'trade_id' | 'trade_date' | 'value_date' | 'amount' | 'version'
type SortDir = 'asc' | 'desc'
type SortSpec = { key: SortKey; dir: SortDir }

function compareText(a: string, b: string) {
  return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' })
}

function compareWorkflow(a: string, b: string) {
  const ai = WORKFLOW_STATUS_ORDER[a] ?? Number.POSITIVE_INFINITY
  const bi = WORKFLOW_STATUS_ORDER[b] ?? Number.POSITIVE_INFINITY
  return ai - bi
}

function compareBy(spec: SortSpec, a: Trade, b: Trade) {
  const mul = spec.dir === 'asc' ? 1 : -1
  switch (spec.key) {
    case 'workflow_status':
      return mul * compareWorkflow(a.workflow_status, b.workflow_status)
    case 'trade_id':
      return mul * compareText(a.trade_id, b.trade_id)
    case 'trade_date':
      return mul * compareText(a.trade_date ?? '', b.trade_date ?? '')
    case 'value_date':
      return mul * compareText(a.value_date ?? '', b.value_date ?? '')
    case 'amount':
      return mul * ((Number(a.amount) || 0) - (Number(b.amount) || 0))
    case 'version':
      return mul * ((Number(a.version) || 0) - (Number(b.version) || 0))
    default:
      return 0
  }
}

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

const SORTABLE_TH: React.CSSProperties = {
  userSelect: 'none',
  cursor: 'pointer',
  whiteSpace: 'nowrap',
}

function sortIndicator(active: boolean, dir: SortDir) {
  if (!active) return <span style={{ color: COLOR.textMuted, marginLeft: 6 }}>⇅</span>
  return <span style={{ color: COLOR.textMuted, marginLeft: 6 }}>{dir === 'asc' ? '▲' : '▼'}</span>
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
  const [filterWorkflow, setFilterWorkflow] = useState('')
  const [filterDate, setFilterDate] = useState('')
  const [applied, setApplied] = useState({ tradeId: '', workflow: '', date: '' })

  // Client-side (UI-only) filter/sort for the currently loaded page items.
  const [uiFilterTradeId, setUiFilterTradeId] = useState('')
  const [uiFilterWorkflow, setUiFilterWorkflow] = useState('')
  const [sortSpecs, setSortSpecs] = useState<SortSpec[]>([
    { key: 'workflow_status', dir: 'asc' },
    { key: 'trade_id', dir: 'desc' },
  ])

  const fetch = async (off = offset) => {
    setLoading(true)
    try {
      const res = await listTrades({
        trade_id: applied.tradeId || undefined,
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
    setApplied({ tradeId: filterTradeId, workflow: filterWorkflow, date: filterDate })
  }

  const handlePageChange = (off: number) => {
    setOffset(off)
    fetch(off)
  }

  const visibleItems = useMemo(() => {
    const tradeIdNeedle = uiFilterTradeId.trim().toLowerCase()
    const workflowNeedle = uiFilterWorkflow

    const filtered = items.filter(t => {
      if (tradeIdNeedle && !t.trade_id.toLowerCase().includes(tradeIdNeedle)) return false
      if (workflowNeedle && t.workflow_status !== workflowNeedle) return false
      return true
    })

    const withIndex = filtered.map((t, i) => ({ t, i }))
    withIndex.sort((x, y) => {
      for (const spec of sortSpecs) {
        const c = compareBy(spec, x.t, y.t)
        if (c !== 0) return c
      }
      return x.i - y.i
    })
    return withIndex.map(x => x.t)
  }, [items, sortSpecs, uiFilterTradeId, uiFilterWorkflow])

  const toggleSort = (key: SortKey) => {
    setSortSpecs(prev => {
      const existing = prev.find(s => s.key === key)
      const nextDir: SortDir = existing?.dir === 'asc' ? 'desc' : 'asc'

      // Keep a deterministic secondary sort.
      if (key === 'trade_id') return [{ key: 'trade_id', dir: nextDir }, { key: 'workflow_status', dir: 'asc' }]
      if (key === 'workflow_status') return [{ key: 'workflow_status', dir: nextDir }, { key: 'trade_id', dir: 'desc' }]

      return [{ key, dir: nextDir }, { key: 'trade_id', dir: 'desc' }]
    })
  }

  const primarySort = sortSpecs[0]

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
                  <th
                    style={{ ...STICKY_TRADE_ID_TH, ...SORTABLE_TH }}
                    onClick={() => toggleSort('trade_id')}
                    title="Sort"
                  >
                    Trade ID{sortIndicator(primarySort?.key === 'trade_id', primarySort?.key === 'trade_id' ? primarySort.dir : 'asc')}
                  </th>
                  <th
                    style={{ ...TH, ...SORTABLE_TH, textAlign: 'center' }}
                    onClick={() => toggleSort('version')}
                    title="Sort"
                  >
                    Ver{sortIndicator(primarySort?.key === 'version', primarySort?.key === 'version' ? primarySort.dir : 'asc')}
                  </th>
                  <th
                    style={{ ...TH, ...SORTABLE_TH }}
                    onClick={() => toggleSort('trade_date')}
                    title="Sort"
                  >
                    Trade Date{sortIndicator(primarySort?.key === 'trade_date', primarySort?.key === 'trade_date' ? primarySort.dir : 'asc')}
                  </th>
                  <th style={TH}>Counterparty LEI</th>
                  <th style={TH}>Instrument</th>
                  <th style={TH}>CCY</th>
                  <th
                    style={{ ...TH, ...SORTABLE_TH, textAlign: 'right' }}
                    onClick={() => toggleSort('amount')}
                    title="Sort"
                  >
                    Amount{sortIndicator(primarySort?.key === 'amount', primarySort?.key === 'amount' ? primarySort.dir : 'asc')}
                  </th>
                  <th
                    style={{ ...TH, ...SORTABLE_TH }}
                    onClick={() => toggleSort('value_date')}
                    title="Sort"
                  >
                    Value Date{sortIndicator(primarySort?.key === 'value_date', primarySort?.key === 'value_date' ? primarySort.dir : 'asc')}
                  </th>
                  <th
                    style={{ ...TH, ...SORTABLE_TH }}
                    onClick={() => toggleSort('workflow_status')}
                    title="Sort (requirements order)"
                  >
                    Workflow{sortIndicator(primarySort?.key === 'workflow_status', primarySort?.key === 'workflow_status' ? primarySort.dir : 'asc')}
                  </th>
                </tr>
                <tr>
                  <th style={STICKY_TRADE_ID_TH}>
                    <input
                      style={{ ...INPUT, width: '100%' }}
                      placeholder="Filter…"
                      value={uiFilterTradeId}
                      onChange={e => setUiFilterTradeId(e.target.value)}
                      onClick={e => e.stopPropagation()}
                    />
                  </th>
                  <th style={TH} />
                  <th style={TH} />
                  <th style={TH} />
                  <th style={TH} />
                  <th style={TH} />
                  <th style={TH} />
                  <th style={TH} />
                  <th style={TH}>
                    <select
                      style={{ ...INPUT, width: '100%' }}
                      value={uiFilterWorkflow}
                      onChange={e => setUiFilterWorkflow(e.target.value)}
                      onClick={e => e.stopPropagation()}
                    >
                      <option value="">All</option>
                      {WORKFLOW_STATUSES.map(s => (
                        <option key={s} value={s}>{WORKFLOW_STATUS_LABELS[s] ?? s}</option>
                      ))}
                    </select>
                  </th>
                </tr>
              </thead>
              <tbody>
                {visibleItems.length === 0 ? (
                  <tr><td colSpan={9} style={{ ...TD, textAlign: 'center', color: COLOR.textMuted, padding: '2rem' }}>No trades found.</td></tr>
                ) : visibleItems.map(t => (
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
