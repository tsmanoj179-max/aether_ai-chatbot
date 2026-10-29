import React, { useState, useRef, useEffect } from 'react';
import {
  Menu,
  Sun,
  Moon,
  Settings,
  BookOpen,
  Search,
  Brain,
  Wrench,
  Command,
  Edit2,
  Check,
  Download,
  Code2,
  Palette,
  Layers,
  X,
  Power,
} from 'lucide-react';
import { api } from '../../api/client';

interface HeaderProps {
  title: string;
  onRenameTitle?: (newTitle: string) => void;
  onToggleSidebar: () => void;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
  onOpenSettings: () => void;
  onOpenCommandPalette: () => void;
  activeContextTab: 'none' | 'canvas' | 'documents' | 'research' | 'memories' | 'tools' | 'gallery';
  onToggleContextTab: (tab: 'canvas' | 'documents' | 'research' | 'memories' | 'tools' | 'gallery') => void;
  onExportConversation?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  onRenameTitle,
  onToggleSidebar,
  theme,
  onToggleTheme,
  onOpenSettings,
  onOpenCommandPalette,
  activeContextTab,
  onToggleContextTab,
  onExportConversation,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(title);
  const [mobileStudioOpen, setMobileStudioOpen] = useState(false);
  const [showExitConfirm, setShowExitConfirm] = useState(false);
  const [isExiting, setIsExiting] = useState(false);
  const mobileStudioRef = useRef<HTMLDivElement>(null);

