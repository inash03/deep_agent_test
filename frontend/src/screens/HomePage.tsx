'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { PageLayout } from '../components/PageLayout'
import { CARD, COLOR, BTN_PRIMARY, BTN_SECONDARY } from '../styles/theme'
import { WORKFLOW_STATUS_COLORS, WORKFLOW_STATUS_LABELS } from '../types/trade'

type Language = 'en' | 'ja'

type SectionContent = {
  title: string
  description: string
  action: string
}

type StatusContent = [status: string, description: string, owner: string]

const SECTION_META = [
  { key: 'trades', path: '/trades', color: COLOR.primary },
  { key: 'exceptions', path: '/stp-exceptions', color: '#f59e0b' },
  { key: 'history', path: '/history', color: '#10b981' },
] as const

const CONTENT: Record<Language, {
  title: string
  intro: string[]
  sections: Record<(typeof SECTION_META)[number]['key'], SectionContent>
  workflowTitle: string
  workflowSteps: string[]
  lifecycleTitle: string
  lifecycleHeaders: string[]
  statuses: StatusContent[]
  languageLabel: string
}> = {
  en: {
    title: 'STP Exception Triage System',
    intro: [
      'This system investigates trades that hit STP exceptions through a two-stage FO to BO workflow.',
      'It starts with rule-based checks, then asks AI agents to diagnose failed rules, identify likely root causes, and recommend corrective actions when human review is needed.',
    ],
    sections: {
      trades: {
        title: 'Trades',
        description: 'View trades, register new trades, run FoCheck and BoCheck, and start FO/BO agent triage.',
        action: 'Open',
      },
      exceptions: {
        title: 'STP Exceptions',
        description: 'Review unresolved STP exceptions, open related trades, and inspect rule violations or exception messages.',
        action: 'Open',
      },
      history: {
        title: 'Triage History',
        description: 'Inspect historical FO/BO agent triage results, diagnoses, root causes, and recommended actions.',
        action: 'Open',
      },
    },
    workflowTitle: 'Workflow Overview',
    workflowSteps: [
      'Register a trade from Trades > New Trade.',
      'Run FoCheck for front-office rule validation.',
      'If FoCheck fails, start FO agent triage and use human approval where needed.',
      'After FO approval, run BoCheck for back-office rule validation.',
      'If BoCheck fails, start BO agent triage and use human approval where needed.',
      'Complete the workflow and review the result in Triage History.',
    ],
    lifecycleTitle: 'Trade Lifecycle',
    lifecycleHeaders: ['Status', 'Description', 'Owner'],
    statuses: [
      ['Initial', 'The trade has just been registered.', 'System'],
      ['FoCheck', 'Front-office rule checks are running.', 'System'],
      ['FoAgentToCheck', 'FoCheck failed, so the FO agent investigates the failed checks.', 'FoAgent'],
      ['FoUserToValidate', 'The FO agent determined that human judgment is required.', 'FoUser'],
      ['FoValidated', 'FO approval is complete.', 'System'],
      ['BoCheck', 'Back-office rule checks are running.', 'System'],
      ['BoAgentToCheck', 'BoCheck failed, so the BO agent investigates the failed checks.', 'BoAgent'],
      ['BoUserToValidate', 'The BO agent determined that human judgment is required.', 'BoUser'],
      ['BoValidated', 'BO approval is complete and the trade is ready for settlement processing.', 'System'],
      ['Done', 'All approvals and validations are complete.', 'System'],
      ['Cancelled', 'A cancel event was approved and the trade was cancelled.', 'System'],
      ['EventPending', 'A new trade version from an Amend or Cancel event is waiting for approval.', 'System'],
    ],
    languageLabel: 'Language',
  },
  ja: {
    title: 'STP 例外トリアージシステム',
    intro: [
      'このシステムは、STP 例外が発生した取引を FO から BO へ進む二段階ワークフローで調査します。',
      'まずルールベースのチェックで問題箇所を特定し、必要に応じて AI エージェントが原因分析、根本原因の推定、対応案の提示を行います。',
    ],
    sections: {
      trades: {
        title: '取引管理',
        description: '取引の一覧確認、新規登録、FoCheck/BoCheck の実行、FO/BO エージェントによる原因調査を行います。',
        action: '開く',
      },
      exceptions: {
        title: 'STP 例外',
        description: '未解決の STP 例外を確認し、関連取引のチェック違反や例外メッセージをたどって対応状況を管理します。',
        action: '開く',
      },
      history: {
        title: 'トリアージ履歴',
        description: 'FO/BO エージェントが実施した調査結果、診断、根本原因、推奨アクションを履歴として確認します。',
        action: '開く',
      },
    },
    workflowTitle: 'ワークフロー概要',
    workflowSteps: [
      'Trades > New Trade から取引を登録します。',
      'FoCheck を実行し、フロントオフィス観点のルール検証を行います。',
      'FoCheck が失敗した場合は FO エージェントのトリアージを開始し、必要に応じて人手承認を行います。',
      'FO 承認後に BoCheck を実行し、バックオフィス観点のルール検証を行います。',
      'BoCheck が失敗した場合は BO エージェントのトリアージを開始し、必要に応じて人手承認を行います。',
      'すべての承認が完了したら、Triage History で結果を確認します。',
    ],
    lifecycleTitle: '取引ライフサイクル',
    lifecycleHeaders: ['ステータス', '説明', '担当'],
    statuses: [
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
    ],
    languageLabel: '表示言語',
  },
}

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
        fontFamily: 'var(--font-mono)',
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

