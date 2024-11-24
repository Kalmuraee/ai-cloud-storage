import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useGenerateResponse } from '../hooks/useApi';
import { RAGRequest, RAGResponse } from '../lib/api/types';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  sources?: string[];
}

export const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { execute: generateResponse, loading } = useGenerateResponse();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!input.trim() || loading) return;

      const userMessage: Message = {
        id: Date.now().toString(),
        content: input,
        role: 'user',
      };

      setMessages((prev) => [...prev, userMessage]);
      setInput('');

      const request: RAGRequest = {
        query: input,
      };

      try {
        const response = await generateResponse(request);
        if (response?.data) {
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            content: response.data.response,
            role: 'assistant',
            sources: response.data.sources,
          };
          setMessages((prev) => [...prev, assistantMessage]);
        }
      } catch (error) {
        console.error('Error generating response:', error);
      }
    },
    [input, loading, generateResponse]
  );

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[70%] rounded-lg p-3 ${
                message.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>
              {message.sources && message.sources.length > 0 && (
                <div className="mt-2 text-sm text-gray-500">
                  <p className="font-medium">Sources:</p>
                  <ul className="list-disc list-inside">
                    {message.sources.map((source, index) => (
                      <li key={index}>{source}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex space-x-4">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            ) : (
              'Send'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
