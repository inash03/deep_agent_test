'use client'

import { useState } from 'react'
import { signIn } from 'next-auth/react'
import { useRouter, useSearchParams } from 'next/navigation'
import { BTN_PRIMARY, CARD, COLOR, INPUT, LABEL } from '../styles/theme'

export function LoginPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const callbackUrl = searchParams.get('callbackUrl') ?? '/'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    const result = await signIn('credentials', {
      username,
      password,
      redirect: false,
      redirectTo: callbackUrl,
    })
    setLoading(false)

    if (result?.error) {
      setError('Invalid username or password.')
      return
    }

    router.push(result?.url ?? callbackUrl)
    router.refresh()
  }

  return (
    <main style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', backgroundColor: '#f1f5f9', padding: '1rem' }}>
      <form onSubmit={submit} style={{ ...CARD, width: '100%', maxWidth: 380 }}>
        <h1 style={{ margin: '0 0 0.35rem', fontSize: '1.35rem', color: COLOR.text }}>STP Triage</h1>
        <p style={{ margin: '0 0 1.25rem', color: COLOR.textMuted, fontSize: '0.875rem' }}>
          Sign in to continue.
        </p>

        {error && (
          <div style={{ backgroundColor: '#fee2e2', color: '#991b1b', padding: '0.75rem', borderRadius: 6, marginBottom: '1rem', fontSize: '0.875rem' }}>
            {error}
          </div>
        )}

        <div style={{ marginBottom: '1rem' }}>
          <label style={LABEL} htmlFor="username">Username</label>
          <input
            id="username"
            style={INPUT}
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            autoComplete="username"
            required
          />
        </div>

        <div style={{ marginBottom: '1.25rem' }}>
          <label style={LABEL} htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            style={INPUT}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
          />
        </div>

        <button type="submit" style={{ ...BTN_PRIMARY, width: '100%' }} disabled={loading}>
          {loading ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
    </main>
  )
}
