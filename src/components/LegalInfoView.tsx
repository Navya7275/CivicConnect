import React, { useState, useTransition } from 'react';
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
  const [isPending, startTransition] = useTransition();

  const filteredActs = mockLegalActs.filter(a => 
    searchQuery.trim() === '' ||
    a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    startTransition(() => {
      setSearchQuery(val);
    });
  };

  return (
    <div className="h-full flex flex-col bg-canvas select-text min-w-0" aria-label="Legislative Index Explorer Panel">
      
      {/* Top Header */}
      <div className="p-6 border-b border-hairline shrink-0">
        <span className="text-caption-mono text-accent-breeze tracking-wider block mb-1">catalog</span>
        <h1 className="text-display-xs text-ink font-semibold">Indian Laws & Acts</h1>
      </div>

      {/* Controls Panel */}
      <div className="p-6 border-b border-hairline shrink-0">
        <div className="relative">
          <label htmlFor="app-act-search" className="sr-only">Search legislation</label>
          <input 
            type="text" 
            id="app-act-search"
            placeholder="Search acts, codes, regulations…" 
            defaultValue={searchQuery}
            onChange={handleSearchChange}
            className="w-full pl-9 pr-4 py-2 bg-canvas-soft border border-hairline rounded-sm text-body-sm focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
          />
          <div className="absolute left-3 top-2.5 text-mute" aria-hidden="true">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          </div>
        </div>
      </div>

      {/* Main Grid View / Section Explorer split pane */}
      <div className="flex-grow overflow-hidden flex flex-col md:flex-row">
        {selectedAct ? (
          /* Sections explorer mode */
          <div className="flex-grow flex flex-col md:flex-row h-full overflow-hidden w-full">
            {/* Sections list */}
            <div className="w-full md:w-1/3 border-b md:border-b-0 md:border-r border-hairline overflow-y-auto max-h-[30vh] md:max-h-none p-4 space-y-1">
              <button 
                onClick={() => { setSelectedAct(null); setActiveSection(null); }}
                className="text-caption-mono-sm text-ink hover:text-accent-sunset flex items-center gap-1 mb-4"
              >
                ➔ back to acts
              </button>
              
              <div className="text-[10px] text-mute/50 uppercase tracking-widest pl-2 mb-2 font-mono">sections</div>
              {selectedAct.sections.map(sec => (
                <button
                  key={sec.number}
                  onClick={() => setActiveSection(sec)}
                  className={`w-full text-left p-2.5 text-body-sm rounded-sm transition-all duration-200 outline-none focus-visible:ring-2 focus-visible:ring-primary ${activeSection?.number === sec.number ? 'bg-canvas-soft text-ink font-medium border-l-2 border-primary' : 'text-mute hover:text-ink hover:bg-canvas-soft/30'}`}
                >
                  <div className="font-mono text-xs text-accent-sunset">{sec.number}</div>
                  <div className="truncate mt-0.5">{sec.title}</div>
                </button>
              ))}
            </div>

            {/* Sections text details */}
            <div className="w-full md:w-2/3 p-6 overflow-y-auto flex flex-col justify-between h-full">
              {activeSection ? (
                <div className="space-y-6">
                  <div>
                    <span className="text-caption-mono text-accent-sunset tracking-wider block mb-1 font-mono">section reference</span>
                    <h2 className="text-body-md md:text-body-lg text-ink font-semibold">{activeSection.number}: {activeSection.title}</h2>
                  </div>
                  <div className="text-body-sm text-mute leading-relaxed bg-canvas border border-hairline rounded-sm p-4 font-mono select-all">
                    {activeSection.content}
                  </div>
                </div>
              ) : (
                <div className="text-center py-16 text-mute">
                  Select a section in the list to view its official legislative text parameters.
                </div>
              )}

              {activeSection && (
                <div className="border-t border-hairline pt-6 mt-6 flex items-center justify-end">
                  <button 
                    onClick={() => onAskAboutLaw(`Explain the provisions of ${selectedAct.name} ${activeSection.number}: ${activeSection.title}`)}
                    className="button-pill button-pill-primary text-caption-mono-sm"
                  >
                    ask assistant about this section
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Acts catalog grid mode */
          <div className="flex-grow overflow-y-auto p-6 space-y-6">
            {filteredActs.length === 0 ? (
              <div className="text-center py-12 text-mute">
                No legislative acts found matching your search.
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-6">
                {filteredActs.map(act => {
                  const isSaved = savedActIds.includes(act.id);
                  return (
                    <div 
                      key={act.id} 
                      className="bg-canvas-card border border-hairline rounded-sm p-6 hover:border-body-mid transition-all duration-300 space-y-4"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="flex items-center gap-2 mb-2 select-none">
                            <span className="text-caption-mono-sm text-accent-breeze bg-accent-breeze/10 px-2 py-0.5 rounded-full uppercase">{act.jurisdiction}</span>
                          </div>
                          <h2 className="text-body-md text-ink font-semibold">{act.name}</h2>
                        </div>

                        {/* Bookmark Button */}
                        <button 
                          type="button"
                          onClick={() => onSaveAct(act)}
                          className={`p-2 rounded-sm border transition-colors outline-none focus-visible:ring-2 focus-visible:ring-primary ${isSaved ? 'bg-accent-sunset/15 border-accent-sunset text-accent-sunset' : 'border-hairline text-mute hover:text-ink hover:bg-canvas-soft'}`}
                          aria-label={isSaved ? `Remove bookmark for ${act.name}` : `Save bookmark for ${act.name}`}
                        >
                          <svg className="w-4 h-4" fill={isSaved ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/></svg>
                        </button>
                      </div>

                      <p className="text-body-sm text-mute leading-relaxed">{act.description}</p>

                      <div className="flex items-center justify-between pt-2 border-t border-hairline/30">
                        <button 
                          onClick={() => { setSelectedAct(act); setActiveSection(act.sections[0] || null); }}
                          className="text-caption-mono-sm text-ink hover:text-accent-sunset transition-colors"
                        >
                          browse sections ({act.sections.length}) ➔
                        </button>
                        <button 
                          onClick={() => onAskAboutLaw(`Explain the structure and main clauses of ${act.name}`)}
                          className="button-pill button-pill-outline text-caption-mono-sm tracking-wider"
                        >
                          ask assistant
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

    </div>
  );
}


