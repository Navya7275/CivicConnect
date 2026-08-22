import React, { useState } from 'react';

interface FeedbackModalProps {
  messageId: string;
  rating: 'helpful' | 'not-helpful';
  onClose: () => void;
  onSubmit: (comment: string, selectedIssues: string[]) => void;
}

const COMMON_ISSUES = [
  'Outdated welfare parameters',
  'Incorrect legal citation',
  'Confusing translation / phrasing',
  'Missing state exemption criteria',
  'Broken official reference URL link',
  'Other visual layout bug'
];

export default function FeedbackModal({ 
  messageId, 
  rating, 
  onClose, 
  onSubmit 
}: FeedbackModalProps) {
  const [comment, setComment] = useState('');
  const [selectedIssues, setSelectedIssues] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleIssueToggle = (issue: string) => {
    setSelectedIssues(prev => 
      prev.includes(issue) ? prev.filter(i => i !== issue) : [...prev, issue]
    );
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1200));
    
    onSubmit(comment, selectedIssues);
    setIsSubmitting(false);
    setIsSubmitted(true);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-canvas/80 backdrop-blur-sm p-4" role="dialog" aria-modal="true" aria-labelledby="feedback-title">
      {/* Modal Canvas Card */}
      <div className="bg-canvas-card border border-hairline rounded-sm w-full max-w-md flex flex-col justify-between overflow-hidden shadow-2xl animate-scale-up">
        
        {/* Header */}
        <div className="p-6 border-b border-hairline flex items-center justify-between">
          <h2 id="feedback-title" className="text-body-md text-ink font-semibold">
            {rating === 'helpful' ? 'Provide Feedback' : 'Report AI Response Issue'}
          </h2>
          <button 
            type="button" 
            onClick={onClose}
            className="p-1.5 text-mute hover:text-ink outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-sm"
            aria-label="Close feedback dialog"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>

        {isSubmitted ? (
          /* Submitted State */
          <div className="p-8 text-center space-y-4">
            <svg className="w-12 h-12 text-accent-sunset mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            <h3 className="text-body-md text-ink font-semibold">Feedback Submitted</h3>
            <p className="text-body-sm text-mute">Thank you for helping us verify our sources and improve accuracy.</p>
            <button 
              type="button" 
              onClick={onClose}
              className="button-pill button-pill-outline text-caption-mono-sm mt-4"
            >
              close
            </button>
          </div>
        ) : (
          /* Form State */
          <form onSubmit={handleFormSubmit}>
            <div className="p-6 space-y-6 max-h-[60vh] overflow-y-auto">
              
              {/* Optional Checklist for issues */}
              {rating === 'not-helpful' && (
                <div className="space-y-3">
                  <span className="text-caption-mono text-mute tracking-wider block font-mono">select issues</span>
                  <div className="grid grid-cols-1 gap-2.5" role="group" aria-label="Response issue selection checklist">
                    {COMMON_ISSUES.map(issue => (
                      <label 
                        key={issue} 
                        className="flex items-start gap-3 p-3 bg-canvas-soft border border-hairline rounded-sm text-body-sm text-mute hover:border-body-mid hover:text-ink cursor-pointer select-none"
                      >
                        <input 
                          type="checkbox" 
                          checked={selectedIssues.includes(issue)}
                          onChange={() => handleIssueToggle(issue)}
                          className="mt-1 w-4 h-4 accent-primary rounded-sm focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
                        />
                        <span>{issue}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Text Comment Input */}
              <div className="flex flex-col gap-2">
                <label htmlFor="feedback-comment" className="text-caption-mono text-mute tracking-wider font-mono">
                  {rating === 'helpful' ? 'additional notes (optional)' : 'details (optional)'}
                </label>
                <textarea 
                  id="feedback-comment"
                  rows={4}
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Explain why this response was helpful or what corrections are needed…"
                  className="w-full px-4 py-3 bg-canvas-soft border border-hairline rounded-sm text-body-sm focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none resize-none"
                ></textarea>
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-hairline bg-canvas-soft/30 flex items-center justify-end gap-3">
              <button 
                type="button" 
                onClick={onClose}
                className="button-pill button-pill-outline text-caption-mono-sm"
              >
                cancel
              </button>
              <button 
                type="submit" 
                disabled={isSubmitting}
                className="button-pill button-pill-primary text-caption-mono-sm inline-flex items-center gap-1.5"
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin h-4 w-4 text-on-primary" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>submitting…</span>
                  </>
                ) : (
                  <span>submit</span>
                )}
              </button>
            </div>
          </form>
        )}

      </div>
    </div>
  );
}


