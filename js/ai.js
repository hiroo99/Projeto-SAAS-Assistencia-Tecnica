// ========================================
// AI.JS - Lógica específica da página Assistente
// ========================================

class ConversationHistory {
  constructor() {
    this.storageKey = "ai_conversations";
    this.maxConversations = 10;
    this.conversations = this.loadConversations();
    this.currentConversationId = null;
  }

  loadConversations() {
    try {
      const stored = localStorage.getItem(this.storageKey);
      return stored ? JSON.parse(stored) : [];
    } catch (e) {
      console.error("Erro ao carregar conversas:", e);
      return [];
    }
  }

  saveConversations() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.conversations));
    } catch (e) {
      console.error("Erro ao salvar conversas:", e);
    }
  }

  createNewConversation() {
    const conversation = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      messages: [
        {
          type: "ai",
          text: 'Olá! Sou seu assistente inteligente. Posso ajudar você a consultar informações sobre:\n\n• Ordens de Serviço: "cliente da OS005", "status da OS010", "OS concluídas hoje"\n• Clientes: "dados do João Silva", "telefone do cliente X"\n• Financeiro: "receitas do mês", "total de vendas"\n• Estoque: "produtos com pouco estoque", "quantidade do produto Y"\n\nO que você gostaria de saber?',
          timestamp: new Date().toISOString(),
          data: null,
        },
      ],
    };

    this.conversations.unshift(conversation);
    if (this.conversations.length > this.maxConversations) {
      this.conversations = this.conversations.slice(0, this.maxConversations);
    }

    this.currentConversationId = conversation.id;
    this.saveConversations();
    return conversation;
  }

  getCurrentConversation() {
    return this.conversations.find((c) => c.id === this.currentConversationId);
  }

  addMessageToCurrent(message) {
    const conversation = this.getCurrentConversation();
    if (conversation) {
      conversation.messages.push(message);
      this.saveConversations();
    }
  }

  loadConversation(conversationId) {
    const conversation = this.conversations.find(
      (c) => c.id === conversationId
    );
    this.currentConversationId = conversationId;
    return conversation;
  }

  clearHistory() {
    this.conversations = [];
    this.currentConversationId = null;
    this.saveConversations();
  }

  getConversationPreview(conversation) {
    const firstUserMessage = conversation.messages.find(
      (m) => m.type === "user"
    );
    const preview = firstUserMessage ? firstUserMessage.text : "Nova conversa";
    return preview.length > 50 ? preview.substring(0, 50) + "..." : preview;
  }

  getConversationTime(conversation) {
    const date = new Date(conversation.timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return date.toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } else if (diffDays === 1) {
      return "Ontem";
    } else if (diffDays < 7) {
      return date.toLocaleDateString("pt-BR", { weekday: "short" });
    } else {
      return date.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
      });
    }
  }
}

class AIChatManager {
  constructor() {
    this.chatMessages = document.getElementById("chatMessages");
    this.chatInput = document.getElementById("chatInput");
    this.sendButton = document.getElementById("sendButton");
    this.newConversationBtn = document.getElementById("newConversationBtn");
    this.clearHistoryBtn = document.getElementById("clearHistoryBtn");
    this.historyList = document.getElementById("historyList");
    this.isLoading = false;
    this.historyManager = new ConversationHistory();

    this.init();
  }

