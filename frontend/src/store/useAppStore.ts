import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api/client';
import {
  Conversation,
  Message,
  ModelInfo,
  ProviderStatus,
  DocumentItem,
  CollectionSummary,
  MemoryItem,
  SystemHealth,
  ToolItem,
  Artifact,
  PersonaId,
  Persona
} from '../types';

export const PERSONAS: Record<PersonaId, Persona> = {
  general: {
    id: 'general',
    name: 'General Assistant',
    icon: 'Sparkles',
    description: 'Balanced, articulate multi-domain intelligence',
    systemPrompt: 'You are AetherAI, a sophisticated, helpful, and highly capable AI workspace assistant.'
  },
  coder: {
    id: 'coder',
    name: 'Senior Architect',
    icon: 'Code2',
    description: 'Clean design patterns, typed code, complete implementations',
    systemPrompt: 'You are AetherAI Senior Software Architect. Provide production-ready, highly robust, cleanly typed, fully functional implementations with error boundaries and architectural context. Avoid placeholders and generate modular, complete code.'
  },
  researcher: {
    id: 'researcher',
    name: 'Research Scientist',
    icon: 'Search',
    description: 'Evidence synthesis, multi-angle citations & gap analysis',
    systemPrompt: 'You are AetherAI Research Scientist. Provide rigorously structured, evidence-backed synthesis with citations, methodology analysis, trade-off comparisons, and identified uncertainty gaps.'
  },
  analyst: {
    id: 'analyst',
    name: 'Data Analyst',
    icon: 'BarChart2',
    description: 'Quantitative breakdowns, statistical comparisons, markdown tables',
    systemPrompt: 'You are AetherAI Senior Data Analyst. Structure answers with quantitative breakdowns, statistical rigor, clear markdown comparison tables, and actionable numerical insights.'
  },
  writer: {
    id: 'writer',
    name: 'Technical Writer',
    icon: 'BookOpen',
    description: 'Structured documentation, executive briefs, polished prose',
    systemPrompt: 'You are AetherAI Technical Communications Specialist. Write comprehensive, well-structured guides with clear headings, bulleted takeaways, and polished prose.'
  }
};

export interface ToastMessage {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  text: string;
}

