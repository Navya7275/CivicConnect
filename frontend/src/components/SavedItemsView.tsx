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
    <div className="h-full flex flex-col bg-muted/20 select-text min-w-0" aria-label="Bookmarked Items Panel">
      
      {/* Top Header */}
      <div className="p-6 border-b border-border shrink-0 bg-card">
        <span className="badge badge-soft mb-2" data-tone="accent">Saved</span>
        <h1 className="text-h2">Bookmarked Schemes & Acts</h1>
      </div>

      {/* Content Area */}
      <div className="flex-grow overflow-y-auto p-6 space-y-8">
        {!hasItems ? (
          <div className="text-center py-20 border border-border border-dashed rounded-ui-lg bg-card max-w-md mx-auto my-12 p-8">
            <svg className="w-10 h-10 mx-auto text-muted-foreground mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
            </svg>
            <h2 className="text-h3 text-lg mb-2">No Saved Items</h2>
            <p className="text-small text-muted-foreground max-w-xs mx-auto">
              Save welfare schemes or legislative acts by clicking the bookmark button while browsing.
            </p>
          </div>
        ) : (
          <div className="space-y-8 max-w-4xl">
            
            {/* Welfare Schemes Category */}
            {savedSchemes.length > 0 && (
              <div className="space-y-4">
                <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider pl-1">
                  Saved Schemes ({savedSchemes.length})
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {savedSchemes.map(sch => (
                    <div key={sch.id} className="card !p-5 space-y-3 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="badge badge-soft uppercase" data-tone="accent">{sch.state}</span>
                          <button 
                            type="button" 
                            onClick={() => onRemoveScheme(sch.id)}
                            className="text-xs text-muted-foreground hover:text-destructive transition-colors cursor-pointer"
                          >
                            Remove
                          </button>
                        </div>
                        <h3 className="font-medium text-base text-foreground mb-1">{sch.name}</h3>
                        <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">{sch.description}</p>
                      </div>

                      <div className="pt-2 border-t border-border flex items-center justify-between">
                        <button 
                          type="button"
                          onClick={() => onAskAboutItem(`What are the latest rules and documents required for ${sch.name}?`)}
                          className="btn btn-secondary btn-sm"
                        >
                          Ask in chat →
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
                <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider pl-1">
                  Saved Acts & Statutes ({savedActs.length})
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {savedActs.map(act => (
                    <div key={act.id} className="card !p-5 space-y-3 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="badge badge-soft uppercase" data-tone="primary">{act.jurisdiction}</span>
                          <button 
                            type="button" 
                            onClick={() => onRemoveAct(act.id)}
                            className="text-xs text-muted-foreground hover:text-destructive transition-colors cursor-pointer"
                          >
                            Remove
                          </button>
                        </div>
                        <h3 className="font-medium text-base text-foreground mb-1">{act.name}</h3>
                        <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">{act.description}</p>
                      </div>

                      <div className="pt-2 border-t border-border flex items-center justify-between">
                        <button 
                          type="button"
                          onClick={() => onAskAboutItem(`Summarize the key provisions of ${act.name}.`)}
                          className="btn btn-secondary btn-sm"
                        >
                          Ask in chat →
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
