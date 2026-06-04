const BASE = '/api/v1'

/**
 * 流式对话 — 返回 ReadableStream 供组件逐字消费
 */
export async function* streamChat(message, threadId = 'default') {
  const response = await fetch(`${BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, thread_id: threadId }),
  })

  if (!response.ok) throw new Error(`HTTP ${response.status}`)

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      const sse = line.trim()
      if (sse.startsWith('data: ')) {
        const data = sse.slice(6)
        if (data === '[DONE]') return
        if (data.startsWith('[ERROR]')) throw new Error(data)
        // JSON 解码 (后端做了 json.dumps 防 SSE 截断)
        try { yield JSON.parse(data) } catch { yield data }
      }
    }
  }
}

/** 健康检查 */
export async function healthCheck() {
  const res = await fetch(`${BASE}/health`)
  return res.json()
}

/** 同步对话 */
export async function chat(message, threadId = 'default') {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, thread_id: threadId }),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}
