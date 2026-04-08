import type { StepOut } from '../types/triage'

interface Props {
  steps: StepOut[]
}

const STEP_COLOR: Record<StepOut['step_type'], string> = {
  tool_call: '#3b82f6',
  hitl_prompt: '#f97316',
  hitl_response: '#8b5cf6',
}

const STEP_LABEL: Record<StepOut['step_type'], string> = {
  tool_call: 'Tool',
  hitl_prompt: 'HITL Prompt',
  hitl_response: 'HITL Response',
}

export function StepList({ steps }: Props) {
  if (steps.length === 0) return null

  return (
    <div style={{ marginTop: '1rem' }}>
      <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Agent Steps</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {steps.map((step, i) => (
          <div
            key={i}
            style={{
              borderLeft: `3px solid ${STEP_COLOR[step.step_type]}`,
              paddingLeft: '0.75rem',
              backgroundColor: '#f9fafb',
              borderRadius: '0 4px 4px 0',
              padding: '0.5rem 0.75rem',
            }}
          >
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.25rem' }}>
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  color: STEP_COLOR[step.step_type],
                  textTransform: 'uppercase',
                }}
              >
                {STEP_LABEL[step.step_type]}
              </span>
              <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{step.name}</span>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>
              <span style={{ fontWeight: 500 }}>Input: </span>
              <code>{JSON.stringify(step.input)}</code>
            </div>
            {step.output !== null && (
              <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '0.1rem' }}>
                <span style={{ fontWeight: 500 }}>Output: </span>
                <code>{JSON.stringify(step.output)}</code>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
