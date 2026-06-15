export default function ChatBubble({ role, text }) {
  const isUser = role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={[
          'max-w-[92%] rounded-2xl px-4 py-3 text-sm shadow-lg sm:max-w-[80%]',
          isUser ? 'bg-cyan-300 text-slate-900' : 'border border-white/10 bg-white/10 text-gray-100 backdrop-blur-xl',
        ].join(' ')}
      >
        <p className="whitespace-pre-wrap">{text}</p>
      </div>
    </div>
  )
}
