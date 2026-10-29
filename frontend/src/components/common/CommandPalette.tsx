import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  Search,
  Plus,
  BookOpen,
  Brain,
  Wrench,
  Sun,
  Moon,
  Settings,
  Download,
  X,
  Palette,
} from 'lucide-react';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onToggle: () => void;
  onNewConversation: () => void;
  onToggleTheme: () => void;
  theme: 'dark' | 'light';
  onOpenContextTab: (tab: 'canvas' | 'documents' | 'research' | 'memories' | 'tools' | 'gallery') => void;
  onOpenSettings: () => void;
  onExport?: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onToggle,
  onNewConversation,
  onToggleTheme,
  theme,
  onOpenContextTab,
  onOpenSettings,
  onExport,
}) => {
  const [query, setQuery] = useState('');
  const [prevQuery, setPrevQuery] = useState(query);
  const [selectedIndex, setSelectedIndex] = useState(0);

  if (prevQuery !== query) {
    setPrevQuery(query);
    setSelectedIndex(0);
  }

  const listRef = useRef<HTMLDivElement>(null);

  const actions = useMemo(() => {
    const list = [
      {
        id: 'new-chat',
        title: 'New Conversation',
        subtitle: 'Create a fresh conversation workspace',
        icon: Plus,
        run: () => {
          onNewConversation();
          onClose();
        },
      },
      {
        id: 'canvas',
        title: 'Open Canvas Studio',
        subtitle: 'Side-by-side live workspace for code & HTML preview',
        icon: BookOpen,
        run: () => {
          onOpenContextTab('canvas');
          onClose();
        },
      },
      {
        id: 'docs',
        title: 'Open Knowledge Library',
        subtitle: 'Inspect and upload documents for local RAG',
        icon: BookOpen,
        run: () => {
          onOpenContextTab('documents');
          onClose();
        },
      },
      {
        id: 'research',
        title: 'Deep Research Studio',
        subtitle: 'Formulate and execute structured multi-step research',
        icon: Search,
        run: () => {
          onOpenContextTab('research');
          onClose();
        },
      },
      {
        id: 'memory',
        title: 'Long-Term Memory Inspector',
        subtitle: 'Curate your persistent assistant preferences',
        icon: Brain,
        run: () => {
          onOpenContextTab('memories');
          onClose();
        },
      },
      {
        id: 'tools',
        title: 'Tool Execution Lab',
        subtitle: 'Test calculator, datetime, and dataset utilities',
        icon: Wrench,
        run: () => {
          onOpenContextTab('tools');
          onClose();
        },
      },
      {
        id: 'gallery',
        title: 'Visual Art & Vision Studio',
        subtitle: 'Generate neural artwork and inspect images with multimodal vision',
        icon: Palette,
        run: () => {
          onOpenContextTab('gallery');
          onClose();
        },
      },
      {
        id: 'theme',
        title: `Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`,
        subtitle: 'Toggle interface color palette',
        icon: theme === 'dark' ? Sun : Moon,
        run: () => {
          onToggleTheme();
          onClose();
        },
      },
      {
        id: 'settings',
        title: 'Open Settings & Providers',
        subtitle: 'Manage API keys, models, and system diagnostics',
        icon: Settings,
        run: () => {
          onOpenSettings();
          onClose();
        },
      },
    ];

    if (onExport) {
      list.push({
        id: 'export',
        title: 'Export Conversation',
        subtitle: 'Download current chat as Markdown artifact',
        icon: Download,
        run: () => {
          onExport();
          onClose();
        },
      });
    }

    return list;
  }, [onNewConversation, onOpenContextTab, onOpenSettings, onToggleTheme, onExport, theme, onClose]);

  const filtered = useMemo(() => {
    return actions.filter(
      a =>
        a.title.toLowerCase().includes(query.toLowerCase()) ||
        a.subtitle.toLowerCase().includes(query.toLowerCase())
    );
  }, [actions, query]);



  // Keyboard shortcut listener for Ctrl+K / Cmd+K and arrow keys
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        onToggle();
      } else if (e.key === 'Escape' && isOpen) {
        onClose();
      } else if (isOpen) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          setSelectedIndex(prev => (prev + 1 < filtered.length ? prev + 1 : 0));
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          setSelectedIndex(prev => (prev - 1 >= 0 ? prev - 1 : filtered.length - 1));
        } else if (e.key === 'Enter') {
          if (filtered[selectedIndex]) {
            e.preventDefault();
            filtered[selectedIndex].run();
          }
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, onToggle, filtered, selectedIndex]);

  // Scroll active item into view
  useEffect(() => {
    if (isOpen && listRef.current) {
      const activeEl = listRef.current.children[selectedIndex] as HTMLElement;
      if (activeEl) {
        activeEl.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [selectedIndex, isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-20 px-3 sm:px-4 bg-black/60 backdrop-blur-xs animate-in fade-in"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="command-palette-title"
        className="w-full max-w-lg rounded-2xl border border-border bg-popover text-popover-foreground shadow-2xl overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Search header */}
        <div className="flex items-center px-4 py-3 border-b border-border/70 gap-2">
          <Search className="w-4 h-4 text-muted-foreground shrink-0" />
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Type a command or search actions..."
            aria-label="Search commands"
            autoFocus
            className="flex-1 bg-transparent text-sm focus:outline-none placeholder:text-muted-foreground text-foreground"
          />
          <button
            onClick={onClose}
            aria-label="Close command palette"
            className="p-1 rounded hover:bg-secondary text-muted-foreground transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <h2 id="command-palette-title" className="sr-only">Command palette</h2>

        {/* Action list */}
        <div ref={listRef} role="listbox" className="max-h-[min(60vh,30rem)] overflow-y-auto p-2 flex flex-col gap-1 scrollbar-thin">
          {filtered.length === 0 ? (
            <div className="text-center py-6 text-xs text-muted-foreground">
              No matching commands.
            </div>
          ) : (
            filtered.map((action, idx) => {
              const Icon = action.icon;
              const isSelected = idx === selectedIndex;
              return (
                <button
                  key={action.id}
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  onClick={action.run}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`flex items-center gap-3 p-2.5 rounded-xl text-left transition-all group ${
                    isSelected ? 'bg-secondary ring-1 ring-primary/40' : 'hover:bg-secondary/70'
                  }`}
                >
                  <div
                    className={`p-2 rounded-lg transition-colors shrink-0 ${
                      isSelected
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-secondary text-foreground group-hover:bg-primary group-hover:text-primary-foreground'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div
                      className={`font-semibold text-xs transition-colors ${
                        isSelected ? 'text-primary' : 'text-foreground group-hover:text-primary'
                      }`}
                    >
                      {action.title}
                    </div>
                    <div className="text-[11px] text-muted-foreground truncate">
                      {action.subtitle}
                    </div>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
