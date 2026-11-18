import { useState, useTransition, type ChangeEvent } from 'react';
import { mockWelfareSchemes } from '../services/mockData';
import type { WelfareScheme } from '../services/api';

interface WelfareSchemesViewProps {
  onAskAboutScheme: (query: string) => void;
  onSaveScheme: (scheme: WelfareScheme) => void;
  savedSchemeIds: string[];
}

export default function WelfareSchemesView({
  onAskAboutScheme,
  onSaveScheme,
  savedSchemeIds
}: WelfareSchemesViewProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [, startTransition] = useTransition();

  const categories = ['All', 'Healthcare', 'Agriculture', 'Social Welfare & Pension'];

  const filteredSchemes = mockWelfareSchemes.filter(s => {
    const matchesCategory = selectedCategory === 'All' || s.category === selectedCategory;
    const matchesSearch = searchQuery.trim() === '' || 
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const handleSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    startTransition(() => {
      setSearchQuery(val);
    });
  };

  return (
    <div className="h-full flex flex-col bg-muted/20 select-text min-w-0" aria-label="Welfare Schemes Catalog Panel">
      
      {/* Top Header */}
      <div className="p-6 border-b border-border shrink-0 bg-card">
        <span className="badge badge-soft mb-2" data-tone="accent">Catalog</span>
        <h1 className="text-h2">Government Welfare Schemes</h1>
      </div>

      {/* Controls Panel */}
      <div className="p-6 border-b border-border shrink-0 space-y-4 bg-muted/30">
        <div className="relative max-w-xl flex items-center">
          <div className="absolute left-3 pointer-events-none text-muted-foreground flex items-center justify-center" aria-hidden="true">
            <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          </div>
          <label htmlFor="app-scheme-search" className="sr-only">Search schemes</label>
          <input 
            type="text" 
            id="app-scheme-search"
            placeholder="Search scheme title, eligibility criteria, keywords…" 
            defaultValue={searchQuery}
            onChange={handleSearchChange}
            className="input input-sm !pl-9"
          />
        </div>

        {/* Categories Tabs */}
        <div className="tabs" role="group" aria-label="Welfare category filters">
          {categories.map(cat => (
            <button 
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              aria-selected={selectedCategory === cat}
              className="tab !h-8 text-xs"
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-grow overflow-y-auto p-6 space-y-6">
        {filteredSchemes.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground text-sm">
            No welfare schemes found matching your search.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl">
            {filteredSchemes.map(sch => {
              const isSaved = savedSchemeIds.includes(sch.id);
              return (
                <div 
                  key={sch.id} 
                  className="card flex flex-col justify-between space-y-4"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="badge badge-soft" data-tone="accent">{sch.state}</span>
                        <span className="badge badge-outline">{sch.category}</span>
                      </div>
                      <button 
                        type="button" 
                        onClick={() => onSaveScheme(sch)}
                        className={`btn btn-ghost btn-sm !h-7 !px-2 ${isSaved ? 'text-accent-fill' : 'text-muted-foreground'}`}
                        title={isSaved ? 'Remove from bookmarks' : 'Save to bookmarks'}
                      >
                        <svg className="w-4 h-4" fill={isSaved ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.75">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
                        </svg>
                      </button>
                    </div>

                    <h2 className="text-h3 text-lg">{sch.name}</h2>
                    <p className="text-small text-muted-foreground leading-relaxed">
                      {sch.description}
                    </p>

                    {/* Eligibility & Benefits Callout */}
                    <div className="p-3 rounded-ui-sm bg-muted/60 text-xs space-y-1.5 border border-border">
                      <div><strong className="text-foreground">Eligibility:</strong> <span className="text-muted-foreground">{sch.eligibility}</span></div>
                      <div><strong className="text-foreground">Benefits:</strong> <span className="text-muted-foreground">{sch.benefits}</span></div>
                    </div>
                  </div>

                  <div className="pt-2 flex items-center justify-between border-t border-border">
                    <button 
                      type="button"
                      onClick={() => onAskAboutScheme(`What are the complete eligibility criteria and required documents for ${sch.name}?`)}
                      className="btn btn-outline btn-sm"
                    >
                      Ask Assistant about this →
                    </button>
                    {sch.source_url && (
                      <a 
                        href={sch.source_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="link text-xs"
                      >
                        Official Portal ↗
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

    </div>
  );
}
