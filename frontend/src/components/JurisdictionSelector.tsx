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
      onChange('state', stateName || 'Maharashtra');
    }
  };

  const handleStateChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onChange('state', e.target.value);
  };

  return (
    <div className="flex items-center gap-2.5 bg-[#f0f0f3] rounded-full p-1 max-w-full">
      
      {/* Segmented Control Pill */}
      <div className="flex items-center gap-1" role="group" aria-label="Legislative Jurisdiction Selection">
        <button 
          type="button"
          onClick={() => handleTypeChange('central')}
          aria-selected={jurisdiction === 'central'}
          className={`h-7 px-3.5 text-xs font-medium rounded-full transition-all duration-150 cursor-pointer ${
            jurisdiction === 'central'
              ? 'bg-white text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Central Acts
        </button>
        <button 
          type="button"
          onClick={() => handleTypeChange('state')}
          aria-selected={jurisdiction === 'state'}
          className={`h-7 px-3.5 text-xs font-medium rounded-full transition-all duration-150 cursor-pointer ${
            jurisdiction === 'state'
              ? 'bg-white text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          State Laws
        </button>
      </div>

      {/* State Dropdown (Conditional) */}
      {jurisdiction === 'state' && (
        <div className="flex items-center gap-1.5 shrink-0 pr-1">
          <label htmlFor="state-select" className="text-xs text-muted-foreground">State:</label>
          <div className="relative inline-flex items-center">
            <select 
              id="state-select"
              value={stateName || 'Maharashtra'} 
              onChange={handleStateChange}
              className="appearance-none bg-white text-foreground rounded-full pl-2.5 pr-6 py-1 text-xs focus:ring-1 focus:ring-ring focus:outline-none cursor-pointer shadow-sm"
            >
              {INDIAN_STATES.map(st => (
                <option key={st} value={st}>{st}</option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2 text-muted-foreground">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>
      )}

      {/* Status indicator */}
      <div className="hidden lg:inline-flex items-center gap-1.5 text-xs text-muted-foreground pl-2.5 pr-2 select-none">
        <span className="w-1.5 h-1.5 rounded-full bg-blue-500" aria-hidden="true"></span>
        <span className="text-[11px] font-medium">{jurisdiction === 'central' ? 'National scope' : `${stateName || 'State'} scope`}</span>
      </div>

    </div>
  );
}