function languageButtonStyle(active: boolean): React.CSSProperties {
  return {
    ...(active ? BTN_PRIMARY : BTN_SECONDARY),
    minWidth: 44,
    justifyContent: 'center',
    padding: '0.4rem 0.75rem',
  }
}

export function HomePage() {
  const router = useRouter()
  const [language, setLanguage] = useState<Language>('en')
  const content = CONTENT[language]

  return (
    <PageLayout
      title={content.title}
      action={
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <span style={{ color: COLOR.textMuted, fontSize: '0.8rem', fontWeight: 600 }}>
            {content.languageLabel}
          </span>
          <div style={{ display: 'inline-flex', gap: 4 }}>
            <button
              type="button"
              style={languageButtonStyle(language === 'en')}
              onClick={() => setLanguage('en')}
              aria-pressed={language === 'en'}
            >
              EN
            </button>
            <button
              type="button"
              style={languageButtonStyle(language === 'ja')}
              onClick={() => setLanguage('ja')}
              aria-pressed={language === 'ja'}
            >
              JP
            </button>
          </div>
        </div>
      }
    >
      <div style={{ color: COLOR.textMuted, marginBottom: '2rem', maxWidth: 800, lineHeight: 1.75 }}>
        {content.intro.map(line => (
          <p key={line} style={{ margin: '0 0 0.35rem' }}>{line}</p>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        {SECTION_META.map(section => {
          const sectionContent = content.sections[section.key]
          return (
            <div key={section.path} style={{ ...CARD, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <h2 style={{ fontSize: '1rem', fontWeight: 700, color: section.color, margin: 0 }}>{sectionContent.title}</h2>
              <p style={{ fontSize: '0.875rem', color: COLOR.textMuted, margin: 0, flex: 1, lineHeight: 1.65 }}>
                {sectionContent.description}
              </p>
              <button
                type="button"
                style={{ ...BTN_PRIMARY, backgroundColor: section.color, alignSelf: 'flex-start' }}
                onClick={() => router.push(section.path)}
              >
                {sectionContent.action}
              </button>
            </div>
          )
        })}
      </div>

      <div style={{ ...CARD, maxWidth: 800, marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: COLOR.text, marginTop: 0, marginBottom: '0.75rem' }}>
          {content.workflowTitle}
        </h2>
        <ol style={{ margin: 0, paddingLeft: '1.25rem', color: COLOR.textMuted, fontSize: '0.875rem', lineHeight: 2 }}>
          {content.workflowSteps.map(step => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </div>

      <section style={CARD}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, color: COLOR.text, marginTop: 0, marginBottom: '0.5rem' }}>
          {content.lifecycleTitle}
        </h2>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem', minWidth: 760 }}>
            <thead>
              <tr>
                {content.lifecycleHeaders.map(header => (
                  <th key={header} style={{ textAlign: 'left', padding: '0.65rem 0.75rem', borderBottom: `2px solid ${COLOR.border}`, color: COLOR.textMuted, fontSize: '0.75rem', textTransform: 'uppercase' }}>
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {content.statuses.map(([status, description, owner]) => (
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
