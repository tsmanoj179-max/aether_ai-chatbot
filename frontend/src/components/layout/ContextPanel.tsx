import React, { useState, useEffect } from 'react';
import {
  DocumentItem,
  CollectionSummary,
  MemoryItem,
  ToolItem,
  Artifact,
  GeneratedImage,
  ImageAnalysisResult,
} from '../../types';
import { api, API_BASE } from '../../api/client';
import {
  X,
  BookOpen,
  Search,
  Brain,
  Wrench,
  Upload,
  Trash2,
  Plus,
  Play,
  FileText,
  Clock,
  Eye,
  Code2,
  Copy,
  Check,
  Download,
  Palette,
  Sparkles,
  RefreshCw,
  Layers,
  Maximize2,
} from 'lucide-react';

interface ContextPanelProps {
  activeTab: 'none' | 'canvas' | 'documents' | 'research' | 'memories' | 'tools' | 'gallery';
  onClose: () => void;
  documents: DocumentItem[];
  collections: CollectionSummary[];
  onUploadDocument: (file: File, collection?: string) => Promise<any>;
  onDeleteDocument: (id: string) => void;
  memories: MemoryItem[];
  onCreateMemory: (content: string, category?: string) => void;
  onDeleteMemory: (id: string) => void;
  onToggleMemory: (id: string, active: boolean) => void;
  onClearMemories: () => void;
  tools: ToolItem[];
  activeArtifact: Artifact | null;
  onUpdateArtifact: (artifact: Artifact) => void;
  onAddToast: (text: string, type: 'info' | 'success' | 'warning' | 'error') => void;
}

