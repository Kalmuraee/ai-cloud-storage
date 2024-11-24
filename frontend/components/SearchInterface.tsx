import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { FiSearch, FiFile, FiClock } from 'react-icons/fi';

interface SearchResult {
  id: string;
  content: string;
  metadata: {
    filename: string;
    type: string;
    lastModified: string;
    path: string;
  };
  score: number;
}

const SearchInterface: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, string>>({});

  const { data: searchResults, isLoading } = useQuery(
    ['search', searchQuery, filters],
    async () => {
      if (!searchQuery) return [];

      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery,
          filters,
          limit: 20
        }),
      });

      if (!response.ok) throw new Error('Search failed');
      return response.json();
    },
    {
      enabled: searchQuery.length > 0,
    }
  );

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Trigger search query refetch
  };

  return (
    <div className="flex flex-col h-full">
      {/* Search Bar */}
      <div className="p-4 border-b">
        <form onSubmit={handleSearch} className="flex gap-4">
          <div className="flex-1 relative">
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search files by content or metadata..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            type="submit"
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Search
          </button>
        </form>

        {/* Filters */}
        <div className="flex gap-4 mt-4">
          <select
            onChange={(e) => setFilters({ ...filters, type: e.target.value })}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Types</option>
            <option value="document">Documents</option>
            <option value="image">Images</option>
            <option value="code">Code</option>
          </select>
          <input
            type="date"
            onChange={(e) => setFilters({ ...filters, date: e.target.value })}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Search Results */}
      <div className="flex-1 overflow-auto p-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          </div>
        ) : searchResults?.length > 0 ? (
          <div className="space-y-4">
            {searchResults.map((result: SearchResult) => (
              <div
                key={result.id}
                className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3 mb-2">
                  <FiFile className="text-gray-500" />
                  <span className="font-medium">{result.metadata.filename}</span>
                  <span className="text-sm text-gray-500">
                    ({result.metadata.type})
                  </span>
                </div>
                <p className="text-gray-600 mb-2">{result.content}</p>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span className="flex items-center gap-1">
                    <FiClock className="text-gray-400" />
                    {new Date(result.metadata.lastModified).toLocaleDateString()}
                  </span>
                  <span>Path: {result.metadata.path}</span>
                  <span>Score: {Math.round(result.score * 100)}%</span>
                </div>
              </div>
            ))}
          </div>
        ) : searchQuery ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <FiSearch className="text-4xl mb-2" />
            <p>No results found for "{searchQuery}"</p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <FiSearch className="text-4xl mb-2" />
            <p>Enter a search query to find files</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchInterface;
