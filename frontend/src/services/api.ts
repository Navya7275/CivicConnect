/**
 * Citation — matches the agreed API contract in docs/PROJECT_PLAN.md section 3.
 *
 * Field names are deliberately snake_case to mirror the backend exactly, so a
 * response from POST /query binds straight onto this type with no translation
 * step that could silently drift.
 *
 * Note that `verified` is NOT here: the verification agent checks the whole
 * answer and returns one verdict per response, so it lives on Message.
 */
export interface Citation {
  act: string;
  section: string;
  jurisdiction: string;   // "Central" or a state name, e.g. "Madhya Pradesh"
  source_url: string;
  chunk_id?: string;      // optional — supplied by the retrieval layer
  excerpt?: string;       // optional — the exact quoted text, when available
}

export type MessageStatus =
  | 'sending'
  | 'understanding'
  | 'searching'
  | 'generating'
  | 'verifying'
  | 'verified'
  | 'needs-clarification'
  | 'error';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  status?: MessageStatus;
  citations?: Citation[];
  /** Response-level verification verdict from the backend. */
  verified?: boolean;
  /** True when the backend needs the user's state before it can answer. */
  needsClarification?: boolean;
  feedback?: 'helpful' | 'not-helpful';
  feedbackComment?: string;
  feedbackIssues?: string[];
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  jurisdiction: 'central' | 'state';
  stateName: string | null;
  timestamp: string;
}

export interface WelfareScheme {
  id: string;
  name: string;
  description: string;
  eligibility: string;
  benefits: string;
  requiredDocuments: string[];
  state: string; // "Central" or State name
  category: string;
  applicationProcess: string;
  sources: Citation[];
}

export interface LegalSection {
  number: string;
  title: string;
  content: string;
}

export interface LegalAct {
  id: string;
  name: string;
  description: string;
  sections: LegalSection[];
  jurisdiction: 'central' | 'state';
  stateName?: string | null;
}

// --- Service layer configuration ---------------------------------------
//
// Both come from the environment so switching between mock data and the real
// backend never requires a source edit. Mock stays the default so the UI runs
// standalone. See frontend/.env.example.
const USE_MOCK = import.meta.env.PUBLIC_USE_MOCK !== 'false';
const API_BASE = import.meta.env.PUBLIC_API_BASE ?? 'http://localhost:8000';

/** The exact response shape of POST /query (PROJECT_PLAN.md section 3). */
interface QueryApiResponse {
  answer: string;
  citations: Citation[];
  jurisdiction: string;
  verified: boolean;
  needs_clarification: boolean;
}

// Active state simulator for loading phases
export type StatusUpdateCallback = (
  status: MessageStatus,
  responseText?: string,
  citations?: Citation[]
) => void;

import { 
  mockConversations, 
  mockWelfareSchemes, 
  mockLegalActs,
  simulateAiResponse
} from './mockData';

export class CivicConnectApi {
  // Conversations are held in memory only, per PROJECT_PLAN.md Appendix A
  // point 6. They are deliberately NOT persisted: cached mock answers
  // reappearing after a rebuild get mistaken for real ones, and silently
  // storing someone's legal questions in their browser is not something our
  // privacy page covers.
  private conversations: Conversation[] = [];

  constructor() {
    this.conversations = [...mockConversations];
  }

  async getConversations(): Promise<Conversation[]> {
    await this.delay(300);
    return [...this.conversations];
  }

