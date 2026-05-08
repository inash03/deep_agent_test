'use client'

import { useRouter } from 'next/navigation'
import { PageLayout } from '../components/PageLayout'
import { CARD, COLOR, BTN_PRIMARY } from '../styles/theme'
import { WORKFLOW_STATUS_COLORS, WORKFLOW_STATUS_LABELS } from '../types/trade'

const SECTIONS = [
  {
    title: '取引管理',
    description: '取引の一覧確認、新規登録、FoCheck/BoCheck の実行、FO/BO エージェントによる原因調査を行います。',
    path: '/trades',
    color: COLOR.primary,
  },
  {
    title: 'STP 例外',
    description: '未解決の STP 例外を確認し、関連取引のチェック違反や例外メッセージをたどって対応状況を管理します。',
    path: '/stp-exceptions',
    color: '#f59e0b',
  },
  {
    title: 'トリアージ履歴',
    description: 'FO/BO エージェントが実施した調査結果、診断、根本原因、推奨アクションを履歴として確認します。',
    path: '/history',
    color: '#10b981',
  },
]

const WORKFLOW_STEPS = [
  'Trades > New Trade から取引を登録します。',
  'FoCheck を実行し、フロントオフィス観点のルール検証を行います。',
  'FoCheck が失敗した場合は FO エージェントのトリアージを開始し、必要に応じて人手承認を行います。',
  'FO 承認後に BoCheck を実行し、バックオフィス観点のルール検証を行います。',
  'BoCheck が失敗した場合は BO エージェントのトリアージを開始し、必要に応じて人手承認を行います。',
  'すべての承認が完了したら、Triage History で結果を確認します。',
]

const STATUSES = [
  ['Initial', '取引が登録された直後の状態です。', 'System'],
  ['FoCheck', 'フロントオフィス観点のルールチェックを実行中です。', 'System'],
  ['FoAgentToCheck', 'FoCheck が失敗し、FO エージェントが違反内容を調査します。', 'FoAgent'],
  ['FoUserToValidate', 'FO エージェントが人手判断を必要と判定した状態です。', 'FoUser'],
  ['FoValidated', 'FO 側の承認が完了した状態です。', 'System'],
  ['BoCheck', 'バックオフィス観点のルールチェックを実行中です。', 'System'],
  ['BoAgentToCheck', 'BoCheck が失敗し、BO エージェントが違反内容を調査します。', 'BoAgent'],
  ['BoUserToValidate', 'BO エージェントが人手判断を必要と判定した状態です。', 'BoUser'],
  ['BoValidated', 'BO 側の承認が完了し、決済処理へ進める状態です。', 'System'],
  ['Done', 'すべての承認と検証が完了した状態です。', 'System'],
  ['Cancelled', 'キャンセルイベントが承認され、取引がキャンセルされた状態です。', 'System'],
  ['EventPending', 'Amend/Cancel による新しい取引バージョンが承認待ちの状態です。', 'System'],
]

function WorkflowStatusPill({ status }: { status: string }) {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 30,
        padding: '0.25rem 0.6rem',
        borderRadius: 6,
        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
        fontSize: '0.78rem',
        fontWeight: 700,
        ...(WORKFLOW_STATUS_COLORS[status] ?? {
          backgroundColor: COLOR.bg,
          color: COLOR.text,
          border: `1px solid ${COLOR.borderDark}`,
        }),
      }}
      title={status}
    >
      {WORKFLOW_STATUS_LABELS[status] ?? status}
    </span>
  )
}

export function HomePage() {
  const router = useRouter()

  return (
    <PageLayout title="STP 例外トリアージシステム">
      <p style={{ color: COLOR.textMuted, marginBottom: '2rem', maxWidth: 760, lineHeight: 1.75 }}>
        このシステムは、STP 例外が発生した取引を FO から BO へ進む二段階ワークフローで調査します。
        まずルールベースのチェックで問題箇所を特定し、必要に応じて AI エージェントが原因分析と対応案の提示を行います。
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        {SECTIONS.map(section => (
          <div key={section.path} style={{ ...CARD, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: section.color, margin: 0 }}>{section.title}</h2>
            <p style={{ fontSize: '0.875rem', color: COLOR.textMuted, margin: 0, flex: 1, lineHeight: 1.65 }}>
              {section.description}
            </p>
            <button
              style={{ ...BTN_PRIMARY, backgroundColor: section.color, alignSelf: 'flex-start' }}
              onClick={() => router.push(section.path)}
            >
              開く
            </button>
          </div>
        ))}
      </div>

      <div style={{ ...CARD, maxWidth: 760, marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: COLOR.text, marginTop: 0, marginBottom: '0.75rem' }}>
          ワークフロー概要
        </h2>
        <ol style={{ margin: 0, paddingLeft: '1.25rem', color: COLOR.textMuted, fontSize: '0.875rem', lineHeight: 2 }}>
          {WORKFLOW_STEPS.map(step => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </div>

      <section style={CARD}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, color: COLOR.text, marginTop: 0, marginBottom: '0.5rem' }}>
          取引ライフサイクル
        </h2>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem', minWidth: 760 }}>
            <thead>
              <tr>
                {['ステータス', '説明', '担当'].map(header => (
                  <th key={header} style={{ textAlign: 'left', padding: '0.65rem 0.75rem', borderBottom: `2px solid ${COLOR.border}`, color: COLOR.textMuted, fontSize: '0.75rem', textTransform: 'uppercase' }}>
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {STATUSES.map(([status, description, owner]) => (
                <tr key={status}>
                  <td style={{ padding: '0.65rem 0.75rem', borderBottom: `1px solid ${COLOR.border}`, verticalAlign: 'top' }}>
                    <WorkflowStatusPill status={status} />
                  </td>
                  <td style={{ padding: '0.65rem 0.75rem', borderBottom: `1px solid ${COLOR.border}`, color: COLOR.text, verticalAlign: 'top', lineHeight: 1.55 }}>
                    {description}
                  </td>
                  <td style={{ padding: '0.65rem 0.75rem', borderBottom: `1px solid ${COLOR.border}`, color: COLOR.textMuted, verticalAlign: 'top' }}>
                    {owner}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </PageLayout>
  )
}