  const handleExitApp = async () => {
    setIsExiting(true);
    try {
      await api.shutdownSystem(true);
    } catch {}
    setTimeout(() => {
      window.close();
    }, 400);
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (mobileStudioRef.current && !mobileStudioRef.current.contains(e.target as Node)) {
        setMobileStudioOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSaveTitle = () => {
    if (editValue.trim() && onRenameTitle) {
      onRenameTitle(editValue.trim());
    }
    setIsEditing(false);
  };

  const handleCancelTitle = () => {
    setEditValue(title);
    setIsEditing(false);
  };

  const studioTabs = [
    { id: 'canvas', label: 'Canvas', icon: Code2, title: 'Interactive Canvas Studio' },
    { id: 'documents', label: 'Docs', icon: BookOpen, title: 'Knowledge Library (RAG)' },
    { id: 'research', label: 'Research', icon: Search, title: 'Deep Research Panel' },
    { id: 'memories', label: 'Memory', icon: Brain, title: 'Long-term Memories' },
    { id: 'tools', label: 'Tools', icon: Wrench, title: 'Tool Execution Lab' },
    { id: 'gallery', label: 'Vision', icon: Palette, title: 'Artwork Gallery & Vision' },
  ] as const;

  return (
    <header className="app-header h-14 border-b border-border/80 bg-background/85 backdrop-blur-md px-3 sm:px-4 flex items-center justify-between gap-2 sm:gap-3 shrink-0 z-20">
      <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
        <button
          onClick={onToggleSidebar}
          aria-label="Toggle navigation"
          className="p-1.5 rounded-lg border border-border/60 hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors shrink-0"
          title="Toggle Sidebar"
        >
          <Menu className="w-4 h-4" />
        </button>

        {isEditing ? (
          <div className="flex items-center gap-1.5 min-w-0 flex-1 max-w-sm">
            <input
              type="text"
              value={editValue}
              onChange={e => setEditValue(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') handleSaveTitle();
                if (e.key === 'Escape') handleCancelTitle();
              }}
              onBlur={handleSaveTitle}
              aria-label="Conversation title"
              autoFocus
              className="w-full text-xs sm:text-sm font-semibold bg-secondary px-2 py-1 rounded border border-primary/50 focus:outline-none"
            />
            <button
              onClick={handleSaveTitle}
              aria-label="Save conversation title"
              className="p-1 rounded bg-primary text-primary-foreground hover:bg-primary/90 shrink-0"
            >
              <Check className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleCancelTitle}
              aria-label="Cancel title edit"
              className="p-1 rounded hover:bg-secondary text-muted-foreground shrink-0"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => {
              setEditValue(title);
              setIsEditing(true);
            }}
            className="app-header-title flex items-center gap-1.5 cursor-pointer group truncate text-left min-w-0"
            aria-label={`Rename conversation: ${title || 'New Conversation'}`}
            title="Click to rename conversation"
          >
            <span className="font-semibold text-xs sm:text-sm text-foreground truncate max-w-[150px] xs:max-w-[200px] sm:max-w-xs md:max-w-md">
              {title || 'New Conversation'}
            </span>
            <Edit2 className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
          </button>
        )}
      </div>

      {/* Right Controls */}
      <div className="app-header-controls flex items-center gap-1 sm:gap-1.5 shrink-0">
        {/* Desktop Contextual Panel Toggles */}
        <div className="hidden sm:flex items-center gap-1 border-r border-border/60 pr-2">
          {studioTabs.map(tab => {
            const Icon = tab.icon;
            const isActive = activeContextTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => onToggleContextTab(tab.id)}
                aria-pressed={isActive}
                className={`p-1.5 rounded-lg border text-xs flex items-center gap-1 transition-colors ${
                  isActive
                    ? 'border-primary/50 bg-primary/10 text-primary font-medium'
                    : 'border-transparent hover:bg-secondary text-muted-foreground hover:text-foreground'
                }`}
                title={tab.title}
              >
                <Icon className="w-3.5 h-3.5" />
                <span className="hidden lg:inline text-[11px] font-medium">{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Mobile Studio Menu Toggle */}
        <div className="relative sm:hidden" ref={mobileStudioRef}>
          <button
            type="button"
            onClick={() => setMobileStudioOpen(!mobileStudioOpen)}
            aria-label="Studio workspaces"
            aria-expanded={mobileStudioOpen}
            className={`p-1.5 rounded-lg border text-xs transition-colors flex items-center gap-1 ${
              activeContextTab !== 'none'
                ? 'border-primary/50 bg-primary/10 text-primary'
                : 'border-border/60 hover:bg-secondary text-muted-foreground hover:text-foreground'
            }`}
            title="Studio Workspaces"
          >
            <Layers className="w-3.5 h-3.5" />
            {activeContextTab !== 'none' && (
              <span className="w-1.5 h-1.5 rounded-full bg-primary" />
            )}
          </button>

          {mobileStudioOpen && (
            <div
              role="menu"
              className="absolute right-0 top-full mt-2 w-48 rounded-xl border border-border bg-popover text-popover-foreground shadow-2xl p-1.5 z-50 animate-in fade-in slide-in-from-top-2"
            >
              <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground border-b border-border/50 mb-1">
                Studio Tools
              </div>
              {studioTabs.map(tab => {
                const Icon = tab.icon;
                const isActive = activeContextTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    role="menuitem"
                    onClick={() => {
                      onToggleContextTab(tab.id);
                      setMobileStudioOpen(false);
                    }}
                    className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs transition-colors text-left ${
                      isActive
                        ? 'bg-primary/15 text-primary font-semibold'
                        : 'hover:bg-secondary text-foreground'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5 text-primary shrink-0" />
                    <span>{tab.title}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Command Palette Button */}
        <button
          onClick={onOpenCommandPalette}
          aria-label="Open command palette"
          className="flex items-center gap-1.5 px-2 sm:px-2.5 py-1.5 rounded-lg border border-border/60 hover:bg-secondary text-muted-foreground hover:text-foreground text-xs transition-colors"
          title="Command Palette (Ctrl+K)"
        >
          <Command className="w-3.5 h-3.5" />
          <span className="hidden sm:inline text-[11px]">⌘K</span>
        </button>

        {/* Export conversation */}
        {onExportConversation && (
          <button
            onClick={onExportConversation}
            aria-label="Export conversation as Markdown"
            className="p-1.5 rounded-lg border border-border/60 hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
            title="Export conversation as Markdown"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
        )}

        {/* Theme toggle */}
        <button
          onClick={onToggleTheme}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          className="p-1.5 rounded-lg border border-border/60 hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5 text-indigo-400" />}
        </button>

        {/* Settings button */}
        <button
          onClick={onOpenSettings}
          aria-label="Open settings"
          className="p-1.5 rounded-lg border border-border/60 hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
          title="Settings & Provider Setup"
        >
          <Settings className="w-3.5 h-3.5" />
        </button>

        {/* Exit Application button */}
        <button
          onClick={() => setShowExitConfirm(true)}
          aria-label="Exit Application"
          className="p-1.5 rounded-lg border border-border/60 hover:border-red-500/50 hover:bg-red-500/10 text-muted-foreground hover:text-red-500 transition-colors"
          title="Exit Application & Stop Services"
        >
          <Power className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Exit Confirmation Dialog */}
      {showExitConfirm && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="exit-dialog-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150"
          onClick={() => !isExiting && setShowExitConfirm(false)}
        >
          <div
            className="w-full max-w-sm rounded-2xl border border-border bg-card p-5 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-red-500/10 text-red-500 border border-red-500/20">
                <Power className="w-5 h-5" />
              </div>
              <div>
                <h3 id="exit-dialog-title" className="text-sm font-semibold text-foreground">
                  Exit AetherAI?
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  This will shut down all backend, frontend, and background services.
                </p>
              </div>
            </div>

            {isExiting ? (
              <div className="py-2 text-center text-xs text-muted-foreground animate-pulse">
                Services stopped. Closing application...
              </div>
            ) : (
              <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/60">
                <button
                  type="button"
                  onClick={() => setShowExitConfirm(false)}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg border border-border hover:bg-secondary text-foreground transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleExitApp}
                  className="px-3.5 py-1.5 text-xs font-medium rounded-lg bg-red-600 hover:bg-red-700 text-white transition-colors shadow-sm"
                >
                  Exit Application
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
