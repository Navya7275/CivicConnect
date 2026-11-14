import type { WelfareScheme, LegalAct } from '../services/api';

interface SavedItemsViewProps {
  savedSchemes: WelfareScheme[];
  savedActs: LegalAct[];
  onRemoveScheme: (id: string) => void;
  onRemoveAct: (id: string) => void;
  onAskAboutItem: (query: string) => void;
}

export default function SavedItemsView({
  savedSchemes,
  savedActs,
  onRemoveScheme,
  onRemoveAct,
  onAskAboutItem
}: SavedItemsViewProps) {
  
  const hasItems = savedSchemes.length > 0 || savedActs.length > 0;

  return (
    <div className="h-full flex flex-col bg-canvas select-text min-w-0" aria-label="Bookmarked Items Panel">
      
      {/* Top Header */}
      <div className="p-6 border-b border-hairline shrink-0">
        <span className="text-caption-mono text-accent-sunset tracking-wider block mb-1">bookmarks</span>
        <h1 className="text-display-xs text-ink font-semibold">Saved Information</h1>
      </div>

      {/* Content Area */}
      <div className="flex-grow overflow-y-auto p-6 space-y-8">
        {!hasItems ? (
          /* Empty State */
          <div className="text-center py-16 border border-hairline border-dashed rounded-sm bg-canvas-card max-w-md mx-auto my-12">
            <svg className="w-12 h-12 mx-auto text-mute/50 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/></svg>
            <h2 className="text-body-md text-ink font-semibold mb-2">No Saved Bookmarks</h2>
            <p className="text-body-sm text-mute max-w-xs mx-auto">
              Save useful welfare schemes or legal acts by clicking the bookmark icons while browsing.
            </p>
          </div>
        ) : (
          <div className="space-y-8 max-w-4xl">
            
            {/* Welfare Schemes Category */}
            {savedSchemes.length > 0 && (
              <div className="space-y-4">
                <div className="text-[10px] text-mute/50 uppercase tracking-widest pl-2 font-mono">welfare schemes ({savedSchemes.length})</div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {savedSchemes.map(sch => (
                    <div key={sch.id} className="bg-canvas-card border border-hairline rounded-sm p-5 space-y-3 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-caption-mono-sm text-accent-sunset bg-accent-sunset/10 px-2 py-0.5 rounded-full uppercase">{sch.state}</span>
                          <button 
                            type="button" 
                            onClick={() => onRemoveScheme(sch.id)}
                            className="text-xs text-mute hover:text-accent-sunset transition-colors"
                            aria-label={`Remove saved scheme ${sch.name}`}
                          >
                            remove
                          </button>
                        </div>
                        <h3 className="text-body-sm text-ink font-semibold line-clamp-1">{sch.name}</h3>
                        <p className="text-xs text-mute line-clamp-2 mt-1 leading-relaxed">{sch.description}</p>
                      </div>
                      <div className="flex items-center justify-end border-t border-hairline/20 pt-3 mt-1">
                        <button 
                          type="button" 
                          onClick={() => onAskAboutItem(`Who is eligible for ${sch.name} and how do I apply?`)}
                          className="button-pill button-pill-outline text-caption-mono-sm py-1"
                        >
                          ask assistant
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Legal Acts Category */}
            {savedActs.length > 0 && (
              <div className="space-y-4">
                <div className="text-[10px] text-mute/50 uppercase tracking-widest pl-2 font-mono">laws & acts ({savedActs.length})</div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {savedActs.map(act => (
                    <div key={act.id} className="bg-canvas-card border border-hairline rounded-sm p-5 space-y-3 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-caption-mono-sm text-accent-breeze bg-accent-breeze/10 px-2 py-0.5 rounded-full uppercase">{act.jurisdiction}</span>
                          <button 
                            type="button" 
                            onClick={() => onRemoveAct(act.id)}
                            className="text-xs text-mute hover:text-accent-sunset transition-colors"
                            aria-label={`Remove saved act ${act.name}`}
                          >
                            remove
                          </button>
                        </div>
                        <h3 className="text-body-sm text-ink font-semibold line-clamp-1">{act.name}</h3>
                        <p className="text-xs text-mute line-clamp-2 mt-1 leading-relaxed">{act.description}</p>
                      </div>
                      <div className="flex items-center justify-end border-t border-hairline/20 pt-3 mt-1">
                        <button 
                          type="button" 
                          onClick={() => onAskAboutItem(`Explain the main provisions of the ${act.name}`)}
                          className="button-pill button-pill-outline text-caption-mono-sm py-1"
                        >
                          ask assistant
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        )}
      </div>

    </div>
  );
}


