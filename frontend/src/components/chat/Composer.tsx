import React, { useState, useRef, useEffect } from 'react';
import { ModelInfo, CollectionSummary, PersonaId } from '../../types';
import { PERSONAS } from '../../store/useAppStore';
import { ModelSelector } from './ModelSelector';
import {
  Send,
  Square,
  Globe,
  Search,
  BookOpen,
  Mic,
  MicOff,
  Paperclip,
  X,
  Code2,
  BarChart2,
  Sparkles,
  Palette,
} from 'lucide-react';

interface ComposerProps {
  onSendMessage: (
    text: string,
    options: {
      webSearch?: boolean;
      deepResearch?: boolean;
      collectionName?: string;
      attachments?: any[];
      systemPrompt?: string;
    }
  ) => void;
  onStop: () => void;
  isGenerating: boolean;
  models: ModelInfo[];
  selectedModelId: string;
  onSelectModel: (id: string) => void;
  collections: CollectionSummary[];
  selectedCollection: string | null;
  onSelectCollection: (name: string | null) => void;
  onFileUpload: (file: File) => Promise<any>;
  onUploadError?: (message: string) => void;
  selectedPersona: PersonaId;
  onSelectPersona: (persona: PersonaId) => void;
  draftText?: string;
  onClearDraft?: () => void;
}