  async createConversation(jurisdiction: 'central' | 'state', stateName: string | null): Promise<Conversation> {
    await this.delay(200);
    const newConv: Conversation = {
      id: `conv_${Date.now()}`,
      title: 'New Conversation',
      messages: [],
      jurisdiction,
      stateName,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    this.conversations.unshift(newConv);
    return newConv;
  }

  async deleteConversation(id: string): Promise<boolean> {
    await this.delay(200);
    this.conversations = this.conversations.filter(c => c.id !== id);
    return true;
  }

  async renameConversation(id: string, newTitle: string): Promise<boolean> {
    await this.delay(200);
    const conv = this.conversations.find(c => c.id === id);
    if (conv) {
      conv.title = newTitle;
      return true;
    }
    return false;
  }

  // Multi-step animated response flow simulating RAG backend lifecycle
  async sendMessageStream(
    conversationId: string, 
    userText: string, 
    onUpdate: StatusUpdateCallback
  ): Promise<void> {
    // 1. Find conversation
    const conv = this.conversations.find(c => c.id === conversationId);
    if (!conv) {
      onUpdate('error', 'Conversation not found');
      return;
    }

    // Add user message
    const userMsg: Message = {
      id: `msg_user_${Date.now()}`,
      role: 'user',
      content: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    conv.messages.push(userMsg);
    
    // Auto-update conversation title if it was the first message
    if (conv.messages.filter(m => m.role === 'user').length === 1) {
      conv.title = userText.length > 25 ? userText.slice(0, 25) + '…' : userText;
    }

    // Trigger update for user message render
    onUpdate('sending', '');

    if (!USE_MOCK) {
      // Real backend. Contract: POST /query with { query, state }.
      // See docs/PROJECT_PLAN.md section 3.
      //
      // Note what we do NOT send: no conversation_id (threading is a UI
      // concern — the backend answers one question at a time), and no
      // jurisdiction (the backend's Query Understanding agent works that out
      // from the question itself).
      try {
        const response = await fetch(`${API_BASE}/query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: userText,
            state: conv.jurisdiction === 'state' ? conv.stateName : null
          })
        });

        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }

        const data: QueryApiResponse = await response.json();

        // The backend could not answer safely without knowing the user's
        // state, so its "answer" is a question back to them. Render it as a
        // clarification prompt rather than a normal answer (PHASES.md D2.4).
        const status: MessageStatus = data.needs_clarification
          ? 'needs-clarification'
          : 'verified';

        const assistantMsg: Message = {
          id: `msg_ai_${Date.now()}`,
          role: 'assistant',
          content: data.answer,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          status,
          citations: data.citations ?? [],
          verified: data.verified,
          needsClarification: data.needs_clarification
        };
        conv.messages.push(assistantMsg);
        onUpdate(status, assistantMsg.content, assistantMsg.citations);
      } catch (err) {
        onUpdate(
          'error',
          `Could not reach the CivicConnect API at ${API_BASE}. Check that the backend is running (uvicorn backend.main:app).`
        );
      }
      return;
    }

    // Simulated RAG Pipeline states
    try {
      // Step A: Understanding Question
      onUpdate('understanding', '');
      await this.delay(1200);

      // Step B: Finding Relevant Sources
      onUpdate('searching', '');
      await this.delay(1500);

      // Step C: Generating Answer
      onUpdate('generating', '');
      await this.delay(1500);

      // Step D: Verifying Citations
      onUpdate('verifying', '');
      await this.delay(1800);

      // Step E: Answer Verified! Pull response details
      const response = simulateAiResponse(userText, conv.jurisdiction, conv.stateName);
      
      const assistantMsg: Message = {
        id: `msg_ai_${Date.now()}`,
        role: 'assistant',
        content: response.content,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        status: 'verified',
        citations: response.citations,
        verified: true,
        needsClarification: false
      };
      conv.messages.push(assistantMsg);
      onUpdate('verified', assistantMsg.content, assistantMsg.citations);
    } catch (e) {
      onUpdate('error', 'An error occurred while processing your request.');
    }
  }

  async sendFeedback(
    conversationId: string, 
    messageId: string, 
    rating: 'helpful' | 'not-helpful', 
    comment?: string,
    selectedIssues?: string[]
  ): Promise<boolean> {
    await this.delay(300);
    const conv = this.conversations.find(c => c.id === conversationId);
    if (conv) {
      const msg = conv.messages.find(m => m.id === messageId);
      if (msg) {
        msg.feedback = rating;
        if (comment) msg.feedbackComment = comment;
        if (selectedIssues) msg.feedbackIssues = selectedIssues;
        return true;
      }
    }
    return false;
  }

  async searchWelfareSchemes(query: string, state?: string | null): Promise<WelfareScheme[]> {
    await this.delay(400);
    let schemes = [...mockWelfareSchemes];
    if (state) {
      schemes = schemes.filter(s => s.state.toLowerCase() === 'central' || s.state.toLowerCase() === state.toLowerCase());
    }
    if (query.trim() !== '') {
      const q = query.toLowerCase();
      schemes = schemes.filter(s => 
        s.name.toLowerCase().includes(q) || 
        s.description.toLowerCase().includes(q) ||
        s.category.toLowerCase().includes(q)
      );
    }
    return schemes;
  }

  async searchLegalActs(query: string, jurisdiction?: 'central' | 'state', stateName?: string | null): Promise<LegalAct[]> {
    await this.delay(400);
    let acts = [...mockLegalActs];
    if (jurisdiction) {
      acts = acts.filter(a => a.jurisdiction === jurisdiction);
      if (jurisdiction === 'state' && stateName) {
        acts = acts.filter(a => a.stateName?.toLowerCase() === stateName.toLowerCase());
      }
    }
    if (query.trim() !== '') {
      const q = query.toLowerCase();
      acts = acts.filter(a => 
        a.name.toLowerCase().includes(q) || 
        a.description.toLowerCase().includes(q) ||
        a.sections.some(s => s.title.toLowerCase().includes(q) || s.content.toLowerCase().includes(q))
      );
    }
    return acts;
  }

  async getWelfareSchemeDetails(id: string): Promise<WelfareScheme | null> {
    await this.delay(200);
    return mockWelfareSchemes.find(s => s.id === id) || null;
  }

  async getLegalActDetails(id: string): Promise<LegalAct | null> {
    await this.delay(200);
    return mockLegalActs.find(a => a.id === id) || null;
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
