export interface Citation {
  id: string;
  actName: string;
  sectionNumber: string;
  jurisdiction: string; // "Central" or "State - <StateName>"
  verified: boolean;
  excerpt: string;
  sourceUrl?: string;
}

export type MessageStatus = 
  | 'sending' 
  | 'understanding' 
  | 'searching' 
  | 'generating' 
  | 'verifying' 
  | 'verified' 
  | 'error';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  status?: MessageStatus;
  citations?: Citation[];
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

// Service Layer Config
const USE_MOCK = true;

// Active state simulator for loading phases
export type StatusUpdateCallback = (status: MessageStatus, responseText?: string, citations?: Citation[]) => void;

import { 
  mockConversations, 
  mockWelfareSchemes, 
  mockLegalActs,
  simulateAiResponse
} from './mockData';

export class CivicConnectApi {
  // Local temporary storage for conversations (resets on reload, or loads from localStorage if available)
  private conversations: Conversation[] = [];

  constructor() {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('civicconnect_history');
      if (stored) {
        try {
          this.conversations = JSON.parse(stored);
        } catch (e) {
          this.conversations = [];
        }
      } else {
        this.conversations = [...mockConversations];
        this.saveToStorage();
      }
    } else {
      this.conversations = [...mockConversations];
    }
  }

  private saveToStorage() {
    if (typeof window !== 'undefined') {
      localStorage.setItem('civicconnect_history', JSON.stringify(this.conversations));
    }
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
    this.saveToStorage();
    return newConv;
  }

  async deleteConversation(id: string): Promise<boolean> {
    await this.delay(200);
    this.conversations = this.conversations.filter(c => c.id !== id);
    this.saveToStorage();
    return true;
  }

  async renameConversation(id: string, newTitle: string): Promise<boolean> {
    await this.delay(200);
    const conv = this.conversations.find(c => c.id === id);
    if (conv) {
      conv.title = newTitle;
      this.saveToStorage();
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
    this.saveToStorage();

    // Trigger update for user message render
    onUpdate('sending', '');

    if (!USE_MOCK) {
      // Future production backend integration
      try {
        const response = await fetch(`/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            conversation_id: conversationId,
            message: userText,
            jurisdiction: conv.jurisdiction,
            state: conv.stateName
          })
        });
        if (!response.ok) throw new Error('API Error');
        const data = await response.json();
        
        const assistantMsg: Message = {
          id: `msg_ai_${Date.now()}`,
          role: 'assistant',
          content: data.answer,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          status: 'verified',
          citations: data.citations || []
        };
        conv.messages.push(assistantMsg);
        this.saveToStorage();
        onUpdate('verified', assistantMsg.content, assistantMsg.citations);
      } catch (err) {
        onUpdate('error', 'Connection to civic-backend failed. Please verify if FastAPI RAG server is running.');
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
        citations: response.citations
      };
      conv.messages.push(assistantMsg);
      this.saveToStorage();
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
        this.saveToStorage();
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
