import { useState, type FormEvent } from 'react';

interface FeedbackModalProps {
  messageId?: string;
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

  const handleFormSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    await new Promise(resolve => setTimeout(resolve, 800));
    
    onSubmit(comment, selectedIssues);
    setIsSubmitting(false);
    setIsSubmitted(true);
  };

  return (
    <div className="dialog-overlay" role="dialog" aria-modal="true" aria-labelledby="feedback-title">
      <div className="dialog">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-border">
          <h2 id="feedback-title" className="text-h3 text-lg">
            {rating === 'helpful' ? 'Share Feedback' : 'Report Response Issue'}
          </h2>
          <button 
            type="button" 
            onClick={onClose}
            className="p-1.5 text-muted-foreground hover:text-foreground rounded-ui-sm transition-colors"
            aria-label="Close dialog"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>

        {isSubmitted ? (
          <div className="py-8 text-center space-y-4">
            <div className="w-12 h-12 rounded-ui-full bg-success/10 text-success mx-auto flex items-center justify-center">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/></svg>
            </div>
            <h3 className="font-medium text-base text-foreground">Feedback Recorded</h3>
            <p className="text-small text-muted-foreground max-w-xs mx-auto">
              Thank you for helping us verify statutory accuracy for Indian citizens.
            </p>
            <button 
              type="button"
              onClick={onClose}
              className="btn btn-primary btn-sm"
            >
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleFormSubmit} className="pt-4 space-y-4">
            {rating === 'not-helpful' && (
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Select issue categories:
                </label>
                <div className="flex flex-wrap gap-2">
                  {COMMON_ISSUES.map(issue => {
                    const isSelected = selectedIssues.includes(issue);
                    return (
                      <button
                        key={issue}
                        type="button"
                        onClick={() => handleIssueToggle(issue)}
                        className={`badge cursor-pointer transition-colors ${isSelected ? 'badge-solid' : 'badge-outline'}`}
                        data-tone="primary"
                      >
                        {issue}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="space-y-2">
              <label htmlFor="feedback-comment" className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Additional remarks (optional):
              </label>
              <textarea
                id="feedback-comment"
                rows={3}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Share any specifics about the citation, clause or wording…"
                className="input text-xs"
              ></textarea>
            </div>

            <div className="pt-3 border-t border-border flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                className="btn btn-secondary btn-sm"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="btn btn-primary btn-sm"
              >
                {isSubmitting ? 'Submitting…' : 'Submit Feedback'}
              </button>
            </div>
          </form>
        )}

      </div>
    </div>
  );
}
