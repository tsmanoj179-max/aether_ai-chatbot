import {
  Conversation,
  Message,
  ModelInfo,
  ProviderStatus,
  DocumentItem,
  CollectionSummary,
  MemoryItem,
  UserSettings,
  SystemHealth,
  ToolItem,
  GeneratedImage,
  ImageAnalysisResult
} from '../types';

export const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : '/api/v1';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      errorDetail = response.statusText;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Health
  getHealth: () => request<SystemHealth>('/health'),

  // Providers & Models
  getProviders: () => request<ProviderStatus[]>('/providers'),
  getModels: () => request<ModelInfo[]>('/models'),

  // Conversations
  getConversations: (query?: string, folder?: string) => {
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (folder) params.append('folder', folder);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return request<Conversation[]>(`/conversations${qs}`);
  },

  createConversation: (payload: { title?: string; model_id?: string; folder?: string; system_prompt?: string }) =>
    request<Conversation>('/conversations', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getConversation: (id: string) =>
    request<Conversation & { messages: Message[] }>(`/conversations/${id}`),

  updateConversation: (id: string, payload: Partial<Conversation>) =>
    request<Conversation>(`/conversations/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  deleteConversation: (id: string) =>
    request<{ status: string; id: string }>(`/conversations/${id}`, {
      method: 'DELETE',
    }),

  exportConversationUrl: (id: string, format: 'markdown' | 'json' = 'markdown') =>
    `${API_BASE}/conversations/${id}/export?format=${format}`,

  // Feedback
  setMessageFeedback: (messageId: string, feedback: 'like' | 'dislike' | null) =>
    request<{ status: string; feedback: string }>(`/messages/${messageId}/feedback`, {
      method: 'POST',
      body: JSON.stringify({ feedback }),
    }),

  // Documents & RAG
  getDocuments: (collection?: string) => {
    const qs = collection ? `?collection=${encodeURIComponent(collection)}` : '';
    return request<DocumentItem[]>(`/documents${qs}`);
  },

  getCollections: () => request<CollectionSummary[]>('/documents/collections'),

  uploadDocument: async (file: File, collection: string = 'default') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('collection', collection);

    const response = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errJson.detail || 'Upload failed');
    }

    return response.json() as Promise<DocumentItem>;
  },

  deleteDocument: (id: string) =>
    request<{ status: string; id: string }>(`/documents/${id}`, {
      method: 'DELETE',
    }),

  searchDocumentChunks: (query: string, collectionName?: string, topK: number = 3) =>
    request<any[]>('/documents/search', {
      method: 'POST',
      body: JSON.stringify({
        query,
        collection_name: collectionName,
        top_k: topK,
      }),
    }),

  // Memories
  getMemories: (activeOnly: boolean = false) =>
    request<MemoryItem[]>(`/memories?active_only=${activeOnly}`),

  createMemory: (content: string, category: string = 'preference') =>
    request<MemoryItem>('/memories', {
      method: 'POST',
      body: JSON.stringify({ content, category }),
    }),

  updateMemory: (id: string, payload: Partial<MemoryItem>) =>
    request<MemoryItem>(`/memories/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  deleteMemory: (id: string) =>
    request<{ status: string; id: string }>(`/memories/${id}`, {
      method: 'DELETE',
    }),

  clearMemories: () =>
    request<{ status: string; deleted_count: number }>('/memories', {
      method: 'DELETE',
    }),

  // Tools
  getTools: () => request<ToolItem[]>('/tools'),
  executeTool: (toolName: string, args: Record<string, any>) =>
    request<any>('/tools/execute', {
      method: 'POST',
      body: JSON.stringify({ tool_name: toolName, arguments: args }),
    }),

  // Settings
  getSettings: () => request<UserSettings>('/settings'),
  updateSettings: (settings: UserSettings) =>
    request<UserSettings>('/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
    }),

  // Image Generation & Vision
  generateImage: (params: { prompt: string; style?: string; aspect_ratio?: string; seed?: number }) =>
    request<GeneratedImage>('/images/generate', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  analyzeImage: async (file: File, question?: string, modelId?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (question) formData.append('question', question);
    if (modelId) formData.append('model_id', modelId);

    const response = await fetch(`${API_BASE}/images/analyze`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      throw new Error('Image analysis failed');
    }
    return response.json() as Promise<ImageAnalysisResult>;
  },

  getImageGallery: (limit: number = 24) =>
    request<{ count: number; images: GeneratedImage[] }>(`/images/gallery?limit=${limit}`),

  getImageStyles: () =>
    request<{ styles: Record<string, string>; aspect_ratios: string[] }>('/images/styles'),

  // Streaming Chat Helper
  streamChat: async (
    payload: {
      conversation_id?: string;
      message: string;
      model_id?: string;
      system_prompt?: string;
      web_search?: boolean;
      deep_research?: boolean;
      collection_name?: string;
      attachments?: any[];
      temperature?: number;
    },
    callbacks: {
      onInit?: (data: { conversation_id: string; title: string }) => void;
      onToken?: (token: string) => void;
      onStatus?: (status: { status: string; provider?: string }) => void;
      onCitation?: (citation: any) => void;
      onDone?: (data: any) => void;
      onError?: (error: string) => void;
    },
    signal?: AbortSignal
  ) => {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal,
    });

    if (!response.ok) {
      let err = 'Failed to connect stream';
      try {
        const j = await response.json();
        err = j.detail || err;
      } catch {}
      throw new Error(err);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('Response body stream is not readable.');

    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith('data: ')) continue;
        const jsonStr = trimmed.slice(6);
        try {
          const event = JSON.parse(jsonStr);
          switch (event.type) {
            case 'init':
              callbacks.onInit?.(event.data);
              break;
            case 'token':
              callbacks.onToken?.(event.data?.token || '');
              break;
            case 'status':
              callbacks.onStatus?.(event.data);
              break;
            case 'citation':
              callbacks.onCitation?.(event.data);
              break;
            case 'done':
              callbacks.onDone?.(event.data);
              break;
            case 'error':
              callbacks.onError?.(event.data?.error || 'Unknown error');
              break;
          }
        } catch {
          // ignore malformed SSE line
        }
      }
    }
  },

  // System Heartbeat & Shutdown
  sendHeartbeat: async () => {
    try {
      await fetch(`${API_BASE}/system/heartbeat`, { method: 'POST' });
      return true;
    } catch {
      return false;
    }
  },

  shutdownSystem: async (immediate: boolean = true) => {
    try {
      await fetch(`${API_BASE}/system/shutdown`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ immediate, reason: 'user_exit' }),
      });
      return true;
    } catch {
      return false;
    }
  },
};
