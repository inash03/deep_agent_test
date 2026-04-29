import { useEffect, useState } from 'react'
import { listRules } from '../api/rules'
import { PageLayout } from '../components/PageLayout'
import { CARD, COLOR, TABLE, TD, TH } from '../styles/theme'
import type { Rule, RuleListResponse } from '../types/rule'

const SEVERITY_STYLE: Record<string, React.CSSProperties> = {
  error: {
    display: 'inline-block',
    padding: '0.15rem 0.55rem',
    borderRadius: 4,
    fontSize: '0.75rem',
    fontWeight: 600,
    backgroundColor: '#fee2e2',
    color: '#991b1b',
  },
  warning: {
    display: 'inline-block',
    padding: '0.15rem 0.55rem',
    borderRadius: 4,
    fontSize: '0.75rem',
    fontWeight: 600,
    backgroundColor: '#fef3c7',
    color: '#92400e',
  },
}

const STUB_BADGE: React.CSSProperties = {
  display: 'inline-block',
  padding: '0.15rem 0.55rem',
  borderRadius: 4,
  fontSize: '0.72rem',
  fontWeight: 600,
  backgroundColor: '#f1f5f9',
  color: '#64748b',
  marginLeft: '0.4rem',
}

function RuleTable({ rules, caption }: { rules: Rule[]; caption: string }) {
  return (
    <div style={{ ...CARD, marginBottom: '1.5rem' }}>
      <h2 style={{ fontSize: '1rem', fontWeight: 700, color: COLOR.text, marginTop: 0, marginBottom: '1rem' }}>
        {caption}
        <span style={{ marginLeft: '0.5rem', fontSize: '0.85rem', fontWeight: 400, color: COLOR.textMuted }}>
          ({rules.length} ルール)
        </span>
      </h2>
      <div style={{ overflowX: 'auto' }}>
        <table style={TABLE}>
          <thead>
            <tr>
              <th style={{ ...TH, width: '22%' }}>ルール名</th>
              <th style={{ ...TH, width: '10%' }}>重要度</th>
              <th style={TH}>チェック内容</th>
            </tr>
          </thead>
          <tbody>
            {rules.map(rule => (
              <tr key={rule.rule_name} style={{ backgroundColor: rule.is_stub ? '#f8fafc' : 'transparent' }}>
                <td style={TD}>
                  <span style={{ fontFamily: 'monospace', fontSize: '0.82rem', color: COLOR.text }}>
                    {rule.rule_name}
                  </span>
                  {rule.is_stub && <span style={STUB_BADGE}>stub</span>}
                </td>
                <td style={TD}>
                  <span style={SEVERITY_STYLE[rule.severity] ?? SEVERITY_STYLE.error}>
                    {rule.severity}
                  </span>
                </td>
                <td style={{ ...TD, color: COLOR.textMuted, fontSize: '0.875rem' }}>
                  {rule.description}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export function RuleListPage() {
  const [data, setData] = useState<RuleListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    listRules()
      .then(setData)
      .catch(() => setError('ルール一覧の取得に失敗しました。'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <PageLayout title="チェックルール一覧">
      {loading && <p style={{ color: COLOR.textMuted }}>Loading…</p>}
      {error && (
        <div style={{
          padding: '0.75rem',
          backgroundColor: '#fee2e2',
          borderRadius: 6,
          color: '#991b1b',
          fontSize: '0.875rem',
          marginBottom: '1rem',
        }}>
          {error}
        </div>
      )}
      {data && (
        <>
          <div style={{ marginBottom: '1rem', padding: '0.75rem 1rem', backgroundColor: '#eff6ff', borderRadius: 6, fontSize: '0.85rem', color: '#1e40af' }}>
            <strong>FO ルール</strong> は Front Office が入力した取引データのバリデーションを行います。
            <strong> BO ルール</strong> はカウンターパーティ・SSI などのマスタデータを参照してプレセトルメント検証を行います。
            <span style={{ color: '#64748b' }}> 「stub」ラベルは現在常にパスするプレースホルダーを示します。</span>
          </div>
          <RuleTable rules={data.fo_rules} caption="FO チェックルール" />
          <RuleTable rules={data.bo_rules} caption="BO チェックルール" />
        </>
      )}
    </PageLayout>
  )
}
