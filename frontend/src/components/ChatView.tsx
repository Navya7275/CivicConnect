import { useState, useEffect, useRef } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import type { Conversation, Message, MessageStatus } from '../services/api';
import Composer from './Composer';
import CitationViewer from './CitationViewer';
import FeedbackModal from './FeedbackModal';

marked.setOptions({
  gfm: true,
  breaks: true,
});

function normalizeMarkdown(content: string): string {
  if (!content) return '';
  return content
    .replace(/([^\n])\s+-\s+\*\*/g, '$1\n- **')
    .replace(/([^\n])\s+-\s+([A-Za-z])/g, '$1\n- $2')
    .replace(/([^\n])\s*(###\s+)/g, '$1\n\n$2');
}

function renderFormattedMessage(rawContent: string): string {
  const normalized = normalizeMarkdown(rawContent);
  const rawHtml = marked.parse(normalized, { async: false }) as string;
  return DOMPurify.sanitize(rawHtml, {
    USE_PROFILES: { html: true },
  });
}

interface ChatViewProps {
  conversation: Conversation | null;
  submitting: boolean;
  activeStatus: MessageStatus | null;
  onSendMessage: (text: string) => void;
  onSendFeedback: (msgId: string, rating: 'helpful' | 'not-helpful', comment?: string, issues?: string[]) => void;
}

const WELCOME_PROMPTS = [
  {
    title: 'Ayushman Bharat PM-JAY',
    query: 'Who is eligible for Ayushman Bharat (PM-JAY) and what documents are required?',
    description: 'Check healthcare coverage rules and socio-economic checklists.'
  },
  {
    title: 'RTI Application Deadlines',
    query: 'How many days does an authority have to respond to an RTI application?',
    description: 'Statutory 30-day timelines and life-and-liberty exceptions.'
  },
  {
    title: 'PM-Kisan Landholder Aid',
    query: 'What is the PM-Kisan scheme income benefit amount and eligibility?',
    description: 'Cultivable land criteria and direct benefit transfer details.'
  }
];

export default function ChatView({
  conversation,
  submitting,
  activeStatus,
  onSendMessage,
  onSendFeedback
}: ChatViewProps) {
  const [activeFeedbackMsg, setActiveFeedbackMsg] = useState<{ id: string; rating: 'helpful' | 'not-helpful' } | null>(null);
  const [copiedMsgId, setCopiedMsgId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation?.messages?.length, submitting, activeStatus]);

  const handleCopyMessage = async (msg: Message) => {
    try {
      await navigator.clipboard.writeText(msg.content);
      setCopiedMsgId(msg.id);
      setTimeout(() => setCopiedMsgId(null), 2000);
    } catch (e) {
      // Fallback
    }
  };

  const handleFeedbackSubmit = (comment: string, selectedIssues: string[]) => {
    if (activeFeedbackMsg) {
      onSendFeedback(activeFeedbackMsg.id, activeFeedbackMsg.rating, comment, selectedIssues);
      setActiveFeedbackMsg(null);
    }
  };

  const messages = conversation?.messages || [];
  const isEmpty = messages.length === 0;

  return (
    <div className="h-full flex flex-col justify-between overflow-hidden bg-background">
      
      {/* Scrollable messages container */}
      <div className="flex-grow overflow-y-auto px-4 py-8">
        <div className="max-w-3xl mx-auto space-y-6">
          
          {isEmpty && (
            <div className="text-center py-16 space-y-10 animate-fade-in">
              <div className="space-y-4 max-w-xl mx-auto">
                <h1 class="text-3xl sm:text-4xl md:text-5xl font-medium tracking-tight text-foreground leading-[1.15]">
                  What can we clarify for you today?
                </h1>
                <p className="text-base text-muted-foreground leading-relaxed">
                  Ask any question on Indian civil statutes, road penalties, welfare scheme benefits, or eligibility procedures.
                </p>
              </div>

              {/* Starter Prompt Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 text-left pt-2">
                {WELCOME_PROMPTS.map((p, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => onSendMessage(p.query)}
                    className="p-5 rounded-2xl border border-black/[0.08] bg-[#fbfbfd] hover:bg-white text-left flex flex-col justify-between group transition-all duration-200 hover:shadow-md hover:border-black/15 cursor-pointer"
                  >
                    <div>
                      <div className="font-medium text-sm text-foreground mb-1.5 group-hover:text-primary transition-colors">
                        {p.title}
                      </div>
                      <div className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                        {p.description}
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground group-hover:text-foreground font-medium mt-4 flex items-center gap-1 transition-colors">
                      <span>Ask question</span>
                      <span className="transform group-hover:translate-x-0.5 transition-transform">→</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Render conversation turns */}
          {messages.map((msg) => {
            const isUser = msg.role === 'user' || (msg as any).sender === 'user';
            const isCopied = copiedMsgId === msg.id;

            return (
              <div 
                key={msg.id}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-2`}
              >
                <div className="flex items-center gap-2 text-xs text-muted-foreground px-1">
                  <span className="font-medium">{isUser ? 'You' : 'CivicConnect'}</span>
                  <span>·</span>
                  <time className="text-mono text-[11px]">{msg.timestamp || 'Just now'}</time>
                </div>

                <div 
                  className={`p-5 text-sm leading-relaxed ${
                    isUser 
                      ? 'bg-[#18181b] text-white font-medium rounded-2xl rounded-tr-sm max-w-[85%] shadow-sm' 
                      : 'bg-[#f7f7f9] border border-black/[0.06] text-foreground rounded-2xl rounded-tl-sm max-w-[90%] shadow-sm'
                  }`}
                >
                  {isUser ? (
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  ) : (
                    <div 
                      className="prose prose-sm max-w-none space-y-3 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_p]:my-2 [&_h3]:font-medium [&_h3]:text-base [&_h3]:my-2 [&_strong]:font-semibold"
                      dangerouslySetInnerHTML={{ __html: renderFormattedMessage(msg.content) }}
                    />
                  )}

                  {/* Citations block for assistant messages */}
                  {!isUser && msg.citations && msg.citations.length > 0 && (
                    <CitationViewer 
                      citations={msg.citations} 
                      verified={msg.verified}
                    />
                  )}
                </div>

                {/* Assistant message action controls */}
                {!isUser && (
                  <div className="flex items-center gap-2 px-1 text-xs text-muted-foreground">
                    <button 
                      type="button" 
                      onClick={() => handleCopyMessage(msg)}
                      className="hover:text-foreground transition-colors cursor-pointer"
                    >
                      {isCopied ? 'Copied ✓' : 'Copy'}
                    </button>
                    <span>·</span>
                    <button 
                      type="button"
                      onClick={() => setActiveFeedbackMsg({ id: msg.id, rating: 'helpful' })}
                      className="hover:text-foreground transition-colors cursor-pointer"
                      title="Mark as helpful"
                    >
                      Helpful
                    </button>
                    <span>·</span>
                    <button 
                      type="button"
                      onClick={() => setActiveFeedbackMsg({ id: msg.id, rating: 'not-helpful' })}
                      className="hover:text-destructive transition-colors cursor-pointer"
                      title="Report an inaccuracy"
                    >
                      Report issue
                    </button>
                  </div>
                )}
              </div>
            );
          })}

          {/* Active Status indicator during streaming */}
          {submitting && (
            <div className="flex items-center gap-3 p-4 rounded-2xl bg-card border border-border shadow-ui-sm w-fit animate-pulse">
              <span className="w-2 h-2 rounded-full bg-primary animate-ping"></span>
              <span className="text-xs font-medium text-foreground">
                {activeStatus === 'sending' && 'Sending question…'}
                {activeStatus === 'searching' && 'Searching statutory acts & welfare database…'}
                {activeStatus === 'synthesizing' && 'Analyzing context and formulating grounded answer…'}
                {activeStatus === 'verifying' && 'Verifying citations against government corpus…'}
                {!activeStatus && 'Processing response…'}
              </span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Composer Bottom Area */}
      <div className="p-4 bg-background/80 backdrop-blur-md shrink-0">
        <div className="max-w-3xl mx-auto">
          <Composer 
            onSend={onSendMessage}
            disabled={submitting}
            submitting={submitting}
          />
          <div className="text-center mt-2">
            <span className="text-[11px] text-muted-foreground">
              CivicConnect is an informational platform. Cross-verify with official gazettes before taking formal legal steps.
            </span>
          </div>
        </div>
      </div>

      {/* Feedback Modal Dialog */}
      {activeFeedbackMsg && (
        <FeedbackModal 
          rating={activeFeedbackMsg.rating}
          onClose={() => setActiveFeedbackMsg(null)}
          onSubmit={handleFeedbackSubmit}
        />
      )}

    </div>
  );
}
