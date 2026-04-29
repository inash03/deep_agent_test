import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listCounterparties } from '../api/counterparties'
import { PageLayout } from '../components/PageLayout'
import { Pagination } from '../components/Pagination'
import { CARD, COLOR, INPUT, TABLE, TD, TH } from '../styles/theme'
import type { Counterparty } from '../types/counterparty'

const LIMIT = 20

export function CounterpartyListPage() {
  const navigate = useNavigate()
  const [items, setItems] = useState<Counterparty[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(false)

  const [filterLei, setFilterLei] = useState('')
  const [filterName, setFilterName] = useState('')
  const [applied, setApplied] = useState({ lei: '', name: '' })

  const fetch = async (off = offset) => {
    setLoading(true)
    try {
      const res = await listCounterparties({ lei: applied.lei || undefined, name: applied.name || undefined, limit: LIMIT, offset: off })
      setItems(res.items)
      setTotal(res.total)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetch(0) }, [applied]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearch = () => {
    setOffset(0)
    setApplied({ lei: filterLei, name: filterName })
  }

  const goToCounterparty = (lei: string) => navigate(`/counterparties/${lei}`)

  return (
    <PageLayout title="Counterparties">
      <div style={{ ...CARD, marginBottom: '1rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div style={{ flex: '1 1 200px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: COLOR.textMuted, marginBottom: 4 }}>LEI</label>
          <input style={INPUT} placeholder="213800..." value={filterLei} onChange={e => setFilterLei(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()} />
        </div>
        <div style={{ flex: '1 1 200px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: COLOR.textMuted, marginBottom: 4 }}>Name</label>
          <input style={INPUT} placeholder="Acme..." value={filterName} onChange={e => setFilterName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()} />
        </div>
        <button
          onClick={handleSearch}
          style={{ padding: '0.45rem 1.25rem', backgroundColor: COLOR.primary, color: '#fff', border: 'none', borderRadius: 6, fontWeight: 600, cursor: 'pointer' }}
        >
          Search
        </button>
      </div>

      <div style={CARD}>
        {loading ? (
          <p style={{ color: COLOR.textMuted, textAlign: 'center', padding: '2rem' }}>Loading…</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={TABLE}>
              <thead>
                <tr>
                  {['LEI', 'Name', 'BIC', 'Active'].map(h => (
                    <th key={h} style={TH}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr><td colSpan={4} style={{ ...TD, textAlign: 'center', color: COLOR.textMuted, padding: '2rem' }}>No counterparties found.</td></tr>
                ) : items.map(cp => (
                  <tr
                    key={cp.lei}
                    onClick={() => goToCounterparty(cp.lei)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        goToCounterparty(cp.lei)
                      }
                    }}
                    tabIndex={0}
                    style={{ cursor: 'pointer' }}
                  >
                    <td style={{ ...TD, fontFamily: 'monospace', fontSize: '0.8rem' }}>{cp.lei}</td>
                    <td style={{ ...TD, fontWeight: 500 }}>{cp.name}</td>
                    <td style={{ ...TD, fontFamily: 'monospace' }}>{cp.bic}</td>
                    <td style={TD}>
                      <span style={{
                        display: 'inline-block', padding: '2px 8px', borderRadius: 9999, fontSize: '0.78rem', fontWeight: 600,
                        ...(cp.is_active
                          ? { backgroundColor: '#d1fae5', color: '#065f46', border: '1px solid #6ee7b7' }
                          : { backgroundColor: '#fee2e2', color: '#991b1b', border: '1px solid #fca5a5' }),
                      }}>
                        {cp.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination total={total} limit={LIMIT} offset={offset} onChange={(off) => { setOffset(off); fetch(off) }} />
      </div>
    </PageLayout>
  )
}
