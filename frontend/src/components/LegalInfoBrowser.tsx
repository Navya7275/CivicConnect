import { useState, useTransition, type ChangeEvent } from 'react';
import { mockLegalActs } from '../services/mockData';
import type { LegalAct, LegalSection } from '../services/api';

export default function LegalInfoBrowser() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedJurisdiction, setSelectedJurisdiction] = useState<'All' | 'central' | 'state'>('All');
  const [activeAct, setActiveAct] = useState<LegalAct | null>(null);
  const [activeSection, setActiveSection] = useState<LegalSection | null>(null);
  const [, startTransition] = useTransition();

  // Filter legal acts
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
      {/* Search Panel */}
      <div className="bg-canvas-card border border-hairline rounded-sm p-6 flex flex-col md:flex-row gap-4">
        {/* Search bar */}
        <div className="flex-grow relative">
          <label htmlFor="act-search" className="sr-only">Search legislation</label>
          <input 
            type="text" 
            id="act-search"
            placeholder="Search acts, sections, keywords (e.g. RTI, common intention)…" 
            defaultValue={searchQuery}
            onChange={handleSearchChange}
            className="w-full pl-10 pr-4 py-3 bg-canvas-soft border border-hairline rounded-sm text-body-md focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
          />
          <div className="absolute left-3 top-3.5 text-mute" aria-hidden="true">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          </div>
        </div>

        {/* Jurisdiction Toggle */}
        <div className="flex items-center border border-hairline rounded-sm p-1 bg-canvas-soft" role="group" aria-label="Legislative Jurisdiction Selection">
          <button 
            onClick={() => setSelectedJurisdiction('All')}
            className={`px-4 py-2 text-caption-mono-sm rounded-sm transition-all duration-200 ${selectedJurisdiction === 'All' ? 'bg-primary text-on-primary' : 'text-mute hover:text-ink'}`}
          >
            all
          </button>
          <button 
            onClick={() => setSelectedJurisdiction('central')}
            className={`px-4 py-2 text-caption-mono-sm rounded-sm transition-all duration-200 ${selectedJurisdiction === 'central' ? 'bg-primary text-on-primary' : 'text-mute hover:text-ink'}`}
          >
            central
          </button>
          <button 
            onClick={() => setSelectedJurisdiction('state')}
            className={`px-4 py-2 text-caption-mono-sm rounded-sm transition-all duration-200 ${selectedJurisdiction === 'state' ? 'bg-primary text-on-primary' : 'text-mute hover:text-ink'}`}
          >
            state
          </button>
        </div>
      </div>

      {/* Acts Display List */}
      {filteredActs.length === 0 ? (
        <div className="text-center py-16 border border-hairline border-dashed rounded-sm bg-canvas-card">
          <svg className="w-12 h-12 mx-auto text-mute mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          <h3 className="text-body-md text-ink font-semibold mb-2">No Legislative Acts Found</h3>
          <p className="text-body-sm text-mute max-w-sm mx-auto">Try typing another keyword like 'RTI' or search Central Acts.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 min-w-0">
          {filteredActs.map(act => (
            <div 
              key={act.id} 
              className="bg-canvas-card border border-hairline rounded-sm p-6 hover:border-body-mid transition-all duration-300 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-caption-mono-sm text-accent-breeze tracking-wider bg-accent-breeze/10 px-2.5 py-0.5 rounded-full uppercase">
                    {act.jurisdiction}
                  </span>
                </div>
                <h3 className="text-body-lg text-ink font-semibold mb-3">{act.name}</h3>
                <p className="text-body-sm text-mute mb-6 line-clamp-3 leading-relaxed">{act.description}</p>
                
                {/* Quick sections count preview */}
                <div className="text-xs text-mute/70 mb-2">
                  Indexed sections: {act.sections.length}
                </div>
              </div>
              <div className="flex items-center justify-between border-t border-hairline/30 pt-4 mt-2">
                <button 
                  onClick={() => setActiveAct(act)}
                  className="text-caption-mono-sm text-ink hover:text-accent-sunset transition-colors"
                  aria-label={`View indexed sections in ${act.name}`}
                >
                  browse sections ➔
                </button>
                <a 
                  href={`/assistant?query=Tell me about the ${act.name}`}
                  className="button-pill button-pill-outline text-caption-mono-sm tracking-wider hover:scale-105"
                >
                  ask assistant
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Act Sections Detail Drawer/Modal */}
      {activeAct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-canvas/80 backdrop-blur-sm p-4" role="dialog" aria-modal="true" aria-labelledby="modal-act-title">
          <div className="bg-canvas-card border border-hairline rounded-sm w-full max-w-2xl max-h-[85vh] flex flex-col animate-scale-up">
            
            {/* Header */}
            <div className="p-6 border-b border-hairline flex items-start justify-between">
              <div>
                <span className="text-caption-mono-sm text-accent-breeze uppercase bg-accent-breeze/10 px-2 py-0.5 rounded-full mb-2 inline-block">{activeAct.jurisdiction}</span>
                <h2 id="modal-act-title" className="text-body-lg md:text-display-xs text-ink font-semibold">{activeAct.name}</h2>
              </div>
              <button 
                onClick={() => { setActiveAct(null); setActiveSection(null); }}
                className="p-1.5 text-mute hover:text-ink outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-sm"
                aria-label="Close sections browser"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
            </div>

            {/* Content Area (Split layout: sections list on left/top, section content on right/bottom) */}
            <div className="flex-grow overflow-hidden flex flex-col md:flex-row">
              {/* Sections List */}
              <div className="w-full md:w-1/3 border-b md:border-b-0 md:border-r border-hairline overflow-y-auto max-h-[30vh] md:max-h-none">
                <div className="p-2 space-y-1">
                  <div className="text-caption-mono-sm text-mute/50 p-2 uppercase">sections</div>
                  {activeAct.sections.map(sec => (
                    <button 
                      key={sec.number}
                      onClick={() => setActiveSection(sec)}
                      className={`w-full text-left p-2.5 text-body-sm rounded-sm transition-all duration-200 outline-none focus-visible:ring-2 focus-visible:ring-primary ${activeSection?.number === sec.number ? 'bg-canvas-soft text-ink font-medium border-l-2 border-primary' : 'text-mute hover:text-ink hover:bg-canvas-soft/40'}`}
                    >
                      <div className="font-mono text-xs text-accent-sunset">{sec.number}</div>
                      <div className="truncate mt-0.5">{sec.title}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Section Details Pane */}
              <div className="w-full md:w-2/3 p-6 overflow-y-auto flex flex-col justify-between max-h-[50vh] md:max-h-none">
                {activeSection ? (
                  <div className="space-y-6">
                    <div>
                      <span className="text-caption-mono text-accent-sunset tracking-wider block mb-1">section reference</span>
                      <h3 className="text-body-lg text-ink font-semibold">{activeSection.number}: {activeSection.title}</h3>
                    </div>
                    <div className="text-body-sm text-mute leading-relaxed bg-canvas border border-hairline rounded-sm p-4 font-mono select-all">
                      {activeSection.content}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 text-mute">
                    <svg className="w-12 h-12 mx-auto text-mute/40 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                    Select a specific section in the left panel to inspect its statutory text clauses.
                  </div>
                )}

                {activeSection && (
                  <div className="border-t border-hairline pt-6 mt-6 flex items-center justify-end">
                    <a 
                      href={`/assistant?query=Explain the provisions of ${activeAct.name} ${activeSection.number}: ${activeSection.title}`}
                      className="button-pill button-pill-primary text-caption-mono-sm"
                    >
                      ask assistant about this section
                    </a>
                  </div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-hairline flex items-center justify-end bg-canvas-soft/30">
              <button 
                onClick={() => { setActiveAct(null); setActiveSection(null); }}
                className="button-pill button-pill-outline text-caption-mono-sm"
              >
                close browser
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}


