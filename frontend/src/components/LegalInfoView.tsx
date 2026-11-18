import { useState, useTransition, type ChangeEvent } from 'react';
import { mockLegalActs } from '../services/mockData';
import type { LegalAct, LegalSection } from '../services/api';

interface LegalInfoViewProps {
  onAskAboutLaw: (query: string) => void;
  onSaveAct: (act: LegalAct) => void;
  savedActIds: string[];
}

export default function LegalInfoView({
  onAskAboutLaw,
  onSaveAct,
  savedActIds
}: LegalInfoViewProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAct, setSelectedAct] = useState<LegalAct | null>(null);
  const [activeSection, setActiveSection] = useState<LegalSection | null>(null);
  const [, startTransition] = useTransition();

  const filteredActs = mockLegalActs.filter(a => 
    searchQuery.trim() === '' ||
    a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    startTransition(() => {
      setSearchQuery(val);
    });
  };

  return (
    <div className="h-full flex flex-col bg-muted/20 select-text min-w-0" aria-label="Legislative Index Explorer Panel">
      
      {/* Top Header */}
      <div className="p-6 border-b border-border shrink-0 bg-card">
        <span className="badge badge-soft mb-2" data-tone="accent">Legislation</span>
        <h1 className="text-h2">Indian Laws & Acts</h1>
      </div>

      {/* Controls Panel */}
      <div className="p-6 border-b border-border shrink-0 bg-muted/30">
        <div className="relative max-w-xl flex items-center">
          <div className="absolute left-3 pointer-events-none text-muted-foreground flex items-center justify-center" aria-hidden="true">
            <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          </div>
          <label htmlFor="app-act-search" className="sr-only">Search legislation</label>
          <input 
            type="text" 
            id="app-act-search"
            placeholder="Search statutory acts, sections, regulations…" 
            defaultValue={searchQuery}
            onChange={handleSearchChange}
            className="input input-sm !pl-9"
          />
        </div>
      </div>

      {/* Main Grid View / Section Explorer split pane */}
      <div className="flex-grow overflow-hidden flex flex-col md:flex-row">
        {selectedAct ? (
          /* Sections explorer mode */
          <div className="flex-grow flex flex-col md:flex-row h-full overflow-hidden w-full">
            {/* Sections list */}
            <div className="w-full md:w-1/3 border-b md:border-b-0 md:border-r border-border overflow-y-auto max-h-[35vh] md:max-h-none p-4 space-y-1 bg-muted/20">
              <button 
                onClick={() => { setSelectedAct(null); setActiveSection(null); }}
                className="btn btn-secondary btn-sm mb-3 gap-1.5"
              >
                ← Back to Acts
              </button>
              
              <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider px-2 py-1">
                Sections ({selectedAct.sections.length})
              </div>
              {selectedAct.sections.map(sec => (
                <button
                  key={sec.number}
                  onClick={() => setActiveSection(sec)}
                  className={`w-full text-left p-2.5 rounded-ui-sm transition-colors text-xs ${activeSection?.number === sec.number ? 'bg-card text-foreground font-medium shadow-ui-sm border border-border' : 'text-muted-foreground hover:text-foreground hover:bg-muted/60'}`}
                >
                  <div className="text-mono font-medium text-accent-foreground">{sec.number}</div>
                  <div className="truncate mt-0.5 text-foreground">{sec.title}</div>
                </button>
              ))}
            </div>

            {/* Section details */}
            <div className="w-full md:w-2/3 p-6 overflow-y-auto flex flex-col justify-between h-full bg-card">
              {activeSection ? (
                <div className="space-y-6">
                  <div>
                    <span className="badge badge-soft mb-2" data-tone="primary">Section Reference</span>
                    <h2 className="text-h3 text-xl">{activeSection.number}: {activeSection.title}</h2>
                    <div className="text-xs text-muted-foreground mt-1">{selectedAct.name}</div>
                  </div>
                  <div className="text-small text-foreground leading-relaxed bg-muted/40 border border-border rounded-ui-md p-5 select-all">
                    {activeSection.content}
                  </div>
                </div>
              ) : (
                <div className="text-center py-16 text-muted-foreground text-sm">
                  Select a section from the left column to view statutory details.
                </div>
              )}

              {activeSection && (
                <div className="pt-6 border-t border-border flex items-center justify-between">
                  <button
                    type="button"
                    onClick={() => onAskAboutLaw(`What does ${activeSection.number} of ${selectedAct.name} state, and how is it applied?`)}
                    className="btn btn-outline btn-sm"
                  >
                    Ask Assistant about {activeSection.number} →
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Acts catalog grid */
          <div className="flex-grow overflow-y-auto p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl">
              {filteredActs.map(act => {
                const isSaved = savedActIds.includes(act.id);
                return (
                  <div key={act.id} className="card flex flex-col justify-between space-y-4">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="badge badge-soft uppercase" data-tone="accent">{act.jurisdiction}</span>
                        <button 
                          type="button" 
                          onClick={() => onSaveAct(act)}
                          className={`btn btn-ghost btn-sm !h-7 !px-2 ${isSaved ? 'text-accent-fill' : 'text-muted-foreground'}`}
                          title={isSaved ? 'Remove bookmark' : 'Save act'}
                        >
                          <svg className="w-4 h-4" fill={isSaved ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.75">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
                          </svg>
                        </button>
                      </div>

                      <h2 className="text-h3 text-lg">{act.name}</h2>
                      <p className="text-small text-muted-foreground leading-relaxed line-clamp-3">
                        {act.description}
                      </p>

                      <div className="text-xs text-muted-foreground">
                        {act.sections.length} sections indexed in database
                      </div>
                    </div>

                    <div className="pt-3 flex items-center justify-between border-t border-border">
                      <button
                        type="button"
                        onClick={() => { setSelectedAct(act); setActiveSection(act.sections[0] || null); }}
                        className="btn btn-secondary btn-sm"
                      >
                        Explore Sections →
                      </button>
                      <button
                        type="button"
                        onClick={() => onAskAboutLaw(`Explain the key provisions and scope of the ${act.name}.`)}
                        className="btn btn-outline btn-sm"
                      >
                        Ask Assistant
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
