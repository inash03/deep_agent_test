import { useNavigate } from 'react-router-dom'
import { PageLayout } from '../components/PageLayout'
import { CARD, COLOR, BTN_PRIMARY } from '../styles/theme'

const SECTIONS = [
  {
    title: 'Trades',
    description:
      'トレードの一覧・新規登録・FoCheck/BoCheck の実行・FO/BO エージェントによるトリアージを行います。各トレードの詳細画面から自動チェックとエージェントトリアージを起動できます。',
    path: '/trades',
    color: COLOR.primary,
  },
  {
    title: 'STP Exceptions',
    description:
      'STP システムから発生した未解決例外の一覧を確認します。例外ごとにトレードへ移動し、FO/BO エージェントによる調査を実施できます。',
    path: '/stp-exceptions',
    color: '#f59e0b',
  },
  {
    title: 'Triage History',
    description:
      'FO/BO エージェントが実行したトリアージの結果履歴を確認します。診断内容・根本原因・実施済みアクションを一覧で参照できます。',
    path: '/history',
    color: '#10b981',
  },
]

export function HomePage() {
  const navigate = useNavigate()

  return (
    <PageLayout title="STP Exception Triage System">
      <p style={{ color: COLOR.textMuted, marginBottom: '2rem', maxWidth: 700, lineHeight: 1.75 }}>
        STP（直通処理）例外を <strong>FO → BO</strong> の 2 段階で自動調査するシステムです。
        まずルールベースのチェック（<strong>FoCheck / BoCheck</strong>）を実行し、
        失敗したルールを AI エージェントが診断して是正アクションを提案します。
        オペレーターはエージェントの提案を承認または却下できます（HITL）。
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        {SECTIONS.map(s => (
          <div key={s.path} style={{ ...CARD, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: s.color, margin: 0 }}>{s.title}</h2>
            <p style={{ fontSize: '0.875rem', color: COLOR.textMuted, margin: 0, flex: 1, lineHeight: 1.65 }}>
              {s.description}
            </p>
            <button
              style={{ ...BTN_PRIMARY, backgroundColor: s.color, alignSelf: 'flex-start' }}
              onClick={() => navigate(s.path)}
            >
              開く →
            </button>
          </div>
        ))}
      </div>

      <div style={{ ...CARD, maxWidth: 700 }}>
        <h2 style={{ fontSize: '0.9rem', fontWeight: 700, color: COLOR.text, marginTop: 0, marginBottom: '0.75rem' }}>
          ワークフロー概要
        </h2>
        <ol style={{ margin: 0, paddingLeft: '1.25rem', color: COLOR.textMuted, fontSize: '0.875rem', lineHeight: 2 }}>
          <li>取引を登録（Trades → New Trade）</li>
          <li>FoCheck を実行 — ルールベースの FO チェック</li>
          <li>失敗ルールがあれば FO エージェントトリアージを起動（HITL あり）</li>
          <li>FO 承認後、BoCheck を実行 — ルールベースの BO チェック</li>
          <li>失敗ルールがあれば BO エージェントトリアージを起動（HITL あり）</li>
          <li>完了 → Triage History で結果を確認</li>
        </ol>
      </div>
    </PageLayout>
  )
}
