'use client'

import { useRouter } from 'next/navigation'
import { PageLayout } from '../components/PageLayout'
import { CARD, COLOR, BTN_PRIMARY } from '../styles/theme'
import { WORKFLOW_STATUS_COLORS, WORKFLOW_STATUS_LABELS } from '../types/trade'

const SECTIONS = [
  {
    title: 'Trades',
    description: 'View trades, register new trades, run FoCheck/BoCheck, and start FO/BO agent triage.',
    path: '/trades',
    color: COLOR.primary,
  },
  {
    title: 'STP Exceptions',
    description: 'Review unresolved STP exceptions, open related trades, and investigate rule violations.',
    path: '/stp-exceptions',
    color: '#f59e0b',
  },
  {
    title: 'Triage History',
    description: 'Inspect historical FO/BO agent triage results, diagnoses, root causes, and actions.',
    path: '/history',
    color: '#10b981',
  },
]

const WORKFLOW_STEPS = [
  'Register a trade from Trades > New Trade.',
  'Run FoCheck for front-office rule validation.',
  'If rules fail, start FO agent triage with HITL where needed.',
  'After FO approval, run BoCheck for back-office rule validation.',
  'If rules fail, start BO agent triage with HITL where needed.',
  'Complete the workflow and review results in Triage History.',
]

const STATUSES = [
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
    <PageLayout title="STP Exception Triage System">
      <p style={{ color: COLOR.textMuted, marginBottom: '2rem', maxWidth: 760, lineHeight: 1.75 }}>
        This system investigates STP exception trades through a two-stage FO to BO workflow.
        It first runs rule-based checks, then asks AI agents to diagnose failed rules and recommend corrective actions.
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
              Open
            </button>
          </div>
        ))}
      </div>

      <div style={{ ...CARD, maxWidth: 760, marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: COLOR.text, marginTop: 0, marginBottom: '0.75rem' }}>
          Workflow Overview
        </h2>
        <ol style={{ margin: 0, paddingLeft: '1.25rem', color: COLOR.textMuted, fontSize: '0.875rem', lineHeight: 2 }}>
          {WORKFLOW_STEPS.map(step => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </div>

      <section style={CARD}>
        <h2 style={{ fontSize: '1rem', fontWeight: 700, color: COLOR.text, marginTop: 0, marginBottom: '0.5rem' }}>
          Trade Lifecycle
        </h2>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem', minWidth: 760 }}>
            <thead>
              <tr>
                {['Status', 'Description', 'Owner'].map(header => (
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