export const ContextPanel: React.FC<ContextPanelProps> = ({
  activeTab,
  onClose,
  documents,
  collections,
  onUploadDocument,
  onDeleteDocument,
  memories,
  onCreateMemory,
  onDeleteMemory,
  onToggleMemory,
  onClearMemories,
  tools,
  activeArtifact,
  onUpdateArtifact,
  onAddToast,
}) => {
  // Canvas Studio states
  const [canvasViewMode, setCanvasViewMode] = useState<'editor' | 'preview'>('editor');
  const [copiedCanvas, setCopiedCanvas] = useState(false);

  useEffect(() => {
    if (activeTab === 'none') return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeTab, onClose]);

  // Document RAG tab states
  const [selectedCollection, setSelectedCollection] = useState<string>('all');
  const [searchChunkQuery, setSearchChunkQuery] = useState('');
  const [chunkSearchResults, setChunkSearchResults] = useState<any[]>([]);
  const [isSearchingChunks, setIsSearchingChunks] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  // Memory tab states
  const [newMemoryContent, setNewMemoryContent] = useState('');
  const [newMemoryCategory, setNewMemoryCategory] = useState('preference');

  // Deep research standalone state
  const [researchQuery, setResearchQuery] = useState('');
  const [researchReport, setResearchReport] = useState('');
  const [researchStatus, setResearchStatus] = useState<string | null>(null);
  const [isResearching, setIsResearching] = useState(false);

  // Tools tab state
  const [selectedTool, setSelectedTool] = useState<string>('calculator');
  const [toolArgs, setToolArgs] = useState<string>('{"expression": "(15 * 4) + 120 / 3"}');
  const [toolResult, setToolResult] = useState<any>(null);
  const [isExecutingTool, setIsExecutingTool] = useState(false);

  // Gallery & Vision tab states
  const [gallerySubTab, setGallerySubTab] = useState<'create' | 'gallery' | 'vision'>('create');
  const [galleryImages, setGalleryImages] = useState<GeneratedImage[]>([]);
  const [isLoadingGallery, setIsLoadingGallery] = useState(false);
  const [genPrompt, setGenPrompt] = useState('');
  const [genStyle, setGenStyle] = useState('photorealistic');
  const [genAspect, setGenAspect] = useState('1:1');
  const [isGeneratingArtwork, setIsGeneratingArtwork] = useState(false);

  // Vision inspection state
  const [visionFile, setVisionFile] = useState<File | null>(null);
  const [visionPreviewUrl, setVisionPreviewUrl] = useState<string | null>(null);
  const [visionQuestion, setVisionQuestion] = useState('');
  const [visionResult, setVisionResult] = useState<ImageAnalysisResult | null>(null);
  const [isAnalyzingVision, setIsAnalyzingVision] = useState(false);

  const fetchGallery = async () => {
    setIsLoadingGallery(true);
    try {
      const res = await api.getImageGallery(30);
      setGalleryImages(res.images || []);
    } catch {
      // ignore
    } finally {
      setIsLoadingGallery(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    if (activeTab === 'gallery') {
      setIsLoadingGallery(true);
      api.getImageGallery(30)
        .then(res => {
          if (!ignore) setGalleryImages(res.images || []);
        })
        .catch(() => {})
        .finally(() => {
          if (!ignore) setIsLoadingGallery(false);
        });
    }
    return () => {
      ignore = true;
    };
  }, [activeTab]);

  const handleGenerateArtwork = async () => {
    if (!genPrompt.trim()) return;
    setIsGeneratingArtwork(true);
    try {
      const res = await api.generateImage({
        prompt: genPrompt.trim(),
        style: genStyle,
        aspect_ratio: genAspect,
      });
      onAddToast('Artwork rendered successfully!', 'success');
      setGalleryImages(prev => [res, ...prev]);
      setGenPrompt('');
      setGallerySubTab('gallery');
    } catch (err: any) {
      onAddToast(`Generation failed: ${err.message}`, 'error');
    } finally {
      setIsGeneratingArtwork(false);
    }
  };

  const handleAnalyzeVision = async () => {
    if (!visionFile) return;
    setIsAnalyzingVision(true);
    try {
      const res = await api.analyzeImage(visionFile, visionQuestion.trim() || undefined);
      setVisionResult(res);
      onAddToast('Visual analysis completed!', 'success');
    } catch (err: any) {
      onAddToast(`Analysis failed: ${err.message}`, 'error');
    } finally {
      setIsAnalyzingVision(false);
    }
  };

  // Handlers
  const handleCopyCanvas = async () => {
    if (!activeArtifact?.content) return;
    try {
      await navigator.clipboard.writeText(activeArtifact.content);
      setCopiedCanvas(true);
      setTimeout(() => setCopiedCanvas(false), 2000);
      onAddToast('Copied to clipboard', 'success');
    } catch {}
  };

  const handleDownloadCanvas = () => {
    if (!activeArtifact) return;
    const blob = new Blob([activeArtifact.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = activeArtifact.title || `artifact.${activeArtifact.language || 'txt'}`;
    a.click();
    URL.revokeObjectURL(url);
    onAddToast('Artifact downloaded', 'info');
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || !files.length) return;
    setIsUploading(true);
    try {
      await onUploadDocument(files[0], selectedCollection === 'all' ? 'default' : selectedCollection);
      onAddToast('Document uploaded and indexed successfully!', 'success');
    } catch (err: any) {
      onAddToast(`Upload failed: ${err.message}`, 'error');
    } finally {
      setIsUploading(false);
    }
  };

  const handleSearchChunks = async () => {
    if (!searchChunkQuery.trim()) return;
    setIsSearchingChunks(true);
    try {
      const data = await api.searchDocumentChunks(
        searchChunkQuery,
        selectedCollection === 'all' ? undefined : selectedCollection,
        3
      );
      setChunkSearchResults(data);
    } catch (e: any) {
      onAddToast(`Search error: ${e.message}`, 'error');
    } finally {
      setIsSearchingChunks(false);
    }
  };

  const handleAddMemory = () => {
    if (!newMemoryContent.trim()) return;
    onCreateMemory(newMemoryContent.trim(), newMemoryCategory);
    setNewMemoryContent('');
    onAddToast('Preference saved to assistant memory', 'success');
  };

  const handleRunStandaloneResearch = async () => {
    if (!researchQuery.trim() || isResearching) return;
    setIsResearching(true);
    setResearchReport('');
    setResearchStatus('Initializing research pipeline...');

    try {
      const res = await fetch(`${API_BASE}/research/deep`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: researchQuery, max_searches: 3 }),
      });

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let accumulated = '';

      while (true) {
        const { done, value } = await reader!.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const ev = JSON.parse(line.slice(6));
            if (ev.type === 'status') {
              setResearchStatus(ev.data.status);
            } else if (ev.type === 'token') {
              accumulated += ev.data.token;
              setResearchReport(accumulated);
            }
          } catch {}
        }
      }
      setResearchStatus(null);
    } catch (e: any) {
      onAddToast(`Research failed: ${e.message}`, 'error');
    } finally {
      setIsResearching(false);
      setResearchStatus(null);
    }
  };

  const handleExecuteTool = async () => {
    setIsExecutingTool(true);
    try {
      const parsedArgs = JSON.parse(toolArgs);
      const res = await api.executeTool(selectedTool, parsedArgs);
      setToolResult(res);
      onAddToast('Tool executed successfully', 'success');
    } catch (e: any) {
      setToolResult({ error: e.message });
      onAddToast(`Tool error: ${e.message}`, 'error');
    } finally {
      setIsExecutingTool(false);
    }
  };

  const filteredDocs =
    selectedCollection === 'all'
      ? documents
      : documents.filter(d => d.collection_name === selectedCollection);

  if (activeTab === 'none') return null;

  return (
    <aside aria-label="Contextual workspace panel" className="context-panel w-84 sm:w-96 md:w-[420px] lg:w-[480px] border-l border-border/80 bg-card flex flex-col shrink-0 h-full overflow-hidden shadow-2xl z-30 transition-all">
      {/* Panel Header */}
      <div className="h-14 border-b border-border/70 px-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          {activeTab === 'canvas' && <Code2 className="w-4 h-4 text-primary" />}
          {activeTab === 'documents' && <BookOpen className="w-4 h-4 text-primary" />}
          {activeTab === 'research' && <Search className="w-4 h-4 text-primary" />}
          {activeTab === 'memories' && <Brain className="w-4 h-4 text-primary" />}
          {activeTab === 'tools' && <Wrench className="w-4 h-4 text-primary" />}
          {activeTab === 'gallery' && <Palette className="w-4 h-4 text-primary" />}
          <span className="font-semibold text-xs capitalize text-foreground">
            {activeTab === 'canvas' && 'Canvas Studio (Artifacts)'}
            {activeTab === 'documents' && 'Knowledge Library (RAG)'}
            {activeTab === 'research' && 'Deep Research Studio'}
            {activeTab === 'memories' && 'Long-Term Memory'}
            {activeTab === 'tools' && 'Tool Execution Lab'}
            {activeTab === 'gallery' && 'Visual Art & Vision Studio'}
          </span>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close contextual panel"
          className="p-1 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Panel Content Body */}
      <div className="flex-1 overflow-y-auto p-4 scrollbar-thin text-xs">
        {/* TAB 0: CANVAS STUDIO (ARTIFACTS) */}
        {activeTab === 'canvas' && (
          <div className="flex flex-col h-full gap-3">
            {activeArtifact ? (
              <>
                {/* Canvas Control Bar */}
                <div className="flex items-center justify-between pb-2 border-b border-border/60">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="font-semibold text-foreground truncate text-xs">
                      {activeArtifact.title || 'Untitled Artifact'}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded font-mono uppercase bg-secondary text-primary font-bold">
                      {activeArtifact.language}
                    </span>
                  </div>

                  <div className="flex items-center gap-1 shrink-0">
                    {/* Mode Toggle */}
                    <div className="flex items-center p-0.5 rounded-lg bg-secondary border border-border/70 mr-1">
                      <button
                        type="button"
                        onClick={() => setCanvasViewMode('editor')}
                        className={`px-2 py-0.5 rounded-md text-[10px] font-semibold transition-all ${
                          canvasViewMode === 'editor'
                            ? 'bg-card text-foreground shadow-xs'
                            : 'text-muted-foreground hover:text-foreground'
                        }`}
                      >
                        Code
                      </button>
                      <button
                        type="button"
                        onClick={() => setCanvasViewMode('preview')}
                        className={`px-2 py-0.5 rounded-md text-[10px] font-semibold transition-all ${
                          canvasViewMode === 'preview'
                            ? 'bg-card text-foreground shadow-xs'
                            : 'text-muted-foreground hover:text-foreground'
                        }`}
                      >
                        Preview
                      </button>
                    </div>

                    <button
                      type="button"
                      onClick={handleCopyCanvas}
                      className="p-1 rounded hover:bg-secondary text-muted-foreground hover:text-foreground"
                      title="Copy code"
                    >
                      {copiedCanvas ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                    <button
                      type="button"
                      onClick={handleDownloadCanvas}
                      className="p-1 rounded hover:bg-secondary text-muted-foreground hover:text-foreground"
                      title="Download artifact"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Editor / Live Preview Container */}
                {canvasViewMode === 'editor' ? (
                  <div className="flex-1 flex flex-col min-h-[350px]">
                    <textarea
                      value={activeArtifact.content}
                      onChange={e => onUpdateArtifact({ ...activeArtifact, content: e.target.value })}
                      className="flex-1 w-full p-3 rounded-xl border border-neutral-800 bg-neutral-950 font-mono text-xs text-neutral-100 leading-relaxed focus:outline-none resize-none scrollbar-thin"
                    />
                  </div>
                ) : (
                  <div className="flex-1 rounded-xl border border-border bg-white overflow-hidden min-h-[350px]">
                    {activeArtifact.language === 'html' || activeArtifact.language === 'svg' ? (
                      <iframe
                        srcDoc={activeArtifact.content}
                        title="Artifact Preview"
                        sandbox="allow-scripts"
                        className="w-full h-full min-h-[350px] border-none"
                      />
                    ) : (
                      <div className="p-4 text-neutral-900 bg-white font-sans text-xs whitespace-pre-wrap leading-relaxed h-full overflow-y-auto">
                        {activeArtifact.content}
                      </div>
                    )}
                  </div>
                )}
              </>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-muted-foreground">
                <Code2 className="w-8 h-8 text-muted-foreground/50 mb-2" />
                <span className="font-semibold text-foreground text-xs">Canvas Studio is Empty</span>
                <p className="text-[11px] text-muted-foreground mt-1 max-w-xs">
                  Click the <strong>"Canvas"</strong> button on any code block in the chat to inspect, edit, and preview it live side-by-side.
                </p>
              </div>
            )}
          </div>
        )}

        {/* TAB 1: KNOWLEDGE LIBRARY */}
        {activeTab === 'documents' && (
          <div className="flex flex-col gap-4">
            {/* Upload Area */}
            <div className="border border-dashed border-border rounded-xl p-4 text-center bg-secondary/30 hover:bg-secondary/50 transition-colors">
              <Upload className="w-6 h-6 text-primary mx-auto mb-2" />
              <div className="font-semibold text-foreground mb-1">Upload Documents</div>
              <p className="text-[11px] text-muted-foreground mb-3">
                PDF, DOCX, TXT, MD, CSV, XLSX (Max 25MB)
              </p>
              <label className="inline-block px-3 py-1.5 rounded-lg bg-primary text-primary-foreground font-semibold cursor-pointer hover:bg-primary/90 text-[11px] transition-all">
                {isUploading ? 'Indexing...' : 'Choose File'}
                <input
                  type="file"
                  onChange={handleFileUpload}
                  disabled={isUploading}
                  className="hidden"
                />
              </label>
            </div>

            {/* Collection filter */}
            <div className="flex items-center justify-between">
              <span className="font-semibold text-[11px] uppercase tracking-wider text-muted-foreground">
                Documents ({filteredDocs.length})
              </span>
              <select
                value={selectedCollection}
                onChange={e => setSelectedCollection(e.target.value)}
                className="px-2 py-1 rounded border border-border bg-card text-[11px]"
              >
                <option value="all">All Collections</option>
                {collections.map(c => (
                  <option key={c.name} value={c.name}>
                    {c.name} ({c.document_count})
                  </option>
                ))}
              </select>
            </div>

            {/* Document list */}
            <div className="flex flex-col gap-2">
              {filteredDocs.length === 0 ? (
                <div className="text-center py-6 text-muted-foreground">
                  No documents in this collection.
                </div>
              ) : (
                filteredDocs.map(doc => (
                  <div
                    key={doc.id}
                    className="p-2.5 rounded-lg border border-border/70 bg-card hover:bg-secondary/40 flex items-center justify-between gap-2"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <FileText className="w-4 h-4 text-primary shrink-0" />
                      <div className="flex flex-col min-w-0">
                        <span className="font-medium text-foreground truncate">{doc.filename}</span>
                        <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                          <span>{doc.chunk_count} chunks</span>
                          <span>•</span>
                          <span className="uppercase">{doc.file_type.replace('.', '')}</span>
                          <span>•</span>
                          <span>{doc.status}</span>
                        </div>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        if (window.confirm(`Delete "${doc.filename}"? This action cannot be undone.`)) {
                          onDeleteDocument(doc.id);
                        }
                      }}
                      aria-label={`Delete ${doc.filename}`}
                      className="p-1 hover:text-destructive text-muted-foreground transition-colors"
                      title="Delete document"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>

            {/* Semantic Chunk Tester */}
            <div className="mt-2 pt-3 border-t border-border">
              <div className="font-semibold text-[11px] uppercase tracking-wider text-muted-foreground mb-2">
                Test Vector Retrieval
              </div>
              <div className="flex gap-1.5 mb-2">
                <input
                  type="text"
                  value={searchChunkQuery}
                  onChange={e => setSearchChunkQuery(e.target.value)}
                  placeholder="Enter test search query..."
                  className="flex-1 px-2.5 py-1.5 rounded-lg border border-border bg-secondary/50 text-xs focus:outline-none"
                />
                <button
                  type="button"
                  onClick={handleSearchChunks}
                  disabled={isSearchingChunks}
                  className="px-2.5 py-1.5 rounded-lg bg-secondary hover:bg-secondary/80 font-medium"
                >
                  Search
                </button>
              </div>
              {chunkSearchResults.length > 0 && (
                <div className="flex flex-col gap-1.5">
                  {chunkSearchResults.map((r, i) => (
                    <div key={i} className="p-2 rounded bg-secondary/60 text-[11px] leading-relaxed">
                      <div className="font-semibold text-primary mb-0.5">
                        {r.filename} (Score: {r.similarity_score})
                      </div>
                      <p className="line-clamp-3 text-muted-foreground">"{r.content}"</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 2: DEEP RESEARCH STUDIO */}
        {activeTab === 'research' && (
          <div className="flex flex-col gap-4">
            <div className="p-3 rounded-lg border border-primary/20 bg-primary/5 text-primary text-[11px] leading-relaxed">
              <strong>Multi-Step Deep Research</strong>: Explores diverse angles, queries verified web sources, deduplicates findings, and synthesizes structured reports with source citations.
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="font-semibold text-foreground">Research Topic</label>
              <textarea
                value={researchQuery}
                onChange={e => setResearchQuery(e.target.value)}
                placeholder="e.g. Current trends in retrieval augmented generation architectures"
                rows={3}
                className="w-full p-2.5 rounded-lg border border-border bg-secondary/40 text-xs focus:outline-none"
              />
              <button
                type="button"
                onClick={handleRunStandaloneResearch}
                disabled={isResearching || !researchQuery.trim()}
                className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 disabled:opacity-50 mt-1"
              >
                <Search className="w-3.5 h-3.5" />
                <span>{isResearching ? 'Executing Research...' : 'Generate Research Report'}</span>
              </button>
            </div>

            {researchStatus && (
              <div className="flex items-center gap-2 p-2 rounded bg-secondary text-primary font-medium animate-pulse text-[11px]">
                <Clock className="w-3.5 h-3.5" />
                <span>{researchStatus}</span>
              </div>
            )}

            {researchReport && (
              <div className="p-3 rounded-xl border border-border bg-card whitespace-pre-wrap leading-relaxed text-foreground">
                {researchReport}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: LONG-TERM MEMORY */}
        {activeTab === 'memories' && (
          <div className="flex flex-col gap-4">
            <div className="p-3 rounded-lg border border-border bg-secondary/30 text-muted-foreground text-[11px] leading-relaxed">
              Curate explicit preferences and facts for AetherAI. Memories are applied transparently to conversations.
            </div>

            {/* Add memory form */}
            <div className="flex flex-col gap-2 p-3 rounded-lg border border-border/80 bg-card">
              <span className="font-semibold text-foreground">Add Custom Preference</span>
              <input
                type="text"
                value={newMemoryContent}
                onChange={e => setNewMemoryContent(e.target.value)}
                placeholder="e.g. Always write code examples in TypeScript"
                className="px-2.5 py-1.5 rounded-lg border border-border bg-secondary/50 focus:outline-none"
              />
              <div className="flex items-center justify-between gap-2">
                <select
                  value={newMemoryCategory}
                  onChange={e => setNewMemoryCategory(e.target.value)}
                  className="px-2 py-1 rounded border border-border bg-card text-[11px]"
                >
                  <option value="preference">Preference</option>
                  <option value="instruction">Instruction</option>
                  <option value="fact">Fact</option>
                </select>
                <button
                  type="button"
                  onClick={handleAddMemory}
                  className="flex items-center gap-1 px-3 py-1 rounded bg-primary text-primary-foreground font-semibold hover:bg-primary/90"
                >
                  <Plus className="w-3 h-3" /> Save
                </button>
              </div>
            </div>

            {/* Memory list */}
            <div className="flex items-center justify-between mt-2">
              <span className="font-semibold text-[11px] uppercase tracking-wider text-muted-foreground">
                Saved Memories ({memories.length})
              </span>
              {memories.length > 0 && (
                <button
                  type="button"
                  onClick={() => {
                    if (window.confirm('Clear all saved memories? This action cannot be undone.')) {
                      onClearMemories();
                    }
                  }}
                  className="text-destructive hover:underline text-[11px]"
                >
                  Clear All
                </button>
              )}
            </div>

            <div className="flex flex-col gap-2">
              {memories.length === 0 ? (
                <div className="text-center py-6 text-muted-foreground">
                  No memories saved yet.
                </div>
              ) : (
                memories.map(mem => (
                  <div
                    key={mem.id}
                    className="p-2.5 rounded-lg border border-border bg-card flex items-start justify-between gap-2"
                  >
                    <div className="flex flex-col gap-1 min-w-0 flex-1">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-[9px] uppercase px-1.5 py-0.2 rounded font-bold bg-secondary text-primary">
                          {mem.category}
                        </span>
                        <span className={`text-[9px] px-1.5 py-0.2 rounded font-medium ${mem.is_active ? 'bg-emerald-500/10 text-emerald-400' : 'bg-secondary text-muted-foreground'}`}>
                          {mem.is_active ? 'Active' : 'Paused'}
                        </span>
                        <span className="text-[10px] text-muted-foreground">
                          {new Date(mem.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-foreground leading-relaxed">{mem.content}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => onToggleMemory(mem.id, !mem.is_active)}
                      aria-pressed={mem.is_active}
                      aria-label={`${mem.is_active ? 'Pause' : 'Activate'} memory`}
                      className="shrink-0 px-2 py-1 rounded-md border border-border/70 text-[10px] text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
                    >
                      {mem.is_active ? 'Pause' : 'Activate'}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        if (window.confirm('Delete this saved memory? This action cannot be undone.')) {
                          onDeleteMemory(mem.id);
                        }
                      }}
                      aria-label="Delete saved memory"
                      className="p-1 hover:text-destructive text-muted-foreground transition-colors shrink-0"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* TAB 4: TOOLS LAB */}
        {activeTab === 'tools' && (
          <div className="flex flex-col gap-4">
            <div className="p-3 rounded-lg border border-border bg-secondary/30 text-muted-foreground text-[11px] leading-relaxed">
              Explore and test built-in tools with isolated AST execution and audit tracking.
            </div>

            <div className="flex flex-col gap-2">
              <label className="font-semibold text-foreground">Select Tool</label>
              <select
                value={selectedTool}
                onChange={e => {
                  setSelectedTool(e.target.value);
                  if (e.target.value === 'calculator') {
                    setToolArgs('{"expression": "(15 * 4) + 120 / 3"}');
                  } else if (e.target.value === 'datetime_util') {
                    setToolArgs('{"action": "current_time"}');
                  } else if (e.target.value === 'web_search') {
                    setToolArgs('{"query": "quantum computing breakthroughs"}');
                  } else if (e.target.value === 'csv_data_analyst') {
                    setToolArgs('{"file_path": "uploads/sample.csv"}');
                  }
                }}
                className="p-2 rounded-lg border border-border bg-card text-xs"
              >
                {tools.map(t => (
                  <option key={t.name} value={t.name}>
                    {t.name}
                  </option>
                ))}
              </select>

              <label className="font-semibold text-foreground mt-2">Arguments (JSON)</label>
              <textarea
                value={toolArgs}
                onChange={e => setToolArgs(e.target.value)}
                rows={4}
                className="w-full p-2.5 rounded-lg border border-border bg-secondary/50 font-mono text-xs focus:outline-none"
              />

              <button
                type="button"
                onClick={handleExecuteTool}
                disabled={isExecutingTool}
                className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 mt-1"
              >
                <Play className="w-3.5 h-3.5" />
                <span>{isExecutingTool ? 'Executing...' : 'Run Tool'}</span>
              </button>
            </div>

            {toolResult && (
              <div className="mt-2">
                <span className="font-semibold text-foreground">Execution Result</span>
                <pre className="p-3 rounded-lg border border-border bg-neutral-950 text-neutral-100 font-mono text-[11px] overflow-x-auto mt-1">
                  {JSON.stringify(toolResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* TAB 5: VISUAL ART & VISION STUDIO */}
        {activeTab === 'gallery' && (
          <div className="flex flex-col gap-3">
            {/* Sub-tab Navigation */}
            <div className="flex items-center gap-1 p-1 bg-secondary/50 rounded-xl border border-border/60">
              <button
                type="button"
                onClick={() => setGallerySubTab('create')}
                className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  gallerySubTab === 'create'
                    ? 'bg-card text-foreground shadow-xs'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5 text-primary" />
                <span>Create</span>
              </button>
              <button
                type="button"
                onClick={() => setGallerySubTab('gallery')}
                className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  gallerySubTab === 'gallery'
                    ? 'bg-card text-foreground shadow-xs'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Layers className="w-3.5 h-3.5 text-primary" />
                <span>Gallery ({galleryImages.length})</span>
              </button>
              <button
                type="button"
                onClick={() => setGallerySubTab('vision')}
                className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  gallerySubTab === 'vision'
                    ? 'bg-card text-foreground shadow-xs'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Eye className="w-3.5 h-3.5 text-primary" />
                <span>Inspector</span>
              </button>
            </div>

            {/* SUB-VIEW 1: CREATE ARTWORK */}
            {gallerySubTab === 'create' && (
              <div className="flex flex-col gap-3 p-3.5 rounded-xl border border-border bg-card/60">
                <div className="flex items-center justify-between">
                  <div className="font-semibold text-foreground flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-primary" />
                    <span>FLUX.1 Neural Studio</span>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                    Zero-Key Free
                  </span>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-medium text-muted-foreground">Prompt</label>
                  <textarea
                    value={genPrompt}
                    onChange={e => setGenPrompt(e.target.value)}
                    placeholder="Describe what you want to create (e.g. A neon cybernetic tiger walking through rain in Neo-Tokyo)..."
                    rows={3}
                    className="w-full p-2.5 rounded-lg border border-border bg-secondary/40 text-xs focus:outline-none focus:border-primary/50"
                  />
                </div>

                {/* Style Presets */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-medium text-muted-foreground">Artistic Style</label>
                  <div className="grid grid-cols-2 gap-1.5">
                    {[
                      { id: 'photorealistic', label: 'Photorealistic' },
                      { id: 'cyberpunk', label: 'Cyberpunk' },
                      { id: 'anime', label: 'Anime Studio' },
                      { id: '3d_render', label: '3D Render' },
                      { id: 'oil_painting', label: 'Oil Painting' },
                      { id: 'concept_art', label: 'Concept Art' },
                    ].map(st => (
                      <button
                        key={st.id}
                        type="button"
                        onClick={() => setGenStyle(st.id)}
                        className={`py-1.5 px-2 rounded-lg text-xs font-medium border text-left transition-all ${
                          genStyle === st.id
                            ? 'border-primary bg-primary/10 text-primary font-semibold'
                            : 'border-border/60 hover:bg-secondary text-muted-foreground hover:text-foreground'
                        }`}
                      >
                        {st.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Aspect Ratio */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-[11px] font-medium text-muted-foreground">Aspect Ratio</label>
                  <div className="flex items-center gap-2">
                    {[
                      { id: '1:1', label: '1:1 Square' },
                      { id: '16:9', label: '16:9 Landscape' },
                      { id: '9:16', label: '9:16 Portrait' },
                    ].map(ar => (
                      <button
                        key={ar.id}
                        type="button"
                        onClick={() => setGenAspect(ar.id)}
                        className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-medium border text-center transition-all ${
                          genAspect === ar.id
                            ? 'border-primary bg-primary/10 text-primary font-semibold'
                            : 'border-border/60 hover:bg-secondary text-muted-foreground hover:text-foreground'
                        }`}
                      >
                        {ar.label}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleGenerateArtwork}
                  disabled={isGeneratingArtwork || !genPrompt.trim()}
                  className="mt-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-primary text-primary-foreground font-semibold text-xs hover:bg-primary/90 disabled:opacity-40 transition-all shadow-md"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>{isGeneratingArtwork ? 'Rendering Neural Artwork...' : 'Generate Artwork'}</span>
                </button>
              </div>
            )}

            {/* SUB-VIEW 2: GALLERY GRID */}
            {gallerySubTab === 'gallery' && (
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-foreground">Generated Artwork</span>
                  <button
                    type="button"
                    onClick={fetchGallery}
                    className="p-1 rounded hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
                    title="Refresh gallery"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isLoadingGallery ? 'animate-spin' : ''}`} />
                  </button>
                </div>

                {galleryImages.length === 0 ? (
                  <div className="p-8 text-center border border-dashed border-border rounded-xl text-muted-foreground">
                    <Palette className="w-8 h-8 mx-auto mb-2 opacity-40 text-primary" />
                    <p className="font-medium text-xs">No images generated yet</p>
                    <p className="text-[11px] mt-1">Use the Create tab or chat prompt "draw an image of..." to begin!</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-2.5">
                    {galleryImages.map(img => (
                      <div
                        key={img.id}
                        className="group relative rounded-xl overflow-hidden border border-border bg-card shadow-xs transition-all hover:border-primary/50"
                      >
                        <img
                          src={img.url}
                          alt={img.prompt}
                          className="w-full aspect-square object-cover"
                          loading="lazy"
                        />
                        <div className="p-2 flex flex-col gap-1">
                          <p className="truncate font-medium text-[11px] text-foreground" title={img.prompt}>
                            {img.prompt}
                          </p>
                          <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                            <span className="capitalize">{img.style || 'photorealistic'}</span>
                            <span className="font-mono">{img.width}x{img.height}</span>
                          </div>
                        </div>

                        {/* Hover Overlay */}
                        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 p-2">
                          <a
                            href={img.url}
                            target="_blank"
                            rel="noreferrer"
                            className="p-1.5 rounded-lg bg-card/90 text-foreground hover:bg-card shadow-sm"
                            title="Open full image"
                          >
                            <Maximize2 className="w-4 h-4" />
                          </a>
                          <button
                            type="button"
                            onClick={async () => {
                              try {
                                const response = await fetch(img.url);
                                const blob = await response.blob();
                                const url = URL.createObjectURL(blob);
                                const a = document.createElement('a');
                                a.href = url;
                                a.download = `${img.id}.jpg`;
                                a.click();
                                URL.revokeObjectURL(url);
                              } catch {
                                window.open(img.url, '_blank');
                              }
                            }}
                            className="p-1.5 rounded-lg bg-card/90 text-foreground hover:bg-card shadow-sm"
                            title="Download"
                          >
                            <Download className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* SUB-VIEW 3: VISUAL INSPECTOR (MULTIMODAL VISION) */}
            {gallerySubTab === 'vision' && (
              <div className="flex flex-col gap-3">
                <div className="p-3.5 rounded-xl border border-border bg-card/60 flex flex-col gap-2.5">
                  <div className="font-semibold text-foreground flex items-center gap-1.5">
                    <Eye className="w-3.5 h-3.5 text-primary" />
                    <span>Multimodal Visual Inspector</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    Upload an image to extract technical properties (palette, aspect ratio, brightness) and execute deep visual scene decomposition.
                  </p>

                  <input
                    type="file"
                    accept="image/*"
                    onChange={e => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setVisionFile(file);
                        setVisionPreviewUrl(URL.createObjectURL(file));
                        setVisionResult(null);
                      }
                    }}
                    className="text-xs file:mr-2 file:py-1 file:px-2.5 file:rounded-md file:border-0 file:text-xs file:bg-primary file:text-primary-foreground hover:file:bg-primary/90 cursor-pointer"
                  />

                  {visionPreviewUrl && (
                    <div className="relative rounded-lg overflow-hidden border border-border/80 max-h-48 flex items-center justify-center bg-secondary/30 mt-1">
                      <img src={visionPreviewUrl} alt="Preview" className="max-h-48 object-contain" />
                    </div>
                  )}

                  <input
                    type="text"
                    value={visionQuestion}
                    onChange={e => setVisionQuestion(e.target.value)}
                    placeholder="Specific question (optional, e.g. What colors and objects are visible?)"
                    className="w-full p-2 rounded-lg border border-border bg-secondary/40 text-xs focus:outline-none"
                  />

                  <button
                    type="button"
                    onClick={handleAnalyzeVision}
                    disabled={isAnalyzingVision || !visionFile}
                    className="flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-primary text-primary-foreground font-semibold text-xs hover:bg-primary/90 disabled:opacity-40 transition-all shadow-xs"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>{isAnalyzingVision ? 'Analyzing Vision...' : 'Inspect Image'}</span>
                  </button>
                </div>

                {visionResult && (
                  <div className="flex flex-col gap-2.5 p-3.5 rounded-xl border border-primary/30 bg-primary/5">
                    <div className="font-semibold text-primary flex items-center justify-between">
                      <span>Inspection Telemetry</span>
                      <span className="text-[10px] font-mono uppercase bg-primary/20 px-1.5 py-0.5 rounded text-primary">
                        {visionResult.engine}
                      </span>
                    </div>

                    {/* Properties grid */}
                    <div className="grid grid-cols-2 gap-1.5 text-[11px]">
                      <div className="p-2 rounded bg-background/80 border border-border/60">
                        <span className="text-muted-foreground block text-[10px]">Dimensions</span>
                        <span className="font-semibold text-foreground">
                          {visionResult.properties?.width} × {visionResult.properties?.height} ({visionResult.properties?.aspect_ratio})
                        </span>
                      </div>
                      <div className="p-2 rounded bg-background/80 border border-border/60">
                        <span className="text-muted-foreground block text-[10px]">Megapixels</span>
                        <span className="font-semibold text-foreground">
                          {visionResult.properties?.megapixels} MP
                        </span>
                      </div>
                      <div className="p-2 rounded bg-background/80 border border-border/60">
                        <span className="text-muted-foreground block text-[10px]">Brightness</span>
                        <span className="font-semibold text-foreground">
                          {Math.round((visionResult.properties?.brightness ?? 0.5) * 100)}%
                        </span>
                      </div>
                      <div className="p-2 rounded bg-background/80 border border-border/60">
                        <span className="text-muted-foreground block text-[10px]">Color Mode</span>
                        <span className="font-semibold text-foreground">
                          {visionResult.properties?.color_mode} ({visionResult.properties?.format})
                        </span>
                      </div>
                    </div>

                    {/* Dominant Palette */}
                    {visionResult.properties?.dominant_colors && (
                      <div className="flex flex-col gap-1 p-2 rounded bg-background/80 border border-border/60">
                        <span className="text-muted-foreground text-[10px]">Extracted Color Palette</span>
                        <div className="flex items-center gap-1.5">
                          {visionResult.properties.dominant_colors.map((c, i) => (
                            <div key={i} className="flex items-center gap-1">
                              <span
                                className="w-3.5 h-3.5 rounded-full border border-border shadow-xs shrink-0"
                                style={{ backgroundColor: c }}
                              />
                              <span className="text-[10px] font-mono text-muted-foreground">{c}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Semantic Analysis */}
                    <div className="mt-1 p-3 rounded-lg bg-background/80 border border-border/60 text-[11px] leading-relaxed text-foreground whitespace-pre-wrap">
                      {visionResult.analysis}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </aside>
  );
};
