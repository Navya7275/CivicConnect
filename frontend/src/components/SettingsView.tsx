interface SettingsViewProps {
  language: string;
  onLanguageChange: (lang: string) => void;
  onClearHistory: () => void;
}

const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'Hindi (हिन्दी)' },
  { code: 'mr', name: 'Marathi (मराठी)' },
  { code: 'ta', name: 'Tamil (தமிழ்)' },
  { code: 'te', name: 'Telugu (తెలుగు)' }
];

export default function SettingsView({
  language,
  onLanguageChange,
  onClearHistory
}: SettingsViewProps) {
  
  const handleClear = () => {
    if (confirm('Are you sure you want to delete all conversations from history? This action cannot be undone.')) {
      onClearHistory();
    }
  };

  return (
    <div className="h-full flex flex-col bg-muted/20 select-text min-w-0" aria-label="Preferences and Account Settings Panel">
      
      {/* Top Header */}
      <div className="p-6 border-b border-border shrink-0 bg-card">
        <span className="badge badge-soft mb-2" data-tone="accent">Preferences</span>
        <h1 className="text-h2">Application Settings</h1>
      </div>

      {/* Content Area - Balanced 2-Column Responsive Grid */}
      <div className="flex-grow overflow-y-auto p-6 md:p-8">
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
          
          {/* Left Column: Account Profile & Interface Preferences */}
          <div className="space-y-6">
            
            {/* User Account / Profile Section */}
            <section className="space-y-2">
              <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider pl-1">
                User Session
              </div>
              <div className="card !p-6 space-y-5">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-ui-full border border-border bg-white flex items-center justify-center p-1.5 shadow-sm select-none shrink-0">
                    <img src="/logo.png" alt="CivicConnect" className="w-full h-full object-contain" />
                  </div>
                  <div>
                    <div className="text-base font-medium text-foreground">Citizen Contributor</div>
                    <div className="text-xs text-muted-foreground mt-0.5">Guest session · Local client cache</div>
                  </div>
                </div>

                <div className="border-t border-border pt-4 flex items-center justify-between text-xs text-muted-foreground">
                  <span>Session Status</span>
                  <span className="badge badge-soft" data-tone="success">Active (Offline Indexed)</span>
                </div>
              </div>
            </section>

            {/* Language Selection */}
            <section className="space-y-2">
              <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider pl-1">
                Interface Language
              </div>
              <div className="card !p-6 space-y-4">
                <div>
                  <div className="text-sm font-medium text-foreground">Preferred Language</div>
                  <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                    Set your preferred language for queries, generated answers, and statutory summaries.
                  </p>
                </div>
                <div className="relative">
                  <select 
                    id="settings-language"
                    value={language}
                    onChange={(e) => onLanguageChange(e.target.value)}
                    className="input input-sm pr-8"
                  >
                    {LANGUAGES.map(lang => (
                      <option key={lang.code} value={lang.code}>{lang.name}</option>
                    ))}
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"/></svg>
                  </div>
                </div>
              </div>
            </section>

          </div>

          {/* Right Column: Privacy, Data Storage & System Information */}
          <div className="space-y-6">
            
            {/* Data & Privacy Management */}
            <section className="space-y-2">
              <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider pl-1">
                Privacy & Data Cache
              </div>
              <div className="card !p-6 space-y-4">
                <div>
                  <div className="text-sm font-medium text-foreground">Clear Local Conversation Cache</div>
                  <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                    Permanently removes all saved message threads, custom prompts, and chat history stored in your browser's local storage.
                  </p>
                </div>

                <div className="pt-2">
                  <button 
                    type="button"
                    onClick={handleClear}
                    className="btn btn-destructive btn-sm"
                  >
                    Clear Conversation History
                  </button>
                </div>
              </div>
            </section>

            {/* Statutory Corpus Info */}
            <section className="space-y-2">
              <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider pl-1">
                Statutory Corpus
              </div>
              <div className="card !p-6 space-y-3 bg-muted/40">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Indexed Provisions:</span>
                  <span className="font-mono font-medium text-foreground">888 sections</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Primary Statutes:</span>
                  <span className="text-foreground">BNS 2023, MV Act 1988, RTI</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Grounding Pipeline:</span>
                  <span className="text-foreground">Hybrid RRF Dense & Lexical</span>
                </div>
                <div className="border-t border-border pt-3 text-[11px] text-muted-foreground leading-relaxed">
                  All statutory sections are indexed from the Gazette of India and official ministry portals.
                </div>
              </div>
            </section>

          </div>

        </div>
      </div>
    </div>
  );
}
