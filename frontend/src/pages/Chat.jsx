import { useState } from 'react'

import ChatWindow from '../components/chat/ChatWindow'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'
import Loader from '../components/ui/Loader'
import { useChat } from '../hooks/useChat'
import { useTickers } from '../hooks/useTickers'

export default function Chat() {
  const [tickerInput, setTickerInput] = useState('AAPL')
  const [prompt, setPrompt] = useState('')
  const { symbol, setSymbol, messages, loading, error, sendMessage, resetConversation } = useChat('AAPL')
  const { tickers } = useTickers()

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!prompt.trim()) return

    const nextSymbol = tickerInput.replace(/[^A-Z]/g, '').slice(0, 10) || 'AAPL'
    setSymbol(nextSymbol)
    const nextPrompt = prompt.trim()
    setPrompt('')

    try {
      await sendMessage(nextPrompt, nextSymbol)
    } catch {
      // Error is surfaced by the hook state.
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <div className="grid gap-4 md:grid-cols-[180px_1fr]">
          <label>
            <span className="mb-2 block text-sm text-gray-400">Ticker Context</span>
            <Input
              value={tickerInput}
              disabled={loading}
              onChange={(e) => setTickerInput(e.target.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 10))}
              maxLength={10}
              list="ticker-options-chat"
            />
            <datalist id="ticker-options-chat">
              {tickers.map((item) => (
                <option key={item} value={item} />
              ))}
            </datalist>
          </label>
          <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-gray-300">
            Active symbol: <span className="font-semibold text-gray-100">{symbol}</span>. Context is sent with each prompt.
          </div>
        </div>
      </Card>

      <Card>
        <ChatWindow messages={messages} />
        {loading && <div className="mt-4"><Loader label="AI is thinking" /></div>}
        {error && <p className="mt-4 text-sm text-rose-300">{error}</p>}

        <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-3 md:flex-row md:items-end">
          <Input
            value={prompt}
            disabled={loading}
            onChange={(e) => setPrompt(e.target.value.slice(0, 4000))}
            placeholder="Ask about trend, risk, or signal rationale..."
            aria-label="Chat prompt"
          />
          <div className="flex items-center justify-between gap-3 md:min-w-[220px] md:flex-col md:items-end">
            <span className="text-xs text-gray-400">{prompt.length}/4000</span>
            <div className="flex gap-3">
              <Button type="submit" disabled={loading || !prompt.trim()}>{loading ? 'Sending...' : 'Send'}</Button>
              <Button type="button" variant="outline" disabled={loading} onClick={resetConversation}>Reset</Button>
            </div>
          </div>
        </form>
      </Card>
    </div>
  )
}
