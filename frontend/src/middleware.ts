import { NextRequest, NextResponse } from 'next/server'
import { Ratelimit } from '@upstash/ratelimit'
import { Redis } from '@upstash/redis'

// Fail open: if Redis is not configured, allow all requests through
function buildRatelimiter(): Ratelimit | null {
  const url = process.env.UPSTASH_REDIS_REST_URL
  const token = process.env.UPSTASH_REDIS_REST_TOKEN
  if (!url || !token) return null

  return new Ratelimit({
    redis: new Redis({ url, token }),
    // 5 attempts per 10 minutes per IP
    limiter: Ratelimit.slidingWindow(5, '10 m'),
    analytics: false,
  })
}

const ratelimiter = buildRatelimiter()

export async function middleware(request: NextRequest) {
  if (request.method !== 'POST') {
    return NextResponse.next()
  }

  if (!ratelimiter) {
    return NextResponse.next()
  }

  const ip =
    request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ??
    '127.0.0.1'

  try {
    const { success, limit, remaining, reset } = await ratelimiter.limit(ip)

    if (!success) {
      const retryAfterSec = Math.ceil((reset - Date.now()) / 1000)
      return new NextResponse(
        JSON.stringify({ error: 'Too many login attempts. Please try again later.' }),
        {
          status: 429,
          headers: {
            'Content-Type': 'application/json',
            'Retry-After': String(retryAfterSec),
            'X-RateLimit-Limit': String(limit),
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': String(reset),
          },
        },
      )
    }

    const response = NextResponse.next()
    response.headers.set('X-RateLimit-Limit', String(limit))
    response.headers.set('X-RateLimit-Remaining', String(remaining))
    return response
  } catch {
    // Redis unavailable — fail open to avoid locking out legitimate users
    return NextResponse.next()
  }
}

export const config = {
  matcher: '/api/auth/callback/credentials',
}
