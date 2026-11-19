import { useState, useEffect } from 'react';
import { CivicConnectApi, type Conversation, type MessageStatus, type WelfareScheme, type LegalAct } from '../services/api';
import Sidebar from './Sidebar';
import ChatView from './ChatView';
import WelfareSchemesView from './WelfareSchemesView';
import LegalInfoView from './LegalInfoView';
import SavedItemsView from './SavedItemsView';
import SettingsView from './SettingsView';
import JurisdictionSelector from './JurisdictionSelector';

export default function AssistantApp() {
  const [api] = useState(() => new CivicConnectApi());
  
  // App views: 'chat' | 'schemes' | 'laws' | 'saved' | 'settings'
  const [currentView, setCurrentView] = useState<'chat' | 'schemes' | 'laws' | 'saved' | 'settings'>('chat');
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  // Core data states
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [savedSchemes, setSavedSchemes] = useState<WelfareScheme[]>([]);
  const [savedActs, setSavedActs] = useState<LegalAct[]>([]);

  // Preferences & Context states
  const [language, setLanguage] = useState('en');
  const [jurisdiction, setJurisdiction] = useState<'central' | 'state'>('central');
  const [stateName, setStateName] = useState<string | null>(null);

  // AI Loading & Stream processing states
  const [submitting, setSubmitting] = useState(false);
  const [activeStatus, setActiveStatus] = useState<MessageStatus | null>(null);

  // Load initial data
  useEffect(() => {
    const initData = async () => {
      const convs = await api.getConversations();
      setConversations(convs);
      
      if (convs.length > 0) {
        setActiveConversationId(convs[0].id);
        setJurisdiction(convs[0].jurisdiction);
        setStateName(convs[0].stateName);
      } else {
        const defConv = await api.createConversation('central', null);
        setConversations([defConv]);
        setActiveConversationId(defConv.id);
      }

      // Load bookmarks
      const storedSchemes = localStorage.getItem('civicconnect_saved_schemes');
      const storedActs = localStorage.getItem('civicconnect_saved_acts');
      if (storedSchemes) setSavedSchemes(JSON.parse(storedSchemes));
      if (storedActs) setSavedActs(JSON.parse(storedActs));
    };

    initData();
  }, [api]);

  // Parse URL query parameters for directory routing integrations
  useEffect(() => {
    if (conversations.length === 0 || !activeConversationId) return;

    const params = new URLSearchParams(window.location.search);
    const urlQuery = params.get('query');
    if (urlQuery) {
      window.history.replaceState({}, document.title, window.location.pathname);
      handleSendMessage(urlQuery);
    }
  }, [conversations.length, activeConversationId]);

  const activeConversation = conversations.find(c => c.id === activeConversationId) || null;

  const handleSendMessage = async (text: string) => {
    if (!activeConversationId || submitting) return;

    setSubmitting(true);
    setActiveStatus('sending');

    try {
      await api.sendMessageStream(
        activeConversationId, 
        text, 
        (status) => {
          setActiveStatus(status);
          
          api.getConversations().then(convs => {
            setConversations(convs);
          });

          if (status === 'verified' || status === 'error' || status === 'needs-clarification') {
            setSubmitting(false);
          }
        }
      );
    } catch (e) {
      setSubmitting(false);
      setActiveStatus('error');
    }
  };

  const handleNewConversation = async () => {
    const newConv = await api.createConversation(jurisdiction, stateName);
    setConversations(prev => [newConv, ...prev]);
    setActiveConversationId(newConv.id);
    setCurrentView('chat');
  };

  const handleDeleteConversation = async (id: string) => {
    await api.deleteConversation(id);
    const updated = await api.getConversations();
    setConversations(updated);
    
    if (activeConversationId === id) {
      if (updated.length > 0) {
        setActiveConversationId(updated[0].id);
      } else {
        const fresh = await api.createConversation(jurisdiction, stateName);
        setConversations([fresh]);
        setActiveConversationId(fresh.id);
      }
    }
  };

  const handleRenameConversation = async (id: string, newTitle: string) => {
    await api.renameConversation(id, newTitle);
    const updated = await api.getConversations();
    setConversations(updated);
  };

  const handleJurisdictionChange = (jur: 'central' | 'state', stName: string | null) => {
    setJurisdiction(jur);
    setStateName(stName);
    
    if (activeConversation) {
      activeConversation.jurisdiction = jur;
      activeConversation.stateName = stName;
      localStorage.setItem('civicconnect_history', JSON.stringify(conversations));
      setConversations([...conversations]);
    }
  };

  const handleSendFeedback = async (
    msgId: string, 
    rating: 'helpful' | 'not-helpful', 
    comment?: string, 
    issues?: string[]
  ) => {
    if (activeConversationId) {
      await api.sendFeedback(activeConversationId, msgId, rating, comment, issues);
      const updated = await api.getConversations();
      setConversations(updated);
    }
  };

  const handleSaveScheme = (scheme: WelfareScheme) => {
    setSavedSchemes(prev => {
      const isSaved = prev.some(s => s.id === scheme.id);
      const updated = isSaved ? prev.filter(s => s.id !== scheme.id) : [...prev, scheme];
      localStorage.setItem('civicconnect_saved_schemes', JSON.stringify(updated));
      return updated;
    });
  };

  const handleSaveAct = (act: LegalAct) => {
    setSavedActs(prev => {
      const isSaved = prev.some(a => a.id === act.id);
      const updated = isSaved ? prev.filter(a => a.id !== act.id) : [...prev, act];
      localStorage.setItem('civicconnect_saved_acts', JSON.stringify(updated));
      return updated;
    });
  };

  const handleClearHistory = () => {
    localStorage.removeItem('civicconnect_history');
    setConversations([]);
    setActiveConversationId(null);
    api.createConversation(jurisdiction, stateName).then(fresh => {
      setConversations([fresh]);
      setActiveConversationId(fresh.id);
    });
  };

  const handleAskFromSubView = (query: string) => {
    setCurrentView('chat');
    handleSendMessage(query);
  };

  return (
    <div className="h-screen w-screen flex bg-muted/40 overflow-hidden text-foreground relative">
      
      {/* Left Sidebar (Desktop: Glass Sidebar, Mobile: Floating Drawer Overlay) */}
      <div className={`h-full shrink-0 z-30 transition-transform duration-base md:translate-x-0 border-r border-border shadow-[1px_0_0_0_var(--border)] ${mobileSidebarOpen ? 'translate-x-0 absolute md:relative' : '-translate-x-full absolute md:relative md:translate-x-0'}`}>
        <Sidebar 
          conversations={conversations}
          activeConversationId={activeConversationId}
          currentView={currentView}
          onSelectConversation={setActiveConversationId}
          onNewConversation={handleNewConversation}
          onDeleteConversation={handleDeleteConversation}
          onRenameConversation={handleRenameConversation}
          onSwitchView={setCurrentView}
          onCloseMobileSidebar={() => setMobileSidebarOpen(false)}
        />
      </div>

      {/* Backdrop overlay for mobile sidebar */}
      {mobileSidebarOpen && (
        <div 
          onClick={() => setMobileSidebarOpen(false)}
          className="md:hidden fixed inset-0 z-20 bg-black/30 backdrop-blur-xs"
          aria-hidden="true"
        ></div>
      )}

      {/* Right Main Panel Shell */}
      <div className="flex-grow flex flex-col h-full min-w-0 relative bg-background">
        
        {/* Top Minimal Toolbar */}
        <header className="h-14 sm:h-16 px-3 sm:px-6 bg-transparent flex items-center justify-between shrink-0 z-10 border-b border-border/40 md:border-none">
          
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Mobile Sidebar Toggle */}
            <button 
              type="button"
              onClick={() => setMobileSidebarOpen(!mobileSidebarOpen)}
              className="md:hidden p-1.5 sm:p-2 text-muted-foreground hover:text-foreground border border-input rounded-md transition-colors"
              aria-label="Toggle navigation history sidebar"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
            </button>

            {/* Current view indicator for mobile */}
            <div className="hidden sm:block md:hidden text-sm font-medium text-foreground capitalize">
              {currentView === 'chat' ? 'Assistant' : currentView}
            </div>
          </div>

          {/* Active Jurisdiction Selector widget (Segmented Control style) */}
          <div className="mx-1 sm:mx-auto md:mx-0 scale-90 sm:scale-100 origin-center">
            <JurisdictionSelector 
              jurisdiction={jurisdiction}
              stateName={stateName}
              onChange={handleJurisdictionChange}
            />
          </div>

          {/* Quick exit Link back to public homepage */}
          <div className="flex items-center gap-2">
            <a 
              href="/"
              className="text-xs font-medium text-muted-foreground hover:text-foreground px-2.5 sm:px-3 py-1.5 rounded-full border border-border hover:bg-muted/50 transition-colors whitespace-nowrap"
            >
              Exit to Home
            </a>
          </div>

        </header>

        {/* Sub-view content router panel */}
        <main className="flex-grow min-h-0 min-w-0 relative bg-background">
          {currentView === 'chat' && (
            <ChatView 
              conversation={activeConversation}
              submitting={submitting}
              activeStatus={activeStatus}
              onSendMessage={handleSendMessage}
              onSendFeedback={handleSendFeedback}
            />
          )}

          {currentView === 'schemes' && (
            <WelfareSchemesView 
              onAskAboutScheme={handleAskFromSubView}
              onSaveScheme={handleSaveScheme}
              savedSchemeIds={savedSchemes.map(s => s.id)}
            />
          )}

          {currentView === 'laws' && (
            <LegalInfoView 
              onAskAboutLaw={handleAskFromSubView}
              onSaveAct={handleSaveAct}
              savedActIds={savedActs.map(a => a.id)}
            />
          )}

          {currentView === 'saved' && (
            <SavedItemsView 
              savedSchemes={savedSchemes}
              savedActs={savedActs}
              onRemoveScheme={(id) => {
                const item = savedSchemes.find(s => s.id === id);
                if (item) handleSaveScheme(item);
              }}
              onRemoveAct={(id) => {
                const item = savedActs.find(a => a.id === id);
                if (item) handleSaveAct(item);
              }}
              onAskAboutItem={handleAskFromSubView}
            />
          )}

          {currentView === 'settings' && (
            <SettingsView 
              language={language}
              onLanguageChange={setLanguage}
              onClearHistory={handleClearHistory}
            />
          )}
        </main>
      </div>

    </div>
  );
}
