import { NextResponse, type NextRequest } from 'next/server'
import { auth } from '../../../../auth'

type Context = {
  params: Promise<{ path: string[] }>
}

const HOP_BY_HOP_HEADERS = new Set([
  'connection',
  'content-length',
  'host',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailer',
  'transfer-encoding',
  'upgrade',
  'cookie',
])

export const runtime = 'nodejs'

async function proxy(request: NextRequest, context: Context) {
  const session = await auth()
  if (!session) {
    return NextResponse.json({ detail: 'Unauthorized' }, { status: 401 })
  }

  const backendUrl = process.env.BACKEND_API_URL
  if (!backendUrl) {
    return NextResponse.json({ detail: 'BACKEND_API_URL is not configured' }, { status: 500 })
  }

  const { path } = await context.params
  const target = new URL(path.join('/'), backendUrl.endsWith('/') ? backendUrl : `${backendUrl}/`)
  target.search = request.nextUrl.search

  const headers = new Headers()
  request.headers.forEach((value, key) => {
    if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) headers.set(key, value)
  })
  const apiKey = process.env.BACKEND_API_KEY
  if (apiKey) headers.set('X-API-Key', apiKey)

  const hasBody = request.method !== 'GET' && request.method !== 'HEAD'
  const upstream = await fetch(target, {
    method: request.method,
    headers,
    body: hasBody ? await request.text() : undefined,
    cache: 'no-store',
  })

  const responseHeaders = new Headers(upstream.headers)
  responseHeaders.delete('content-encoding')
  responseHeaders.delete('content-length')

  return new NextResponse(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  })
}

export const GET = proxy
export const POST = proxy
export const PATCH = proxy
export const PUT = proxy
export const DELETE = proxy
