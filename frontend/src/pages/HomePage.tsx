import type React from 'react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageLayout } from '../components/PageLayout'
import { CARD, COLOR, BTN_PRIMARY, BTN_SECONDARY } from '../styles/theme'

type Language = 'en' | 'ja'

const COPY = {
  en: {
    title: 'STP Exception Triage System',
    intro: (
      <>
        This system investigates STP exception trades through a two-stage <strong>FO to BO</strong> workflow.
        It first runs rule-based checks (<strong>FoCheck / BoCheck</strong>), then asks AI agents to diagnose failed
        rules and recommend corrective actions. Operators can approve or reject agent proposals through HITL.
      </>
    ),
    open: 'Open',
    sections: [
      {
        title: 'Trades',
        description:
          'View trades, register new trades, run FoCheck/BoCheck, and start FO/BO agent triage from each trade detail page.',
        path: '/trades',
        color: COLOR.primary,
      },
      {
        title: 'STP Exceptions',
        description:
          'Review unresolved exceptions raised by the STP system, jump to the related trade, and investigate them with FO/BO agents.',
        path: '/stp-exceptions',
        color: '#f59e0b',
      },
      {
        title: 'Triage History',
        description:
          'Inspect historical FO/BO agent triage results, including diagnoses, root causes, and completed actions.',
        path: '/history',
        color: '#10b981',
      },
    ],
    workflowTitle: 'Workflow Overview',
    workflowSteps: [
      'Register a trade from Trades > New Trade.',
      'Run FoCheck for front-office rule validation.',
      'If rules fail, start FO agent triage with HITL where needed.',
      'After FO approval, run BoCheck for back-office rule validation.',
      'If rules fail, start BO agent triage with HITL where needed.',
      'Complete the workflow and review results in Triage History.',
    ],
    statusTitle: 'Trade Lifecycle (WorkflowStatus)',
    statusLead:
      'Trades move through these statuses in order. When FoCheck or BoCheck passes all rules, the corresponding agent triage step is skipped.',
    statusHeaders: ['Status', 'Description', 'Owner'],
    transitionTitle: 'Status Transition Diagram',
    transitionNote:
      'The BO agent may send a trade back to the FO agent once. If the same issue remains on the second BO triage, the flow escalates to a BO user.',
    statuses: [
      ['Initial', 'Trade has just been registered.', 'System'],
      ['FoCheck', 'Front-office rule checks are running.', 'System'],
      ['FoAgentToCheck', 'FoCheck failed, so FoAgent triages the failed checks.', 'FoAgent'],
      ['FoUserToValidate', 'FoAgent determined that human judgment is required.', 'FoUser'],
      ['FoValidated', 'FO approval is complete.', 'System'],
      ['BoCheck', 'Back-office rule checks are running.', 'System'],
      ['BoAgentToCheck', 'BoCheck failed, so BoAgent triages the failed checks.', 'BoAgent'],
      ['BoUserToValidate', 'BoAgent determined that human judgment is required.', 'BoUser'],
      ['BoValidated', 'BO approval is complete and the trade is ready for settlement processing.', 'System'],
      ['Done', 'All approvals are complete.', 'System'],
      ['Cancelled', 'A cancel event was approved and the trade was cancelled.', 'System'],
      ['EventPending', 'A new trade version is waiting for Amend/Cancel event approval.', 'System'],
    ],
    transitionRows: [
      ['Initial', 'FoCheck', 'Auto or manual trigger'],
      ['FoCheck', 'FoValidated', 'All rules passed'],
      ['FoCheck', 'FoAgentToCheck', 'Failures found'],
      ['FoAgentToCheck', 'FoValidated', 'Agent resolved'],
      ['FoAgentToCheck', 'FoUserToValidate', 'Human judgment required'],
      ['FoUserToValidate', 'FoValidated', 'FO user approved'],
      ['FoValidated', 'BoCheck', 'Auto or manual trigger'],
      ['BoCheck', 'BoValidated', 'All rules passed'],
      ['BoCheck', 'BoAgentToCheck', 'Failures found'],
      ['BoAgentToCheck', 'BoValidated', 'Agent resolved'],
      ['BoAgentToCheck', 'FoAgentToCheck', 'Sent back to FO, first time only'],
      ['BoAgentToCheck', 'BoUserToValidate', 'Cannot resolve or second BO issue'],
      ['BoUserToValidate', 'BoValidated', 'BO user approved'],
      ['BoValidated', 'Done', 'Settlement handoff complete'],
      ['Done', 'Cancelled', 'Cancel event approved'],
    ],
  },
  ja: {
    title: 'STP 例外トリアージシステム',
    intro: (
      <>
        STP（直通処理）例外を <strong>FO → BO</strong> の 2 段階で自動調査するシステムです。
        まずルールベースのチェック（<strong>FoCheck / BoCheck</strong>）を実行し、
        失敗したルールを AI エージェントが診断して是正アクションを提案します。
        オペレーターはエージェントの提案を承認または却下できます（HITL）。
      </>
    ),
    open: '開く',
    sections: [
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
    ],
    workflowTitle: 'ワークフロー概要',
    workflowSteps: [
      '取引を登録（Trades > New Trade）',
      'FoCheck を実行し、FO 側のルールチェックを行う',
      '失敗ルールがあれば FO エージェントトリアージを起動（必要に応じて HITL）',
      'FO 承認後、BoCheck を実行し、BO 側のルールチェックを行う',
      '失敗ルールがあれば BO エージェントトリアージを起動（必要に応じて HITL）',
      '完了後、Triage History で結果を確認',
    ],
    statusTitle: '取引ライフサイクル（WorkflowStatus）',
    statusLead:
      '取引は以下のステータスを順に遷移します。FoCheck / BoCheck が全通過した場合は、対応するエージェントトリアージをスキップします。',
    statusHeaders: ['ステータス', '説明', '担当'],
    transitionTitle: 'ステータス遷移図',
    transitionNote:
      'BoAgent は 1 回目のみ FO へ差し戻せます。同じ問題が 2 回目の BO トリアージでも残る場合は、BoUser へエスカレーションします。',
    statuses: [
      ['Initial', '取引登録直後', 'システム'],
      ['FoCheck', 'フロントオフィス ルールチェック実行中', 'システム'],
      ['FoAgentToCheck', 'FoCheck 失敗あり。FoAgent が失敗チェックをトリアージ', 'FoAgent'],
      ['FoUserToValidate', 'FoAgent が人間判断が必要と判定', 'FoUser'],
      ['FoValidated', 'FO 承認完了', 'システム'],
      ['BoCheck', 'バックオフィス ルールチェック実行中', 'システム'],
      ['BoAgentToCheck', 'BoCheck 失敗あり。BoAgent が失敗チェックをトリアージ', 'BoAgent'],
      ['BoUserToValidate', 'BoAgent が人間判断が必要と判定', 'BoUser'],
      ['BoValidated', 'BO 承認完了。精算システムへ送出可能', 'システム'],
      ['Done', '全承認完了', 'システム'],
      ['Cancelled', 'Cancel イベントが承認され取引が取り消された', 'システム'],
      ['EventPending', 'Amend / Cancel イベント承認待ち中の新バージョン', 'システム'],
    ],
    transitionRows: [
      ['Initial', 'FoCheck', '自動または手動トリガー'],
      ['FoCheck', 'FoValidated', '全通過'],
      ['FoCheck', 'FoAgentToCheck', '失敗あり'],
      ['FoAgentToCheck', 'FoValidated', 'エージェント解決'],
      ['FoAgentToCheck', 'FoUserToValidate', '人間判断が必要'],
      ['FoUserToValidate', 'FoValidated', 'FO ユーザー承認'],
      ['FoValidated', 'BoCheck', '自動または手動トリガー'],
      ['BoCheck', 'BoValidated', '全通過'],
      ['BoCheck', 'BoAgentToCheck', '失敗あり'],
      ['BoAgentToCheck', 'BoValidated', 'エージェント解決'],
      ['BoAgentToCheck', 'FoAgentToCheck', 'FO へ差し戻し（1 回目のみ）'],
      ['BoAgentToCheck', 'BoUserToValidate', '解決不能または 2 回目も問題あり'],
      ['BoUserToValidate', 'BoValidated', 'BO ユーザー承認'],
      ['BoValidated', 'Done', '精算連携完了'],
      ['Done', 'Cancelled', 'Cancel イベント承認'],
    ],
  },
} as const

