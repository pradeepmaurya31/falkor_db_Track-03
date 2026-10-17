import React, { useState } from 'react';

export default function ChatDrawer({ token }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async (e) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || !token) return;

    const userMsg = trimmed;
    setInput('');
    setMessages((prev) => [...prev, { sender: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch('http://localhost:8000/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: userMsg }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Chat request failed');
      }

      if (!res.body) {
        throw new Error('No response body returned by the chat API');
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let agentReply = '';

      setMessages((prev) => [...prev, { sender: 'agent', text: '...' }]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          const dataLine = line.trim();
          if (!dataLine.startsWith('data:')) continue;

          const messageText = dataLine.replace(/^data:\s*/, '').trim();
          if (!messageText || messageText === '[DONE]') continue;

          agentReply = messageText;
          setMessages((prev) => {
            const nextMessages = [...prev];
            nextMessages[nextMessages.length - 1] = { sender: 'agent', text: agentReply };
            return nextMessages;
          });
        }
      }

      if (buffer.trim()) {
        const messageText = buffer.trim().replace(/^data:\s*/, '');
        if (messageText && messageText !== '[DONE]') {
          agentReply = messageText;
          setMessages((prev) => {
            const nextMessages = [...prev];
            nextMessages[nextMessages.length - 1] = { sender: 'agent', text: agentReply };
            return nextMessages;
          });
        }
      }
    } catch (err) {
      console.error(err);
      setMessages((prev) => [...prev, { sender: 'agent', text: err.message || 'Something went wrong while sending the message.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-96 h-screen bg-white border-l flex flex-col fixed right-0 top-0 shadow-xl">
      <div className="bg-blue-600 text-white p-4 font-bold">Enterprise Assistant</div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`p-3 rounded-lg max-w-[85%] ${m.sender === 'user' ? 'ml-auto bg-blue-100 text-blue-900' : 'mr-auto bg-gray-100 text-gray-800'}`}
          >
            <p className="text-sm whitespace-pre-line">{m.text}</p>
          </div>
        ))}
      </div>
      <form onSubmit={sendMessage} className="p-3 border-t flex gap-2">
        <input
          type="text"
          className="flex-1 border rounded px-3 py-2 text-sm focus:outline-none"
          placeholder="Ask anything or raise a ticket..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button type="submit" disabled={loading} className="bg-blue-600 text-white px-4 py-2 rounded text-sm disabled:opacity-60">
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
}