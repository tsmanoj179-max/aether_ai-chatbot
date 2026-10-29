import React, { useState, useRef, useEffect } from 'react';
import { ModelInfo } from '../../types';
import { ChevronUp, ChevronDown, Cpu, Sparkles, Zap, Shield, Search, Check, Info, X } from 'lucide-react';

interface ModelSelectorProps {
  models: ModelInfo[];
  selectedModelId: string;
  onSelectModel: (id: string) => void;
  direction?: 'up' | 'down';
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  models,
  selectedModelId,
  onSelectModel,
  direction = 'up',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [prevSearch, setPrevSearch] = useState(search);
  const [highlightedIndex, setHighlightedIndex] = useState(0);

  if (prevSearch !== search) {
    setPrevSearch(search);
    setHighlightedIndex(0);
  }

  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredModels = models.filter(
    m =>
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      m.provider.toLowerCase().includes(search.toLowerCase()) ||
      m.description.toLowerCase().includes(search.toLowerCase())
  );



  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      } else if (event.key === 'ArrowDown') {
        event.preventDefault();
        setHighlightedIndex(prev => (prev + 1 < filteredModels.length ? prev + 1 : 0));
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        setHighlightedIndex(prev => (prev - 1 >= 0 ? prev - 1 : filteredModels.length - 1));
      } else if (event.key === 'Enter') {
        if (filteredModels[highlightedIndex]) {
          event.preventDefault();
          onSelectModel(filteredModels[highlightedIndex].id);
          setIsOpen(false);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredModels, highlightedIndex, onSelectModel]);

  // Scroll highlighted item into view
  useEffect(() => {
    if (isOpen && listRef.current) {
      const activeEl = listRef.current.children[highlightedIndex] as HTMLElement;
      if (activeEl) {
        activeEl.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [highlightedIndex, isOpen]);

  const selectedModel = models.find(m => m.id === selectedModelId) || models[0];
  const isUp = direction === 'up';

  return (
    <div className="relative inline-block" ref={containerRef}>
      <button
        type="button"
        onClick={() => {
          setIsOpen(open => !open);
          setSearch('');
          setTimeout(() => searchInputRef.current?.focus(), 50);
        }}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-label={`Select model. Current model: ${selectedModel?.name || 'none selected'}`}
        className="flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3 py-1.5 rounded-lg border border-border/80 bg-card hover:bg-secondary/70 text-foreground text-xs font-medium transition-all shadow-xs focus:outline-none focus:ring-2 focus:ring-primary/20"
      >
        <Sparkles className="w-3.5 h-3.5 text-primary shrink-0" />
        <span className="font-semibold truncate max-w-[100px] xs:max-w-[130px] sm:max-w-[160px]">
          {selectedModel?.name || 'Select Model'}
        </span>
        <span className="text-[10px] px-1.5 py-0.5 rounded uppercase font-bold tracking-wider bg-secondary text-muted-foreground shrink-0 hidden xs:inline-block">
          {selectedModel?.tier || 'Free'}
        </span>
        {isUp ? (
          <ChevronUp className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
        )}
      </button>

      {isOpen && (
        <div
          role="dialog"
          aria-label="Model Engine Selector"
          className={`model-menu absolute ${
            isUp ? 'bottom-full mb-2 slide-in-from-bottom-2' : 'top-full mt-2 slide-in-from-top-2'
          } left-0 z-50 w-[min(23rem,calc(100vw-32px))] max-h-[min(70vh,580px)] flex flex-col rounded-xl border border-border bg-popover text-popover-foreground shadow-2xl p-2.5 backdrop-blur-md animate-in fade-in`}
        >
          {/* Header & Search */}
          <div className="pb-2 mb-2 border-b border-border/50">
            <div className="flex items-center justify-between mb-2 px-0.5">
              <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                Select Model Engine
              </span>
              <span className="text-[10px] text-muted-foreground">
                {models.filter(model => model.is_available).length} available
              </span>
            </div>
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                ref={searchInputRef}
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search models, providers, specs..."
                aria-label="Filter models"
                className="w-full pl-8 pr-7 py-1.5 rounded-lg bg-secondary/60 text-xs border border-border/70 focus:outline-none focus:border-primary/50 text-foreground placeholder:text-muted-foreground"
              />
              {search && (
                <button
                  type="button"
                  onClick={() => setSearch('')}
                  aria-label="Clear search"
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* Model options list */}
          <div ref={listRef} role="listbox" className="flex-1 overflow-y-auto space-y-1.5 scrollbar-thin pr-1">
            {filteredModels.length === 0 ? (
              <div className="p-4 text-center text-xs text-muted-foreground">
                No matching models found.
              </div>
            ) : (
              filteredModels.map((model, index) => {
                const isSelected = model.id === selectedModelId;
                const isHighlighted = index === highlightedIndex;

                let Icon = Cpu;
                let badgeColor = 'bg-secondary text-muted-foreground';

                if (model.provider === 'mock') {
                  Icon = Shield;
                  badgeColor = 'bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-500/20';
                } else if (model.provider === 'gemini') {
                  Icon = Sparkles;
                  badgeColor = 'bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border border-indigo-500/20';
                } else if (model.provider === 'groq') {
                  Icon = Zap;
                  badgeColor = 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20';
                } else if (model.provider === 'free_ai' || model.provider === 'openai') {
                  Icon = Sparkles;
                  badgeColor = 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20';
                } else if (model.provider === 'ollama') {
                  Icon = Cpu;
                  badgeColor = 'bg-purple-500/10 text-purple-700 dark:text-purple-300 border border-purple-500/20';
                }

                return (
                  <button
                    key={model.id}
                    type="button"
                    role="option"
                    aria-selected={isSelected}
                    onClick={() => {
                      onSelectModel(model.id);
                      setIsOpen(false);
                    }}
                    onMouseEnter={() => setHighlightedIndex(index)}
                    className={`w-full flex flex-col items-start gap-1 p-2.5 rounded-lg text-left transition-all border ${
                      isSelected
                        ? 'bg-primary/10 border-primary/40 text-primary font-medium'
                        : isHighlighted
                        ? 'bg-secondary/80 border-border text-foreground'
                        : 'border-transparent hover:bg-secondary/70 hover:border-border/60 text-foreground'
                    }`}
                  >
                    <div className="flex items-center justify-between w-full">
                      <div className="flex items-center gap-1.5 font-semibold text-xs">
                        <Icon className="w-3.5 h-3.5 shrink-0" />
                        <span>{model.name}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className={`text-[9px] uppercase px-1.5 py-0.2 rounded font-mono font-bold ${badgeColor}`}>
                          {model.provider}
                        </span>
                        {isSelected && <Check className="w-3.5 h-3.5 text-primary shrink-0" />}
                      </div>
                    </div>

                    <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
                      {model.description}
                    </p>

                    {/* Capability pills */}
                    <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-secondary text-muted-foreground font-mono">
                        {(model.context_window / 1024).toFixed(0)}k context
                      </span>
                      {model.capabilities.vision && (
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-secondary text-muted-foreground">
                          Vision
                        </span>
                      )}
                      {model.capabilities.tool_calling && (
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-secondary text-muted-foreground">
                          Tools
                        </span>
                      )}
                      {model.capabilities.deep_research && (
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-secondary text-muted-foreground flex items-center gap-0.5">
                          <Search className="w-2.5 h-2.5" /> Research
                        </span>
                      )}
                      {(model.tier === 'mock' || model.tier === 'free') && (
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 font-semibold">
                          {model.tier === 'mock' ? 'Demo' : 'Free'}
                        </span>
                      )}
                      {model.is_available ? (
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-primary/10 text-primary font-medium">
                          Available
                        </span>
                      ) : (
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-secondary text-muted-foreground font-medium">
                          Unavailable
                        </span>
                      )}
                    </div>
                  </button>
                );
              })
            )}
          </div>

          {/* Quick Info footer */}
          <div className="mt-2 pt-2 border-t border-border/50 flex items-center justify-between text-[10px] text-muted-foreground px-1">
            <span className="flex items-center gap-1">
              <Info className="w-3 h-3" /> Auto-failover active
            </span>
            <span>Arrow keys ↑↓ Enter</span>
          </div>
        </div>
      )}
    </div>
  );
};
