import type { ReactNode } from 'react'
import { COLOR } from '../styles/theme'

interface Props {
  title: string
  action?: ReactNode
  children: ReactNode
}

export function PageLayout({ title, action, children }: Props) {
  return (
    <div style={{ maxWidth: 1140, margin: '0 auto', padding: '1.5rem 1rem', paddingTop: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
        <h1 style={{ fontSize: '1.35rem', fontWeight: 700, color: COLOR.text, margin: 0 }}>
          {title}
        </h1>
        {action}
      </div>
      {children}
    </div>
  )
}
