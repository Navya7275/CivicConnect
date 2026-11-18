import React, { useRef, useEffect } from 'react';

interface ComposerProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  submitting?: boolean;
}

export default function Composer({ onSend, disabled = false, submitting = false }: ComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // Auto-grow height based on content
  const handleInput = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    const textarea = textareaRef.current;
    if (textarea && textarea.value.trim() && !disabled && !submitting) {
      onSend(textarea.value.trim());
      textarea.value = '';
      textarea.style.height = 'auto';
    }
  };

  useEffect(() => {
    if (textareaRef.current && !disabled && !submitting) {
      textareaRef.current.focus();
    }
  }, [disabled, submitting]);

  return (
    <div className="relative flex items-end gap-2 bg-[#f4f4f6] rounded-3xl p-2.5 w-full focus-within:bg-[#efeff2] focus-within:ring-2 focus-within:ring-black/10 transition-all duration-200 min-w-0 shadow-xs">
      <label htmlFor="composer-input" className="sr-only">Type your question about Indian laws or welfare schemes</label>
      <textarea
        id="composer-input"
        ref={textareaRef}
        rows={1}
        onInput={handleInput}
        onKeyDown={handleKeyDown}
        placeholder="Ask a question about welfare eligibility, penalties, or statutory rights…"
        disabled={disabled || submitting}
        className="flex-grow min-w-0 bg-transparent border-0 rounded-none px-4 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-0 resize-none h-10 max-h-[180px] leading-relaxed self-center"
        autoComplete="off"
        spellCheck="true"
      ></textarea>

      {/* Send Button */}
      <button
        type="button"
        onClick={handleSubmit}
        disabled={disabled || submitting}
        className="btn btn-primary !h-9 !w-9 !p-0 rounded-full shrink-0 self-center shadow-sm cursor-pointer disabled:opacity-40"
        aria-label="Send message to assistant"
      >
        {submitting ? (
          <svg className="animate-spin h-4 w-4 text-primary-foreground" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        ) : (
          <svg className="w-4 h-4 text-primary-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18"/>
          </svg>
        )}
      </button>
    </div>
  );
}
