import { BTN_SECONDARY, COLOR } from '../styles/theme'

interface Props {
  total: number
  limit: number
  offset: number
  onChange: (offset: number) => void
}

export function Pagination({ total, limit, offset, onChange }: Props) {
  if (total <= limit) return null
  const page = Math.floor(offset / limit) + 1
  const totalPages = Math.ceil(total / limit)

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '1rem', justifyContent: 'flex-end' }}>
      <span style={{ fontSize: '0.8rem', color: COLOR.textMuted }}>
        Page {page} / {totalPages} ({total} total)
      </span>
      <button
        style={BTN_SECONDARY}
        disabled={offset === 0}
        onClick={() => onChange(Math.max(0, offset - limit))}
      >
        ← Prev
      </button>
      <button
        style={BTN_SECONDARY}
        disabled={offset + limit >= total}
        onClick={() => onChange(offset + limit)}
      >
        Next →
      </button>
    </div>
  )
}
