import React, { useState, useTransition } from 'react';
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
  const [selectedScheme, setSelectedScheme] = useState<WelfareScheme | null>(null);
  const [isPending, startTransition] = useTransition();

  const categories = ['All', 'Healthcare', 'Agriculture', 'Social Welfare & Pension'];

  const filteredSchemes = mockWelfareSchemes.filter(s => {
    const matchesCategory = selectedCategory === 'All' || s.category === selectedCategory;
    const matchesSearch = searchQuery.trim() === '' || 
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    startTransition(() => {
      setSearchQuery(val);
    });
  };

  return (
    <div className="h-full flex flex-col bg-canvas select-text min-w-0" aria-label="Welfare Schemes Catalog Panel">
      
      {/* Top Header */}
      <div className="p-6 border-b border-hairline shrink-0">
        <span className="text-caption-mono text-accent-sunset tracking-wider block mb-1">catalog</span>
        <h1 className="text-display-xs text-ink font-semibold">Government Welfare Schemes</h1>
      </div>

      {/* Controls Panel */}
      <div className="p-6 border-b border-hairline shrink-0 space-y-4">
        <div className="relative">
          <label htmlFor="app-scheme-search" className="sr-only">Search schemes</label>
          <input 
            type="text" 
            id="app-scheme-search"
            placeholder="Search scheme title, eligibility keywords…" 
            defaultValue={searchQuery}
            onChange={handleSearchChange}
            className="w-full pl-9 pr-4 py-2 bg-canvas-soft border border-hairline rounded-sm text-body-sm focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
          />
          <div className="absolute left-3 top-2.5 text-mute" aria-hidden="true">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          </div>
        </div>

        {/* Horizontal Scrollable Categories */}
        <div className="flex flex-wrap gap-2 items-center" role="group" aria-label="Welfare category filters">
          {categories.map(cat => (
            <button 
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`button-pill text-caption-mono-sm transition-all duration-200 ${selectedCategory === cat ? 'button-pill-primary' : 'button-pill-outline'}`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area (Scrollable Catalog Grid) */}
      <div className="flex-grow overflow-y-auto p-6 space-y-6">
        {filteredSchemes.length === 0 ? (
          <div className="text-center py-12 text-mute">
            No welfare schemes found matching your search.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6">
            {filteredSchemes.map(sch => {
              const isSaved = savedSchemeIds.includes(sch.id);
              return (
                <div 
                  key={sch.id} 
                  className="bg-canvas-card border border-hairline rounded-sm p-6 hover:border-body-mid transition-all duration-300 space-y-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-2 select-none">
                        <span className="text-caption-mono-sm text-accent-sunset bg-accent-sunset/10 px-2 py-0.5 rounded-full uppercase">{sch.state}</span>
                        <span className="text-caption-mono-sm text-mute uppercase">{sch.category}</span>
                      </div>
                      <h2 className="text-body-md text-ink font-semibold">{sch.name}</h2>
                    </div>

                    {/* Bookmark Button */}
                    <button 
                      type="button"
                      onClick={() => onSaveScheme(sch)}
                      className={`p-2 rounded-sm border transition-colors outline-none focus-visible:ring-2 focus-visible:ring-primary ${isSaved ? 'bg-accent-sunset/15 border-accent-sunset text-accent-sunset' : 'border-hairline text-mute hover:text-ink hover:bg-canvas-soft'}`}
                      aria-label={isSaved ? `Remove bookmark for ${sch.name}` : `Save bookmark for ${sch.name}`}
                    >
                      <svg className="w-4 h-4" fill={isSaved ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/></svg>
                    </button>
                  </div>

                  <p className="text-body-sm text-mute leading-relaxed">{sch.description}</p>

                  {/* Expandable details drawer inside card */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs pt-2">
                    <div className="bg-canvas border border-hairline p-4 rounded-sm">
                      <span className="text-caption-mono-sm text-accent-breeze tracking-wider block mb-1.5 lowercase">eligibility:</span>
                      <p className="text-mute">{sch.eligibility}</p>
                    </div>
                    <div className="bg-canvas border border-hairline p-4 rounded-sm">
                      <span className="text-caption-mono-sm text-accent-sunset-soft tracking-wider block mb-1.5 lowercase">benefits:</span>
                      <p className="text-mute">{sch.benefits}</p>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-hairline/30">
                    <div className="text-xs text-mute/60">
                      Required Documents: {sch.requiredDocuments.join(', ')}
                    </div>
                    <button 
                      type="button"
                      onClick={() => onAskAboutScheme(`Who is eligible for ${sch.name} and what documents are required?`)}
                      className="button-pill button-pill-outline text-caption-mono-sm tracking-wider hover:scale-105"
                    >
                      ask assistant about this
                    </button>
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


