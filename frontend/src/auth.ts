import NextAuth from 'next-auth'
import Credentials from 'next-auth/providers/credentials'
import bcrypt from 'bcryptjs'
import { getLockoutStatus, recordFailure, recordSuccess } from './account-lockout'

export const { handlers, auth, signIn, signOut } = NextAuth({
  secret: process.env.AUTH_SECRET,
  session: { strategy: 'jwt' },
  pages: {
    signIn: '/login',
  },
  providers: [
    Credentials({
      credentials: {
        username: { label: 'Username', type: 'text' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        const expectedUser = process.env.APP_USERNAME?.trim()
        const passwordHash = process.env.APP_PASSWORD_HASH?.trim()
        const username = String(credentials?.username ?? '').trim()
        const password = String(credentials?.password ?? '')

        if (!expectedUser || !passwordHash) {
          console.warn('Credentials sign-in is not configured: APP_USERNAME or APP_PASSWORD_HASH is missing.')
          return null
        }

        if (!passwordHash.startsWith('$2')) {
          console.warn('Credentials sign-in is not configured: APP_PASSWORD_HASH does not look like a bcrypt hash.')
          return null
        }

        // Check account lockout before verifying credentials
        const lockout = await getLockoutStatus(username)
        if (lockout.locked) {
          const minutes = Math.ceil(lockout.remainingSeconds / 60)
          console.warn(`Credentials sign-in rejected: account locked for ${minutes} more minute(s).`)
          return null
        }

        // Always run bcrypt.compare to prevent timing-based username enumeration
        const ok = await bcrypt.compare(password || '', passwordHash)
        if (username !== expectedUser || !password || !ok) {
          await recordFailure(username)
          console.warn('Credentials sign-in rejected.')
          return null
        }

        await recordSuccess(username)
        return {
          id: expectedUser,
          name: expectedUser,
        }
      },
    }),
  ],
})
