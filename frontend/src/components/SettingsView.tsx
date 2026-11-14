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

  const handleLogout = () => {
    alert('Logout simulated successfully. The profile settings are ready for Firebase or OAuth integrations.');
  };

  return (
    <div className="h-full flex flex-col bg-canvas select-text min-w-0" aria-label="Preferences and Account Settings Panel">
      
      {/* Top Header */}
      <div className="p-6 border-b border-hairline shrink-0">
        <span className="text-caption-mono text-mute tracking-wider block mb-1">settings</span>
        <h1 className="text-display-xs text-ink font-semibold">Preferences & Profile</h1>
      </div>

      {/* Content Area */}
      <div className="flex-grow overflow-y-auto p-6 space-y-8 max-w-lg">
        
        {/* Profile details (Mock) */}
        <section className="space-y-4">
          <span className="text-caption-mono text-accent-sunset tracking-wider block font-mono">user account</span>
          <div className="bg-canvas-card border border-hairline rounded-sm p-5 space-y-4">
            <div className="flex items-center gap-4">
              {/* Mock avatar circle */}
              <div className="w-12 h-12 rounded-full border border-hairline bg-canvas flex items-center justify-center text-ink text-body-md font-mono select-none">
                CC
              </div>
              <div>
                <div className="text-body-sm text-ink font-semibold">Citizen Contributor</div>
                <div className="text-xs text-mute mt-0.5">citizen@civicconnect.org</div>
              </div>
            </div>

            <div className="border-t border-hairline/30 pt-4 flex items-center justify-between">
              <span className="text-xs text-mute">Auth Status: Guest Session</span>
              <button 
                type="button" 
                onClick={handleLogout}
                className="text-xs text-accent-sunset hover:underline outline-none focus-visible:ring-1 focus-visible:ring-primary rounded-sm"
              >
                sign out
              </button>
            </div>
          </div>
        </section>

        {/* Language Selection */}
        <section className="space-y-4">
          <span className="text-caption-mono text-accent-breeze tracking-wider block font-mono font-semibold">localization</span>
          <div className="bg-canvas-card border border-hairline rounded-sm p-5 space-y-4">
            <div className="flex flex-col gap-2">
              <label htmlFor="language-select" className="text-body-sm text-ink">Primary Language Preference</label>
              <p className="text-xs text-mute leading-relaxed">
                Choose the primary language for AI responses. Source citations will maintain their original legal filing language.
              </p>
              <select 
                id="language-select"
                value={language}
                onChange={(e) => onLanguageChange(e.target.value)}
                className="w-full px-4 py-2.5 bg-canvas-soft border border-hairline rounded-sm text-body-sm focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
              >
                {LANGUAGES.map(lang => (
                  <option key={lang.code} value={lang.code}>{lang.name}</option>
                ))}
              </select>
            </div>
          </div>
        </section>

        {/* Data Management */}
        <section className="space-y-4">
          <span className="text-caption-mono text-accent-dusk tracking-wider block font-mono">data control</span>
          <div className="bg-canvas-card border border-hairline rounded-sm p-5 space-y-4">
            <div className="space-y-2">
              <h3 className="text-body-sm text-ink">Clear Cached Storage</h3>
              <p className="text-xs text-mute leading-relaxed">
                Delete all conversations cached locally in your browser's memory storage (`localStorage`).
              </p>
            </div>
            <button 
              type="button"
              onClick={handleClear}
              className="button-pill button-pill-outline text-caption-mono-sm text-accent-sunset hover:bg-accent-sunset/10 hover:border-accent-sunset"
            >
              clear all history
            </button>
          </div>
        </section>

      </div>

    </div>
  );
}