  init() {
    // Configurar event listeners
    this.sendButton.addEventListener("click", () => this.enviarMensagem());
    this.chatInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.enviarMensagem();
      }
    });

    this.newConversationBtn.addEventListener("click", () =>
      this.novaConversa()
    );
    this.clearHistoryBtn.addEventListener("click", () =>
      this.limparHistorico()
    );

    // Inicializar conversa atual ou criar nova
    this.inicializarConversa();

    // Carregar histórico
    this.carregarHistorico();

    // Focar no input ao carregar
    this.chatInput.focus();

    console.log("✅ Chat IA inicializado");
  }

  inicializarConversa() {
    // Se não há conversa atual, criar uma nova
    if (!this.historyManager.currentConversationId) {
      const conversation = this.historyManager.createNewConversation();
      this.carregarMensagensConversa(conversation);
    } else {
      // Carregar conversa atual
      const conversation = this.historyManager.getCurrentConversation();
      if (conversation) {
        this.carregarMensagensConversa(conversation);
      } else {
        // Conversa não existe mais, criar nova
        const newConversation = this.historyManager.createNewConversation();
        this.carregarMensagensConversa(newConversation);
      }
    }
  }

  novaConversa() {
    const conversation = this.historyManager.createNewConversation();
    this.carregarMensagensConversa(conversation);
    this.carregarHistorico();
    this.chatInput.focus();
  }

  limparHistorico() {
    if (
      confirm(
        "Tem certeza que deseja limpar todo o histórico de conversas? Esta ação não pode ser desfeita."
      )
    ) {
      this.historyManager.clearHistory();
      this.novaConversa();
      this.carregarHistorico();
    }
  }

  carregarMensagensConversa(conversation) {
    // Limpar mensagens atuais
    this.chatMessages.innerHTML = "";

    // Carregar mensagens da conversa
    conversation.messages.forEach((message) => {
      if (message.type === "user") {
        this.adicionarMensagemUsuarioSalva(message);
      } else if (message.type === "ai") {
        this.adicionarMensagemIASalva(message);
      }
    });
  }

  adicionarMensagemUsuarioSalva(message) {
    const mensagemHTML = `
            <div class="message user-message">
                <div class="message-content">
                    <div class="message-text">${this.escapeHtml(
                      message.text
                    )}</div>
                    <div class="message-time">${this.formatarHora(
                      new Date(message.timestamp)
                    )}</div>
                </div>
                <div class="message-avatar">
                    <span class="user-icon">👤</span>
                </div>
            </div>
        `;

    this.chatMessages.insertAdjacentHTML("beforeend", mensagemHTML);
  }

  adicionarMensagemIASalva(message) {
    let conteudoExtra = "";

    // Adicionar dados estruturados se disponíveis
    if (message.data && message.data.tipo) {
      switch (message.data.tipo) {
        case "os":
          const os = message.data.dados;
          conteudoExtra = `
                        <div class="data-preview os-preview">
                            <h4>📋 Ordem de Serviço ${os.numeroOS}</h4>
                            <div class="preview-details">
                                <span><strong>Cliente:</strong> ${
                                  os.clienteNome
                                }</span>
                                <span><strong>Status:</strong> ${this.formatarStatus(
                                  os.status
                                )}</span>
                                <span><strong>Aparelho:</strong> ${
                                  os.tipoAparelho
                                } ${os.marcaModelo}</span>
                                <span><strong>Valor:</strong> R$ ${os.valorOrcamento.toFixed(
                                  2
                                )}</span>
                            </div>
                        </div>
                    `;
          break;

        case "cliente":
          const cliente = message.data.dados;
          conteudoExtra = `
                        <div class="data-preview cliente-preview">
                            <h4>👤 Cliente: ${cliente.nome}</h4>
                            <div class="preview-details">
                                <span><strong>CPF/CNPJ:</strong> ${
                                  cliente.cpf_cnpj
                                }</span>
                                <span><strong>Telefone:</strong> ${
                                  cliente.telefone
                                }</span>
                                <span><strong>Email:</strong> ${
                                  cliente.email || "Não informado"
                                }</span>
                            </div>
                        </div>
                    `;
          break;

        case "financeiro":
          const fin = message.data.dados;
          conteudoExtra = `
                        <div class="data-preview financeiro-preview">
                            <h4>💰 Dados Financeiros</h4>
                            <div class="preview-details">
                                <span><strong>Receitas Totais:</strong> R$ ${fin.receitas_totais.toFixed(
                                  2
                                )}</span>
                                <span><strong>OS Entregues:</strong> ${
                                  fin.os_entregues
                                }</span>
                                <span><strong>Total de OS:</strong> ${
                                  fin.total_os
                                }</span>
                                <span><strong>Total de Clientes:</strong> ${
                                  fin.total_clientes
                                }</span>
                            </div>
                        </div>
                    `;
          break;

        case "produtos":
          const prod = message.data.dados;
          const baixoEstoque = prod.baixo_estoque.slice(0, 5);
          conteudoExtra = `
                        <div class="data-preview produtos-preview">
                            <h4>📦 Estoque</h4>
                            <div class="preview-details">
                                <span><strong>Total de Produtos:</strong> ${
                                  prod.total_produtos
                                }</span>
                                <span><strong>Com Estoque Baixo:</strong> ${
                                  baixoEstoque.length
                                } produtos</span>
                            </div>
                            ${
                              baixoEstoque.length > 0
                                ? `
                                <div class="produtos-lista">
                                    <small><strong>Produtos com estoque baixo:</strong></small>
                                    <ul>
                                        ${baixoEstoque
                                          .map(
                                            (p) =>
                                              `<li>${p.nome}: ${p.quantidade}/${p.estoqueMinimo} unidades</li>`
                                          )
                                          .join("")}
                                    </ul>
                                </div>
                            `
                                : ""
                            }
                        </div>
                    `;
          break;
      }
    }

    const mensagemHTML = `
            <div class="message ai-message">
                <div class="message-avatar">
                    <span class="ai-icon">🤖</span>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-author">Assistente</span>
                        <span class="message-time">${this.formatarHora(
                          new Date(message.timestamp)
                        )}</span>
                    </div>
                    <div class="message-text">
                        ${this.escapeHtml(message.text)}
                        ${conteudoExtra}
                    </div>
                </div>
            </div>
        `;

    this.chatMessages.insertAdjacentHTML("beforeend", mensagemHTML);
  }

  carregarHistorico() {
    const conversations = this.historyManager.conversations;

    if (conversations.length === 0) {
      this.historyList.innerHTML = `
                <div class="history-empty">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.5">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14,2 14,8 20,8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                        <polyline points="10,9 9,9 8,9"></polyline>
                    </svg>
                    <p>Nenhuma conversa ainda</p>
                    <small>Comece uma nova conversa para ver o histórico aqui</small>
                </div>
            `;
      return;
    }

    this.historyList.innerHTML = conversations
      .map((conversation) => {
        const isActive =
          conversation.id === this.historyManager.currentConversationId;
        const preview =
          this.historyManager.getConversationPreview(conversation);
        const time = this.historyManager.getConversationTime(conversation);

        return `
                <div class="history-item ${
                  isActive ? "active" : ""
                }" data-conversation-id="${
          conversation.id
        }" onclick="carregarConversa('${conversation.id}')">
                    <div class="history-content">
                        <div class="history-preview">${this.escapeHtml(
                          preview
                        )}</div>
                        <div class="history-time">${time}</div>
                    </div>
                    <div class="history-indicator">
                        <span class="message-count">${
                          conversation.messages.length - 1
                        }</span>
                    </div>
                </div>
            `;
      })
      .join("");
  }

  carregarConversaPorId(conversationId) {
    const conversation = this.historyManager.loadConversation(conversationId);
    if (conversation) {
      this.carregarMensagensConversa(conversation);
      this.carregarHistorico();
    }
  }

  async enviarMensagem() {
    const mensagem = this.chatInput.value.trim();
    if (!mensagem || this.isLoading) return;

    // Limpar input
    this.chatInput.value = "";

    // Adicionar mensagem do usuário
    this.adicionarMensagemUsuario(mensagem);

    // Mostrar loading
    this.mostrarLoading();

    // Enviar para API
    try {
      const resposta = await this.consultarIA(mensagem);
      this.removerLoading();
      this.adicionarMensagemIA(resposta);
    } catch (error) {
      console.error("Erro na consulta IA:", error);
      this.removerLoading();
      this.adicionarMensagemErro();
    }
  }

  async consultarIA(consulta) {
    const response = await fetch("/api/ai/consulta", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getToken()}`,
      },
      body: JSON.stringify({ consulta }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.mensagem || "Erro na consulta");
    }

    return await response.json();
  }

  adicionarMensagemUsuario(texto) {
    const timestamp = new Date().toISOString();
    const messageData = {
      type: "user",
      text: texto,
      timestamp: timestamp,
      data: null,
    };

    // Salvar no histórico
    this.historyManager.addMessageToCurrent(messageData);

    const mensagemHTML = `
            <div class="message user-message">
                <div class="message-content">
                    <div class="message-text">${this.escapeHtml(texto)}</div>
                    <div class="message-time">${this.formatarHora(
                      new Date()
                    )}</div>
                </div>
                <div class="message-avatar">
                    <span class="user-icon">👤</span>
                </div>
            </div>
        `;

    this.chatMessages.insertAdjacentHTML("beforeend", mensagemHTML);
    this.scrollParaBaixo();
  }

  adicionarMensagemIA(resposta) {
    const timestamp = new Date().toISOString();
    const messageData = {
      type: "ai",
      text: resposta.resposta,
      timestamp: timestamp,
      data: resposta.dados,
    };

    // Salvar no histórico
    this.historyManager.addMessageToCurrent(messageData);

    let conteudoExtra = "";

    // Adicionar dados estruturados se disponíveis
    if (resposta.dados && resposta.dados.tipo) {
      switch (resposta.dados.tipo) {
        case "os":
          const os = resposta.dados.dados;
          conteudoExtra = `
                        <div class="data-preview os-preview">
                            <h4>📋 Ordem de Serviço ${os.numeroOS}</h4>
                            <div class="preview-details">
                                <span><strong>Cliente:</strong> ${
                                  os.clienteNome
                                }</span>
                                <span><strong>Status:</strong> ${this.formatarStatus(
                                  os.status
                                )}</span>
                                <span><strong>Aparelho:</strong> ${
                                  os.tipoAparelho
                                } ${os.marcaModelo}</span>
                                <span><strong>Valor:</strong> R$ ${os.valorOrcamento.toFixed(
                                  2
                                )}</span>
                            </div>
                        </div>
                    `;
          break;

        case "cliente":
          const cliente = resposta.dados.dados;
          conteudoExtra = `
                        <div class="data-preview cliente-preview">
                            <h4>👤 Cliente: ${cliente.nome}</h4>
                            <div class="preview-details">
                                <span><strong>CPF/CNPJ:</strong> ${
                                  cliente.cpf_cnpj
                                }</span>
                                <span><strong>Telefone:</strong> ${
                                  cliente.telefone
                                }</span>
                                <span><strong>Email:</strong> ${
                                  cliente.email || "Não informado"
                                }</span>
                            </div>
                        </div>
                    `;
          break;

        case "financeiro":
          const fin = resposta.dados.dados;
          conteudoExtra = `
                        <div class="data-preview financeiro-preview">
                            <h4>💰 Dados Financeiros</h4>
                            <div class="preview-details">
                                <span><strong>Receitas Totais:</strong> R$ ${fin.receitas_totais.toFixed(
                                  2
                                )}</span>
                                <span><strong>OS Entregues:</strong> ${
                                  fin.os_entregues
                                }</span>
                                <span><strong>Total de OS:</strong> ${
                                  fin.total_os
                                }</span>
                                <span><strong>Total de Clientes:</strong> ${
                                  fin.total_clientes
                                }</span>
                            </div>
                        </div>
                    `;
          break;

        case "produtos":
          const prod = resposta.dados.dados;
          const baixoEstoque = prod.baixo_estoque.slice(0, 5); // Limitar a 5 produtos
          conteudoExtra = `
                        <div class="data-preview produtos-preview">
                            <h4>📦 Estoque</h4>
                            <div class="preview-details">
                                <span><strong>Total de Produtos:</strong> ${
                                  prod.total_produtos
                                }</span>
                                <span><strong>Com Estoque Baixo:</strong> ${
                                  baixoEstoque.length
                                } produtos</span>
                            </div>
                            ${
                              baixoEstoque.length > 0
                                ? `
                                <div class="produtos-lista">
                                    <small><strong>Produtos com estoque baixo:</strong></small>
                                    <ul>
                                        ${baixoEstoque
                                          .map(
                                            (p) =>
                                              `<li>${p.nome}: ${p.quantidade}/${p.estoqueMinimo} unidades</li>`
                                          )
                                          .join("")}
                                    </ul>
                                </div>
                            `
                                : ""
                            }
                        </div>
                    `;
          break;
      }
    }

    const mensagemHTML = `
            <div class="message ai-message">
                <div class="message-avatar">
                    <span class="ai-icon">🤖</span>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-author">Assistente</span>
                        <span class="message-time">${this.formatarHora(
                          new Date()
                        )}</span>
                    </div>
                    <div class="message-text">
                        ${this.escapeHtml(resposta.resposta)}
                        ${conteudoExtra}
                    </div>
                </div>
            </div>
        `;

    this.chatMessages.insertAdjacentHTML("beforeend", mensagemHTML);
    this.scrollParaBaixo();

    // Atualizar histórico após adicionar mensagem
    this.carregarHistorico();
  }

  adicionarMensagemErro() {
    const mensagemHTML = `
            <div class="message ai-message error-message">
                <div class="message-avatar">
                    <span class="ai-icon">⚠️</span>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-author">Assistente IA</span>
                        <span class="message-time">${this.formatarHora(
                          new Date()
                        )}</span>
                    </div>
                    <div class="message-text">
                        Desculpe, houve um erro ao processar sua consulta. Tente novamente ou reformule sua pergunta.
                    </div>
                </div>
            </div>
        `;

    this.chatMessages.insertAdjacentHTML("beforeend", mensagemHTML);
    this.scrollParaBaixo();
  }

  mostrarLoading() {
    this.isLoading = true;
    this.sendButton.disabled = true;
    this.chatInput.disabled = true;

    const loadingHTML = `
            <div class="message ai-message loading-message" id="loadingMessage">
                <div class="message-avatar">
                    <span class="ai-icon">🤖</span>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-author">Assistente IA</span>
                        <span class="message-time">${this.formatarHora(
                          new Date()
                        )}</span>
                    </div>
                    <div class="message-text">
                        <div class="loading-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                        Processando sua consulta...
                    </div>
                </div>
            </div>
        `;

    this.chatMessages.insertAdjacentHTML("beforeend", loadingHTML);
    this.scrollParaBaixo();
  }

  removerLoading() {
    this.isLoading = false;
    this.sendButton.disabled = false;
    this.chatInput.disabled = false;

    const loadingMessage = document.getElementById("loadingMessage");
    if (loadingMessage) {
      loadingMessage.remove();
    }
  }

  formatarStatus(status) {
    const statusMap = {
      aguardando: "Aguardando",
      em_reparo: "Em Reparo",
      pronto: "Pronto",
      entregue: "Entregue",
      cancelado: "Cancelado",
    };
    return statusMap[status] || status;
  }

  formatarHora(data) {
    return data.toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  scrollParaBaixo() {
    setTimeout(() => {
      this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }, 100);
  }
}

// Função para usar exemplos
function usarExemplo(exemplo) {
  const chatInput = document.getElementById("chatInput");
  if (chatInput) {
    chatInput.value = exemplo;
    chatInput.focus();
  }
}

// Função global para carregar conversa do histórico
function carregarConversa(conversationId) {
  if (window.aiChatManager) {
    window.aiChatManager.carregarConversaPorId(conversationId);
  }
}

// Função auxiliar para obter token
function getToken() {
  return (
    localStorage.getItem("ia_sistem_token") ||
    sessionStorage.getItem("ia_sistem_token")
  );
}

// Inicializar quando DOM estiver pronto
document.addEventListener("DOMContentLoaded", function () {
  // Protege a página
  protegerPagina();

  // Inicializar chat IA
  if (document.getElementById("chatMessages")) {
    window.aiChatManager = new AIChatManager();
    console.log("✅ Assistente carregado!");
  }
});

console.log("✅ ai.js carregado com sucesso!");
