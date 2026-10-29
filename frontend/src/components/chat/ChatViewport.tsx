import React, { useRef, useEffect } from 'react';
import { Message, Citation } from '../../types';
import { MessageItem } from './MessageItem';
import { CitationBadge } from './CitationBadge';
import { Sparkles, Code2, Search, BookOpen, Compass, ArrowUpRight } from 'lucide-react';

interface ChatViewportProps {
  messages: Message[];
  isGenerating: boolean;
  streamingContent: string;
  generationStatus: string | null;
  currentCitations: Citation[];
  onStarterPromptClick: (prompt: string, sendImmediately?: boolean) => void;
  onFeedback?: (messageId: string, feedback: 'like' | 'dislike' | null) => void;
  onRegenerate?: (message: Message) => void;
  onEditAndResubmit?: (originalMessage: Message, newText: string) => void;
  onOpenInCanvas?: (content: string, language: string) => void;
}

const STARTER_PROMPTS = [
  {
    icon: Code2,
    category: 'Architecture & ML',
    title: 'Understand a complex idea',
    prompt: 'Explain how transformer models work in plain language, then give me a concrete example.',
  },
  {
    icon: Search,
    category: 'Investigation',
    title: 'Explore an unfamiliar topic',
    prompt: 'Introduce climate tipping points, including the key ideas, trade-offs, and uncertainties.',
  },
  {
    icon: BookOpen,
    category: 'Refinement',
    title: 'Review or improve writing',
    prompt: 'Show me how you would edit a technical design document for clarity, and explain what changed.',
  },
  {
    icon: Compass,
    category: 'Debugging',
    title: 'Work through a coding problem',
    prompt: 'Show me a clear, robust process for debugging an async Python or TypeScript error, with a small example.',
  },
];

export const ChatViewport: React.FC<ChatViewportProps> = ({
  messages,
  isGenerating,
  streamingContent,
  generationStatus,
  currentCitations,
  onStarterPromptClick,
  onFeedback,
  onRegenerate,
  onEditAndResubmit,
  onOpenInCanvas,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  const viewportRef = useRef<HTMLDivElement>(null);
  const shouldAutoScrollRef = useRef(true);
  const lastMessageIdRef = useRef(messages[messages.length - 1]?.id);

  useEffect(() => {
    const latestMessage = messages[messages.length - 1];
    if (latestMessage?.id !== lastMessageIdRef.current) {
      if (latestMessage?.role === 'user') shouldAutoScrollRef.current = true;
      lastMessageIdRef.current = latestMessage?.id;
    }
    if (shouldAutoScrollRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'auto', block: 'end' });
    }
  }, [messages, streamingContent, generationStatus]);

  const handleScroll = () => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    shouldAutoScrollRef.current =
      viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight < 160;
  };

  if (messages.length === 0 && !isGenerating) {
    return (
      <div className="chat-viewport welcome-state flex-1 min-h-0 overflow-y-auto scrollbar-thin flex flex-col items-center justify-center text-center">
        <div className="welcome-mark w-14 h-14 rounded-2xl flex items-center justify-center text-white mb-6 animate-in zoom-in-95">
          <Sparkles className="w-6 h-6" />
        </div>
        <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-primary">
          <span className="w-1.5 h-1.5 rounded-full bg-primary" />
          Your AI workspace
        </div>
        <h1 className="text-[clamp(1.7rem,4vw,2.25rem)] font-semibold text-foreground mb-2 tracking-tight">
          Welcome to AetherAI
        </h1>
        <p className="text-sm text-muted-foreground leading-relaxed max-w-md mb-7">
          Start with a question, a coding problem, or a new idea. Choose a model and tools that fit the work.
        </p>

        {/* Starter prompt cards */}
        <div className="w-full text-left">
          <div className="flex items-center justify-between mb-2.5 px-0.5">
            <span className="text-[11px] font-semibold tracking-wider uppercase text-muted-foreground">
              Curated Starting Points
            </span>
            <span className="text-[10px] text-muted-foreground">
              Click to draft or use arrow to run
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
            {STARTER_PROMPTS.map(item => {
              const Icon = item.icon;
              return (
                <div
                  key={item.title}
                  onClick={() => onStarterPromptClick(item.prompt, false)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onStarterPromptClick(item.prompt, false);
                    }
                  }}
                  className="starter-card flex items-start justify-between gap-3 p-4 rounded-2xl text-left cursor-pointer group border border-border/80 hover:border-primary/50 transition-all shadow-xs"
                >
                  <div className="flex items-start gap-3 min-w-0 flex-1">
                    <div className="p-2 rounded-xl bg-secondary/80 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors shrink-0 mt-0.5">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-[13px] text-foreground group-hover:text-primary transition-colors truncate">
                          {item.title}
                        </span>
                        <span className="text-[9px] px-1.5 py-0.2 rounded-full bg-secondary text-muted-foreground font-mono shrink-0">
                          {item.category}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                        {item.prompt}
                      </div>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={e => {
                      e.stopPropagation();
                      onStarterPromptClick(item.prompt, true);
                    }}
                    aria-label={`Send prompt now: ${item.title}`}
                    title="Send immediately"
                    className="p-1.5 rounded-lg text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors opacity-70 group-hover:opacity-100 shrink-0 self-center"
                  >
                    <ArrowUpRight className="w-4 h-4" />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div ref={viewportRef} onScroll={handleScroll} className="chat-viewport flex-1 overflow-y-auto scrollbar-thin flex flex-col">
      {/* Existing messages */}
      {messages.map(msg => (
        <MessageItem
          key={msg.id}
          message={msg}
          onFeedback={onFeedback}
          onRegenerate={onRegenerate}
          onEditAndResubmit={onEditAndResubmit}
          onOpenInCanvas={onOpenInCanvas}
        />
      ))}

      {/* Real-time Streaming message */}
      {isGenerating && (
        <div className="message-row is-assistant w-full py-5 px-4 md:px-6 transition-colors animate-in fade-in">
          <div className="message-inner max-w-3xl mx-auto flex gap-4">
            <div className="message-avatar w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-white font-semibold text-xs shadow-sm bg-gradient-to-tr from-primary to-indigo-500">
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <span className="font-semibold text-xs text-foreground">AetherAI</span>
                {generationStatus && (
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 font-medium" role="status" aria-live="polite">
                    {generationStatus}
                  </span>
                )}
              </div>

              {streamingContent ? (
                <div className="message-markdown text-sm text-foreground leading-relaxed whitespace-pre-wrap font-sans">
                  {streamingContent}
                  <span className="inline-block w-2 h-4 ml-1 bg-primary animate-pulse align-middle" />
                </div>
              ) : (
                <div className="flex items-center gap-2 text-xs text-muted-foreground" role="status" aria-live="polite">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                  <span>Synthesizing response...</span>
                </div>
              )}

              {/* Citations arriving live */}
              {currentCitations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-border/40">
                  <div className="text-[11px] font-semibold text-muted-foreground mb-1.5 uppercase tracking-wider">
                    Sourced Evidence ({currentCitations.length})
                  </div>
                  <div className="flex flex-wrap">
                    {currentCitations.map((cite, i) => (
                      <CitationBadge key={i} citation={cite} index={i} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} className="h-4 shrink-0" />
    </div>
  );
};
