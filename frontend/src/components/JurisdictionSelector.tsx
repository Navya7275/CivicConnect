import React from 'react';

interface JurisdictionSelectorProps {
  jurisdiction: 'central' | 'state';
  stateName: string | null;
  onChange: (jurisdiction: 'central' | 'state', stateName: string | null) => void;
}

const INDIAN_STATES = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 
  'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 
  'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 
  'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 
  'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 
  'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Delhi'
];

export default function JurisdictionSelector({ 
  jurisdiction, 
  stateName, 
  onChange 
}: JurisdictionSelectorProps) {
  
  const handleTypeChange = (type: 'central' | 'state') => {
    if (type === 'central') {
      onChange('central', null);
    } else {
      onChange('state', stateName || 'Maharashtra'); // Default to Maharashtra if none selected
    }
  };

  const handleStateChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onChange('state', e.target.value);
  };

  return (
    <div className="flex flex-wrap items-center gap-2.5 sm:gap-3 bg-canvas-card border border-hairline rounded-sm p-2 sm:p-2.5 w-full">
      
      {/* Toggle Buttons */}
      <div className="flex items-center bg-canvas-soft border border-hairline rounded-sm p-0.5 shrink-0" role="group" aria-label="Legislative Jurisdiction Selection">
        <button 
          type="button"
          onClick={() => handleTypeChange('central')}
          className={`px-3.5 py-1 text-caption-mono-sm rounded-sm transition-all duration-200 outline-none focus-visible:ring-2 focus-visible:ring-primary ${jurisdiction === 'central' ? 'bg-primary text-on-primary font-medium' : 'text-mute hover:text-ink'}`}
        >
          central
        </button>
        <button 
          type="button"
          onClick={() => handleTypeChange('state')}
          className={`px-3.5 py-1 text-caption-mono-sm rounded-sm transition-all duration-200 outline-none focus-visible:ring-2 focus-visible:ring-primary ${jurisdiction === 'state' ? 'bg-primary text-on-primary font-medium' : 'text-mute hover:text-ink'}`}
        >
          state
        </button>
      </div>

      {/* State Dropdown (Conditional) */}
      {jurisdiction === 'state' && (
        <div className="inline-flex items-center gap-1.5 shrink-0">
          <label htmlFor="state-select" className="text-caption-mono-sm text-mute shrink-0 lowercase">state:</label>
          <div className="relative inline-flex items-center">
            <select 
              id="state-select"
              value={stateName || 'Madhya Pradesh'} 
              onChange={handleStateChange}
              className="appearance-none bg-canvas-soft border border-hairline hover:border-hairline/80 rounded-sm pl-3 pr-8 py-1 min-w-[150px] text-body-sm text-ink focus-visible:ring-1 focus-visible:ring-primary focus-visible:outline-none cursor-pointer"
            >
              {INDIAN_STATES.map(st => (
                <option key={st} value={st} className="bg-canvas-card text-ink">{st}</option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2 text-mute">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>
      )}

      {/* Indicator summary */}
      <div className="hidden sm:inline-flex items-center gap-1.5 text-caption-mono-sm text-mute shrink-0 ml-auto select-none lowercase pr-1">
        <span className="w-1.5 h-1.5 rounded-full bg-accent-sunset animate-pulse" aria-hidden="true"></span>
        active: {jurisdiction === 'central' ? 'central legislation' : `${stateName || 'state'} context`}
      </div>

    </div>
  );
}


