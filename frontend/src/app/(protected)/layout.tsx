import type { ReactNode } from 'react'
import { redirect } from 'next/navigation'
import { auth } from '../../auth'
import { NavBar } from '../../components/NavBar'

export default async function ProtectedLayout({ children }: { children: ReactNode }) {
  const session = await auth()
  if (!session) redirect('/login')

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f1f5f9', paddingTop: 52, overflowX: 'hidden' }}>
      <NavBar />
      {children}
    </div>
  )
}
