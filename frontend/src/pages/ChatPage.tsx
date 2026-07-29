import { useRef, useState, type FormEvent } from 'react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { streamFetch } from '@/lib/sse'

type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'm0',
      role: 'assistant',
      content: 'Ask about open investigations, IOCs, or run a cross-platform search.',
    },
  ])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || streaming) return

    const userMsg: ChatMessage = { id: `u-${Date.now()}`, role: 'user', content: text }
    const assistantId = `a-${Date.now()}`
    setMessages((prev) => [...prev, userMsg, { id: assistantId, role: 'assistant', content: '' }])
    setInput('')
    setStreaming(true)

    const ac = new AbortController()
    abortRef.current = ac

    await streamFetch(
      '/api/v1/chat/stream',
      { method: 'POST', body: { message: text } },
      {
        onMessage: (data) => {
          let token = data
          try {
            const parsed = JSON.parse(data) as { token?: string; content?: string }
            token = parsed.token ?? parsed.content ?? data
          } catch {
            /* plain text token */
          }
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, content: m.content + token } : m)),
          )
        },
        onError: () => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId && !m.content
                ? {
                    ...m,
                    content:
                      'Stream unavailable — API chat endpoint not ready. Demo: correlated 14 events across Graylog + OpenSearch for the finance VPC case.',
                  }
                : m,
            ),
          )
        },
        onDone: () => setStreaming(false),
      },
      ac.signal,
    )
    setStreaming(false)
  }

  return (
    <div className="flex h-[calc(100vh-3rem)] flex-col gap-4">
      <header>
        <h1 className="text-xl font-semibold text-slate-50">AI chat</h1>
        <p className="text-sm text-slate-400">SSE token stream from the investigation agents.</p>
      </header>
      <Card className="flex min-h-0 flex-1 flex-col" padded={false}>
        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
          {messages.map((m) => (
            <div
              key={m.id}
              className={
                m.role === 'user'
                  ? 'ml-8 rounded-lg border border-cyan-500/20 bg-cyan-500/10 px-3 py-2 text-sm text-slate-100'
                  : 'mr-8 rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-200'
              }
            >
              <div className="mb-1 text-[10px] uppercase tracking-wide text-slate-500">{m.role}</div>
              <div className="whitespace-pre-wrap font-mono text-[13px] leading-relaxed">
                {m.content || (streaming ? '…' : '')}
              </div>
            </div>
          ))}
        </div>
        <form
          onSubmit={onSubmit}
          className="flex gap-2 border-t border-slate-700/70 p-3"
        >
          <input
            className="min-w-0 flex-1 rounded-md border border-slate-600 bg-slate-950/80 px-3 py-2 text-sm text-slate-100 outline-none focus:border-cyan-500/70"
            placeholder="Ask the SOC agents…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={streaming}
          />
          <Button type="submit" disabled={streaming || !input.trim()}>
            {streaming ? 'Streaming…' : 'Send'}
          </Button>
        </form>
      </Card>
    </div>
  )
}
