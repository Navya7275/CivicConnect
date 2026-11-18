import { useState, type MouseEvent, type FormEvent } from 'react';
import type { Conversation } from '../services/api';

interface SidebarProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  currentView: 'chat' | 'schemes' | 'laws' | 'saved' | 'settings';
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
  onRenameConversation: (id: string, newTitle: string) => void;
  onSwitchView: (view: 'chat' | 'schemes' | 'laws' | 'saved' | 'settings') => void;
  onCloseMobileSidebar?: () => void;
}

export default function Sidebar({
  conversations,
  activeConversationId,
  currentView,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  onRenameConversation,
  onSwitchView,
  onCloseMobileSidebar
}: SidebarProps) {
  const [historySearch, setHistorySearch] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const filteredHistory = conversations.filter(conv => 
    conv.title.toLowerCase().includes(historySearch.toLowerCase())
  );

  const startRename = (conv: Conversation, e: MouseEvent) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditTitle(conv.title);
  };

  const saveRename = (id: string, e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (editTitle.trim()) {
      onRenameConversation(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const handleSelectConv = (id: string) => {
    onSelectConversation(id);
    onSwitchView('chat');
    if (onCloseMobileSidebar) onCloseMobileSidebar();
  };

  const handleNewChat = () => {
    onNewConversation();
    onSwitchView('chat');
    if (onCloseMobileSidebar) onCloseMobileSidebar();
  };

  return (
    <aside className="flex flex-col h-full sidebar-glass w-72 shrink-0 select-none min-w-0 border-r border-border" aria-label="Application Navigation and History">
      
      {/* Brand Header */}
      <div className="h-16 px-5 flex items-center justify-between shrink-0">
        <a href="/" className="flex items-center gap-2.5 outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-md py-1">
          <img src="/logo.png" alt="CivicConnect Logo" className="w-7 h-7 object-contain drop-shadow-sm" />
          <span className="font-medium text-[15px] tracking-tight text-foreground">CivicConnect</span>
        </a>
        
        {onCloseMobileSidebar && (
          <button 
            type="button"
            onClick={onCloseMobileSidebar}
            className="md:hidden p-1.5 text-muted-foreground hover:text-foreground rounded-md transition-colors"
            aria-label="Close navigation panel"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.75" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        )}
      </div>

      {/* Action Panel: New Chat */}
      <div className="p-4 shrink-0">
        <button 
          type="button"
          onClick={handleNewChat}
          className="btn btn-primary w-full btn-sm flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4"/></svg>
          <span>New Chat</span>
        </button>
      </div>

      {/* Navigation Views Section */}
      <div className="px-3 py-2 flex flex-col gap-1 shrink-0">
        <button 
          type="button"
          onClick={() => { onSwitchView('schemes'); if (onCloseMobileSidebar) onCloseMobileSidebar(); }}
          className={`nav-link w-full justify-start gap-2.5 ${currentView === 'schemes' ? 'bg-accent text-accent-foreground font-medium' : ''}`}
        >
          <svg className="w-4 h-4 shrink-0 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.75">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
          </svg>
          <span>Welfare Schemes</span>
        </button>

        <button 
          type="button"
          onClick={() => { onSwitchView('laws'); if (onCloseMobileSidebar) onCloseMobileSidebar(); }}
          className={`nav-link w-full justify-start gap-2.5 ${currentView === 'laws' ? 'bg-accent text-accent-foreground font-medium' : ''}`}
        >
          <svg className="w-4 h-4 shrink-0 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.75">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
          </svg>
          <span>Laws & Acts</span>
        </button>

        <button 
          type="button"
          onClick={() => { onSwitchView('saved'); if (onCloseMobileSidebar) onCloseMobileSidebar(); }}
          className={`nav-link w-full justify-start gap-2.5 ${currentView === 'saved' ? 'bg-accent text-accent-foreground font-medium' : ''}`}
        >
          <svg className="w-4 h-4 shrink-0 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.75">
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
          </svg>
          <span>Saved Items</span>
        </button>
      </div>

      {/* History Search Header */}
      <div className="p-3 shrink-0">
        <div className="relative flex items-center">
          <div className="absolute left-3 pointer-events-none text-muted-foreground flex items-center justify-center">
            <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          </div>
          <input 
            type="text" 
            placeholder="Search conversations…" 
            value={historySearch}
            onChange={(e) => setHistorySearch(e.target.value)}
            className="input input-sm !pl-9 text-xs"
          />
        </div>
      </div>

      {/* Scrollable Chat History List */}
      <div className="flex-grow overflow-y-auto px-2 py-1 space-y-1">
        <div className="px-3 py-1.5 text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
          Conversations ({filteredHistory.length})
        </div>

        {filteredHistory.length === 0 ? (
          <div className="px-3 py-6 text-center text-xs text-muted-foreground">
            No conversations found.
          </div>
        ) : (
          filteredHistory.map(conv => {
            const isActive = currentView === 'chat' && activeConversationId === conv.id;
            return (
              <div 
                key={conv.id}
                onClick={() => handleSelectConv(conv.id)}
                className={`group relative flex items-center justify-between px-3 py-2 rounded-ui-sm cursor-pointer transition-colors text-sm ${isActive ? 'bg-card text-foreground shadow-ui-sm font-medium border border-border' : 'text-muted-foreground hover:text-foreground hover:bg-muted/70'}`}
              >
                {editingId === conv.id ? (
                  <form onSubmit={(e) => saveRename(conv.id, e)} className="flex-grow mr-2" onClick={(e) => e.stopPropagation()}>
                    <input 
                      type="text" 
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onBlur={() => setEditingId(null)}
                      autoFocus
                      className="w-full px-2 py-1 text-xs bg-background border border-ring rounded-sm outline-none text-foreground"
                    />
                  </form>
                ) : (
                  <div className="flex items-center gap-2 truncate mr-2 flex-grow">
                    <svg className="w-3.5 h-3.5 shrink-0 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.75">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                    </svg>
                    <span className="truncate text-xs">{conv.title}</span>
                  </div>
                )}

                {/* Edit & Delete hover controls */}
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button 
                    type="button"
                    onClick={(e) => startRename(conv, e)}
                    className="p-1 hover:text-foreground rounded"
                    title="Rename conversation"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.75"><path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>
                  </button>
                  <button 
                    type="button"
                    onClick={(e) => { e.stopPropagation(); onDeleteConversation(conv.id); }}
                    className="p-1 hover:text-destructive rounded"
                    title="Delete conversation"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.75"><path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Settings / Footer Profile */}
      <div className="p-3 shrink-0">
        <button 
          type="button"
          onClick={() => { onSwitchView('settings'); if (onCloseMobileSidebar) onCloseMobileSidebar(); }}
          className={`nav-link w-full justify-start gap-2.5 ${currentView === 'settings' ? 'bg-accent text-accent-foreground font-medium' : ''}`}
        >
          <svg className="w-4 h-4 shrink-0 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.75">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
          <span className="text-xs">Preferences & Settings</span>
        </button>
      </div>

    </aside>
  );
}
