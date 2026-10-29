import React, { useState, useMemo } from 'react';
import { Conversation, ProviderStatus } from '../../types';
import {
  Plus,
  Search,
  Pin,
  Trash2,
  Edit2,
  Sparkles,
  Settings,
  X,
  MessageSquare,
  ShieldCheck,
  Calendar,
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
  onRenameConversation: (id: string, newTitle: string) => void;
  onTogglePin: (id: string, currentPinned: boolean) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  providers: ProviderStatus[];
  onOpenSettings: () => void;
}

function groupConversationsByDate(convs: Conversation[]) {
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const yesterdayStart = todayStart - 86400000;
  const lastWeekStart = todayStart - 7 * 86400000;

  const today: Conversation[] = [];
  const yesterday: Conversation[] = [];
  const pastWeek: Conversation[] = [];
  const older: Conversation[] = [];

  for (const c of convs) {
    const time = new Date(c.updated_at || c.created_at).getTime();
    if (time >= todayStart) {
      today.push(c);
    } else if (time >= yesterdayStart) {
      yesterday.push(c);
    } else if (time >= lastWeekStart) {
      pastWeek.push(c);
    } else {
      older.push(c);
    }
  }

  return { today, yesterday, pastWeek, older };
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  onRenameConversation,
  onTogglePin,
  searchQuery,
  onSearchChange,
  providers,
  onOpenSettings,
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  // Exclude internal CLI sessions from web conversation list
  const userConversations = useMemo(() => {
    return conversations.filter(
      c => c.folder !== 'cli' && !c.title.toLowerCase().startsWith('cli session')
    );
  }, [conversations]);

  const filteredConversations = useMemo(() => {
    if (!searchQuery.trim()) return userConversations;
    const q = searchQuery.toLowerCase();
    return userConversations.filter(c => c.title.toLowerCase().includes(q));
  }, [userConversations, searchQuery]);

  const pinnedConversations = useMemo(() => {
    return filteredConversations.filter(c => c.pinned);
  }, [filteredConversations]);

  const unpinnedConversations = useMemo(() => {
    return filteredConversations.filter(c => !c.pinned);
  }, [filteredConversations]);

  const grouped = useMemo(() => {
    return groupConversationsByDate(unpinnedConversations);
  }, [unpinnedConversations]);

  const handleStartRename = (conv: Conversation, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditTitle(conv.title);
  };

  const handleFinishRename = (id: string) => {
    if (editTitle.trim()) {
      onRenameConversation(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const handleCancelRename = () => {
    setEditingId(null);
    setEditTitle('');
  };

  const geminiProvider = providers.find(p => p.name === 'gemini');
  const groqProvider = providers.find(p => p.name === 'groq');

  const activeProviderName = geminiProvider?.is_configured
    ? 'Gemini 2.5 Active'
    : groqProvider?.is_configured
    ? 'GroqCloud Active'
    : 'Mock Simulator Active';

  const renderConversationGroup = (title: string, list: Conversation[], icon?: any) => {
    if (list.length === 0) return null;
    const IconComponent = icon;
    return (
      <div className="mb-3">
        <div className="flex items-center gap-1.5 px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
          {IconComponent && <IconComponent className="w-3 h-3 text-primary" />}
          <span>{title}</span>
          <span className="ml-auto text-[9px] font-normal opacity-70">({list.length})</span>
        </div>
        <div className="flex flex-col gap-0.5 mt-1">
          {list.map(conv => (
            <ConversationItem
              key={conv.id}
              conversation={conv}
              isActive={conv.id === activeConversationId}
              isEditing={editingId === conv.id}
              editTitle={editTitle}
              setEditTitle={setEditTitle}
              onFinishRename={() => handleFinishRename(conv.id)}
              onCancelRename={handleCancelRename}
              onStartRename={e => handleStartRename(conv, e)}
              onSelect={() => {
                onSelectConversation(conv.id);
                if (window.innerWidth < 768) onClose();
              }}
              onDelete={e => {
                e.stopPropagation();
                if (window.confirm(`Delete "${conv.title}"? This action cannot be undone.`)) {
                  onDeleteConversation(conv.id);
                }
              }}
              onTogglePin={e => {
                e.stopPropagation();
                onTogglePin(conv.id, conv.pinned);
              }}
            />
          ))}
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-30 bg-black/50 md:hidden backdrop-blur-xs transition-opacity"
        />
      )}

      <aside
        aria-label="Main navigation"
        className={`sidebar-shell fixed md:relative inset-y-0 left-0 z-40 w-72 bg-card border-r border-border/80 flex flex-col transition-[width,transform,border-color] duration-200 ease-out shrink-0 ${
          isOpen ? 'translate-x-0 md:w-72' : '-translate-x-full md:translate-x-0 md:w-0 md:border-r-0 md:overflow-hidden'
        }`}
      >
        {/* Brand Header */}
        <div className="sidebar-brand h-14 border-b border-border/70 px-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-primary to-cyan-400 flex items-center justify-center text-white shadow-md shadow-primary/20">
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <span className="font-bold text-sm text-foreground tracking-tight">AetherAI</span>
              <span className="block text-[10px] text-muted-foreground tracking-wide">Workspace</span>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close navigation"
            className="md:hidden p-1 rounded-lg hover:bg-secondary text-muted-foreground transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            onClick={() => {
              onNewConversation();
              if (window.innerWidth < 768) onClose();
            }}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 text-xs font-semibold shadow-md transition-all group"
          >
            <Plus className="w-4 h-4 group-hover:rotate-90 transition-transform" />
            <span>New Conversation</span>
          </button>
        </div>

        {/* Search Input */}
        <div className="px-3 pb-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => onSearchChange(e.target.value)}
              placeholder="Search conversations..."
              aria-label="Search conversations"
              className="w-full pl-8 pr-7 py-1.5 rounded-lg border border-border/60 bg-secondary/50 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => onSearchChange('')}
                aria-label="Clear conversation search"
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto px-2 py-1 scrollbar-thin">
          {searchQuery ? (
            /* Search results view */
            <div>
              <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                Matches ({filteredConversations.length})
              </div>
              {filteredConversations.length === 0 ? (
                <div className="px-3 py-6 text-center text-xs text-muted-foreground">
                  No conversations match "{searchQuery}".
                </div>
              ) : (
                <div className="flex flex-col gap-0.5 mt-1">
                  {filteredConversations.map(conv => (
                    <ConversationItem
                      key={conv.id}
                      conversation={conv}
                      isActive={conv.id === activeConversationId}
                      isEditing={editingId === conv.id}
                      editTitle={editTitle}
                      setEditTitle={setEditTitle}
                      onFinishRename={() => handleFinishRename(conv.id)}
                      onCancelRename={handleCancelRename}
                      onStartRename={e => handleStartRename(conv, e)}
                      onSelect={() => {
                        onSelectConversation(conv.id);
                        if (window.innerWidth < 768) onClose();
                      }}
                      onDelete={e => {
                        e.stopPropagation();
                        if (window.confirm(`Delete "${conv.title}"? This action cannot be undone.`)) {
                          onDeleteConversation(conv.id);
                        }
                      }}
                      onTogglePin={e => {
                        e.stopPropagation();
                        onTogglePin(conv.id, conv.pinned);
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
          ) : (
            /* Standard Chronological / Pinned view */
            <>
              {/* Pinned section */}
              {renderConversationGroup('Pinned', pinnedConversations, Pin)}

              {/* Timeframe sections */}
              {renderConversationGroup('Today', grouped.today)}
              {renderConversationGroup('Yesterday', grouped.yesterday)}
              {renderConversationGroup('Previous 7 Days', grouped.pastWeek)}
              {renderConversationGroup('Older', grouped.older, Calendar)}

              {conversations.length === 0 && (
                <div className="px-3 py-6 text-center text-xs text-muted-foreground">
                  No conversations yet.
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer: Provider Status & Settings */}
        <div className="p-3 border-t border-border/70 flex flex-col gap-2 bg-secondary/20">
          <button
            onClick={onOpenSettings}
            className="flex items-center justify-between w-full p-2 rounded-lg bg-card border border-border/70 hover:bg-secondary text-left transition-colors text-xs"
          >
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-3.5 h-3.5 text-primary shrink-0" />
              <div className="flex flex-col">
                <span className="font-semibold text-foreground text-[11px]">Provider Engine</span>
                <span className="text-[10px] text-muted-foreground">{activeProviderName}</span>
              </div>
            </div>
            <Settings className="w-3.5 h-3.5 text-muted-foreground" />
          </button>
        </div>
      </aside>
    </>
  );
};

interface ConversationItemProps {
  conversation: Conversation;
  isActive: boolean;
  isEditing: boolean;
  editTitle: string;
  setEditTitle: (val: string) => void;
  onFinishRename: () => void;
  onCancelRename: () => void;
  onStartRename: (e: React.MouseEvent) => void;
  onSelect: () => void;
  onDelete: (e: React.MouseEvent) => void;
  onTogglePin: (e: React.MouseEvent) => void;
}

const ConversationItem: React.FC<ConversationItemProps> = ({
  conversation,
  isActive,
  isEditing,
  editTitle,
  setEditTitle,
  onFinishRename,
  onCancelRename,
  onStartRename,
  onSelect,
  onDelete,
  onTogglePin,
}) => {
  return (
    <div
      className={`group relative flex items-center justify-between px-2.5 py-2 rounded-lg cursor-pointer text-xs transition-all ${
        isActive
          ? 'bg-primary/10 text-primary font-semibold border border-primary/30 shadow-xs'
          : 'hover:bg-secondary text-foreground/85 hover:text-foreground'
      }`}
    >
      <div className="flex items-center gap-2 min-w-0 flex-1">
        {isEditing ? (
          <input
            type="text"
            value={editTitle}
            onChange={e => setEditTitle(e.target.value)}
            onBlur={onFinishRename}
            onKeyDown={e => {
              if (e.key === 'Enter') onFinishRename();
              if (e.key === 'Escape') onCancelRename();
            }}
            autoFocus
            aria-label="Edit conversation title"
            className="w-full bg-secondary px-1.5 py-0.5 rounded border border-primary text-xs focus:outline-none"
          />
        ) : (
          <button
            type="button"
            onClick={onSelect}
            aria-current={isActive ? 'page' : undefined}
            aria-label={`Open conversation: ${conversation.title}`}
            className="conversation-item-trigger flex items-center gap-2 min-w-0 w-full text-left"
          >
            <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-primary' : 'opacity-70'}`} />
            <span className="truncate">{conversation.title}</span>
          </button>
        )}
      </div>

      {/* Action buttons on hover */}
      <div className="conversation-actions flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-1 shrink-0">
        <button
          onClick={onTogglePin}
          aria-label={conversation.pinned ? 'Unpin conversation' : 'Pin conversation'}
          className={`p-1 rounded hover:bg-background ${
            conversation.pinned ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
          }`}
          title={conversation.pinned ? 'Unpin' : 'Pin to top'}
        >
          <Pin className="w-3 h-3" />
        </button>
        <button
          onClick={onStartRename}
          aria-label="Rename conversation"
          className="p-1 rounded hover:bg-background text-muted-foreground hover:text-foreground"
          title="Rename"
        >
          <Edit2 className="w-3 h-3" />
        </button>
        <button
          onClick={onDelete}
          aria-label="Delete conversation"
          className="p-1 rounded hover:bg-background text-muted-foreground hover:text-destructive"
          title="Delete"
        >
          <Trash2 className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
};