export const Composer: React.FC<ComposerProps> = ({
  onSendMessage,
  onStop,
  isGenerating,
  models,
  selectedModelId,
  onSelectModel,
  collections,
  selectedCollection,
  onSelectCollection,
  onFileUpload,
  onUploadError,
  selectedPersona,
  onSelectPersona,
  draftText,
  onClearDraft,
}) => {
  const [input, setInput] = useState('');
  const [webSearch, setWebSearch] = useState(false);
  const [deepResearch, setDeepResearch] = useState(false);
  const [attachments, setAttachments] = useState<any[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isDraggingOver, setIsDraggingOver] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);
  const voiceBaseRef = useRef('');
  const voiceFinalRef = useRef('');
  const previewUrlsRef = useRef<string[]>([]);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Handle suggestion cards / external draft population
  useEffect(() => {
    if (draftText) {
      setInput(draftText);
      onClearDraft?.();
      setTimeout(() => {
        textareaRef.current?.focus();
        if (textareaRef.current) {
          textareaRef.current.style.height = 'auto';
          textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 220)}px`;
        }
      }, 50);
    }
  }, [draftText, onClearDraft]);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 220)}px`;
    }
  }, [input]);

  // Web Speech recognition setup
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onresult = (event: any) => {
        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            voiceFinalRef.current += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        setInput(`${voiceBaseRef.current}${voiceFinalRef.current || interimTranscript ? ' ' : ''}${voiceFinalRef.current}${interimTranscript}`.trimStart());
      };

      recognition.onerror = () => setIsRecording(false);
      recognition.onend = () => setIsRecording(false);

      recognitionRef.current = recognition;
    }
  }, []);

  const toggleRecording = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in this browser.');
      return;
    }

    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    } else {
      voiceBaseRef.current = input.trimEnd();
      voiceFinalRef.current = '';
      recognitionRef.current.start();
      setIsRecording(true);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || isGenerating) return;

    onSendMessage(trimmed, {
      webSearch,
      deepResearch,
      collectionName: selectedCollection || undefined,
      attachments: attachments.length ? attachments : undefined,
      systemPrompt: PERSONAS[selectedPersona].systemPrompt,
    });

    setInput('');
    setAttachments([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const processFiles = async (files: FileList | File[]) => {
    if (!files || !files.length) return;

    setIsUploading(true);
    try {
      const fileArray = Array.from(files);
      for (let i = 0; i < fileArray.length; i++) {
        const file = fileArray[i];
        const isImg = file.type.startsWith('image/') || /\.(png|jpe?g|webp|gif|bmp)$/i.test(file.name);
        const previewUrl = isImg ? URL.createObjectURL(file) : undefined;
        if (previewUrl) previewUrlsRef.current.push(previewUrl);

        let base64Data: string | undefined = undefined;
        if (isImg) {
          try {
            base64Data = await new Promise<string>((resolve) => {
              const reader = new FileReader();
              reader.onloadend = () => resolve(reader.result as string);
              reader.onerror = () => resolve('');
              reader.readAsDataURL(file);
            });
          } catch {}
        }

        const doc = await onFileUpload(file);
        setAttachments(prev => [
          ...prev,
          {
            filename: file.name,
            file_type: file.type || (isImg ? 'image/jpeg' : 'document'),
            file_size: file.size,
            doc_id: doc?.id,
            preview_url: previewUrl,
            base64: base64Data,
            file_path: doc?.file_path,
          },
        ]);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'The file could not be uploaded.';
      onUploadError?.(`Upload failed: ${message}`);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      await processFiles(e.target.files);
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    const pastedFiles: File[] = [];
    for (let i = 0; i < items.length; i++) {
      if (items[i].kind === 'file') {
        const file = items[i].getAsFile();
        if (file) pastedFiles.push(file);
      }
    }

    if (pastedFiles.length > 0) {
      e.preventDefault();
      processFiles(pastedFiles);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => {
      const target = prev[index];
      if (target?.preview_url) {
        URL.revokeObjectURL(target.preview_url);
        previewUrlsRef.current = previewUrlsRef.current.filter(url => url !== target.preview_url);
      }
      return prev.filter((_, i) => i !== index);
    });
  };

  useEffect(() => () => {
    previewUrlsRef.current.forEach(url => URL.revokeObjectURL(url));
  }, []);

  const personaList: { id: PersonaId; label: string; icon: any }[] = [
    { id: 'general', label: 'General', icon: Sparkles },
    { id: 'coder', label: 'Architect', icon: Code2 },
    { id: 'researcher', label: 'Researcher', icon: Search },
    { id: 'analyst', label: 'Analyst', icon: BarChart2 },
    { id: 'writer', label: 'Writer', icon: BookOpen },
  ];

  return (
    <div className="composer-wrap w-full max-w-3xl mx-auto">
      {/* Workspace Persona Switcher Bar */}
      <div className="persona-switcher flex items-center gap-1.5 mb-2 overflow-x-auto scrollbar-none py-0.5">
        <span className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground mr-1 shrink-0">
          Role:
        </span>
        {personaList.map(p => {
          const Icon = p.icon;
          const isSelected = selectedPersona === p.id;
          return (
            <button
              key={p.id}
              type="button"
              onClick={() => onSelectPersona(p.id)}
              className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium transition-all shrink-0 border ${
                isSelected
                  ? 'border-primary/50 bg-primary/10 text-primary font-semibold shadow-xs'
                  : 'border-border/60 hover:bg-secondary text-muted-foreground hover:text-foreground'
              }`}
              title={PERSONAS[p.id].description}
            >
              <Icon className="w-3 h-3" />
              <span>{p.label}</span>
            </button>
          );
        })}
      </div>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`composer-box relative rounded-2xl border bg-card shadow-lg transition-all focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/10 ${
          isDraggingOver
            ? 'border-primary ring-2 ring-primary/20 bg-primary/5'
            : 'border-border/80'
        }`}
      >
        {/* Drag-and-drop overlay cue */}
        {isDraggingOver && (
          <div className="absolute inset-0 z-20 flex items-center justify-center rounded-2xl bg-background/80 backdrop-blur-xs border-2 border-dashed border-primary text-primary font-medium text-xs pointer-events-none">
            Drop documents or images to attach
          </div>
        )}

        {/* Attachments preview tray */}
        {attachments.length > 0 && (
          <div className="composer-attachments flex flex-wrap gap-2 p-2.5 border-b border-border/50 bg-secondary/30">
            {attachments.map((att, i) => (
              <div
                key={i}
                className="attachment-chip flex items-center gap-2 px-2 py-1.5 rounded-xl bg-secondary text-xs text-foreground border border-border"
              >
                {att.preview_url ? (
                  <img
                    src={att.preview_url}
                    alt={att.filename}
                    className="attachment-thumb w-8 h-8 rounded-lg object-cover border border-border/60"
                  />
                ) : (
                  <Paperclip className="w-4 h-4 text-primary" />
                )}
                <span className="truncate max-w-[130px] font-medium">{att.filename}</span>
                <span className="hidden sm:inline text-[10px] text-muted-foreground">{formatFileSize(att.file_size)}</span>
                <button
                  type="button"
                  onClick={() => removeAttachment(i)}
                  aria-label={`Remove ${att.filename}`}
                  className="p-1 rounded-md hover:bg-destructive/10 hover:text-destructive transition-colors ml-1"
                  title="Remove attachment"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Textarea input */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          placeholder={`Message AetherAI as ${PERSONAS[selectedPersona].name}…`}
          aria-label="Message AetherAI"
          aria-describedby="composer-keyboard-hint"
          rows={1}
          disabled={isGenerating}
          className="composer-textarea w-full resize-none bg-transparent px-4 py-3.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none scrollbar-none leading-relaxed"
        />

        {/* Action Controls Toolbar */}
        <div className="composer-toolbar flex items-center justify-between px-3 pb-2.5 pt-1 border-t border-border/40 gap-2 flex-wrap">
          <div className="composer-toolbar-main flex items-center gap-1.5 flex-wrap">
            {/* Model Selector (Opens Upwards!) */}
            <ModelSelector
              models={models}
              selectedModelId={selectedModelId}
              onSelectModel={onSelectModel}
              direction="up"
            />

            {/* Hidden File Input */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              multiple
              accept=".pdf,.docx,.txt,.md,.csv,.xlsx,.png,.jpg,.jpeg,.webp"
              className="hidden"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading || isGenerating}
              aria-label={isUploading ? 'Uploading attachments' : 'Attach files'}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-border/60 hover:bg-secondary text-muted-foreground hover:text-foreground text-xs transition-colors"
              title="Attach documents, spreadsheets, or images"
            >
              <Paperclip className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{isUploading ? 'Uploading…' : 'Attach'}</span>
            </button>

            {/* Web Search Toggle */}
            <button
              type="button"
              onClick={() => setWebSearch(!webSearch)}
              aria-pressed={webSearch}
              className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg border text-xs transition-all ${
                webSearch
                  ? 'border-blue-500/50 bg-blue-500/10 text-blue-400 font-medium'
                  : 'border-border/60 hover:bg-secondary text-muted-foreground hover:text-foreground'
              }`}
              title="Ground response with live web search"
            >
              <Globe className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Search</span>
            </button>

            {/* Deep Research Mode Toggle */}
            <button
              type="button"
              onClick={() => setDeepResearch(!deepResearch)}
              aria-pressed={deepResearch}
              className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg border text-xs transition-all ${
                deepResearch
                  ? 'border-purple-500/50 bg-purple-500/10 text-purple-400 font-medium'
                  : 'border-border/60 hover:bg-secondary text-muted-foreground hover:text-foreground'
              }`}
              title="Execute multi-step structured research report"
            >
              <Search className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Research</span>
            </button>

            {/* AI Image Generation Button */}
            <button
              type="button"
              onClick={() => {
                if (!input.trim()) {
                  setInput('Generate a photorealistic image of ');
                } else if (!input.toLowerCase().includes('generate') && !input.toLowerCase().includes('draw') && !input.toLowerCase().includes('paint')) {
                  setInput(prev => `Generate an image of ${prev}`);
                }
                textareaRef.current?.focus();
              }}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-border/60 hover:bg-secondary text-muted-foreground hover:text-foreground text-xs transition-colors hover:border-pink-500/40 hover:text-pink-400"
              title="Generate AI artwork from prompt using FLUX.1 engine"
            >
              <Palette className="w-3.5 h-3.5 text-pink-400" />
              <span className="hidden sm:inline">Draw</span>
            </button>

            {/* Collection Context Filter if any available */}
            {collections.length > 0 && (
              <select
                value={selectedCollection || ''}
                onChange={e => onSelectCollection(e.target.value || null)}
                aria-label="Knowledge collection"
                className="px-2 py-1.5 rounded-lg border border-border/60 bg-card text-muted-foreground hover:text-foreground text-xs focus:outline-none"
                title="Select Knowledge Collection for RAG context"
              >
                <option value="">No Collection</option>
                {collections.map(c => (
                  <option key={c.name} value={c.name}>
                    📚 {c.name} ({c.document_count})
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="flex items-center gap-1.5 ml-auto">
            {/* Voice Input */}
            <button
              type="button"
              onClick={toggleRecording}
              aria-label={isRecording ? 'Stop voice input' : 'Start voice input'}
              aria-pressed={isRecording}
              className={`p-2 rounded-lg border transition-all ${
                isRecording
                  ? 'border-rose-500 bg-rose-500/10 text-rose-400 animate-pulse'
                  : 'border-border/60 hover:bg-secondary text-muted-foreground hover:text-foreground'
              }`}
              title={isRecording ? 'Stop recording voice' : 'Speech to text'}
            >
              {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>

            {/* Send or Stop Button */}
            {isGenerating ? (
              <button
                type="button"
                onClick={onStop}
                aria-label="Stop response generation"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-destructive text-destructive-foreground hover:bg-destructive/90 text-xs font-semibold shadow-sm transition-all"
                title="Stop generation"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
                <span>Stop</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSubmit}
                disabled={!input.trim()}
                aria-label="Send message"
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-40 disabled:hover:bg-primary text-xs font-semibold shadow-md transition-all"
              >
                <span>Send</span>
                <Send className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>
      <span className="sr-only" role="status" aria-live="polite">{isUploading ? 'Uploading attachments' : ''}</span>
      <div id="composer-keyboard-hint" className="composer-hint hidden sm:block mt-2 px-1 text-right text-[10px]">
        Enter to send <span className="mx-1 opacity-50">·</span> Shift + Enter for a new line
      </div>
    </div>
  );
};
