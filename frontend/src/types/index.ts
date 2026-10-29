export interface Citation {
  title: string;
  url: string;
  snippet?: string;
}

export interface Attachment {
  filename: string;
  file_type: string;
  file_size: number;
  preview_url?: string;
  base64?: string;
  file_path?: string;
  doc_id?: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  created_at: string;
  model_used?: string;
  provider_used?: string;
  finish_reason?: string;
  tool_calls?: any[];
  citations?: Citation[];
  attachments?: Attachment[];
  feedback?: 'like' | 'dislike' | null;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  pinned: boolean;
  folder?: string | null;
  model_id: string;
  system_prompt?: string | null;
  message_count?: number;
  last_message?: string | null;
}

export interface ModelCapability {
  streaming: boolean;
  vision: boolean;
  tool_calling: boolean;
  structured_output: boolean;
  web_search: boolean;
  deep_research: boolean;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  description: string;
  capabilities: ModelCapability;
  is_available: boolean;
  context_window: number;
  tier: 'free' | 'paid' | 'local' | 'mock';
}

export interface ProviderStatus {
  name: string;
  display_name: string;
  is_configured: boolean;
  is_available: boolean;
  models: ModelInfo[];
  error_message?: string | null;
}

export interface DocumentItem {
  id: string;
  collection_name: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: 'uploaded' | 'processing' | 'ready' | 'error';
  chunk_count: number;
  created_at: string;
  error_message?: string | null;
}

export interface CollectionSummary {
  name: string;
  document_count: number;
  total_chunks: number;
}

export interface MemoryItem {
  id: string;
  content: string;
  category: string;
  confidence: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  source_conversation_id?: string | null;
}

export interface UserSettings {
  theme: 'dark' | 'light';
  default_model: string;
  model_routing_enabled: boolean;
  memory_enabled: boolean;
  search_provider: string;
  temperature: number;
  system_prompt?: string;
  stream_responses: boolean;
}

export interface SystemHealth {
  status: string;
  version: string;
  database: string;
  active_provider: string;
  configured_providers: Record<string, boolean>;
  timestamp: string;
}

export interface ToolItem {
  name: string;
  description: string;
  parameters: any;
  requires_confirmation: boolean;
  timeout_seconds: number;
}

export interface Artifact {
  id: string;
  title: string;
  language: string;
  content: string;
  type: 'code' | 'html' | 'markdown' | 'svg';
}

export type PersonaId = 'general' | 'coder' | 'researcher' | 'analyst' | 'writer';

export interface Persona {
  id: PersonaId;
  name: string;
  icon: string;
  systemPrompt: string;
  description: string;
}

export interface GeneratedImage {
  id: string;
  url: string;
  prompt: string;
  style: string;
  aspect_ratio: string;
  width: number;
  height: number;
  provider: string;
  created_at: string;
  filename: string;
}

export interface ImageAnalysisResult {
  analysis: string;
  properties: {
    width?: number;
    height?: number;
    megapixels?: number;
    format?: string;
    color_mode?: string;
    aspect_ratio?: string;
    brightness?: number;
    dominant_colors?: string[];
  };
  engine: string;
}
