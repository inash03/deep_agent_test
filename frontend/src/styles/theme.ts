import type React from 'react'

// ---------------------------------------------------------------------------
// Colors
// ---------------------------------------------------------------------------
export const COLOR = {
  primary: '#2563eb',
  primaryHover: '#1d4ed8',
  danger: '#dc2626',
  dangerHover: '#b91c1c',
  success: '#16a34a',
  warning: '#d97706',
  border: '#e5e7eb',
  borderDark: '#d1d5db',
  bg: '#f9fafb',
  bgWhite: '#ffffff',
  text: '#111827',
  textMuted: '#6b7280',
  textLight: '#9ca3af',
} as const

// ---------------------------------------------------------------------------
// Shared style objects
// ---------------------------------------------------------------------------

export const CARD: React.CSSProperties = {
  backgroundColor: COLOR.bgWhite,
  border: `1px solid ${COLOR.border}`,
  borderRadius: 8,
  padding: '1.25rem',
  boxShadow: '0 1px 3px rgba(0,0,0,0.07)',
}

export const BTN_BASE: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.25rem',
  padding: '0.45rem 1rem',
  borderRadius: 6,
  border: 'none',
  cursor: 'pointer',
  fontWeight: 600,
  fontSize: '0.875rem',
  transition: 'background-color 0.15s',
}

export const BTN_PRIMARY: React.CSSProperties = {
  ...BTN_BASE,
  backgroundColor: COLOR.primary,
  color: '#fff',
}

export const BTN_DANGER: React.CSSProperties = {
  ...BTN_BASE,
  backgroundColor: COLOR.danger,
  color: '#fff',
}

export const BTN_SECONDARY: React.CSSProperties = {
  ...BTN_BASE,
  backgroundColor: COLOR.bg,
  color: COLOR.text,
  border: `1px solid ${COLOR.border}`,
}

export const INPUT: React.CSSProperties = {
  padding: '0.45rem 0.75rem',
  border: `1px solid ${COLOR.borderDark}`,
  borderRadius: 6,
  fontSize: '0.875rem',
  outline: 'none',
  width: '100%',
  boxSizing: 'border-box',
}

export const LABEL: React.CSSProperties = {
  display: 'block',
  fontSize: '0.8rem',
  fontWeight: 600,
  color: COLOR.textMuted,
  marginBottom: '0.3rem',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
}

export const TABLE: React.CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
  fontSize: '0.875rem',
}

export const TH: React.CSSProperties = {
  textAlign: 'left',
  padding: '0.6rem 0.75rem',
  borderBottom: `2px solid ${COLOR.border}`,
  color: COLOR.textMuted,
  fontWeight: 600,
  fontSize: '0.75rem',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  whiteSpace: 'nowrap',
}

export const TD: React.CSSProperties = {
  padding: '0.6rem 0.75rem',
  borderBottom: `1px solid ${COLOR.border}`,
  color: COLOR.text,
  verticalAlign: 'middle',
}
