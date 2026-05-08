import NextAuth from 'next-auth'
import Credentials from 'next-auth/providers/credentials'
import bcrypt from 'bcryptjs'

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

        if (username !== expectedUser || !password) {
          console.warn('Credentials sign-in rejected: username mismatch or empty password.')
          return null
        }

        const ok = await bcrypt.compare(password, passwordHash)
        if (!ok) {
          console.warn('Credentials sign-in rejected: password hash comparison failed.')
          return null
        }

        return {
          id: expectedUser,
          name: expectedUser,
        }
      },
    }),
  ],
})
