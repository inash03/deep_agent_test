import { Suspense } from 'react'
import { LoginPage } from '../../screens/LoginPage'

export default function Page() {
  return (
    <Suspense fallback={null}>
      <LoginPage />
    </Suspense>
  )
}
