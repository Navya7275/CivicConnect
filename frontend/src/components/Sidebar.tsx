import { useState, type MouseEvent, type SubmitEvent } from 'react';
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

  // Filter conversation history
  const filteredHistory = conversations.filter(conv => 
    conv.title.toLowerCase().includes(historySearch.toLowerCase())
  );

  const startRename = (conv: Conversation, e: MouseEvent) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditTitle(conv.title);
  };

  const saveRename = (id: string, e: SubmitEvent<HTMLFormElement>) => {
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
    <aside className="flex flex-col h-full bg-canvas border-r border-hairline w-72 shrink-0 select-none min-w-0" aria-label="Application Navigation and History">
      
      {/* Brand Header */}
      <div className="p-6 border-b border-hairline flex items-center justify-between shrink-0">
        <a href="/" className="flex items-center gap-2 outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-sm">
          <img src="/logo.svg" width="22" height="22" alt="" aria-hidden="true" />
          <span className="text-caption-mono text-ink tracking-wider lowercase">civic<span className="text-accent-sunset">connect</span></span>
        </a>
        
        {/* Mobile Close Button (shows only if toggle callback provided) */}
        {onCloseMobileSidebar && (
          <button 
            type="button"
            onClick={onCloseMobileSidebar}
            className="md:hidden p-1 text-mute hover:text-ink outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-sm"
            aria-label="Close navigation panel"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        )}
      </div>

      {/* Action Panel: New Chat */}
      <div className="p-4 shrink-0">
        <button 
          type="button"
          onClick={handleNewChat}
          className="button-pill button-pill-outline w-full py-2.5 text-caption-mono-sm tracking-widest text-ink hover:scale-105 active:scale-95 flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          <span>new chat</span>
        </button>
      </div>

      {/* Navigation Views Section */}
      <div className="px-4 py-2 flex flex-col gap-1 shrink-0 border-b border-hairline/50">
        {/* Schemes */}
        <button 
          type="button"
          onClick={() => { onSwitchView('schemes'); if (onCloseMobileSidebar) onCloseMobileSidebar(); }}
          className={`flex items-center gap-3 px-3 py-2 text-body-sm rounded-sm transition-all duration-200 text-left outline-none focus-visible:ring-2 focus-visible:ring-primary ${currentView === 'schemes' ? 'bg-canvas-soft text-ink font-medium border-l border-primary' : 'text-mute hover:text-ink hover:bg-canvas-soft/30'}`}
        >
          <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
          <span>Welfare Schemes</span>
        </button>

        {/* Laws */}
        <button 
          type="button"
          onClick={() => { onSwitchView('laws'); if (onCloseMobileSidebar) onCloseMobileSidebar(); }}
          className={`flex items-center gap-3 px-3 py-2 text-body-sm rounded-sm transition-all duration-200 text-left outline-none focus-visible:ring-2 focus-visible:ring-primary ${currentView === 'laws' ? 'bg-canvas-soft text-ink font-medium border-l border-primary' : 'text-mute hover:text-ink hover:bg-canvas-soft/30'}`}
        >
          <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
          <span>Laws & Acts</span>
        </button>

        {/* Saved Bookmarks */}
        <button 
          type="button"
          onClick={() => { onSwitchView('saved'); if (onCloseMobileSidebar) onCloseMobileSidebar(); }}
          className={`flex items-center gap-3 px-3 py-2 text-body-sm rounded-sm transition-all duration-200 text-left outline-none focus-visible:ring-2 focus-visible:ring-primary ${currentView === 'saved' ? 'bg-canvas-soft text-ink font-medium border-l border-primary' : 'text-mute hover:text-ink hover:bg-canvas-soft/30'}`}
        >
          <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/></svg>
          <span>Saved Bookmarks</span>
        </button>
      </div>

      {/* History Search */}
      <div className="px-4 pt-4 shrink-0">
        <div className="relative">
          <label htmlFor="history-search" className="sr-only">Search conversation history</label>
          <input 
            type="text" 
            id="history-search"
            value={historySearch}
            onChange={(e) => setHistorySearch(e.target.value)}
            placeholder="Search history…" 
            className="w-full pl-8 pr-3 py-1.5 bg-canvas-soft border border-hairline rounded-sm text-xs focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
          />
          <div className="absolute left-2.5 top-2 text-mute" aria-hidden="true">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          </div>
        </div>
      </div>

      {/* History List Section */}
      <div className="flex-grow overflow-y-auto px-4 py-2 space-y-1">
        <div className="text-[10px] text-mute/50 uppercase tracking-widest pl-2 mb-2 font-mono">history</div>
        
        {filteredHistory.length === 0 ? (
          <div className="text-center py-8 text-xs text-mute/60">
            Empty history
          </div>
        ) : (
          filteredHistory.map(conv => (
            <div 
              key={conv.id}
              onClick={() => handleSelectConv(conv.id)}
              className={`group relative flex items-center justify-between px-3 py-2.5 rounded-sm transition-all duration-200 text-left outline-none cursor-pointer focus-visible:ring-2 focus-visible:ring-primary ${activeConversationId === conv.id && currentView === 'chat' ? 'bg-canvas-card text-ink border-l-2 border-primary font-medium' : 'text-mute hover:text-ink hover:bg-canvas-soft/40'}`}
            >
              {editingId === conv.id ? (
                /* Rename input form */
                <form 
                  onSubmit={(e) => saveRename(conv.id, e)} 
                  onClick={(e) => e.stopPropagation()}
                  className="w-full flex items-center gap-1.5"
                >
                  <label htmlFor={`rename-conv-${conv.id}`} className="sr-only">Rename conversation title</label>
                  <input 
                    type="text" 
                    id={`rename-conv-${conv.id}`}
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onBlur={() => setEditingId(null)}
                    className="w-full px-2 py-0.5 bg-canvas border border-hairline rounded-sm text-xs text-ink focus-visible:ring-1 focus-visible:ring-primary"
                    autoFocus
                  />
                </form>
              ) : (
                /* Static item display */
                <>
                  <div className="flex-grow min-w-0 pr-6">
                    <div className="text-xs truncate font-sans">{conv.title}</div>
                    <div className="text-[9px] text-mute/50 lowercase mt-0.5">{conv.jurisdiction === 'central' ? 'central' : `${conv.stateName || 'state'}`}</div>
                  </div>

                  {/* Actions (pencil / delete) on hover */}
                  <div className="absolute right-2 top-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity bg-canvas-card p-0.5 rounded-sm">
                    <button 
                      type="button"
                      onClick={(e) => startRename(conv, e)}
                      className="p-0.5 text-mute hover:text-ink rounded-sm focus-visible:ring-1 focus-visible:ring-primary outline-none"
                      aria-label={`Rename chat titled ${conv.title}`}
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>
                    </button>
                    <button 
                      type="button"
                      onClick={(e) => { e.stopPropagation(); onDeleteConversation(conv.id); }}
                      className="p-0.5 text-mute hover:text-accent-sunset rounded-sm focus-visible:ring-1 focus-visible:ring-primary outline-none"
                      aria-label={`Delete chat titled ${conv.title}`}
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-4v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                    </button>
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>

      {/* Settings, Profile, Logout Footer Section */}
      <div className="p-4 border-t border-hairline flex flex-col gap-2 bg-canvas-card/30 shrink-0">
        <button 
          type="button"
          onClick={() => { onSwitchView('settings'); if (onCloseMobileSidebar) onCloseMobileSidebar(); }}
          className={`flex items-center gap-3 px-3 py-2 text-body-sm rounded-sm transition-all duration-200 text-left outline-none focus-visible:ring-2 focus-visible:ring-primary ${currentView === 'settings' ? 'bg-canvas-soft text-ink font-medium border-l border-primary' : 'text-mute hover:text-ink hover:bg-canvas-soft/30'}`}
        >
          <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          <span>Preferences & Profile</span>
        </button>
      </div>

    </aside>
  );
}


