import { useState, useTransition, type ChangeEvent } from 'react';
import { mockWelfareSchemes } from '../services/mockData';
import type { WelfareScheme } from '../services/api';

export default function WelfareSchemesBrowser() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedState, setSelectedState] = useState('All');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedScheme, setSelectedScheme] = useState<WelfareScheme | null>(null);
  const [, startTransition] = useTransition();

  const states = ['All', 'Central', 'Maharashtra'];
  const categories = ['All', 'Healthcare', 'Agriculture', 'Social Welfare & Pension'];

  // Filter schemes
  const filteredSchemes = mockWelfareSchemes.filter(s => {
    const matchesState = selectedState === 'All' || s.state.toLowerCase() === selectedState.toLowerCase();
    const matchesCategory = selectedCategory === 'All' || s.category === selectedCategory;
    const matchesSearch = searchQuery.trim() === '' || 
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesState && matchesCategory && matchesSearch;
  });

  const handleSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    startTransition(() => {
      setSearchQuery(val);
    });
  };

  return (
    <div className="space-y-8 min-w-0">
      {/* Search & Filters Panel */}
      <div className="bg-canvas-card border border-hairline rounded-sm p-6 space-y-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search Bar */}
          <div className="flex-grow relative">
            <label htmlFor="scheme-search" className="sr-only font-sans">Search schemes</label>
            <input 
              type="text" 
              id="scheme-search"
              placeholder="Search scheme name, benefit details…" 
              defaultValue={searchQuery}
              onChange={handleSearchChange}
              className="w-full pl-10 pr-4 py-3 bg-canvas-soft border border-hairline rounded-sm text-body-md focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
            />
            {/* Search Icon */}
            <div className="absolute left-3 top-3.5 text-mute" aria-hidden="true">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            </div>
          </div>

          {/* State Dropdown */}
          <div className="w-full md:w-48 flex flex-col gap-1">
            <label htmlFor="state-filter" className="sr-only">State Jurisdiction</label>
            <select 
              id="state-filter"
              value={selectedState} 
              onChange={(e) => setSelectedState(e.target.value)}
              className="w-full px-4 py-3 bg-canvas-soft border border-hairline rounded-sm text-body-md focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
            >
              {states.map(st => (
                <option key={st} value={st}>{st} Jurisdiction</option>
              ))}
            </select>
          </div>
        </div>

        {/* Category Filters */}
        <div className="flex flex-wrap gap-2 items-center" role="group" aria-label="Scheme Category Filters">
          <span className="text-caption-mono-sm text-mute mr-2 lowercase">categories:</span>
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

      {/* Schemes Grid */}
      {filteredSchemes.length === 0 ? (
        <div className="text-center py-16 border border-hairline border-dashed rounded-sm bg-canvas-card">
          <svg className="w-12 h-12 mx-auto text-mute mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          <h3 className="text-body-md text-ink font-semibold mb-2">No Schemes Found</h3>
          <p className="text-body-sm text-mute max-w-sm mx-auto">Try refining your search terms or selecting a different jurisdiction.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 min-w-0">
          {filteredSchemes.map(sch => (
            <div 
              key={sch.id} 
              className="bg-canvas-card border border-hairline rounded-sm p-6 hover:border-body-mid transition-all duration-300 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-4 mb-4">
                  <span className="text-caption-mono-sm text-accent-sunset tracking-wider uppercase bg-accent-sunset/10 px-2.5 py-0.5 rounded-full">
                    {sch.state}
                  </span>
                  <span className="text-caption-mono-sm text-mute uppercase">{sch.category}</span>
                </div>
                <h3 className="text-body-lg text-ink font-semibold mb-3">{sch.name}</h3>
                <p className="text-body-sm text-mute line-clamp-3 mb-6 leading-relaxed">{sch.description}</p>
              </div>
              <div className="flex items-center justify-between border-t border-hairline/30 pt-4 mt-2">
                <button 
                  onClick={() => setSelectedScheme(sch)}
                  className="text-caption-mono-sm text-ink hover:text-accent-sunset transition-colors"
                  aria-label={`View detail specifications for ${sch.name}`}
                >
                  view details ➔
                </button>
                <a 
                  href={`/assistant?query=Tell me about eligibility for ${sch.name}`}
                  className="button-pill button-pill-outline text-caption-mono-sm tracking-wider hover:scale-105"
                >
                  ask assistant
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Scheme Details Modal Dialog */}
      {selectedScheme && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-canvas/80 backdrop-blur-sm p-4" role="dialog" aria-modal="true" aria-labelledby="modal-scheme-title">
          <div className="bg-canvas-card border border-hairline rounded-sm w-full max-w-2xl max-h-[85vh] flex flex-col animate-scale-up">
            
            {/* Modal Header */}
            <div className="p-6 border-b border-hairline flex items-start justify-between">
              <div>
                <div className="flex gap-2 mb-2">
                  <span className="text-caption-mono-sm text-accent-sunset uppercase bg-accent-sunset/10 px-2 py-0.5 rounded-full">{selectedScheme.state}</span>
                  <span className="text-caption-mono-sm text-mute uppercase px-2 py-0.5">{selectedScheme.category}</span>
                </div>
                <h2 id="modal-scheme-title" className="text-body-lg md:text-display-xs text-ink font-semibold">{selectedScheme.name}</h2>
              </div>
              <button 
                onClick={() => setSelectedScheme(null)}
                className="p-1.5 text-mute hover:text-ink outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-sm"
                aria-label="Close details modal"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
            </div>

            {/* Modal Content (Scrollable) */}
            <div className="p-6 overflow-y-auto space-y-6 text-body-sm leading-relaxed">
              <div>
                <span className="text-caption-mono text-mute tracking-wider block mb-2">description</span>
                <p className="text-mute">{selectedScheme.description}</p>
              </div>

              <div>
                <span className="text-caption-mono text-accent-breeze tracking-wider block mb-2">eligibility criteria</span>
                <p className="text-body-sm text-ink bg-canvas-soft border border-hairline rounded-sm p-4">{selectedScheme.eligibility}</p>
              </div>

              <div>
                <span className="text-caption-mono text-accent-sunset tracking-wider block mb-2">benefits & coverage</span>
                <p className="text-body-sm text-ink bg-canvas-soft border border-hairline rounded-sm p-4">{selectedScheme.benefits}</p>
              </div>

              <div>
                <span className="text-caption-mono text-mute tracking-wider block mb-2">required documents</span>
                <ul className="list-disc pl-5 space-y-1 text-mute">
                  {selectedScheme.requiredDocuments.map((doc, idx) => (
                    <li key={idx}>{doc}</li>
                  ))}
                </ul>
              </div>

              <div>
                <span className="text-caption-mono text-accent-dusk tracking-wider block mb-2">application process</span>
                <p className="text-mute">{selectedScheme.applicationProcess}</p>
              </div>

              {selectedScheme.sources.length > 0 && (
                <div>
                  <span className="text-caption-mono text-mute tracking-wider block mb-2">supporting citations</span>
                  <div className="space-y-3">
                    {selectedScheme.sources.map((src, srcIdx) => (
                      <div key={src.chunk_id ?? `${src.act}-${src.section}-${srcIdx}`} className="border border-hairline bg-canvas rounded-sm p-4 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-caption-mono-sm text-ink font-semibold">{src.act}</span>
                          <span className="text-caption-mono-sm text-mute uppercase">{src.section}</span>
                        </div>
                        <p className="text-xs text-mute/80 italic">"{src.excerpt}"</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t border-hairline flex items-center justify-end gap-3 bg-canvas-soft/30">
              <button 
                onClick={() => setSelectedScheme(null)}
                className="button-pill button-pill-outline text-caption-mono-sm"
              >
                close
              </button>
              <a 
                href={`/assistant?query=Explain application process for ${selectedScheme.name}`}
                className="button-pill button-pill-primary text-caption-mono-sm"
              >
                ask assistant
              </a>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}


