import { useState, useRef, useEffect } from 'react';
import type { Citation } from '../services/api';

interface CitationViewerProps {
  citations: Citation[];
  /**
   * Whether the answer as a whole passed citation verification.
   */
  verified?: boolean;
}

export default function CitationViewer({ citations, verified = false }: CitationViewerProps) {
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [popoverOpen, setPopoverOpen] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const closeTimerRef = useRef<NodeJS.Timeout | null>(null);

  if (!citations || citations.length === 0) return null;

  // Clear timer on unmount
  useEffect(() => {
    return () => {
      if (closeTimerRef.current) clearTimeout(closeTimerRef.current);
    };
  }, []);

  // Close popover when clicking outside or pressing Escape
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setPopoverOpen(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setPopoverOpen(false);
        setActiveCitation(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const handleMouseEnter = () => {
    if (closeTimerRef.current) {
      clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
    setPopoverOpen(true);
  };

  const handleMouseLeave = () => {
    // 200ms grace period so moving cursor to popover doesn't trigger sudden flickering
    closeTimerRef.current = setTimeout(() => {
      setPopoverOpen(false);
    }, 200);
  };

  const primaryCitation = citations[0];
  const moreCount = citations.length - 1;
  const primaryLabel = primaryCitation.act.length > 20 
    ? `${primaryCitation.act.slice(0, 18)}...` 
    : primaryCitation.act;

  const handleCopy = async (cit: Citation) => {
    const text = cit.excerpt
      ? `${cit.act}, ${cit.section} (${cit.jurisdiction}) - Excerpt: "${cit.excerpt}"`
      : `${cit.act}, ${cit.section} (${cit.jurisdiction}) - ${cit.source_url}`;
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(`${cit.act}-${cit.section}`);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (e) {
      // Fallback
    }
  };

  return (
    <div 
      ref={containerRef} 
      className="relative mt-3 inline-block"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Sleek compact source pill matching Perplexity/Apple design */}
      <button
        type="button"
        onClick={() => setPopoverOpen(prev => !prev)}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#2a2a2a] hover:bg-[#333333] text-[#e0e0e0] border border-white/10 transition-colors text-xs font-medium cursor-pointer shadow-sm select-none"
        aria-label="View sources"
        aria-expanded={popoverOpen}
      >
        {/* Source icon/dot */}
        <span className="w-1.5 h-1.5 rounded-full bg-accent-sunset shrink-0" />
        <span className="truncate max-w-[160px] sm:max-w-[200px]">{primaryLabel}</span>
        {moreCount > 0 && (
          <span className="text-white/60 font-normal">+{moreCount}</span>
        )}
      </button>

      {/* Floating Popover Box with smooth opacity & scale transitions */}
      <div 
        className={`absolute left-0 bottom-full mb-2 z-40 w-80 max-w-[90vw] rounded-xl bg-[#1c1c1e] border border-white/10 shadow-2xl overflow-hidden transition-all duration-200 ease-out origin-bottom-left ${
          popoverOpen 
            ? 'opacity-100 scale-100 pointer-events-auto translate-y-0' 
            : 'opacity-0 scale-95 pointer-events-none translate-y-1'
        }`}
      >
        <div className="p-3 border-b border-white/5 flex items-center justify-between">
          <span className="text-xs font-semibold text-white/90 uppercase tracking-wider">
            Sources ({citations.length})
          </span>
          <span className="text-[11px] text-accent-sunset bg-accent-sunset/10 px-2 py-0.5 rounded-full uppercase tracking-wider font-mono">
            {verified ? 'verified' : 'sources'}
          </span>
        </div>

        <div className="max-h-64 overflow-y-auto divide-y divide-white/5">
          {citations.map((cit, idx) => {
            const displayTitle = cit.act;
            const subtext = cit.section ? `Section: ${cit.section}` : cit.jurisdiction;

            return (
              <div
                key={cit.chunk_id || `${cit.act}-${idx}`}
                onClick={() => {
                  setActiveCitation(cit);
                  setPopoverOpen(false);
                }}
                className="p-3 hover:bg-white/5 cursor-pointer transition-colors group flex items-start gap-2.5 text-left"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-accent-sunset/80 mt-1.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-white group-hover:text-accent-sunset transition-colors leading-snug line-clamp-2">
                    {displayTitle}
                  </div>
                  <div className="text-[11px] text-white/50 mt-0.5 truncate font-mono">
                    {subtext}
                  </div>
                </div>
                <svg 
                  className="w-3.5 h-3.5 text-white/40 group-hover:text-white shrink-0 mt-0.5 transition-colors" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                </svg>
              </div>
            );
          })}
        </div>
      </div>

      {/* Citation Details Drawer (when item in popover is clicked) */}
      {activeCitation && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/70 backdrop-blur-xs" role="dialog" aria-modal="true" aria-labelledby="drawer-title">
          <div className="absolute inset-0" onClick={() => setActiveCitation(null)} />
          
          <div className="relative bg-[#18181b] border-l border-white/10 w-full max-w-md h-full flex flex-col justify-between shadow-2xl z-10 animate-slide-left">
            {/* Header */}
            <div className="p-6 border-b border-white/10 flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs text-accent-sunset tracking-wider bg-accent-sunset/10 px-2 py-0.5 rounded-full uppercase font-mono">
                    {verified ? 'verified source' : 'source'}
                  </span>
                  <span className="text-xs text-white/50 uppercase font-mono">{activeCitation.jurisdiction}</span>
                </div>
                <h2 id="drawer-title" className="text-base text-white font-semibold leading-snug">{activeCitation.act}</h2>
              </div>
              <button 
                type="button"
                onClick={() => setActiveCitation(null)}
                className="p-1.5 text-white/50 hover:text-white rounded-md transition-colors"
                aria-label="Close"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto space-y-5 flex-grow text-sm leading-relaxed text-white/80">
              {activeCitation.section && (
                <div>
                  <span className="text-xs text-white/40 tracking-wider block mb-1 font-mono uppercase">section / clause</span>
                  <span className="text-sm text-white font-medium">{activeCitation.section}</span>
                </div>
              )}

              {activeCitation.excerpt && (
                <div>
                  <span className="text-xs text-accent-sunset tracking-wider block mb-1 font-mono uppercase">statutory excerpt</span>
                  <div className="bg-[#121214] border border-white/10 rounded-lg p-3.5 text-xs text-white/80 leading-relaxed font-mono select-all">
                    "{activeCitation.excerpt}"
                  </div>
                </div>
              )}

              {(activeCitation.reference_url || activeCitation.source_url) && (
                <div>
                  <span className="text-xs text-white/40 tracking-wider block mb-1 font-mono uppercase">documentation</span>
                  <a
                    href={activeCitation.reference_url || activeCitation.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs text-white hover:text-accent-sunset underline underline-offset-4"
                  >
                    <span>Read the law yourself</span>
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-5 border-t border-white/10 bg-[#121214] flex items-center justify-between">
              <button 
                type="button"
                onClick={() => handleCopy(activeCitation)}
                className="px-3 py-1.5 rounded-md border border-white/20 text-xs text-white hover:bg-white/5 transition-colors inline-flex items-center gap-1.5"
              >
                {copiedId === `${activeCitation.act}-${activeCitation.section}` ? (
                  <>
                    <svg className="w-3.5 h-3.5 text-accent-sunset" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    <span>Copied</span>
                  </>
                ) : (
                  <>
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m-6 4h10m-5-5l5 5-5 5" />
                    </svg>
                    <span>Copy Citation</span>
                  </>
                )}
              </button>
              <button 
                type="button"
                onClick={() => setActiveCitation(null)}
                className="px-4 py-1.5 rounded-md bg-white text-black text-xs font-medium hover:bg-white/90 transition-colors"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
