import React, { useEffect, useRef } from 'react';
import { useAppStore } from './store/useAppStore';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { ContextPanel } from './components/layout/ContextPanel';
import { ChatViewport } from './components/chat/ChatViewport';
import { Composer } from './components/chat/Composer';
import { CommandPalette } from './components/common/CommandPalette';
import { SettingsModal } from './components/settings/SettingsModal';
import { ToastContainer } from './components/common/Toast';
import { api, API_BASE } from './api/client';

export function App() {
  const store = useAppStore();
  const wasMobileRef = useRef(window.innerWidth < 768);
  const { setSidebarOpen } = store;

  // Background heartbeat & shutdown listener
  useEffect(() => {
    // Initial heartbeat
    api.sendHeartbeat().catch(() => {});

    // Periodic heartbeat every 3.5 seconds
    const hbInterval = setInterval(() => {
      api.sendHeartbeat().catch(() => {});
    }, 3500);

    // Graceful unload notification on tab or window close
    const handleUnload = () => {
      const shutdownUrl = `${API_BASE}/system/shutdown`;
      const payload = JSON.stringify({ immediate: false, reason: 'window_unload' });
      if (navigator.sendBeacon) {
        navigator.sendBeacon(shutdownUrl, payload);
      } else {
        fetch(shutdownUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: payload,
          keepalive: true,
        }).catch(() => {});
      }
    };

    window.addEventListener('pagehide', handleUnload);
    window.addEventListener('beforeunload', handleUnload);

    return () => {
      clearInterval(hbInterval);
      window.removeEventListener('pagehide', handleUnload);
      window.removeEventListener('beforeunload', handleUnload);
    };
  }, []);

  useEffect(() => {
    const handleResize = () => {
      const isMobile = window.innerWidth < 768;
      if (isMobile && !wasMobileRef.current) {
        setSidebarOpen(false);
      }
      wasMobileRef.current = isMobile;
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [setSidebarOpen]);

  const activeConv = store.conversations.find(c => c.id === store.activeConversationId);
  const currentTitle = activeConv?.title || 'New Conversation';

  const handleFileUpload = async (file: File) => {
    return await api.uploadDocument(file, store.selectedCollection || 'default');
  };

  const handleExportConversation = () => {
    if (!store.activeConversationId) return;
    const exportUrl = api.exportConversationUrl(store.activeConversationId, 'markdown');
    window.open(exportUrl, '_blank');
  };

  const handleOpenInCanvas = (content: string, language: string) => {
    store.setActiveArtifact({
      id: Date.now().toString(),
      title: `${language.toUpperCase()} Artifact`,
      language,
      content,
      type: 'code',
    });
    store.setContextPanelTab('canvas');
    store.addToast(`Opened in Canvas Studio`, 'info');
  };

  return (
    <div className="app-shell flex h-screen w-screen overflow-hidden bg-background text-foreground">
      {/* Toast notifications */}
      <ToastContainer toasts={store.toasts} onRemove={store.removeToast} />

      {/* Command Palette */}
      <CommandPalette
        isOpen={store.commandPaletteOpen}
        onClose={() => store.setCommandPaletteOpen(false)}
        onToggle={() => store.setCommandPaletteOpen(prev => !prev)}
        onNewConversation={store.newConversation}
        onToggleTheme={store.toggleTheme}
        theme={store.theme}
        onOpenContextTab={tab => {
          store.setContextPanelTab(tab);
          store.setCommandPaletteOpen(false);
        }}
        onOpenSettings={() => {
          store.setSettingsModalOpen(true);
          store.setCommandPaletteOpen(false);
        }}
        onExport={store.activeConversationId ? handleExportConversation : undefined}
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={store.settingsModalOpen}
        onClose={() => store.setSettingsModalOpen(false)}
        providers={store.providers}
        systemHealth={store.systemHealth}
        theme={store.theme}
        onToggleTheme={store.toggleTheme}
        onAddToast={store.addToast}
      />

      {/* 1. Left Navigation Sidebar */}
      <Sidebar
        isOpen={store.sidebarOpen}
        onClose={() => store.setSidebarOpen(false)}
        conversations={store.conversations}
        activeConversationId={store.activeConversationId}
        onSelectConversation={store.selectConversation}
        onNewConversation={store.newConversation}
        onDeleteConversation={store.deleteConversation}
        onRenameConversation={store.renameConversation}
        onTogglePin={store.togglePinConversation}
        searchQuery={store.searchQuery}
        onSearchChange={store.setSearchQuery}
        providers={store.providers}
        onOpenSettings={() => store.setSettingsModalOpen(true)}
      />

      {/* 2. Main Conversation Workspace */}
      <main className="workspace-main flex-1 flex flex-col min-w-0 h-full overflow-hidden relative">
        <Header
          title={currentTitle}
          onRenameTitle={
            store.activeConversationId
              ? newTitle => store.renameConversation(store.activeConversationId!, newTitle)
              : undefined
          }
          onToggleSidebar={() => store.setSidebarOpen(!store.sidebarOpen)}
          theme={store.theme}
          onToggleTheme={store.toggleTheme}
          onOpenSettings={() => store.setSettingsModalOpen(true)}
          onOpenCommandPalette={() => store.setCommandPaletteOpen(true)}
          activeContextTab={store.contextPanelTab}
          onToggleContextTab={tab =>
            store.setContextPanelTab(store.contextPanelTab === tab ? 'none' : tab)
          }
          onExportConversation={store.activeConversationId ? handleExportConversation : undefined}
        />

        <div className="flex-1 flex flex-col min-h-0 overflow-hidden relative select-text">
          <ChatViewport
            messages={store.messages}
            isGenerating={store.isGenerating}
            streamingContent={store.streamingContent}
            generationStatus={store.generationStatus}
            currentCitations={store.currentCitations}
            onStarterPromptClick={(prompt, sendImmediately) => {
              if (sendImmediately) {
                store.sendMessage(prompt);
              } else {
                store.setComposerDraft(prompt);
                store.addToast('Prompt loaded into composer', 'info');
              }
            }}
            onFeedback={store.handleFeedback}
            onRegenerate={msg => store.sendMessage(`Please refine or re-evaluate: ${msg.content}`)}
            onEditAndResubmit={(_msg, newText) => store.sendMessage(newText)}
            onOpenInCanvas={handleOpenInCanvas}
          />

          <Composer
            onSendMessage={(text, opts) => store.sendMessage(text, opts)}
            onStop={store.stopGeneration}
            isGenerating={store.isGenerating}
            models={store.models}
            selectedModelId={store.selectedModelId}
            onSelectModel={store.setSelectedModelId}
            collections={store.collections}
            selectedCollection={store.selectedCollection}
            onSelectCollection={store.setSelectedCollection}
            onFileUpload={handleFileUpload}
            selectedPersona={store.selectedPersona}
            onSelectPersona={store.setSelectedPersona}
            onUploadError={message => store.addToast(message, 'error')}
            draftText={store.composerDraft}
            onClearDraft={() => store.setComposerDraft('')}
          />
        </div>
      </main>

      {/* 3. Optional Right Contextual Panel */}
      {store.contextPanelTab !== 'none' && (
        <div
          className="fixed inset-0 z-30 bg-black/45 backdrop-blur-[2px] md:hidden"
          onClick={() => store.setContextPanelTab('none')}
          aria-hidden="true"
        />
      )}
      <ContextPanel
        activeTab={store.contextPanelTab}
        onClose={() => store.setContextPanelTab('none')}
        documents={store.documents}
        collections={store.collections}
        onUploadDocument={handleFileUpload}
        onDeleteDocument={async id => {
          await api.deleteDocument(id);
          store.setDocuments(prev => prev.filter(d => d.id !== id));
          store.addToast('Document deleted', 'info');
        }}
        memories={store.memories}
        onCreateMemory={async (content, cat) => {
          const mem = await api.createMemory(content, cat);
          store.setMemories(prev => [mem, ...prev]);
        }}
        onDeleteMemory={async id => {
          await api.deleteMemory(id);
          store.setMemories(prev => prev.filter(m => m.id !== id));
          store.addToast('Memory removed', 'info');
        }}
        onToggleMemory={async (id, active) => {
          const updated = await api.updateMemory(id, { is_active: active });
          store.setMemories(prev => prev.map(m => (m.id === id ? updated : m)));
        }}
        onClearMemories={async () => {
          await api.clearMemories();
          store.setMemories([]);
          store.addToast('All memories cleared', 'info');
        }}
        tools={store.tools}
        activeArtifact={store.activeArtifact}
        onUpdateArtifact={store.setActiveArtifact}
        onAddToast={store.addToast}
      />
    </div>
  );
}

export default App;
