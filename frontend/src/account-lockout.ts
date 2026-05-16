import { Redis } from '@upstash/redis'

const MAX_FAILURES = 5
const LOCKOUT_SECONDS = 15 * 60 // 15 minutes

function buildRedis(): Redis | null {
  const url = process.env.UPSTASH_REDIS_REST_URL
  const token = process.env.UPSTASH_REDIS_REST_TOKEN
  if (!url || !token) return null
  return new Redis({ url, token })
}

function lockoutKey(username: string): string {
  return `auth:lockout:${username}`
}

export type LockoutStatus =
  | { locked: false }
  | { locked: true; remainingSeconds: number }

/**
 * Returns lockout state for the given username.
 * Returns { locked: false } when Redis is unavailable (fail open).
 */
export async function getLockoutStatus(username: string): Promise<LockoutStatus> {
  const redis = buildRedis()
  if (!redis) return { locked: false }

  try {
    const raw = await redis.get<{ count: number }>(lockoutKey(username))
    if (!raw || raw.count < MAX_FAILURES) return { locked: false }

    const ttl = await redis.ttl(lockoutKey(username))
    if (ttl <= 0) return { locked: false }

    return { locked: true, remainingSeconds: ttl }
  } catch {
    return { locked: false }
  }
}

/**
 * Records a failed login attempt. Locks the account after MAX_FAILURES.
 * No-op when Redis is unavailable.
 */
export async function recordFailure(username: string): Promise<void> {
  const redis = buildRedis()
  if (!redis) return

  try {
    const key = lockoutKey(username)
    const count = await redis.incr(key)
    if (count === 1) {
      // First failure: set expiry window. Subsequent failures extend only on lockout.
      await redis.expire(key, LOCKOUT_SECONDS)
    } else if (count >= MAX_FAILURES) {
      // Reached threshold: reset the TTL so the full lockout window starts now
      await redis.expire(key, LOCKOUT_SECONDS)
    }
  } catch {
    // ignore
  }
}

/**
 * Clears the failure counter after a successful login.
 * No-op when Redis is unavailable.
 */
export async function recordSuccess(username: string): Promise<void> {
  const redis = buildRedis()
  if (!redis) return

  try {
    await redis.del(lockoutKey(username))
  } catch {
    // ignore
  }
}
