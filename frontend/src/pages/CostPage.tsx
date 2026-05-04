import { useEffect, useState } from 'react'
import { getCostSummary, listCostLogs } from '../api/cost'
import { PageLayout } from '../components/PageLayout'
import { CARD, COLOR, TABLE, TD, TH } from '../styles/theme'
import type { CostSummary, LlmCostLog } from '../types/cost'

const MODEL_SHORT: Record<string, string> = {
  'claude-sonnet-4-6': 'Sonnet 4.6',
  'claude-haiku-4-5-20251001': 'Haiku 4.5',
  'text-embedding-3-small': 'Embed 3-small',
}

function agentColor(agentType: string): string {
  if (agentType === 'fo') return '#2563eb'
  if (agentType === 'bo') return '#16a34a'
  if (agentType === 'rag') return '#9333ea'
  return '#6b7280'
}

function fmt(usd: number): string {
  return usd < 0.000001 ? '$0.000000' : `$${usd.toFixed(6)}`
}

function fmtTokens(n: number): string {
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n)
}

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div style={{ ...CARD, flex: '1 1 180px', minWidth: 160 }}>
      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: COLOR.textMuted, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>
        {label}
      </div>
      <div style={{ fontSize: '1.5rem', fontWeight: 700, color: COLOR.text }}>{value}</div>
      {sub && <div style={{ fontSize: '0.75rem', color: COLOR.textMuted, marginTop: '0.25rem' }}>{sub}</div>}
    </div>
  )
}

