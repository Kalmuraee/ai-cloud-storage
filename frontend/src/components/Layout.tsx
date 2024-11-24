import React from 'react';
import { useUIStore } from '../store/store';
import { DocumentUploader } from './DocumentUploader';
import { DocumentList } from './DocumentList';
import { Search } from './Search';
import { Chat } from './Chat';

export const Layout: React.FC = () => {
  const { sidebarOpen, currentView, setSidebarOpen, setCurrentView } = useUIStore();

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? 'w-64' : 'w-0'
        } transition-all duration-300 bg-white shadow-lg overflow-hidden`}
      >
        <div className="p-4">
          <DocumentUploader />
          <DocumentList />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white shadow-sm">
          <div className="flex items-center justify-between px-4 py-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-lg hover:bg-gray-100"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>

            <nav className="flex space-x-4">
              <button
                onClick={() => setCurrentView('documents')}
                className={`px-4 py-2 rounded-lg ${
                  currentView === 'documents'
                    ? 'bg-blue-500 text-white'
                    : 'hover:bg-gray-100'
                }`}
              >
                Documents
              </button>
              <button
                onClick={() => setCurrentView('search')}
                className={`px-4 py-2 rounded-lg ${
                  currentView === 'search'
                    ? 'bg-blue-500 text-white'
                    : 'hover:bg-gray-100'
                }`}
              >
                Search
              </button>
              <button
                onClick={() => setCurrentView('chat')}
                className={`px-4 py-2 rounded-lg ${
                  currentView === 'chat'
                    ? 'bg-blue-500 text-white'
                    : 'hover:bg-gray-100'
                }`}
              >
                Chat
              </button>
            </nav>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto">
          {currentView === 'documents' && (
            <div className="p-4">
              <h1 className="text-2xl font-bold mb-4">Documents</h1>
              <DocumentList />
            </div>
          )}
          {currentView === 'search' && (
            <div className="p-4">
              <h1 className="text-2xl font-bold mb-4">Search</h1>
              <Search />
            </div>
          )}
          {currentView === 'chat' && (
            <div className="h-full">
              <Chat />
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
