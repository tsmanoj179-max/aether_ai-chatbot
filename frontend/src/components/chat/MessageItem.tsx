import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Message } from '../../types';
import { CodeBlock } from './CodeBlock';
import { CitationBadge } from './CitationBadge';
import {
  Copy,
  Check,
  ThumbsUp,
  ThumbsDown,
  Volume2,
  VolumeX,
  RotateCw,
  Sparkles,
  User,
  Paperclip,
  Brain,
  ChevronDown,
  ChevronUp,
  Edit2,
  CheckCheck,
  Maximize2,
  Download,
  ZoomIn,
  ZoomOut,
  X,
  Image as ImageIcon,
} from 'lucide-react';

interface MessageItemProps {
  message: Message;
  onFeedback?: (messageId: string, feedback: 'like' | 'dislike' | null) => void;
  onRegenerate?: (message: Message) => void;
  onEditAndResubmit?: (originalMessage: Message, newText: string) => void;
  onOpenInCanvas?: (content: string, language: string) => void;
}

export const MessageItem: React.FC<MessageItemProps> = ({
  message,
  onFeedback,
  onRegenerate,
  onEditAndResubmit,
  onOpenInCanvas,
}) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(message.content);
  const [showThinking, setShowThinking] = useState(false);
  const [lightboxImage, setLightboxImage] = useState<{ src: string; alt: string; prompt?: string } | null>(null);
  const [zoom, setZoom] = useState<number>(1);
  const [copiedLink, setCopiedLink] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && lightboxImage) {
        setLightboxImage(null);
        setZoom(1);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [lightboxImage]);

  const downloadImage = async (url: string, filename: string) => {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = filename || 'artwork.jpg';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(blobUrl);
    } catch {
      window.open(url, '_blank');
    }
  };

  // Check if content has thinking / reasoning block (e.g. <think>...</think> or ### Reasoning:)
  let mainContent = message.content;
  let thoughtProcess: string | null = null;

  const thinkMatch = message.content.match(/<think>([\s\S]*?)<\/think>/i);
  if (thinkMatch) {
    thoughtProcess = thinkMatch[1].trim();
    mainContent = message.content.replace(/<think>[\s\S]*?<\/think>/i, '').trim();
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(mainContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  const toggleSpeak = () => {
    if (!('speechSynthesis' in window)) return;

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(mainContent);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  const handleSaveEdit = () => {
    if (editText.trim() && onEditAndResubmit) {
      onEditAndResubmit(message, editText.trim());
      setIsEditing(false);
    }
  };

  // Word & token estimates
  const wordCount = mainContent.trim().split(/\s+/).filter(Boolean).length;
  const estimatedTokens = Math.round(mainContent.length / 4);

  return (
    <div
      className={`message-row group w-full py-5 px-4 md:px-6 transition-colors ${
        isUser ? 'is-user bg-transparent' : 'is-assistant bg-transparent'
      }`}
    >
      <div className="message-inner max-w-3xl mx-auto flex gap-4">
        {/* Avatar */}
        <div
          className={`message-avatar w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-white font-semibold text-xs shadow-sm ${
            isUser
              ? 'bg-neutral-800 text-neutral-200'
              : 'bg-gradient-to-tr from-primary to-indigo-500'
          }`}
        >
          {isUser ? <User className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
        </div>

        {/* Content & Metadata */}
        <div className="message-content flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-xs text-foreground">
                {isUser ? 'You' : 'AetherAI'}
              </span>
              {!isUser && message.model_used && (
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-secondary text-muted-foreground font-mono">
                  {message.model_used}
                </span>
              )}
              {!isUser && message.provider_used === 'mock' && (
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-blue-500/10 text-blue-400 font-medium">
                  Simulator
                </span>
              )}
            </div>

            <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
              {!isUser && (
                <span className="hidden sm:inline">
                  {wordCount} words • ~{estimatedTokens} tokens
                </span>
              )}
              <span>
                {new Date(message.created_at).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            </div>
          </div>

          {/* Attachments preview */}
          {message.attachments && message.attachments.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {message.attachments.map((att, i) => {
                const isImageAtt =
                  att.file_type?.startsWith('image/') ||
                  att.preview_url ||
                  /\.(png|jpe?g|webp|gif|bmp)$/i.test(att.filename);
                return (
                  <div
                    key={i}
                    onClick={() => {
                      if (isImageAtt && att.preview_url) {
                        setLightboxImage({ src: att.preview_url, alt: att.filename });
                        setZoom(1);
                      }
                    }}
                    className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-border bg-secondary/40 text-xs transition-colors ${
                      isImageAtt && att.preview_url
                        ? 'cursor-pointer hover:border-primary/50 hover:bg-secondary/70'
                        : ''
                    }`}
                  >
                    {isImageAtt && att.preview_url ? (
                      <img
                        src={att.preview_url}
                        alt={att.filename}
                        className="w-5 h-5 rounded object-cover border border-border/60"
                      />
                    ) : isImageAtt ? (
                      <ImageIcon className="w-3.5 h-3.5 text-primary" />
                    ) : (
                      <Paperclip className="w-3.5 h-3.5 text-primary" />
                    )}
                    <span className="truncate max-w-[150px] font-medium">{att.filename}</span>
                  </div>
                );
              })}
            </div>
          )}

          {/* Thought Process Accordion */}
          {thoughtProcess && (
            <div className="mb-3 rounded-xl border border-primary/20 bg-primary/5 overflow-hidden text-xs">
              <button
                type="button"
                onClick={() => setShowThinking(!showThinking)}
                className="w-full flex items-center justify-between px-3.5 py-2 font-medium text-primary hover:bg-primary/10 transition-colors"
              >
                <div className="flex items-center gap-1.5">
                  <Brain className="w-3.5 h-3.5" />
                  <span>Thinking & Reasoning Steps</span>
                </div>
                {showThinking ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>
              {showThinking && (
                <div className="p-3.5 border-t border-primary/20 text-muted-foreground whitespace-pre-wrap leading-relaxed font-mono text-[11px] bg-background/50">
                  {thoughtProcess}
                </div>
              )}
            </div>
          )}

          {/* User Inline Editing Mode */}
          {isUser && isEditing ? (
            <div className="space-y-2 mt-1">
              <textarea
                value={editText}
                onChange={e => setEditText(e.target.value)}
                rows={3}
                className="w-full p-2.5 rounded-lg border border-primary bg-secondary/50 text-xs text-foreground focus:outline-none"
              />
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleSaveEdit}
                  className="px-3 py-1 rounded-md bg-primary text-primary-foreground font-semibold text-xs hover:bg-primary/90 flex items-center gap-1"
                >
                  <CheckCheck className="w-3 h-3" /> Resubmit
                </button>
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="px-3 py-1 rounded-md border border-border text-xs hover:bg-secondary"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            /* Message Markdown Body */
            <div className="message-markdown prose prose-sm dark:prose-invert max-w-none text-foreground leading-relaxed break-words">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ inline, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || '');
                    const codeStr = String(children).replace(/\n$/, '');
                    return !inline ? (
                      <CodeBlock
                        language={match ? match[1] : 'text'}
                        value={codeStr}
                        onOpenInCanvas={onOpenInCanvas}
                      />
                    ) : (
                      <code
                        className="px-1.5 py-0.5 rounded bg-secondary font-mono text-xs text-primary font-medium"
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  },
                  a({ href, children, ...props }: any) {
                    return (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary underline decoration-primary/40 hover:decoration-current transition-colors break-words"
                        {...props}
                      >
                        {children}
                      </a>
                    );
                  },
                  table({ children, ...props }: any) {
                    return (
                      <div className="my-3 overflow-x-auto rounded-xl border border-border/70 shadow-xs">
                        <table className="w-full text-left text-xs border-collapse" {...props}>
                          {children}
                        </table>
                      </div>
                    );
                  },
                  blockquote({ children, ...props }: any) {
                    return (
                      <blockquote
                        className="my-3 pl-3.5 border-l-2 border-primary/60 italic text-muted-foreground bg-primary/5 py-1.5 pr-3 rounded-r-lg"
                        {...props}
                      >
                        {children}
                      </blockquote>
                    );
                  },
                  img({ src, alt }: any) {
                    const resolvedSrc = src || '';
                    return (
                      <div className="my-3.5 relative group rounded-2xl overflow-hidden border border-border/80 bg-secondary/15 shadow-md transition-all hover:border-primary/50 max-w-xl">
                        <img
                          src={resolvedSrc}
                          alt={alt || 'Visual Generation'}
                          onClick={() => {
                            setLightboxImage({ src: resolvedSrc, alt: alt || 'Generated Artwork' });
                            setZoom(1);
                          }}
                          className="w-full h-auto object-cover cursor-zoom-in rounded-2xl max-h-[500px] transition-transform duration-300 group-hover:scale-[1.01]"
                          loading="lazy"
                        />
                        <div className="absolute top-2.5 right-2.5 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity bg-background/85 backdrop-blur-md px-2 py-1 rounded-xl border border-border/60 shadow-lg">
                          <button
                            type="button"
                            onClick={() => {
                              setLightboxImage({ src: resolvedSrc, alt: alt || 'Generated Artwork' });
                              setZoom(1);
                            }}
                            className="p-1.5 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
                            title="Fullscreen Zoom"
                          >
                            <Maximize2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            type="button"
                            onClick={() => downloadImage(resolvedSrc, `${(alt || 'aether-art').slice(0, 30)}.jpg`)}
                            className="p-1.5 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
                            title="Download Artwork"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </button>
                        </div>
                        {alt && (
                          <div className="px-3.5 py-2 border-t border-border/40 bg-card/75 backdrop-blur-xs flex items-center justify-between text-xs text-muted-foreground">
                            <span className="truncate italic max-w-[80%] font-medium">"{alt}"</span>
                            <span className="text-[10px] font-bold text-primary tracking-wider uppercase shrink-0">FLUX.1 Neural</span>
                          </div>
                        )}
                      </div>
                    );
                  },
                }}
              >
                {mainContent}
              </ReactMarkdown>
            </div>
          )}

          {/* Sourced Citations */}
          {message.citations && message.citations.length > 0 && (
            <div className="mt-3 pt-3 border-t border-border/40">
              <div className="text-[11px] font-semibold text-muted-foreground mb-1.5 uppercase tracking-wider">
                Sources & Citations
              </div>
              <div className="flex flex-wrap">
                {message.citations.map((cite, i) => (
                  <CitationBadge key={i} citation={cite} index={i} />
                ))}
              </div>
            </div>
          )}

          {/* Action Toolbar */}
          <div className="message-actions flex items-center gap-1 mt-3 opacity-80 group-hover:opacity-100 transition-opacity">
            {isUser && !isEditing && onEditAndResubmit && (
              <button
                type="button"
                onClick={() => {
                  setEditText(message.content);
                  setIsEditing(true);
                }}
                className="p-1.5 rounded hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1 text-[11px]"
                title="Edit and resubmit message"
              >
                <Edit2 className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Edit</span>
              </button>
            )}

            {!isUser && (
              <>
                <button
                  type="button"
                  onClick={handleCopy}
                  aria-label={copied ? 'Response copied' : 'Copy response'}
                  className="p-1.5 rounded hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
                  title="Copy response"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>

                <button
                  type="button"
                  onClick={toggleSpeak}
                  aria-label={isSpeaking ? 'Stop reading response aloud' : 'Read response aloud'}
                  className={`p-1.5 rounded hover:bg-secondary transition-colors ${
                    isSpeaking ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
                  }`}
                  title={isSpeaking ? 'Stop speaking' : 'Read aloud'}
                >
                  {isSpeaking ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
                </button>

                {onRegenerate && (
                  <button
                    type="button"
                    onClick={() => onRegenerate(message)}
                    aria-label="Regenerate response"
                    className="p-1.5 rounded hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
                    title="Regenerate response"
                  >
                    <RotateCw className="w-3.5 h-3.5" />
                  </button>
                )}

                {onFeedback && (
                  <>
                    <button
                      type="button"
                      onClick={() =>
                        onFeedback(message.id, message.feedback === 'like' ? null : 'like')
                      }
                      aria-label={message.feedback === 'like' ? 'Remove positive feedback' : 'Mark response helpful'}
                      aria-pressed={message.feedback === 'like'}
                      className={`p-1.5 rounded hover:bg-secondary transition-colors ${
                        message.feedback === 'like' ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
                      }`}
                      title="Helpful response"
                    >
                      <ThumbsUp className="w-3.5 h-3.5" />
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        onFeedback(message.id, message.feedback === 'dislike' ? null : 'dislike')
                      }
                      aria-label={message.feedback === 'dislike' ? 'Remove negative feedback' : 'Mark response unhelpful'}
                      aria-pressed={message.feedback === 'dislike'}
                      className={`p-1.5 rounded hover:bg-secondary transition-colors ${
                        message.feedback === 'dislike' ? 'text-destructive' : 'text-muted-foreground hover:text-foreground'
                      }`}
                      title="Unhelpful response"
                    >
                      <ThumbsDown className="w-3.5 h-3.5" />
                    </button>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Lightbox Modal */}
      {lightboxImage && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={lightboxImage.alt || 'Artwork preview'}
          className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/90 backdrop-blur-md p-4 animate-in fade-in duration-200"
          onClick={() => setLightboxImage(null)}
        >
          {/* Top Control Bar */}
          <div
            className="w-full max-w-5xl flex items-center justify-between py-2.5 px-4 mb-2 bg-card/90 backdrop-blur-md border border-border/60 rounded-xl text-xs text-foreground z-10 shadow-xl"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center gap-2 truncate max-w-md">
              <Sparkles className="w-4 h-4 text-primary shrink-0" />
              <span className="truncate font-semibold">{lightboxImage.alt || 'Generated Artwork'}</span>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => setZoom(prev => Math.max(0.5, prev - 0.25))}
                className="p-1.5 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
                title="Zoom Out"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="text-[11px] font-mono px-1 text-muted-foreground">{Math.round(zoom * 100)}%</span>
              <button
                type="button"
                onClick={() => setZoom(prev => Math.min(3, prev + 0.25))}
                className="p-1.5 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
                title="Zoom In"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => setZoom(1)}
                className="px-2 py-1 text-[11px] rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground border border-border/60 transition-colors"
                title="Reset Zoom"
              >
                Reset
              </button>

              <div className="h-4 w-px bg-border/60 mx-1" />

              <button
                type="button"
                onClick={() => {
                  navigator.clipboard.writeText(lightboxImage.src);
                  setCopiedLink(true);
                  setTimeout(() => setCopiedLink(false), 2000);
                }}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-border/60 hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
                title="Copy Link"
              >
                {copiedLink ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span className="text-[11px] hidden sm:inline">{copiedLink ? 'Copied' : 'Link'}</span>
              </button>

              <button
                type="button"
                onClick={() =>
                  downloadImage(lightboxImage.src, `${(lightboxImage.alt || 'artwork').slice(0, 30)}.jpg`)
                }
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-colors shadow-xs"
                title="Download full resolution"
              >
                <Download className="w-3.5 h-3.5" />
                <span className="text-[11px] hidden sm:inline">Save</span>
              </button>

              <button
                type="button"
                onClick={() => setLightboxImage(null)}
                className="p-1.5 ml-2 rounded-lg hover:bg-destructive/20 hover:text-destructive text-muted-foreground transition-colors"
                title="Close Lightbox (Esc)"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Lightbox Image Stage */}
          <div
            className="flex-1 w-full max-w-5xl flex items-center justify-center overflow-auto p-2"
            onClick={e => e.stopPropagation()}
          >
            <img
              src={lightboxImage.src}
              alt={lightboxImage.alt}
              style={{ transform: `scale(${zoom})`, transition: 'transform 0.15s ease-out' }}
              className="max-h-[82vh] max-w-[90vw] object-contain rounded-xl shadow-2xl border border-border/40"
            />
          </div>
        </div>
      )}
    </div>
  );
};
