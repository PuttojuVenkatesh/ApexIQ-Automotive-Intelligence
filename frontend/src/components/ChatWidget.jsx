import { useEffect, useRef, useState } from 'react';
import { Check, Loader2, Send, X } from 'lucide-react';
import { askAIChat } from '../services/api';

function FormattedAnswer({ content }) {
  if (!content) return null;

  const lines = content.split('\n');
  const elements = [];
  let listItems = [];

  const flushList = () => {
    if (!listItems.length) return;
    elements.push(
      <ul key={`list-${elements.length}`} className="my-3 space-y-2.5">
        {listItems.map((item, index) => (
          <li key={index} className="flex gap-3">
            <span className="mt-[10px] w-1.5 h-1.5 flex-none rounded-full bg-[#171719]" />
            <span>{renderInline(item)}</span>
          </li>
        ))}
      </ul>
    );
    listItems = [];
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushList();
      return;
    }

    if (trimmed.startsWith('### ')) {
      flushList();
      elements.push(
        <h3 key={index} className="mt-5 mb-2 text-[13px] font-bold uppercase tracking-[0.12em] text-[#171719]">
          {trimmed.replace(/^###\s*/, '')}
        </h3>
      );
      return;
    }

    if (trimmed.startsWith('- ')) {
      listItems.push(trimmed.replace(/^-\s*/, '').replace(/\*{1,2}$/, '').trim());
      return;
    }

    flushList();
    elements.push(
      <p key={index} className="my-2 text-[#373738]">
        {renderInline(trimmed)}
      </p>
    );
  });
  flushList();

  return <div>{elements}</div>;
}

function renderInline(text) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index} className="font-bold text-[#171719]">{part.slice(2, -2)}</strong>;
    }
    return <span key={index}>{part}</span>;
  });
}

export default function ChatWidget({ isOpen, onClose, initialQuery = '' }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Welcome to GearGuide. I can help you compare models, understand specifications and choose the right SUV.\n\nWhat would you like to explore?',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    if (initialQuery && isOpen) sendMessage(initialQuery);
  }, [initialQuery, isOpen]);

  const sendMessage = async (textToSend) => {
    const query = (textToSend || input).trim();
    if (!query || loading) return;

    const conversationHistory = messages
      .filter((message) => message.role === 'user' || message.role === 'assistant')
      .slice(-8)
      .map(({ role, content }) => ({ role, content }));
    setMessages((previous) => [...previous, { role: 'user', content: query }]);
    setInput('');
    setLoading(true);

    try {
      const response = await askAIChat(query, sessionId, null, conversationHistory);
      if (response.session_id) setSessionId(response.session_id);
      setMessages((previous) => [
        ...previous,
        { role: 'assistant', content: response.answer, verified: true, relatedVehicles: response.related_vehicles || [] },
      ]);
    } catch {
      setMessages((previous) => [
        ...previous,
        { role: 'assistant', content: 'That request could not be completed. Please try again.', verified: false },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const prompts = [
    'Compare Alcazar and Creta',
    'Show Creta engine options',
    'Which SUV has the best safety features?',
  ];

  return (
    <div className="fixed inset-y-0 right-0 z-[70] w-full sm:w-[560px] bg-white text-[#171719] shadow-[-30px_0_80px_rgba(0,0,0,.28)] flex flex-col">
      <div className="h-20 px-5 sm:px-7 bg-[#171719] text-white flex items-center justify-between">
        <div>
          <p className="text-[10px] uppercase tracking-[0.24em] text-white/50 mb-1">ApexIQ</p>
          <h2 className="text-xl font-black">GearGuide</h2>
        </div>
        <button onClick={onClose} className="w-11 h-11 border border-white/25 flex items-center justify-center hover:bg-white hover:text-[#171719] transition-colors" aria-label="Close GearGuide">
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-5 sm:px-7 py-8 space-y-7">
        {messages.map((message, index) => (
          <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`w-full ${message.role === 'user' ? 'max-w-[88%] ml-auto text-right' : 'max-w-[92%]'}`}>
              <p className="text-[10px] uppercase tracking-[0.18em] text-[#85847d] mb-2">
                {message.role === 'user' ? 'You' : 'GearGuide'}
              </p>
              <div
                className={`text-[15px] sm:text-base leading-7 ${
                  message.role === 'user'
                    ? 'inline-block bg-[#171719] text-white px-5 py-3 rounded-[20px] rounded-br-md'
                    : 'bg-[#f7f7f5] border border-[#e7e5df] px-5 py-5 rounded-[16px] rounded-tl-md'
                }`}
              >
                {message.role === 'assistant'
                  ? <FormattedAnswer content={message.content} />
                  : message.content}
              </div>
              {message.role === 'assistant' && message.verified && (
                <p className="mt-3 flex items-center gap-2 text-[10px] uppercase tracking-[0.16em] text-[#77766f]">
                  <Check className="w-3.5 h-3.5" />
                  Verified vehicle details
                </p>
              )}
              {message.role === 'assistant' && message.relatedVehicles?.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {message.relatedVehicles.map((vehicle) => (
                    <a
                      key={vehicle.url}
                      href={vehicle.url}
                      onClick={onClose}
                      className="inline-flex items-center gap-2 rounded-full border border-[#d5d2c9] bg-white px-4 py-2 text-xs font-semibold text-[#343431] hover:border-[#171719] transition-colors"
                    >
                      {vehicle.label} <span aria-hidden="true">↗</span>
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-3 text-sm text-[#77766f]">
            <Loader2 className="w-4 h-4 animate-spin" />
            Reviewing vehicle specifications
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {messages.length === 1 && (
        <div className="px-5 sm:px-7 pb-5">
          <p className="text-[10px] uppercase tracking-[0.18em] text-[#85847d] mb-3">Suggested questions</p>
          <div className="flex flex-col border-t border-[#c7c4ba]">
            {prompts.map((prompt) => (
              <button
                key={prompt}
                onClick={() => sendMessage(prompt)}
                className="text-left border-b border-[#c7c4ba] py-4 text-sm font-semibold hover:pl-2 transition-all"
              >
                {prompt} <span className="float-right">→</span>
              </button>
            ))}
          </div>
        </div>
      )}

      <form
        onSubmit={(event) => {
          event.preventDefault();
          sendMessage();
        }}
        className="p-5 sm:p-7 border-t border-[#e1dfd7] bg-white"
      >
        <div className="flex items-end border-b-2 border-[#171719]">
          <input
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask about specifications or features"
            className="flex-1 bg-transparent py-4 text-base outline-none placeholder:text-[#85847d]"
          />
          <button type="submit" disabled={!input.trim() || loading} className="w-12 h-12 mb-1 bg-[#171719] text-white flex items-center justify-center disabled:opacity-30">
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  );
}
