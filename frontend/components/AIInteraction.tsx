import React, { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation } from 'react-query';
import { FiSend, FiCpu, FiImage, FiFileText, FiCode } from 'react-icons/fi';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachments?: {
    type: string;
    url: string;
    preview?: string;
  }[];
}

interface AIAction {
  type: string;
  description: string;
  icon: React.ReactNode;
}

const AIInteraction: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);
  
  const availableActions: AIAction[] = [
    {
      type: 'analyze',
      description: 'Analyze document content',
      icon: <FiFileText />,
    },
    {
      type: 'process_image',
      description: 'Process and analyze images',
      icon: <FiImage />,
    },
    {
      type: 'code_analysis',
      description: 'Analyze code files',
      icon: <FiCode />,
    },
  ];

  // Scroll to bottom when messages change
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // AI interaction mutation
  const aiMutation = useMutation(
    async ({ message, files }: { message: string; files: File[] }) => {
      const formData = new FormData();
      formData.append('message', message);
      files.forEach(file => formData.append('files', file));

      const response = await fetch('/api/ai/interact', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('AI interaction failed');
      return response.json();
    },
    {
      onSuccess: (data) => {
        setMessages(prev => [
          ...prev,
          {
            id: Date.now().toString(),
            role: 'assistant',
            content: data.response,
            timestamp: new Date(),
            attachments: data.attachments,
          },
        ]);
        setSelectedFiles([]);
        setInput('');
      },
    }
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && selectedFiles.length === 0) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
      attachments: selectedFiles.map(file => ({
        type: file.type,
        url: URL.createObjectURL(file),
        preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
      })),
    };

    setMessages(prev => [...prev, newMessage]);
    aiMutation.mutate({ message: input, files: selectedFiles });
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Actions Bar */}
      <div className="p-4 border-b bg-white">
        <h2 className="text-lg font-medium mb-3">AI Assistant</h2>
        <div className="flex gap-3">
          {availableActions.map(action => (
            <button
              key={action.type}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100"
            >
              {action.icon}
              <span>{action.description}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-auto p-4">
        <div className="space-y-4">
          {messages.map(message => (
            <div
              key={message.id}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-3/4 p-4 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-white border'
                }`}
              >
                <p>{message.content}</p>
                {message.attachments && message.attachments.length > 0 && (
                  <div className="mt-2 space-y-2">
                    {message.attachments.map((attachment, index) => (
                      <div key={index} className="flex items-center gap-2">
                        {attachment.preview ? (
                          <img
                            src={attachment.preview}
                            alt="Preview"
                            className="w-16 h-16 object-cover rounded"
                          />
                        ) : (
                          <div className="w-16 h-16 flex items-center justify-center bg-gray-100 rounded">
                            <FiFileText className="text-2xl text-gray-500" />
                          </div>
                        )}
                        <a
                          href={attachment.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm underline"
                        >
                          View attachment
                        </a>
                      </div>
                    ))}
                  </div>
                )}
                <div className="mt-1 text-xs opacity-70">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4 border-t bg-white">
        <form onSubmit={handleSubmit} className="flex gap-4">
          <input
            type="file"
            multiple
            onChange={(e) => setSelectedFiles(Array.from(e.target.files || []))}
            className="hidden"
            id="file-input"
          />
          <label
            htmlFor="file-input"
            className="px-4 py-2 border rounded-lg hover:bg-gray-50 cursor-pointer"
          >
            Attach Files
          </label>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything about your files..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={aiMutation.isLoading}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {aiMutation.isLoading ? (
              <FiCpu className="animate-spin" />
            ) : (
              <FiSend />
            )}
          </button>
        </form>
        {selectedFiles.length > 0 && (
          <div className="mt-2 flex gap-2">
            {selectedFiles.map((file, index) => (
              <div
                key={index}
                className="px-2 py-1 bg-gray-100 rounded-lg text-sm flex items-center gap-2"
              >
                <span>{file.name}</span>
                <button
                  onClick={() => {
                    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
                  }}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AIInteraction;
