import { useState, useRef, useEffect } from 'react';
import type { Citation } from '../services/api';

interface CitationViewerProps {
  citations: Citation[];
  verified?: boolean;
}

export default function CitationViewer({ citations, verified = false }: CitationViewerProps) {
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [popoverOpen, setPopoverOpen] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const closeTimerRef = useRef<NodeJS.Timeout | null>(null);

  if (!citations || citations.length === 0) return null;

  useEffect(() => {
    return () => {
      if (closeTimerRef.current) clearTimeout(closeTimerRef.current);
    };
  }, []);

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
    closeTimerRef.current = setTimeout(() => {
      setPopoverOpen(false);
    }, 200);
  };

  const primaryCitation = citations[0];
  const moreCount = citations.length - 1;
  const primaryLabel = primaryCitation.act.length > 22 
    ? `${primaryCitation.act.slice(0, 20)}…` 
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
      {/* Refined Minimalist Source Pill */}
      <button
        type="button"
        onClick={() => setPopoverOpen(prev => !prev)}
        className="inline-flex items-center gap-2 px-3 py-1 rounded-ui-full bg-muted hover:bg-muted/80 text-foreground border border-border transition-colors text-xs font-medium cursor-pointer shadow-ui-sm select-none"
        aria-label="View sources"
        aria-expanded={popoverOpen}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-accent-fill shrink-0" />
        <span className="truncate max-w-[180px] sm:max-w-[220px]">{primaryLabel}</span>
        {primaryCitation.section && (
          <span className="text-mono text-[11px] text-muted-foreground">{primaryCitation.section}</span>
        )}
        {moreCount > 0 && (
          <span className="badge badge-soft !h-4 !px-1.5 !text-[10px]" data-tone="primary">+{moreCount}</span>
        )}
        {verified && (
          <span className="text-success text-[11px] font-medium" title="Verified against corpus">
            ✓
          </span>
        )}
      </button>

      {/* Popover Card */}
      {popoverOpen && (
        <div 
          className="absolute left-0 bottom-full mb-2 w-80 sm:w-96 bg-card border border-border rounded-ui-lg shadow-ui-lg p-4 z-30 animate-fade-in"
          role="region"
          aria-label="Citations list"
        >
          <div className="flex items-center justify-between pb-3 border-b border-border mb-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Source Citations</span>
              {verified && (
                <span className="badge badge-soft" data-tone="success">Verified</span>
              )}
            </div>
            <span className="text-mono text-xs text-muted-foreground">{citations.length} cited</span>
          </div>

          <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
            {citations.map((cit, idx) => {
              const citKey = `${cit.act}-${cit.section}`;
              const isCopied = copiedId === citKey;
              return (
                <div key={idx} className="p-3 rounded-ui-sm bg-muted/60 border border-border text-xs space-y-1.5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="font-medium text-foreground">
                      {cit.act}
                      {cit.section && <span className="ml-1 text-muted-foreground">· {cit.section}</span>}
                    </div>
                    <span className="badge badge-outline !h-4 !px-1.5 !text-[10px] uppercase shrink-0">
                      {cit.jurisdiction}
                    </span>
                  </div>

                  {cit.excerpt && (
                    <blockquote className="text-muted-foreground italic border-l-2 border-border pl-2 my-1 leading-relaxed text-[11px]">
                      "{cit.excerpt}"
                    </blockquote>
                  )}

                  <div className="flex items-center justify-between pt-1 text-[11px]">
                    {cit.source_url ? (
                      <a 
                        href={cit.source_url} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="link"
                      >
                        Official Gazette ↗
                      </a>
                    ) : (
                      <span className="text-muted-foreground">National Statutory Archive</span>
                    )}

                    <button 
                      type="button" 
                      onClick={() => handleCopy(cit)}
                      className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                    >
                      {isCopied ? 'Copied ✓' : 'Copy'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
