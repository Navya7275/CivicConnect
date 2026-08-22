import React, { useState } from 'react';
import type { Citation } from '../services/api';

interface CitationViewerProps {
  citations: Citation[];
}

export default function CitationViewer({ citations }: CitationViewerProps) {
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  if (!citations || citations.length === 0) return null;

  const handleCopy = async (cit: Citation) => {
    const text = `${cit.actName}, ${cit.sectionNumber} (${cit.jurisdiction}) - Excerpt: "${cit.excerpt}"`;
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(cit.id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (e) {
      // Fallback
    }
  };

  return (
    <div className="mt-4 flex flex-wrap gap-2 items-center">
      <span className="text-caption-mono-sm text-mute shrink-0 lowercase">sources:</span>
      
      {citations.map((cit, idx) => (
        <button 
          key={cit.id}
          type="button"
          onClick={() => setActiveCitation(cit)}
          className="inline-flex items-center gap-1.5 px-3 py-1 bg-canvas-soft border border-hairline hover:border-body-mid rounded-full text-caption-mono-sm text-body-md transition-all duration-200 outline-none focus-visible:ring-2 focus-visible:ring-primary"
          aria-label={`View citation details from ${cit.actName} ${cit.sectionNumber}`}
        >
          {/* Verified Check Icon */}
          {cit.verified && (
            <svg className="w-3.5 h-3.5 text-accent-sunset" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
            </svg>
          )}
          <span>{cit.actName.slice(0, 15)}… {cit.sectionNumber}</span>
        </button>
      ))}

      {/* Citation Details Drawer (Overlay Panel) */}
      {activeCitation && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-canvas/80 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="drawer-title">
          {/* Background dismiss click area */}
          <div className="absolute inset-0" onClick={() => setActiveCitation(null)}></div>
          
          <div className="relative bg-canvas-card border-l border-hairline w-full max-w-md h-full flex flex-col justify-between shadow-2xl animate-slide-left z-10">
            
            {/* Drawer Header */}
            <div className="p-6 border-b border-hairline flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-caption-mono-sm text-accent-sunset tracking-wider bg-accent-sunset/10 px-2 py-0.5 rounded-full uppercase">
                    {activeCitation.verified ? 'verified source' : 'unverified'}
                  </span>
                  <span className="text-caption-mono-sm text-mute uppercase">{activeCitation.jurisdiction}</span>
                </div>
                <h2 id="drawer-title" className="text-body-lg text-ink font-semibold">{activeCitation.actName}</h2>
              </div>
              <button 
                type="button"
                onClick={() => setActiveCitation(null)}
                className="p-1.5 text-mute hover:text-ink outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-sm"
                aria-label="Close citation details panel"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
            </div>

            {/* Drawer Content */}
            <div className="p-6 overflow-y-auto space-y-6 flex-grow text-body-sm leading-relaxed">
              {/* Section details */}
              <div>
                <span className="text-caption-mono text-mute tracking-wider block mb-2 font-mono">section/clause</span>
                <span className="text-body-md text-ink font-semibold">{activeCitation.sectionNumber}</span>
              </div>

              {/* Supporting excerpt */}
              <div>
                <span className="text-caption-mono text-accent-sunset tracking-wider block mb-2 font-mono">supporting excerpt</span>
                <div className="bg-canvas border border-hairline rounded-sm p-4 text-body-sm text-mute leading-relaxed font-mono select-all">
                  "{activeCitation.excerpt}"
                </div>
              </div>

              {/* Official Source Link */}
              {activeCitation.sourceUrl && (
                <div>
                  <span className="text-caption-mono text-mute tracking-wider block mb-2 font-mono">official documentation</span>
                  <a 
                    href={activeCitation.sourceUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-body-sm text-ink hover:text-accent-sunset underline underline-offset-4 outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-sm"
                  >
                    <span>Visit government portal</span>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
                  </a>
                </div>
              )}
            </div>

            {/* Drawer Footer Action Bar */}
            <div className="p-6 border-t border-hairline bg-canvas-soft flex items-center justify-between">
              <button 
                type="button"
                onClick={() => handleCopy(activeCitation)}
                className="button-pill button-pill-outline text-caption-mono-sm inline-flex items-center gap-1.5"
              >
                {copiedId === activeCitation.id ? (
                  <>
                    <svg className="w-4 h-4 text-accent-sunset" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                    <span>copied</span>
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m-6 4h10m-5-5l5 5-5 5"/></svg>
                    <span>copy citation</span>
                  </>
                )}
              </button>
              <button 
                type="button"
                onClick={() => setActiveCitation(null)}
                className="button-pill button-pill-primary text-caption-mono-sm"
              >
                done
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}


