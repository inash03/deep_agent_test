import type { TriageStatus } from '../types/triage'

interface Props {
  status: TriageStatus
}

const STYLES: Record<TriageStatus, React.CSSProperties> = {
  COMPLETED: {
    backgroundColor: '#d1fae5',
    color: '#065f46',
    border: '1px solid #6ee7b7',
  },
  PENDING_APPROVAL: {
    backgroundColor: '#fff7ed',
    color: '#9a3412',
    border: '1px solid #fed7aa',
  },
}

export function StatusBadge({ status }: Props) {
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 10px',
        borderRadius: '9999px',
        fontSize: '0.85rem',
        fontWeight: 600,
        ...STYLES[status],
      }}
    >
      {status === 'COMPLETED' ? 'COMPLETED' : 'PENDING APPROVAL'}
    </span>
  )
}
