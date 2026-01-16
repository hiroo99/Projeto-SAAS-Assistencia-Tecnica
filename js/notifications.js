// ========================================
// SISTEMA DE NOTIFICAÇÕES
// ========================================

class NotificationManager {
    constructor() {
        this.notificationBtn = document.getElementById('notificationBtn');
        this.notificationDropdown = document.getElementById('notificationDropdown');
        this.notificationList = document.getElementById('notificationList');
        this.notificationCount = document.getElementById('notificationCount');
        this.markAllReadBtn = document.getElementById('markAllReadBtn');
        this.viewAllBtn = document.getElementById('viewAllNotificationsBtn');

        this.notificacoes = [];
        this.isOpen = false;

        this.init();
    }

    init() {
        // Event listeners
        this.notificationBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown();
        });

        this.markAllReadBtn.addEventListener('click', () => {
            this.marcarTodasComoLidas();
        });

        this.viewAllBtn.addEventListener('click', () => {
            this.verTodasNotificacoes();
        });

        // Fechar dropdown ao clicar fora
        document.addEventListener('click', (e) => {
            if (!this.notificationDropdown.contains(e.target) && e.target !== this.notificationBtn) {
                this.closeDropdown();
            }
        });

        // Fechar dropdown no ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.closeDropdown();
            }
        });

        // Carregar notificações iniciais
        this.carregarNotificacoes();

        // Atualizar contador periodicamente
        setInterval(() => {
            this.atualizarContador();
        }, 30000); // A cada 30 segundos
    }

    toggleDropdown() {
        if (this.isOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }

    openDropdown() {
        this.notificationDropdown.classList.add('active');
        this.isOpen = true;

        // Recarregar notificações quando abrir
        this.carregarNotificacoes();
    }

    closeDropdown() {
        this.notificationDropdown.classList.remove('active');
        this.isOpen = false;
    }

    async carregarNotificacoes() {
        try {
            const response = await fetch('/api/notificacoes', {
                headers: {
                    'Authorization': `Bearer ${getToken()}`
                }
            });

            if (response.ok) {
                this.notificacoes = await response.json();
                this.renderizarNotificacoes();
                this.atualizarContador();
            } else {
                console.error('Erro ao carregar notificações:', response.status);
            }
        } catch (error) {
            console.error('Erro ao carregar notificações:', error);
        }
    }

    async atualizarContador() {
        try {
            const response = await fetch('/api/notificacoes/contador', {
                headers: {
                    'Authorization': `Bearer ${getToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                const count = data.nao_lidas || 0;
                this.notificationCount.textContent = count;
                this.notificationCount.style.display = count > 0 ? 'flex' : 'none';
            }
        } catch (error) {
            console.error('Erro ao atualizar contador:', error);
        }
    }

    renderizarNotificacoes() {
        if (this.notificacoes.length === 0) {
            this.notificationList.innerHTML = `
                <div class="notification-empty">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.5">
                        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                        <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                    </svg>
                    <p>Nenhuma notificação</p>
                </div>
            `;
            return;
        }

        // Mostrar apenas as 5 mais recentes no dropdown
        const notificacoesRecentes = this.notificacoes.slice(0, 5);

        this.notificationList.innerHTML = notificacoesRecentes.map(notif => `
            <div class="notification-item ${notif.lida ? '' : 'unread'}" data-id="${notif.id}">
                <div class="notification-content">
                    <div class="notification-icon ${notif.tipo}">
                        ${this.getIconForTipo(notif.tipo)}
                    </div>
                    <div class="notification-text">
                        <span class="notification-title">${this.escapeHtml(notif.titulo)}</span>
                        <div class="notification-message">${this.escapeHtml(notif.mensagem)}</div>
                        <div class="notification-time">${this.formatarTempo(notif.criado_em)}</div>
                    </div>
                </div>
            </div>
        `).join('');

        // Adicionar event listeners aos itens
        this.notificationList.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', () => {
                const notifId = parseInt(item.dataset.id);
                this.clicarNotificacao(notifId);
            });
        });
    }

    getIconForTipo(tipo) {
        const icones = {
            'os_atrasada': '<i class="bi bi-hourglass"></i>',
            'estoque_critico': '<i class="bi bi-exclamation-triangle"></i>',
            'os_pronta': '<i class="bi bi-check-circle"></i>',
            'cliente_novo': '<i class="bi bi-person"></i>'
        };
        return icones[tipo] || '<i class="bi bi-bell"></i>';
    }

    formatarTempo(dataString) {
        if (!dataString) return '';

        const data = new Date(dataString);
        const agora = new Date();
        const diffMs = agora - data;
        const diffMin = Math.floor(diffMs / (1000 * 60));
        const diffHoras = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDias = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffMin < 1) return 'Agora';
        if (diffMin < 60) return `${diffMin}min atrás`;
        if (diffHoras < 24) return `${diffHoras}h atrás`;
        if (diffDias < 7) return `${diffDias}d atrás`;

        return data.toLocaleDateString('pt-BR');
    }

    async clicarNotificacao(notificacaoId) {
        const notificacao = this.notificacoes.find(n => n.id === notificacaoId);
        if (!notificacao) return;

        // Marcar como lida se não estiver
        if (!notificacao.lida) {
            await this.marcarComoLida(notificacaoId);
        }

        // Navegar baseado no tipo e dados de referência
        this.navegarParaNotificacao(notificacao);

        // Fechar dropdown
        this.closeDropdown();
    }

    async marcarComoLida(notificacaoId) {
        try {
            const response = await fetch(`/api/notificacoes/${notificacaoId}/lida`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${getToken()}`
                }
            });

            if (response.ok) {
                // Atualizar localmente
                const notif = this.notificacoes.find(n => n.id === notificacaoId);
                if (notif) {
                    notif.lida = true;
                    this.renderizarNotificacoes();
                    this.atualizarContador();
                }
            }
        } catch (error) {
            console.error('Erro ao marcar notificação como lida:', error);
        }
    }

    async marcarTodasComoLidas() {
        try {
            const response = await fetch('/api/notificacoes/marcar-todas-lidas', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${getToken()}`
                }
            });

            if (response.ok) {
                // Atualizar localmente
                this.notificacoes.forEach(n => n.lida = true);
                this.renderizarNotificacoes();
                this.atualizarContador();
            }
        } catch (error) {
            console.error('Erro ao marcar todas como lidas:', error);
        }
    }

    navegarParaNotificacao(notificacao) {
        const dados = notificacao.dados_referencia || {};

        switch (notificacao.tipo) {
            case 'os_atrasada':
            case 'os_pronta':
                if (dados.os_id) {
                    window.location.href = `/os#view=${dados.os_id}`;
                } else {
                    window.location.href = '/os';
                }
                break;
            case 'estoque_critico':
                if (dados.produto_id) {
                    window.location.href = `/estoque#view=${dados.produto_id}`;
                } else {
                    window.location.href = '/estoque';
                }
                break;
            case 'cliente_novo':
                if (dados.cliente_id) {
                    window.location.href = `/clientes#view=${dados.cliente_id}`;
                } else {
                    window.location.href = '/clientes';
                }
                break;
            default:
                window.location.href = '/dashboard';
        }
    }

    verTodasNotificacoes() {
        // Marcar todas as notificações como lidas
        this.marcarTodasComoLidas();
        // Fechar o dropdown
        this.closeDropdown();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Método público para adicionar notificação manualmente (útil para testes)
    adicionarNotificacao(tipo, titulo, mensagem, dadosReferencia = {}) {
        // Este método pode ser usado para adicionar notificações via JavaScript
        console.log('Nova notificação:', { tipo, titulo, mensagem, dadosReferencia });
    }
}

// Função auxiliar para obter token (usando a mesma chave do auth.js)
function getToken() {
    return localStorage.getItem('ia_sistem_token') || sessionStorage.getItem('ia_sistem_token');
}

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('notificationBtn')) {
        window.notificationManager = new NotificationManager();
        console.log('✅ Sistema de notificações inicializado!');
    }
});
