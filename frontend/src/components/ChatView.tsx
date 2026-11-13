import { useState, useEffect, useRef } from 'react';
import type { Conversation, Message, MessageStatus } from '../services/api';
import Composer from './Composer';
import CitationViewer from './CitationViewer';
import FeedbackModal from './FeedbackModal';

interface ChatViewProps {
  conversation: Conversation | null;
  submitting: boolean;
  activeStatus: MessageStatus | null;
  onSendMessage: (text: string) => void;
  onSendFeedback: (msgId: string, rating: 'helpful' | 'not-helpful', comment?: string, issues?: string[]) => void;
}

const WELCOME_PROMPTS = [
  {
    title: 'Ayushman Bharat Care',
    query: 'Who is eligible for Ayushman Bharat (PM-JAY) and what documents are required?',
    description: 'Check healthcare plan limits and socio-economic checklists.'
  },
  {
    title: 'RTI Request Timelines',
    query: 'How many days does an authority have to respond to an RTI application?',
    description: 'Understand statutory deadlines and life-and-liberty exceptions.'
  },
  {
    title: 'PM-Kisan Farm Support',
    query: 'What is the PM-Kisan scheme income benefit amount?',
    description: 'Verify cultivable land guidelines and bank account seeding details.'
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

  // Auto-scroll to bottom of chat
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

  // Maps processing statuses to human-friendly lowercase tracked strings
  const getStatusText = (status: MessageStatus) => {
    switch (status) {
      case 'sending': return 'sending message…';
      case 'understanding': return 'analyzing query context…';
      case 'searching': return 'retrieving legislative references…';
      case 'generating': return 'compiling context summary…';
      case 'verifying': return 'verifying citation alignments…';
      case 'verified': return 'sources verified';
      case 'needs-clarification': return 'which state?';
      default: return 'processing…';
    }
  };

  return (
    <div className="flex flex-col h-full bg-canvas relative overflow-hidden min-w-0 flex-grow" aria-label="Conversation Window">
      
      {/* Scrollable Message Canvas */}
      <div className="flex-grow overflow-y-auto px-3 sm:px-6 py-4 sm:py-8 space-y-6 sm:space-y-8 select-text">
        {!conversation || conversation.messages.length === 0 ? (
          /* Empty / Welcome State Card */
          <div className="max-w-xl mx-auto py-12 space-y-10">
            <div className="text-center space-y-4">
              <span className="text-caption-mono text-accent-sunset tracking-[0.15em] block">welcome to assistant</span>
              <h2 className="text-display-sm text-ink leading-tight">Ask CivicConnect about Indian laws and welfare benefits</h2>
              <p className="text-body-sm text-mute leading-relaxed max-w-sm mx-auto">
                Select an example topic below or query the assistant in plain words.
              </p>
            </div>

            {/* Example query prompts cards */}
            <div className="grid grid-cols-1 gap-4" role="group" aria-label="Suggested starting questions">
              {WELCOME_PROMPTS.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => onSendMessage(prompt.query)}
                  className="w-full text-left bg-canvas-card border border-hairline hover:border-body-mid rounded-sm p-5 transition-all duration-200 outline-none focus-visible:ring-2 focus-visible:ring-primary"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-caption-mono-sm text-ink font-semibold lowercase">{prompt.title}</span>
                    <span className="text-caption-mono-sm text-mute">➔</span>
                  </div>
                  <p className="text-body-sm text-ink mb-1">{prompt.query}</p>
                  <p className="text-xs text-mute">{prompt.description}</p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Message List */
          <div className="max-w-2xl mx-auto space-y-8">
            {conversation.messages.map(msg => (
              <div 
                key={msg.id} 
                className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} space-y-2`}
              >
                {/* Role title & Timestamp header */}
                <div className="flex items-center gap-2 text-caption-mono-sm text-mute/50 select-none lowercase">
                  <span>{msg.role === 'user' ? 'citizen' : 'assistant'}</span>
                  <span>•</span>
                  <span>{msg.timestamp}</span>
                  {msg.role === 'assistant' && msg.verified && (
                    <>
                      <span>•</span>
                      <span className="inline-flex items-center gap-1 text-accent-sunset bg-accent-sunset/10 border border-accent-sunset/30 px-2 py-0.5 rounded-full text-[10px] tracking-wider uppercase font-semibold">
                        <svg className="w-3 h-3 text-accent-sunset" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7"/>
                        </svg>
                        verified
                      </span>
                    </>
                  )}
                  {msg.role === 'assistant' && msg.verified === false && !msg.needsClarification && (
                    <>
                      <span>•</span>
                      <span className="inline-flex items-center gap-1 text-mute bg-canvas-soft border border-hairline px-2 py-0.5 rounded-full text-[10px] tracking-wider uppercase">
                        unverified
                      </span>
                    </>
                  )}
                </div>

                {/* Message bubble */}
                <div 
                  className={`w-full max-w-full px-5 py-4 border rounded-sm text-body-sm leading-relaxed ${msg.role === 'user' ? 'bg-canvas border-hairline/80 text-ink max-w-[85%] sm:max-w-[70%]' : 'bg-canvas-card border-hairline text-body'}`}
                >
                  {/* Verified Answer Headline Banner (Visible at a glance without opening drawer) */}
                  {msg.role === 'assistant' && msg.verified && (
                    <div className="mb-3.5 flex items-center gap-2 text-xs font-mono text-accent-sunset bg-accent-sunset/10 border border-accent-sunset/20 rounded px-2.5 py-1.5 w-fit">
                      <svg className="w-3.5 h-3.5 text-accent-sunset shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7"/>
                      </svg>
                      <span className="font-semibold uppercase tracking-wider text-[11px]">Verified Statutory Answer</span>
                      <span className="text-mute/60 hidden sm:inline">— grounded in official statutory sources</span>
                    </div>
                  )}

                  {/* Markdown summaries rendered cleanly */}
                  <div className="prose prose-invert max-w-none text-body-sm space-y-4">
                    {msg.content.split('\n\n').map((paragraph, pIdx) => {
                      if (paragraph.startsWith('###')) {
                        return <h3 key={pIdx} className="text-body-md text-ink font-semibold mt-4 mb-2">{paragraph.replace('###', '').trim()}</h3>;
                      }
                      if (paragraph.startsWith('- ') || paragraph.startsWith('* ')) {
                        return (
                          <ul key={pIdx} className="list-disc pl-5 space-y-1.5 my-2">
                            {paragraph.split('\n').map((li, liIdx) => (
                              <li key={liIdx}>{li.replace(/^[\-\*]\s+/, '')}</li>
                            ))}
                          </ul>
                        );
                      }
                      if (paragraph.startsWith('1. ') || paragraph.startsWith('2. ') || paragraph.startsWith('3. ')) {
                        return (
                          <ol key={pIdx} className="list-decimal pl-5 space-y-1.5 my-2">
                            {paragraph.split('\n').map((li, liIdx) => (
                              <li key={liIdx}>{li.replace(/^\d+\.\s+/, '')}</li>
                            ))}
                          </ol>
                        );
                      }
                      return <p key={pIdx} className="whitespace-pre-wrap">{paragraph}</p>;
                    })}
                  </div>

                  {/* Clarification prompt: the backend needs the user's state
                      before it can answer safely, so there are no citations to
                      show. Nudge them at the jurisdiction selector instead of
                      rendering this like a normal answer. */}
                  {msg.role === 'assistant' && msg.needsClarification && (
                    <div className="mt-4 flex items-start gap-3 rounded-sm border border-accent-sunset/40 bg-accent-sunset/5 p-4">
                      <svg className="w-5 h-5 shrink-0 text-accent-sunset mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                      <p className="text-body-sm text-mute leading-relaxed">
                        Pick your state or union territory from the selector above, then ask again.
                        Laws like rent control and minimum wages are set by each state separately,
                        so answering without knowing yours could give you another state&rsquo;s rules.
                      </p>
                    </div>
                  )}

                  {/* Inline Citations cards list */}
                  {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
                    <CitationViewer citations={msg.citations} verified={msg.verified} />
                  )}

                  {/* Hybrid Retrieval Breakdown Table (Dense Score, BM25 Rank, Fused RRF Rank) */}
                  {msg.role === 'assistant' && msg.citations && msg.citations.some(c => c._retrieval_scores) && (
                    <details className="mt-4 pt-3 border-t border-hairline/60 group">
                      <summary className="cursor-pointer text-caption-mono-sm text-mute hover:text-ink transition-colors flex items-center gap-1.5 select-none">
                        <span className="group-open:rotate-90 transition-transform duration-150 inline-block text-[10px]">▶</span>
                        <span>Hybrid Retrieval Breakdown (Dense + BM25 + RRF)</span>
                      </summary>
                      <div className="mt-2.5 overflow-x-auto">
                        <table className="w-full text-left text-xs font-mono text-mute/80 border border-hairline/60 rounded">
                          <thead className="bg-canvas-soft text-[10px] uppercase tracking-wider text-mute border-b border-hairline/60">
                            <tr>
                              <th className="py-1.5 px-3">Source Chunk</th>
                              <th className="py-1.5 px-3">Dense Score</th>
                              <th className="py-1.5 px-3">BM25 Rank</th>
                              <th className="py-1.5 px-3">Fused RRF Rank</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-hairline/40 text-[11px]">
                            {msg.citations.map((c, idx) => (
                              <tr key={idx} className="hover:bg-canvas-soft/50">
                                <td className="py-1.5 px-3 text-ink">{c.act} {c.section}</td>
                                <td className="py-1.5 px-3">
                                  {c._retrieval_scores?.dense_score !== undefined ? c._retrieval_scores.dense_score.toFixed(3) : '—'}
                                </td>
                                <td className="py-1.5 px-3">
                                  {c._retrieval_scores?.bm25_rank !== undefined ? `#${c._retrieval_scores.bm25_rank}` : '—'}
                                </td>
                                <td className="py-1.5 px-3 text-accent-sunset font-semibold">
                                  {c._retrieval_scores?.rrf_rank !== undefined ? `#${c._retrieval_scores.rrf_rank}` : `#${idx + 1}`}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </details>
                  )}
                </div>

                {/* Assistant Response Actions Bar (helpful / copy) */}
                {msg.role === 'assistant' && msg.status === 'verified' && (
                  <div className="flex items-center gap-4 text-caption-mono-sm text-mute select-none pt-1">
                    <button 
                      onClick={() => handleCopyMessage(msg)}
                      className="hover:text-ink transition-colors outline-none focus-visible:ring-1 focus-visible:ring-primary rounded-sm py-0.5 px-1"
                      aria-label="Copy AI response to clipboard"
                    >
                      {copiedMsgId === msg.id ? 'copied' : 'copy'}
                    </button>
                    <span>|</span>
                    <button 
                      onClick={() => onSendFeedback(msg.id, 'helpful')}
                      className={`transition-colors outline-none focus-visible:ring-1 focus-visible:ring-primary rounded-sm py-0.5 px-1 ${msg.feedback === 'helpful' ? 'text-accent-sunset font-semibold' : 'hover:text-ink'}`}
                      aria-label="Mark response as helpful"
                    >
                      helpful
                    </button>
                    <span>/</span>
                    <button 
                      onClick={() => setActiveFeedbackMsg({ id: msg.id, rating: 'not-helpful' })}
                      className={`transition-colors outline-none focus-visible:ring-1 focus-visible:ring-primary rounded-sm py-0.5 px-1 ${msg.feedback === 'not-helpful' ? 'text-accent-sunset font-semibold' : 'hover:text-ink'}`}
                      aria-label="Mark response as not helpful and file report"
                    >
                      report issue
                    </button>
                  </div>
                )}
              </div>
            ))}

            {/* Dynamic Simulated Stream Loading States */}
            {submitting && activeStatus && activeStatus !== 'verified' && (
              <div className="flex flex-col items-start space-y-2 animate-pulse">
                <div className="flex items-center gap-2 text-caption-mono-sm text-mute/50 select-none lowercase">
                  <span>assistant</span>
                  <span>•</span>
                  <span>processing…</span>
                </div>
                
                <div className="w-full bg-canvas-card border border-hairline rounded-sm p-5 space-y-4">
                  {/* Animated progress text based on current step */}
                  <div className="flex items-center gap-3 text-caption-mono-sm text-ink lowercase">
                    {/* Loading pulse dot */}
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-sunset opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-accent-sunset"></span>
                    </span>
                    <span aria-live="polite">{getStatusText(activeStatus)}</span>
                  </div>

                  {/* Skeletal loaders for answer */}
                  <div className="space-y-2">
                    <div className="h-3.5 bg-canvas-soft rounded-sm w-[90%]"></div>
                    <div className="h-3.5 bg-canvas-soft rounded-sm w-[75%]"></div>
                    <div className="h-3.5 bg-canvas-soft rounded-sm w-[50%]"></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Message Composer Bar Wrapper */}
      <div className="p-3 sm:p-6 border-t border-hairline bg-canvas shrink-0">
        <div className="max-w-2xl mx-auto">
          <Composer 
            onSend={onSendMessage}
            disabled={submitting}
            submitting={submitting}
          />
          <div className="text-[10px] text-mute/40 text-center mt-2.5 leading-normal select-none lowercase">
            ctrl+enter or enter to send · shift+enter for new line · informational content only
          </div>
        </div>
      </div>

      {/* Feedback dialog display overlay */}
      {activeFeedbackMsg && (
        <FeedbackModal
          messageId={activeFeedbackMsg.id}
          rating={activeFeedbackMsg.rating}
          onClose={() => setActiveFeedbackMsg(null)}
          onSubmit={handleFeedbackSubmit}
        />
      )}

    </div>
  );
}


