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
      {/* Search & Filters Solid Panel */}
      <div className="card !p-6 space-y-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search Bar */}
          <div className="flex-grow relative flex items-center">
            <div className="absolute left-3.5 pointer-events-none text-muted-foreground flex items-center justify-center" aria-hidden="true">
              <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            </div>
            <label htmlFor="scheme-search" className="sr-only">Search schemes</label>
            <input 
              type="text" 
              id="scheme-search"
              placeholder="Search scheme name, benefit details, keywords…" 
              defaultValue={searchQuery}
              onChange={handleSearchChange}
              className="input !pl-11"
            />
          </div>

          {/* State Dropdown */}
          <div className="w-full md:w-52">
            <label htmlFor="state-filter" className="sr-only">State Jurisdiction</label>
            <div className="relative">
              <select 
                id="state-filter"
                value={selectedState} 
                onChange={(e) => setSelectedState(e.target.value)}
                className="input pr-8"
              >
                {states.map(st => (
                  <option key={st} value={st}>{st} Scope</option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"/></svg>
              </div>
            </div>
          </div>
        </div>

        {/* Category Filters Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pt-2" role="group" aria-label="Scheme Category Filters">
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider shrink-0 mr-1">Category:</span>
          <div className="tabs">
            {categories.map(cat => (
              <button 
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                aria-selected={selectedCategory === cat}
                className="tab !h-8 text-xs shrink-0"
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Schemes Grid */}
      {filteredSchemes.length === 0 ? (
        <div className="text-center py-20 border border-border border-dashed rounded-ui-lg bg-card p-8">
          <svg className="w-10 h-10 mx-auto text-muted-foreground mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <h3 className="text-h3 text-lg mb-2">No Schemes Found</h3>
          <p className="text-small text-muted-foreground max-w-sm mx-auto">
            Try refining your search terms or selecting a different jurisdiction.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 min-w-0">
          {filteredSchemes.map(sch => (
            <div 
              key={sch.id} 
              className="card flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <span className="badge badge-soft" data-tone="accent">{sch.state}</span>
                  <span className="badge badge-outline">{sch.category}</span>
                </div>

                <h3 className="text-h3 text-xl">{sch.name}</h3>
                <p className="text-small text-muted-foreground leading-relaxed">
                  {sch.description}
                </p>

                <div className="p-4 rounded-ui-sm bg-muted/60 text-xs space-y-2 border border-border">
                  <div>
                    <strong className="text-foreground">Eligibility:</strong>{' '}
                    <span className="text-muted-foreground">{sch.eligibility}</span>
                  </div>
                  <div>
                    <strong className="text-foreground">Benefit Entitlement:</strong>{' '}
                    <span className="text-muted-foreground">{sch.benefits}</span>
                  </div>
                  <div>
                    <strong className="text-foreground">Mandatory Documents:</strong>{' '}
                    <span className="text-muted-foreground">{sch.documents_required}</span>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-border flex items-center justify-between">
                <a 
                  href={`/assistant?query=${encodeURIComponent(`What are the complete eligibility criteria, benefits, and required documents for ${sch.name}?`)}`}
                  className="btn btn-outline btn-sm"
                >
                  Ask Assistant →
                </a>
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
          ))}
        </div>
      )}
    </div>
  );
}
