import { memo } from 'react'

import ChatBubble from './ChatBubble'
import EmptyState from '../ui/EmptyState'

const ChatWindow = memo(function ChatWindow({ messages }) {
  return (
    <div className="flex h-[26rem] flex-col gap-4 overflow-y-auto rounded-2xl border border-white/10 bg-slate-950/40 p-4" role="log" aria-live="polite" aria-relevant="additions text">
      {messages.length ? (
        messages.map((message) => (
          <ChatBubble key={message.id} role={message.role} text={message.text} />
        ))
      ) : (
        <div className="flex h-full items-center justify-center">
          <EmptyState
            title="Start a conversation"
            description="Ask for a market view, signal explanation, or a risk summary for the selected ticker."
          />
        </div>
      )}
    </div>
  )
})

export default ChatWindow