export function CostPage() {
  const [summary, setSummary] = useState<CostSummary | null>(null)
  const [logs, setLogs] = useState<LlmCostLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getCostSummary(30), listCostLogs(100)])
      .then(([s, l]) => {
        setSummary(s)
        setLogs(l.items)
      })
      .catch(() => setError('Failed to load cost data.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <PageLayout title="LLM Cost"><p style={{ color: COLOR.textMuted }}>Loading…</p></PageLayout>
  if (error || !summary) return <PageLayout title="LLM Cost"><p style={{ color: COLOR.danger }}>{error || 'No data'}</p></PageLayout>

  const avgCost = summary.total_runs > 0 ? summary.total_cost_usd / summary.total_runs : 0

  return (
    <PageLayout title="LLM Cost">
      {/* ── Summary cards ── */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
        <StatCard label="Total Cost" value={fmt(summary.total_cost_usd)} />
        <StatCard label="Total Runs" value={String(summary.total_runs)} sub={`${summary.total_calls} LLM calls`} />
        <StatCard label="Avg / Run" value={fmt(avgCost)} />
        <StatCard label="Input Tokens" value={fmtTokens(summary.total_input_tokens)} />
        <StatCard label="Output Tokens" value={fmtTokens(summary.total_output_tokens)} />
      </div>

      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
        {/* ── By agent ── */}
        <div style={{ ...CARD, flex: '1 1 260px' }}>
          <h3 style={{ margin: '0 0 0.75rem', fontSize: '0.9rem', color: COLOR.text }}>By Agent</h3>
          <table style={TABLE}>
            <thead>
              <tr>
                <th style={TH}>Agent</th>
                <th style={{ ...TH, textAlign: 'right' }}>Runs</th>
                <th style={{ ...TH, textAlign: 'right' }}>Calls</th>
                <th style={{ ...TH, textAlign: 'right' }}>Cost</th>
              </tr>
            </thead>
            <tbody>
              {summary.by_agent.length === 0 && (
                <tr><td colSpan={4} style={{ ...TD, color: COLOR.textMuted }}>No data</td></tr>
              )}
              {summary.by_agent.map(a => (
                <tr key={a.agent_type}>
                  <td style={TD}><span style={{ fontWeight: 600, textTransform: 'uppercase', color: agentColor(a.agent_type) }}>{a.agent_type}</span></td>
                  <td style={{ ...TD, textAlign: 'right' }}>{a.run_count}</td>
                  <td style={{ ...TD, textAlign: 'right' }}>{a.call_count}</td>
                  <td style={{ ...TD, textAlign: 'right', fontFamily: 'monospace' }}>{fmt(a.cost_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* ── By model ── */}
        <div style={{ ...CARD, flex: '1 1 260px' }}>
          <h3 style={{ margin: '0 0 0.75rem', fontSize: '0.9rem', color: COLOR.text }}>By Model</h3>
          <table style={TABLE}>
            <thead>
              <tr>
                <th style={TH}>Model</th>
                <th style={{ ...TH, textAlign: 'right' }}>Calls</th>
                <th style={{ ...TH, textAlign: 'right' }}>Cost</th>
              </tr>
            </thead>
            <tbody>
              {summary.by_model.length === 0 && (
                <tr><td colSpan={3} style={{ ...TD, color: COLOR.textMuted }}>No data</td></tr>
              )}
              {summary.by_model.map(m => (
                <tr key={m.model}>
                  <td style={TD}>{MODEL_SHORT[m.model] ?? m.model}</td>
                  <td style={{ ...TD, textAlign: 'right' }}>{m.call_count}</td>
                  <td style={{ ...TD, textAlign: 'right', fontFamily: 'monospace' }}>{fmt(m.cost_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* ── Daily breakdown ── */}
        <div style={{ ...CARD, flex: '2 1 340px' }}>
          <h3 style={{ margin: '0 0 0.75rem', fontSize: '0.9rem', color: COLOR.text }}>Daily Cost (last 30 days)</h3>
          {summary.daily_costs.length === 0 ? (
            <p style={{ color: COLOR.textMuted, fontSize: '0.875rem' }}>No data yet.</p>
          ) : (
            <table style={TABLE}>
              <thead>
                <tr>
                  <th style={TH}>Date</th>
                  <th style={{ ...TH, textAlign: 'right' }}>Runs</th>
                  <th style={{ ...TH, textAlign: 'right' }}>Calls</th>
                  <th style={{ ...TH, textAlign: 'right' }}>Cost</th>
                </tr>
              </thead>
              <tbody>
                {summary.daily_costs.map(d => (
                  <tr key={d.date}>
                    <td style={TD}>{d.date}</td>
                    <td style={{ ...TD, textAlign: 'right' }}>{d.run_count}</td>
                    <td style={{ ...TD, textAlign: 'right' }}>{d.call_count}</td>
                    <td style={{ ...TD, textAlign: 'right', fontFamily: 'monospace' }}>{fmt(d.cost_usd)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* ── Recent log entries ── */}
      <div style={CARD}>
        <h3 style={{ margin: '0 0 0.75rem', fontSize: '0.9rem', color: COLOR.text }}>Recent LLM Calls (latest 100)</h3>
        {logs.length === 0 ? (
          <p style={{ color: COLOR.textMuted, fontSize: '0.875rem' }}>No cost logs recorded yet. Logs are saved when FO/BO triage runs complete.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={TABLE}>
              <thead>
                <tr>
                  <th style={TH}>Time</th>
                  <th style={TH}>Trade</th>
                  <th style={TH}>Agent</th>
                  <th style={TH}>Node</th>
                  <th style={TH}>Model</th>
                  <th style={{ ...TH, textAlign: 'right' }}>In</th>
                  <th style={{ ...TH, textAlign: 'right' }}>Out</th>
                  <th style={{ ...TH, textAlign: 'right' }}>Cost</th>
                </tr>
              </thead>
              <tbody>
                {logs.map(l => (
                  <tr key={l.id}>
                    <td style={{ ...TD, whiteSpace: 'nowrap', fontSize: '0.8rem', color: COLOR.textMuted }}>
                      {new Date(l.created_at).toLocaleString()}
                    </td>
                    <td style={TD}>{l.trade_id ?? '—'}</td>
                    <td style={TD}>
                      <span style={{ fontWeight: 600, textTransform: 'uppercase', color: agentColor(l.agent_type) }}>
                        {l.agent_type}
                      </span>
                    </td>
                    <td style={{ ...TD, fontSize: '0.8rem', color: COLOR.textMuted }}>{l.node}</td>
                    <td style={TD}>{MODEL_SHORT[l.model] ?? l.model}</td>
                    <td style={{ ...TD, textAlign: 'right' }}>{fmtTokens(l.input_tokens)}</td>
                    <td style={{ ...TD, textAlign: 'right', color: l.agent_type === 'rag' ? COLOR.textMuted : undefined }}>
                      {l.agent_type === 'rag' ? '—' : fmtTokens(l.output_tokens)}
                    </td>
                    <td style={{ ...TD, textAlign: 'right', fontFamily: 'monospace', fontWeight: 600 }}>{fmt(l.cost_usd)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </PageLayout>
  )
}
