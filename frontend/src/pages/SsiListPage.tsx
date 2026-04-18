import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listSsis } from '../api/ssis'
import { PageLayout } from '../components/PageLayout'
import { Pagination } from '../components/Pagination'
import { CARD, COLOR, INPUT, TABLE, TD, TH } from '../styles/theme'
import type { Ssi } from '../types/ssi'

const LIMIT = 50

export function SsiListPage() {
  const navigate = useNavigate()
  const [items, setItems] = useState<Ssi[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(false)
  const [filterLei, setFilterLei] = useState('')
  const [filterExternal, setFilterExternal] = useState<string>('')
  const [applied, setApplied] = useState({ lei: '', external: '' })

  useEffect(() => {
    setLoading(true)
    const isExternal = applied.external === 'true' ? true : applied.external === 'false' ? false : undefined
    listSsis({ lei: applied.lei || undefined, is_external: isExternal, limit: LIMIT, offset })
      .then(r => { setItems(r.items); setTotal(r.total) })
      .finally(() => setLoading(false))
  }, [offset, applied])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setOffset(0)
    setApplied({ lei: filterLei, external: filterExternal })
  }

  return (
    <PageLayout title="Settlement Standing Instructions">
      <div style={{ ...CARD, marginBottom: '1rem' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: COLOR.textMuted, marginBottom: 2 }}>LEI</label>
            <input style={INPUT} value={filterLei} onChange={e => setFilterLei(e.target.value)} placeholder="Search LEI…" />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: COLOR.textMuted, marginBottom: 2 }}>Type</label>
            <select style={{ ...INPUT, minWidth: 130 }} value={filterExternal} onChange={e => setFilterExternal(e.target.value)}>
              <option value="">All</option>
              <option value="false">Internal</option>
              <option value="true">External</option>
            </select>
          </div>
          <button type="submit" style={{ padding: '0.4rem 1rem', background: COLOR.primary, color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: '0.875rem' }}>
            Search
          </button>
        </form>
      </div>

      <div style={CARD}>
        {loading ? (
          <p style={{ color: COLOR.textMuted }}>Loading…</p>
        ) : (
          <table style={TABLE}>
            <thead>
              <tr>
                <TH>LEI</TH>
                <TH>Currency</TH>
                <TH>BIC</TH>
                <TH>Account</TH>
                <TH>IBAN</TH>
                <TH>Type</TH>
                <TH>Updated</TH>
                <TH></TH>
              </tr>
            </thead>
            <tbody>
              {items.map(row => (
                <tr key={row.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <TD style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{row.lei}</TD>
                  <TD>{row.currency}</TD>
                  <TD style={{ fontFamily: 'monospace' }}>{row.bic}</TD>
                  <TD style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{row.account}</TD>
                  <TD style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: row.iban ? '#111' : COLOR.textMuted }}>
                    {row.iban ?? '—'}
                  </TD>
                  <TD>
                    <span style={{ padding: '2px 8px', borderRadius: 9999, fontSize: '0.75rem', background: row.is_external ? '#dbeafe' : '#d1fae5', color: row.is_external ? '#1e40af' : '#065f46' }}>
                      {row.is_external ? 'External' : 'Internal'}
                    </span>
                  </TD>
                  <TD style={{ fontSize: '0.8rem', color: COLOR.textMuted }}>{new Date(row.updated_at).toLocaleDateString()}</TD>
                  <TD>
                    {!row.is_external && (
                      <button
                        onClick={() => navigate(`/ssis/${row.id}`)}
                        style={{ fontSize: '0.8rem', padding: '2px 10px', border: '1px solid #d1d5db', borderRadius: 4, background: '#fff', cursor: 'pointer' }}
                      >
                        Edit
                      </button>
                    )}
                  </TD>
                </tr>
              ))}
              {items.length === 0 && (
                <tr><td colSpan={8} style={{ padding: '1rem', textAlign: 'center', color: COLOR.textMuted }}>No SSIs found</td></tr>
              )}
            </tbody>
          </table>
        )}
        <Pagination total={total} limit={LIMIT} offset={offset} onChange={setOffset} />
      </div>
    </PageLayout>
  )
}
