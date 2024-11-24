import React, { useCallback, useEffect } from 'react';
import { useSearch, useQuerySuggestions } from '../hooks/useApi';
import { useSearchStore } from '../store/store';
import { SearchRequest } from '../lib/api/types';
import { useDebounce } from '../hooks/useDebounce';

export const Search: React.FC = () => {
  const {
    searchQuery,
    searchResults,
    isSearching,
    setSearchQuery,
    setSearchResults,
    setIsSearching,
  } = useSearchStore();

  const { execute: search, loading: searchLoading } = useSearch();
  const { execute: getSuggestions, data: suggestions } = useQuerySuggestions();

  const debouncedQuery = useDebounce(searchQuery, 300);

  useEffect(() => {
    if (debouncedQuery) {
      const searchRequest: SearchRequest = {
        query: debouncedQuery,
        page: 1,
        limit: 10,
      };
      search(searchRequest);
    }
  }, [debouncedQuery, search]);

  useEffect(() => {
    if (searchQuery.length >= 2) {
      getSuggestions(searchQuery);
    }
  }, [searchQuery, getSuggestions]);

  const handleSearchChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      setSearchQuery(event.target.value);
      setIsSearching(true);
    },
    [setSearchQuery, setIsSearching]
  );

  return (
    <div className="p-4">
      <div className="relative">
        <input
          type="text"
          className="w-full px-4 py-2 text-gray-900 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
          placeholder="Search documents..."
          value={searchQuery}
          onChange={handleSearchChange}
        />
        {searchLoading && (
          <div className="absolute right-3 top-2.5">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-900"></div>
          </div>
        )}
      </div>

      {suggestions && suggestions.length > 0 && (
        <div className="mt-2 bg-white rounded-lg shadow-lg">
          {suggestions.map((suggestion, index) => (
            <div
              key={index}
              className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
              onClick={() => setSearchQuery(suggestion)}
            >
              {suggestion}
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 space-y-4">
        {searchResults.map((result) => (
          <div
            key={result.id}
            className="p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
          >
            <h3 className="font-medium">{result.title}</h3>
            <p className="mt-1 text-sm text-gray-600">{result.content_type}</p>
            {result.doc_metadata && (
              <div className="mt-2 text-sm text-gray-500">
                <pre className="whitespace-pre-wrap">
                  {JSON.stringify(result.doc_metadata, null, 2)}
                </pre>
              </div>
            )}
          </div>
        ))}
        {!searchLoading && searchResults.length === 0 && searchQuery && (
          <div className="text-center text-gray-500">No results found</div>
        )}
      </div>
    </div>
  );
};
