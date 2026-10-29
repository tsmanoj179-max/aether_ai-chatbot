import React, { useState, useEffect } from 'react';
import { UserSettings, ProviderStatus, SystemHealth } from '../../types';
import { api } from '../../api/client';
import {
  X,
  Settings,
  Shield,
  Sparkles,
  Zap,
  Cpu,
  Key,
  Database,
  CheckCircle2,
} from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  providers: ProviderStatus[];
  systemHealth: SystemHealth | null;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
  onAddToast: (text: string, type: 'info' | 'success' | 'warning' | 'error') => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  providers,
  systemHealth,
  theme,
  onToggleTheme,
  onAddToast,
}) => {
  const [activeTab, setActiveTab] = useState<'general' | 'providers' | 'diagnostics'>('general');
  const [settings, setSettings] = useState<UserSettings>({
    theme: theme,
    default_model: 'aether-mock-omni',
    model_routing_enabled: true,
    memory_enabled: true,
    search_provider: 'duckduckgo',
    temperature: 0.7,
    system_prompt: 'You are AetherAI, an expert, thoughtful, and articulate AI workspace assistant.',
    stream_responses: true,
  });

  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      api.getSettings().then(setSettings).catch(() => {});
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await api.updateSettings(settings);
      onAddToast('Settings saved successfully', 'success');
      onClose();
    } catch (e: any) {
      onAddToast(`Failed to save settings: ${e.message}`, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs animate-in fade-in"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-modal-title"
        className="settings-modal-surface w-full max-w-2xl rounded-2xl border border-border bg-card text-foreground shadow-2xl flex flex-col max-h-[85vh] overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="h-14 border-b border-border/80 px-5 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <Settings className="w-4 h-4 text-primary" />
            <h2 id="settings-modal-title" className="font-bold text-sm">Settings & Provider Configuration</h2>
          </div>
          <button onClick={onClose} aria-label="Close settings" className="p-1 rounded-lg hover:bg-secondary text-muted-foreground">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab navigation */}
        <div className="settings-tabs flex border-b border-border/60 px-5 gap-2 sm:gap-4 shrink-0 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('general')}
            className={`flex-1 sm:flex-none py-2.5 border-b-2 transition-colors ${
              activeTab === 'general'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <span className="sm:hidden">General</span>
            <span className="hidden sm:inline">General & Routing</span>
          </button>
          <button
            onClick={() => setActiveTab('providers')}
            className={`flex-1 sm:flex-none py-2.5 border-b-2 transition-colors ${
              activeTab === 'providers'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <span className="sm:hidden">Providers</span>
            <span className="hidden sm:inline">Providers & API Keys</span>
          </button>
          <button
            onClick={() => setActiveTab('diagnostics')}
            className={`flex-1 sm:flex-none py-2.5 border-b-2 transition-colors ${
              activeTab === 'diagnostics'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <span className="sm:hidden">Diagnostics</span>
            <span className="hidden sm:inline">System Diagnostics</span>
          </button>
        </div>

        {/* Content body */}
        <div className="flex-1 overflow-y-auto p-5 scrollbar-thin text-xs space-y-5">
          {/* TAB 1: GENERAL */}
          {activeTab === 'general' && (
            <div className="space-y-4">
              <div>
                <label className="font-semibold text-foreground block mb-1">Appearance</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      if (theme !== 'dark') onToggleTheme();
                    }}
                    className={`flex-1 p-2.5 rounded-lg border text-xs font-medium text-center ${
                      theme === 'dark' ? 'border-primary bg-primary/10 text-primary font-bold' : 'border-border'
                    }`}
                  >
                    Dark Theme (Default)
                  </button>
                  <button
                    onClick={() => {
                      if (theme !== 'light') onToggleTheme();
                    }}
                    className={`flex-1 p-2.5 rounded-lg border text-xs font-medium text-center ${
                      theme === 'light' ? 'border-primary bg-primary/10 text-primary font-bold' : 'border-border'
                    }`}
                  >
                    Light Theme
                  </button>
                </div>
              </div>

              <div>
                <label className="font-semibold text-foreground block mb-1">
                  Default Temperature ({settings.temperature})
                </label>
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.05"
                  value={settings.temperature}
                  onChange={e => setSettings({ ...settings, temperature: parseFloat(e.target.value) })}
                  className="w-full accent-primary cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
                  <span>Deterministic (0.0)</span>
                  <span>Balanced (0.7)</span>
                  <span>Creative (1.0)</span>
                </div>
              </div>

              <div>
                <label className="font-semibold text-foreground block mb-1">
                  Default System Prompt
                </label>
                <textarea
                  value={settings.system_prompt || ''}
                  onChange={e => setSettings({ ...settings, system_prompt: e.target.value })}
                  rows={3}
                  className="w-full p-2.5 rounded-lg border border-border bg-secondary/40 text-xs focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg border border-border bg-secondary/30">
                <div>
                  <div className="font-semibold text-foreground">Intelligent Model Routing</div>
                  <div className="text-[11px] text-muted-foreground">
                    Automatically route coding, reasoning, and research tasks to eligible configured models.
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={settings.model_routing_enabled}
                  onChange={e => setSettings({ ...settings, model_routing_enabled: e.target.checked })}
                  className="w-4 h-4 accent-primary"
                />
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg border border-border bg-secondary/30">
                <div>
                  <div className="font-semibold text-foreground">Long-Term Memory Injection</div>
                  <div className="text-[11px] text-muted-foreground">
                    Apply saved preferences and instructions to new conversational prompts.
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={settings.memory_enabled}
                  onChange={e => setSettings({ ...settings, memory_enabled: e.target.checked })}
                  className="w-4 h-4 accent-primary"
                />
              </div>
            </div>
          )}

          {/* TAB 2: PROVIDERS & API KEYS */}
          {activeTab === 'providers' && (
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl border border-primary/20 bg-primary/5 text-primary text-xs leading-relaxed flex items-start gap-2.5">
                <Key className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">Zero-Exposure Security Guarantee:</span> API keys are stored exclusively in your server-side <code className="px-1 py-0.5 rounded bg-primary/10 font-mono text-[11px]">.env</code> file and never sent to frontend storage or exposed over untrusted networks.
                </div>
              </div>

              <div className="flex flex-col gap-2.5">
                {providers.map(p => {
                  let Icon = Shield;
                  if (p.name === 'gemini') Icon = Sparkles;
                  else if (p.name === 'groq') Icon = Zap;
                  else if (p.name === 'ollama') Icon = Cpu;

                  return (
                    <div
                      key={p.name}
                      className="p-3 rounded-xl border border-border bg-card flex items-start justify-between gap-3"
                    >
                      <div className="flex items-start gap-2.5">
                        <div className="p-2 rounded-lg bg-secondary text-primary mt-0.5">
                          <Icon className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="font-semibold text-foreground flex items-center gap-1.5">
                            <span>{p.display_name}</span>
                            {p.is_configured ? (
                              <span className="text-[10px] px-1.5 py-0.2 rounded font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                Configured
                              </span>
                            ) : (
                              <span className="text-[10px] px-1.5 py-0.2 rounded font-medium bg-secondary text-muted-foreground">
                                Not Configured
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] text-muted-foreground mt-0.5">
                            {p.name === 'mock' && 'Built-in deterministic simulator. Zero configuration required.'}
                            {p.name === 'gemini' && 'Add GEMINI_API_KEY in backend/.env for Gemini 2.5 Flash / Pro.'}
                            {p.name === 'groq' && 'Add GROQ_API_KEY in backend/.env for ultra-fast Llama 3.3.'}
                            {p.name === 'openai' && 'Add OPENAI_API_KEY and OPENAI_API_BASE in backend/.env.'}
                            {p.name === 'ollama' && 'Runs on http://localhost:11434 with local quantized models.'}
                          </div>
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <span className="text-[10px] text-muted-foreground">
                          {p.models.length} models
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 3: DIAGNOSTICS */}
          {activeTab === 'diagnostics' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl border border-border bg-secondary/20">
                  <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">
                    Backend Health
                  </span>
                  <div className="text-sm font-semibold text-emerald-400 flex items-center gap-1 mt-1">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>{systemHealth?.status || 'Operational'}</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl border border-border bg-secondary/20">
                  <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">
                    Persistence Database
                  </span>
                  <div className="text-sm font-semibold text-foreground flex items-center gap-1 mt-1">
                    <Database className="w-4 h-4 text-primary" />
                    <span>{systemHealth?.database || 'SQLite Local'}</span>
                  </div>
                </div>
              </div>

              <div className="p-3.5 rounded-xl border border-border bg-card">
                <span className="font-semibold text-foreground block mb-1">
                  Development Host Specs:
                </span>
                <ul className="list-disc list-inside space-y-1 text-muted-foreground text-[11px]">
                  <li>CPU: Intel Core i7-13620H (16 Threads)</li>
                  <li>Memory: 16 GB RAM (CPU-bounded vector cosine indexing)</li>
                  <li>Local Vector Storage: Sparse TF-IDF cosine index in SQLite</li>
                  <li>Inference Strategy: Cloud API endpoints with zero-key demonstration mock fallback</li>
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div className="h-14 border-t border-border/80 px-5 flex items-center justify-end gap-2 shrink-0 bg-secondary/20">
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 rounded-lg border border-border text-xs font-medium hover:bg-secondary transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-1.5 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 text-xs transition-all shadow-md"
          >
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
};