export function useAppStore() {
  // Theme
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    return (localStorage.getItem('aetherai_theme') as 'dark' | 'light') || 'dark';
  });

  // Layout states
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(() => window.innerWidth >= 768);
  const [contextPanelTab, setContextPanelTab] = useState<'none' | 'canvas' | 'documents' | 'research' | 'memories' | 'tools' | 'gallery'>('none');
  const [settingsModalOpen, setSettingsModalOpen] = useState<boolean>(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState<boolean>(false);

  // Active Canvas Artifact
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(null);

  // Persona
  const [selectedPersona, setSelectedPersona] = useState<PersonaId>('general');

  // Data states
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>('aether-mock-omni');
  const [providers, setProviders] = useState<ProviderStatus[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);

  // Context & Addon states
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [collections, setCollections] = useState<CollectionSummary[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [tools, setTools] = useState<ToolItem[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);

  // Streaming states
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [streamingContent, setStreamingContent] = useState<string>('');
  const [generationStatus, setGenerationStatus] = useState<string | null>(null);
  const [currentCitations, setCurrentCitations] = useState<any[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Notifications
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = useCallback((text: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts(prev => [...prev, { id, type, text }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  // Theme synchronization
  useEffect(() => {
    localStorage.setItem('aetherai_theme', theme);
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  }, []);

  // Draft text for Composer (populated by suggestions, canvas, etc.)
  const [composerDraft, setComposerDraft] = useState<string>('');

  // Select Conversation
  const selectConversation = useCallback(async (id: string) => {
    setActiveConversationId(id);
    try {
      const details = await api.getConversation(id);
      setMessages(details.messages || []);
      if (details.model_id) setSelectedModelId(details.model_id);
    } catch (e: any) {
      addToast(`Failed to load conversation: ${e.message}`, 'error');
    }
  }, [addToast]);

  // Load initial backend configurations
  const loadInitialData = useCallback(async () => {
    try {
      const [health, modelList, provList, convs, docs, cols, mems, toolList] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getModels().catch(() => []),
        api.getProviders().catch(() => []),
        api.getConversations().catch(() => []),
        api.getDocuments().catch(() => []),
        api.getCollections().catch(() => []),
        api.getMemories().catch(() => []),
        api.getTools().catch(() => []),
      ]);

      if (health) setSystemHealth(health);
      if (modelList.length) setModels(modelList);
      if (provList.length) setProviders(provList);
      if (convs) setConversations(convs);
      if (docs) setDocuments(docs);
      if (cols) setCollections(cols);
      if (mems) setMemories(mems);
      if (toolList) setTools(toolList);

      // Select first conversation if none selected
      if (convs && convs.length > 0 && !activeConversationId) {
        selectConversation(convs[0].id);
      }
    } catch (e: any) {
      addToast(`Error connecting to backend: ${e.message}`, 'error');
    }
  }, [activeConversationId, selectConversation, addToast]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Create new conversation
  const newConversation = useCallback(async () => {
    try {
      const conv = await api.createConversation({
        title: 'New Conversation',
        model_id: selectedModelId,
      });
      setConversations(prev => [conv, ...prev]);
      setActiveConversationId(conv.id);
      setMessages([]);
      addToast('Started new conversation', 'info');
    } catch (e: any) {
      addToast(`Could not create conversation: ${e.message}`, 'error');
    }
  }, [selectedModelId, addToast]);

  // Delete conversation
  const deleteConversation = useCallback(async (id: string) => {
    try {
      await api.deleteConversation(id);
      setConversations(prev => prev.filter(c => c.id !== id));
      if (activeConversationId === id) {
        setActiveConversationId(null);
        setMessages([]);
      }
      addToast('Conversation removed', 'info');
    } catch (e: any) {
      addToast(`Failed to delete conversation: ${e.message}`, 'error');
    }
  }, [activeConversationId, addToast]);

  // Rename conversation
  const renameConversation = useCallback(async (id: string, newTitle: string) => {
    try {
      const updated = await api.updateConversation(id, { title: newTitle });
      setConversations(prev => prev.map(c => (c.id === id ? { ...c, title: updated.title } : c)));
      addToast('Conversation renamed', 'success');
    } catch (e: any) {
      addToast(`Failed to rename: ${e.message}`, 'error');
    }
  }, [addToast]);

  // Pin / Unpin conversation
  const togglePinConversation = useCallback(async (id: string, currentPinned: boolean) => {
    try {
      const updated = await api.updateConversation(id, { pinned: !currentPinned });
      setConversations(prev =>
        prev.map(c => (c.id === id ? { ...c, pinned: updated.pinned } : c)).sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0))
      );
    } catch (e: any) {
      addToast(`Failed to update pin: ${e.message}`, 'error');
    }
  }, [addToast]);

  // Send Message & Stream
  const sendMessage = useCallback(
    async (
      text: string,
      options: {
        webSearch?: boolean;
        deepResearch?: boolean;
        collectionName?: string;
        attachments?: any[];
        systemPrompt?: string;
      } = {}
    ) => {
      if (!text.trim() || isGenerating) return;

      const userMsgId = 'temp-user-' + Date.now();
      const asstMsgId = 'temp-asst-' + Date.now();

      // Optimistic user message insertion
      const optimisticUserMsg: Message = {
        id: userMsgId,
        conversation_id: activeConversationId || '',
        role: 'user',
        content: text,
        created_at: new Date().toISOString(),
        attachments: options.attachments,
      };

      setMessages(prev => [...prev, optimisticUserMsg]);
      setIsGenerating(true);
      setStreamingContent('');
      setGenerationStatus('Initiating request...');
      setCurrentCitations([]);

      const controller = new AbortController();
      abortControllerRef.current = controller;

      let accumulated = '';
      const citationsAcc: any[] = [];

      try {
        await api.streamChat(
          {
            conversation_id: activeConversationId || undefined,
            message: text,
            model_id: selectedModelId,
            system_prompt: options.systemPrompt || PERSONAS[selectedPersona].systemPrompt,
            web_search: options.webSearch,
            deep_research: options.deepResearch,
            collection_name: options.collectionName || selectedCollection || undefined,
            attachments: options.attachments,
          },
          {
            onInit: data => {
              if (!activeConversationId && data.conversation_id) {
                setActiveConversationId(data.conversation_id);
                setConversations(prev => [
                  {
                    id: data.conversation_id,
                    title: data.title || 'New Conversation',
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                    pinned: false,
                    model_id: selectedModelId,
                  },
                  ...prev,
                ]);
              }
            },
            onToken: token => {
              accumulated += token;
              setStreamingContent(accumulated);
            },
            onStatus: status => {
              setGenerationStatus(status.status);
            },
            onCitation: cite => {
              citationsAcc.push(cite);
              setCurrentCitations([...citationsAcc]);
            },
            onDone: data => {
              // Finalize message in state
              const completedMsg: Message = {
                id: asstMsgId,
                conversation_id: activeConversationId || '',
                role: 'assistant',
                content: accumulated,
                created_at: new Date().toISOString(),
                model_used: data.model_used || selectedModelId,
                provider_used: data.provider_used,
                finish_reason: data.finish_reason || 'stop',
                citations: citationsAcc.length ? citationsAcc : undefined,
              };
              setMessages(prev => [...prev, completedMsg]);
              setStreamingContent('');
              setGenerationStatus(null);
            },
            onError: err => {
              addToast(`Generation error: ${err}`, 'error');
              setGenerationStatus(null);
            },
          },
          controller.signal
        );
      } catch (err: any) {
        if (err.name === 'AbortError') {
          addToast('Generation cancelled.', 'info');
          if (accumulated) {
            setMessages(prev => [
              ...prev,
              {
                id: asstMsgId,
                conversation_id: activeConversationId || '',
                role: 'assistant',
                content: accumulated + ' *(Cancelled)*',
                created_at: new Date().toISOString(),
                model_used: selectedModelId,
                finish_reason: 'cancelled',
              },
            ]);
          }
        } else {
          addToast(err.message || 'Error communicating with model', 'error');
        }
      } finally {
        setIsGenerating(false);
        setStreamingContent('');
        setGenerationStatus(null);
        abortControllerRef.current = null;
        // Refresh conversations list to update titles/timestamps
        api.getConversations().then(setConversations).catch(() => {});
      }
    },
    [activeConversationId, isGenerating, selectedModelId, selectedCollection, selectedPersona, addToast]
  );

  // Stop generation
  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  // Feedback
  const handleFeedback = useCallback(
    async (messageId: string, feedback: 'like' | 'dislike' | null) => {
      try {
        await api.setMessageFeedback(messageId, feedback);
        setMessages(prev => prev.map(m => (m.id === messageId ? { ...m, feedback } : m)));
        addToast(feedback ? `Feedback noted: ${feedback}` : 'Feedback removed', 'info');
      } catch (e: any) {
        addToast(`Failed to set feedback: ${e.message}`, 'error');
      }
    },
    [addToast]
  );

  return {
    theme,
    toggleTheme,
    sidebarOpen,
    setSidebarOpen,
    contextPanelTab,
    setContextPanelTab,
    settingsModalOpen,
    setSettingsModalOpen,
    commandPaletteOpen,
    setCommandPaletteOpen,

    conversations,
    activeConversationId,
    messages,
    models,
    selectedModelId,
    setSelectedModelId,
    providers,
    systemHealth,

    documents,
    setDocuments,
    collections,
    setCollections,
    selectedCollection,
    setSelectedCollection,
    memories,
    setMemories,
    tools,
    searchQuery,
    setSearchQuery,
    selectedFolder,
    setSelectedFolder,

    isGenerating,
    streamingContent,
    generationStatus,
    currentCitations,

    toasts,
    addToast,
    removeToast,

    composerDraft,
    setComposerDraft,

    activeArtifact,
    setActiveArtifact,
    selectedPersona,
    setSelectedPersona,

    loadInitialData,
    selectConversation,
    newConversation,
    deleteConversation,
    renameConversation,
    togglePinConversation,
    sendMessage,
    stopGeneration,
    handleFeedback,
  };
}
