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
    <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 bg-canvas-card border border-hairline rounded-sm p-3 min-w-0">
      
      {/* Toggle Buttons */}
      <div className="flex items-center bg-canvas-soft border border-hairline rounded-sm p-0.5" role="group" aria-label="Legislative Jurisdiction Selection">
        <button 
          type="button"
          onClick={() => handleTypeChange('central')}
          className={`flex-1 sm:flex-initial px-4 py-1.5 text-caption-mono-sm rounded-sm transition-all duration-200 outline-none focus-visible:ring-2 focus-visible:ring-primary ${jurisdiction === 'central' ? 'bg-primary text-on-primary font-medium' : 'text-mute hover:text-ink'}`}
        >
          central
        </button>
        <button 
          type="button"
          onClick={() => handleTypeChange('state')}
          className={`flex-1 sm:flex-initial px-4 py-1.5 text-caption-mono-sm rounded-sm transition-all duration-200 outline-none focus-visible:ring-2 focus-visible:ring-primary ${jurisdiction === 'state' ? 'bg-primary text-on-primary font-medium' : 'text-mute hover:text-ink'}`}
        >
          state
        </button>
      </div>

      {/* State Dropdown (Conditional) */}
      {jurisdiction === 'state' && (
        <div className="flex-grow flex items-center gap-2 min-w-[200px]">
          <label htmlFor="state-select" className="text-caption-mono-sm text-mute shrink-0 lowercase">state:</label>
          <select 
            id="state-select"
            value={stateName || 'Madhya Pradesh'} 
            onChange={handleStateChange}
            className="flex-grow min-w-[150px] px-3 py-1.5 bg-canvas-soft border border-hairline rounded-sm text-body-sm text-ink focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
          >
            {INDIAN_STATES.map(st => (
              <option key={st} value={st} className="bg-canvas-card text-ink">{st}</option>
            ))}
          </select>
        </div>
      )}

      {/* Indicator summary */}
      <div className="hidden lg:flex items-center gap-1.5 text-caption-mono-sm text-mute shrink-0 ml-auto select-none lowercase">
        <span className="w-1.5 h-1.5 rounded-full bg-accent-sunset animate-pulse" aria-hidden="true"></span>
        active: {jurisdiction === 'central' ? 'central legislation' : `${stateName} context`}
      </div>

    </div>
  );
}