const diagramLineStyle = {
  display: 'grid',
  gridTemplateColumns: 'minmax(130px, 0.9fr) auto minmax(130px, 0.9fr) minmax(160px, 1.2fr)',
  gap: '0.65rem',
  alignItems: 'center',
  padding: '0.55rem 0',
  borderBottom: `1px solid ${COLOR.border}`,
} satisfies React.CSSProperties

const statusPillStyle = {
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  minHeight: 30,
  padding: '0.25rem 0.6rem',
  borderRadius: 6,
  border: `1px solid ${COLOR.borderDark}`,
  backgroundColor: COLOR.bg,
  color: COLOR.text,
  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
  fontSize: '0.78rem',
  fontWeight: 700,
} satisfies React.CSSProperties

export function HomePage() {
  const navigate = useNavigate()
  const [language, setLanguage] = useState<Language>('en')
  const copy = COPY[language]

  return (
    <PageLayout
      title={copy.title}
      action={
        <div style={{ display: 'inline-flex', gap: '0.35rem' }} aria-label="Language switcher">
          {(['en', 'ja'] as const).map(option => (
            <button
              key={option}
              type="button"
              style={{
                ...BTN_SECONDARY,
                padding: '0.4rem 0.75rem',
                backgroundColor: language === option ? COLOR.primary : COLOR.bgWhite,
                color: language === option ? '#fff' : COLOR.text,
                borderColor: language === option ? COLOR.primary : COLOR.borderDark,
              }}
              aria-pressed={language === option}
              onClick={() => setLanguage(option)}
            >
              {option.toUpperCase()}
            </button>
          ))}
        </div>
      }
    >
      <p style={{ color: COLOR.textMuted, marginBottom: '2rem', maxWidth: 760, lineHeight: 1.75 }}>
        {copy.intro}
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        {copy.sections.map(s => (
          <div key={s.path} style={{ ...CARD, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: s.color, margin: 0 }}>{s.title}</h2>
            <p style={{ fontSize: '0.875rem', color: COLOR.textMuted, margin: 0, flex: 1, lineHeight: 1.65 }}>
              {s.description}
            </p>
            <button
              style={{ ...BTN_PRIMARY, backgroundColor: s.color, alignSelf: 'flex-start' }}
              onClick={() => navigate(s.path)}
            >
              {copy.open} →
            </button>
          </div>
        ))}
      </div>

      <div style={{ ...CARD, maxWidth: 760, marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: COLOR.text, marginTop: 0, marginBottom: '0.75rem' }}>
          {copy.workflowTitle}
        </h2>
        <ol style={{ margin: 0, paddingLeft: '1.25rem', color: COLOR.textMuted, fontSize: '0.875rem', lineHeight: 2 }}>
          {copy.workflowSteps.map(step => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </div>

      <section style={{ ...CARD, marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, color: COLOR.text, marginTop: 0, marginBottom: '0.5rem' }}>
          {copy.statusTitle}
        </h2>
        <p style={{ color: COLOR.textMuted, marginTop: 0, marginBottom: '1rem', maxWidth: 850, lineHeight: 1.65, fontSize: '0.875rem' }}>
          {copy.statusLead}
        </p>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem', minWidth: 760 }}>
            <thead>
              <tr>
                {copy.statusHeaders.map(header => (
                  <th
                    key={header}
                    style={{
                      textAlign: 'left',
                      padding: '0.65rem 0.75rem',
                      borderBottom: `2px solid ${COLOR.border}`,
                      color: COLOR.textMuted,
                      fontSize: '0.75rem',
                      textTransform: 'uppercase',
                    }}
                  >
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {copy.statuses.map(([status, description, owner]) => (
                <tr key={status}>
                  <td style={{ padding: '0.65rem 0.75rem', borderBottom: `1px solid ${COLOR.border}`, verticalAlign: 'top' }}>
                    <span style={statusPillStyle}>{status}</span>
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

      <section style={{ ...CARD }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, color: COLOR.text, marginTop: 0, marginBottom: '0.5rem' }}>
          {copy.transitionTitle}
        </h2>
        <p style={{ color: COLOR.textMuted, marginTop: 0, marginBottom: '1rem', maxWidth: 850, lineHeight: 1.65, fontSize: '0.875rem' }}>
          {copy.transitionNote}
        </p>
        <div style={{ overflowX: 'auto' }}>
          <div style={{ minWidth: 760 }}>
            {copy.transitionRows.map(([from, to, condition]) => (
              <div key={`${from}-${to}-${condition}`} style={diagramLineStyle}>
                <span style={statusPillStyle}>{from}</span>
                <span style={{ color: COLOR.primary, fontWeight: 800 }}>→</span>
                <span style={statusPillStyle}>{to}</span>
                <span style={{ color: COLOR.textMuted, fontSize: '0.82rem', lineHeight: 1.45 }}>{condition}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </PageLayout>
  )
}
