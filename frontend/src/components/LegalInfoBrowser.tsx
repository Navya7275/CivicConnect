import { useState, useTransition, type ChangeEvent } from 'react';
import { mockLegalActs } from '../services/mockData';
import type { LegalAct, LegalSection } from '../services/api';

export default function LegalInfoBrowser() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedJurisdiction, setSelectedJurisdiction] = useState<'All' | 'central' | 'state'>('All');
  const [activeAct, setActiveAct] = useState<LegalAct | null>(null);
  const [activeSection, setActiveSection] = useState<LegalSection | null>(null);
  const [, startTransition] = useTransition();

  const filteredActs = mockLegalActs.filter(a => {
    const matchesJur = selectedJurisdiction === 'All' || a.jurisdiction === selectedJurisdiction;
    const matchesSearch = searchQuery.trim() === '' ||
      a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.sections.some(s => s.title.toLowerCase().includes(searchQuery.toLowerCase()) || s.content.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesJur && matchesSearch;
  });

  const handleSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    startTransition(() => {
      setSearchQuery(val);
    });
  };

  return (
    <div className="space-y-8 min-w-0">
      {/* Search & Scope Panel */}
      <div className="card !p-6 flex flex-col md:flex-row gap-4 items-center justify-between">
        {/* Search bar */}
        <div className="flex-grow w-full relative flex items-center">
          <div className="absolute left-3.5 pointer-events-none text-muted-foreground flex items-center justify-center" aria-hidden="true">
            <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          </div>
          <label htmlFor="act-search" className="sr-only">Search legislation</label>
          <input 
            type="text" 
            id="act-search"
            placeholder="Search statutory acts, sections, keywords (e.g. RTI, penalties, bail)…" 
            defaultValue={searchQuery}
            onChange={handleSearchChange}
            className="input !pl-11"
          />
        </div>

        {/* Jurisdiction Segmented Control */}
        <div className="tabs shrink-0" role="group" aria-label="Legislative Jurisdiction Selection">
          <button 
            type="button"
            onClick={() => setSelectedJurisdiction('All')}
            aria-selected={selectedJurisdiction === 'All'}
            className="tab"
          >
            All Acts
          </button>
          <button 
            type="button"
            onClick={() => setSelectedJurisdiction('central')}
            aria-selected={selectedJurisdiction === 'central'}
            className="tab"
          >
            Central
          </button>
          <button 
            type="button"
            onClick={() => setSelectedJurisdiction('state')}
            aria-selected={selectedJurisdiction === 'state'}
            className="tab"
          >
            State
          </button>
        </div>
      </div>

      {/* Acts Display List */}
      {filteredActs.length === 0 ? (
        <div className="text-center py-20 border border-border border-dashed rounded-ui-lg bg-card p-8">
          <svg className="w-10 h-10 mx-auto text-muted-foreground mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <h3 className="text-h3 text-lg mb-2">No Legislative Acts Found</h3>
          <p className="text-small text-muted-foreground max-w-sm mx-auto">
            Try typing another keyword like 'RTI' or search Central Acts.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 min-w-0">
          {filteredActs.map(act => (
            <div 
              key={act.id} 
              className="card flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="badge badge-soft uppercase" data-tone="accent">
                    {act.jurisdiction}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {act.sections.length} sections indexed
                  </span>
                </div>

                <h3 className="text-h3 text-xl">{act.name}</h3>
                <p className="text-small text-muted-foreground line-clamp-3 leading-relaxed">
                  {act.description}
                </p>
              </div>

              <div className="pt-4 border-t border-border flex items-center justify-between">
                <a 
                  href={`/assistant?query=${encodeURIComponent(`Explain the primary purpose, structure, and key sections of the ${act.name}.`)}`}
                  className="btn btn-outline btn-sm"
                >
                  Ask Assistant →
                </a>
                <span className="text-xs text-muted-foreground">Official Gazette Grounded</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
