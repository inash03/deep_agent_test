import NextAuth from 'next-auth'
import Credentials from 'next-auth/providers/credentials'
import bcrypt from 'bcryptjs'

export const { handlers, auth, signIn, signOut } = NextAuth({
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
        const expectedUser = process.env.APP_USERNAME
        const passwordHash = process.env.APP_PASSWORD_HASH
        const username = String(credentials?.username ?? '')
        const password = String(credentials?.password ?? '')

        if (!expectedUser || !passwordHash || username !== expectedUser || !password) {
          return null
        }

        const ok = await bcrypt.compare(password, passwordHash)
        if (!ok) return null

        return {
          id: expectedUser,
          name: expectedUser,
        }
      },
    }),
  ],
})
