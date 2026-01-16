// ========================================
// ESTOQUE.JS - Gerenciamento de Estoque
// ========================================
// Este arquivo contém todas as funções relacionadas ao módulo de estoque

// Array que mantém os produtos em memória durante a sessão
let produtosEmMemoria = [];

// Variáveis globais
let produtosFiltrados = [];
let produtoAtual = null;
let paginaAtual = 1;
const itensPorPagina = 10;

// ============================
// FUNÇÕES DE DADOS
// ============================

/**
 * Carrega todos os produtos da API
 * @returns {Promise<Array>} Array de produtos
 */
async function carregarProdutos() {
    try {
        const produtos = await listarProdutosApi();
        produtosEmMemoria = produtos || [];
    } catch (e) {
        produtosEmMemoria = [];
    }
    return produtosEmMemoria;
}

/**
 * Adiciona um novo produto via API
 * @param {object} produto - Dados do produto
 * @returns {Promise<object>} Produto criado com ID
 */
async function adicionarProduto(produto) {
    try {
        // Prepara dados para API
        const dadosApi = {
            nome: produto.nome,
            categoria: produto.categoria,
            codigo: produto.codigo || gerarCodigoProduto(),
            descricao: produto.descricao || null,
            quantidade: parseInt(produto.quantidade) || 0,
            estoqueMinimo: parseInt(produto.estoqueMinimo) || 0,
            precoCusto: parseFloat(produto.precoCusto?.replace(/[^\d,]/g, '').replace(',', '.')) || 0,
            precoVenda: parseFloat(produto.precoVenda?.replace(/[^\d,]/g, '').replace(',', '.')) || 0,
            fornecedor: produto.fornecedor || null,
            localizacao: produto.localizacao || null,
        };

        const criado = await criarProdutoApi(dadosApi);
        produtosEmMemoria.push(criado);

        console.log('✅ Produto adicionado:', criado.nome);
        return criado;
    } catch (e) {
        console.error('❌ Erro ao adicionar produto:', e);
        // Re-lança o erro para que o código que chama possa tratar
        throw e;
    }
}

/**
 * Atualiza um produto existente via API
 * @param {string|number} id - ID do produto
 * @param {object} dadosAtualizados - Novos dados do produto
 * @returns {Promise<boolean>} true se atualizou com sucesso
 */
async function atualizarProduto(id, dadosAtualizados) {
    const indice = produtosEmMemoria.findIndex(p => p.id === parseInt(id));

    if (indice === -1) {
        console.error('❌ Produto não encontrado:', id);
        throw new Error('Produto não encontrado');
    }

    try {
        // Prepara dados para API (sem ID, timestamps)
        const dadosApi = {
            nome: dadosAtualizados.nome,
            categoria: dadosAtualizados.categoria,
            codigo: dadosAtualizados.codigo,
            descricao: dadosAtualizados.descricao || null,
            quantidade: parseInt(dadosAtualizados.quantidade) || 0,
            estoqueMinimo: parseInt(dadosAtualizados.estoqueMinimo) || 0,
            precoCusto: parseFloat(dadosAtualizados.precoCusto?.replace(/[^\d,]/g, '').replace(',', '.')) || 0,
            precoVenda: parseFloat(dadosAtualizados.precoVenda?.replace(/[^\d,]/g, '').replace(',', '.')) || 0,
            fornecedor: dadosAtualizados.fornecedor || null,
            localizacao: dadosAtualizados.localizacao || null,
        };

        const atualizado = await atualizarProdutoApi(id, dadosApi);
        produtosEmMemoria[indice] = atualizado;

        console.log('✅ Produto atualizado:', atualizado.nome);
        return true;
    } catch (e) {
        console.error('❌ Erro ao atualizar produto:', e);
        // Re-lança o erro para que o código que chama possa tratar
        throw e;
    }
}

/**
 * Remove um produto via API
 * @param {string|number} id - ID do produto
 * @returns {Promise<boolean>} true se removeu com sucesso
 */
async function removerProduto(id) {
    const indice = produtosEmMemoria.findIndex(p => p.id === parseInt(id));

    if (indice === -1) {
        console.error('❌ Produto não encontrado:', id);
        return false;
    }

    const nomeProduto = produtosEmMemoria[indice].nome;
    await deletarProdutoApi(id);
    produtosEmMemoria.splice(indice, 1);

    console.log('✅ Produto removido:', nomeProduto);
    return true;
}

/**
 * Busca um produto por ID
 */
function buscarProdutoPorId(id) {
    return produtosEmMemoria.find(p => p.id === parseInt(id)) || null;
}

/**
 * Busca produtos por termo
 */
function buscarProdutos(termo) {
    if (!termo || termo.trim() === '') {
        return produtosEmMemoria;
    }
    
    const termoLower = termo.toLowerCase();
    
    return produtosEmMemoria.filter(produto => {
        return (
            produto.nome.toLowerCase().includes(termoLower) ||
            produto.codigo.toLowerCase().includes(termoLower) ||
            produto.categoria.toLowerCase().includes(termoLower) ||
            (produto.descricao && produto.descricao.toLowerCase().includes(termoLower))
        );
    });
}

/**
 * Gera código do produto
 */
function gerarCodigoProduto() {
    const proximoNumero = produtosEmMemoria.length + 1;
    return `P${proximoNumero.toString().padStart(4, '0')}`;
}

/**
 * Calcula status do estoque
 */
function calcularStatusEstoque(quantidade, estoqueMinimo) {
    if (quantidade <= 0) return 'sem_estoque';
    if (quantidade <= estoqueMinimo) return 'critico';
    if (quantidade <= estoqueMinimo * 1.5) return 'baixo';
    return 'ok';
}

/**
 * Valida formulário de produto
 */
function validarFormularioProduto(dados) {
    const erros = [];
    
    if (!dados.nome || dados.nome.trim() === '') {
        erros.push('Nome do produto é obrigatório');
    }
    
    if (!dados.categoria || dados.categoria.trim() === '') {
        erros.push('Categoria é obrigatória');
    }
    
    if (!dados.codigo || dados.codigo.trim() === '') {
        erros.push('Código é obrigatório');
    }
    
    if (dados.quantidade < 0) {
        erros.push('Quantidade não pode ser negativa');
    }
    
    if (dados.estoqueMinimo < 0) {
        erros.push('Estoque mínimo não pode ser negativo');
    }
    
    if (dados.precoCusto < 0) {
        erros.push('Preço de custo não pode ser negativo');
    }
    
    if (dados.precoVenda < 0) {
        erros.push('Preço de venda não pode ser negativo');
    }
    
    return {
        valido: erros.length === 0,
        erros: erros
    };
}

// ============================
// FUNÇÕES DE INTERFACE
// ============================

/**
 * Atualiza as estatísticas na tela
 */
function atualizarEstatisticas() {
    const total = produtosEmMemoria.length;
    const valorTotal = produtosEmMemoria.reduce((total, p) => total + (p.quantidade * p.precoCusto), 0);
    const estoqueBaixo = produtosEmMemoria.filter(p => calcularStatusEstoque(p.quantidade, p.estoqueMinimo) === 'baixo').length;
    const estoqueCritico = produtosEmMemoria.filter(p => calcularStatusEstoque(p.quantidade, p.estoqueMinimo) === 'critico').length;

    document.getElementById('totalProdutos').textContent = total;
    document.getElementById('valorTotal').textContent = `R$ ${valorTotal.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    document.getElementById('estoqueBaixo').textContent = estoqueBaixo;
    document.getElementById('estoqueCritico').textContent = estoqueCritico;
}

/**
 * Renderiza a tabela de produtos
 */
function renderizarTabela() {
    const inicio = (paginaAtual - 1) * itensPorPagina;
    const fim = inicio + itensPorPagina;
    const produtosPagina = produtosFiltrados.slice(inicio, fim);

    const tbody = document.getElementById('productsTableBody');
    tbody.innerHTML = '';

    if (produtosPagina.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" style="text-align: center; padding: 40px; color: var(--gray-medium);">
                    <div style="font-size: 48px; margin-bottom: 20px;"><i class="bi bi-box-seam"></i></div>
                    <div>Nenhum produto encontrado</div>
                    <div style="font-size: 14px; margin-top: 10px;">
                        ${produtosEmMemoria.length === 0 ? 'Cadastre seu primeiro produto!' : 'Tente ajustar os filtros de busca.'}
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    produtosPagina.forEach(produto => {
        const row = document.createElement('tr');
        const status = calcularStatusEstoque(produto.quantidade, produto.estoqueMinimo);
        const valorTotal = produto.quantidade * produto.precoCusto;
        
        row.innerHTML = `
            <td><strong>${produto.codigo}</strong></td>
            <td>
                <div class="product-info">
                    <div class="product-img">${getIconeCategoria(produto.categoria)}</div>
                    <div>
                        <div class="product-name">${produto.nome}</div>
                        ${produto.descricao ? `<div class="product-desc">${produto.descricao.substring(0, 50)}${produto.descricao.length > 50 ? '...' : ''}</div>` : ''}
                    </div>
                </div>
            </td>
            <td>${produto.categoria}</td>
            <td class="quantidade-cell ${status === 'critico' ? 'critico' : status === 'baixo' ? 'baixo' : ''}">
                <strong>${produto.quantidade}</strong>
            </td>
            <td>${produto.estoqueMinimo}</td>
            <td>R$ ${produto.precoCusto.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
            <td>R$ ${valorTotal.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
            <td><span class="stock-badge ${status}">${getStatusText(status)}</span></td>
            <td>
                <div class="actions-cell">
                    <button class="action-btn-small btn-view" onclick="visualizarProduto('${produto.id}')" title="Visualizar">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="action-btn-small btn-edit" onclick="editarProduto('${produto.id}')" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="action-btn-small btn-delete" onclick="excluirProduto('${produto.id}')" title="Excluir">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Renderiza a paginação
 */
function renderizarPaginacao() {
    const totalPaginas = Math.ceil(produtosFiltrados.length / itensPorPagina);
    const pagination = document.getElementById('pagination');
    
    if (totalPaginas <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let paginacaoHTML = '<div class="pagination-controls">';
    
    // Botão anterior
    if (paginaAtual > 1) {
        paginacaoHTML += `<button class="pagination-btn" onclick="irParaPagina(${paginaAtual - 1})">‹ Anterior</button>`;
    }
    
    // Números das páginas
    for (let i = 1; i <= totalPaginas; i++) {
        if (i === paginaAtual) {
            paginacaoHTML += `<button class="pagination-btn active">${i}</button>`;
        } else {
            paginacaoHTML += `<button class="pagination-btn" onclick="irParaPagina(${i})">${i}</button>`;
        }
    }
    
    // Botão próximo
    if (paginaAtual < totalPaginas) {
        paginacaoHTML += `<button class="pagination-btn" onclick="irParaPagina(${paginaAtual + 1})">Próximo ›</button>`;
    }
    
    paginacaoHTML += '</div>';
    pagination.innerHTML = paginacaoHTML;
}

/**
 * Vai para uma página específica
 */
function irParaPagina(pagina) {
    paginaAtual = pagina;
    renderizarTabela();
    renderizarPaginacao();
}

/**
 * Aplica filtros de busca
 */
function aplicarFiltros() {
    const termoBusca = document.getElementById('searchInput').value.trim();
    const filtroCategoria = document.getElementById('categoryFilter').value;
    const filtroStatus = document.querySelector('.filter-btn.active[data-filter]')?.getAttribute('data-filter') || 'all';

    // Busca por termo
    let produtos = buscarProdutos(termoBusca);

    // Filtro por categoria
    if (filtroCategoria) {
        produtos = produtos.filter(p => p.categoria.toLowerCase() === filtroCategoria.toLowerCase());
    }

    // Filtro por status
    if (filtroStatus !== 'all') {
        produtos = produtos.filter(p => {
            const status = calcularStatusEstoque(p.quantidade, p.estoqueMinimo);
            return status === filtroStatus;
        });
    }

    produtosFiltrados = produtos;
    paginaAtual = 1;
    renderizarTabela();
    renderizarPaginacao();
}

/**
 * Limpa todos os filtros
 */
function limparFiltros() {
    document.getElementById('searchInput').value = '';
    document.getElementById('categoryFilter').value = '';
    document.querySelectorAll('.filter-btn[data-filter]').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector('.filter-btn[data-filter="all"]').classList.add('active');
    
    aplicarFiltros();
}

// ============================
// FUNÇÕES AUXILIARES
// ============================

/**
 * Retorna ícone da categoria
 */
function getIconeCategoria(categoria) {
    const icones = {
        'Telas': '<i class="bi bi-phone"></i>',
        'Baterias': '<i class="bi bi-battery"></i>',
        'Câmeras': '<i class="bi bi-camera"></i>',
        'Conectores': '<i class="bi bi-plug"></i>',
        'Alto-falantes': '<i class="bi bi-volume-up"></i>',
        'Outros': '<i class="bi bi-tools"></i>'
    };
    return icones[categoria] || '<i class="bi bi-box-seam"></i>';
}

/**
 * Retorna texto do status
 */
function getStatusText(status) {
    const statusMap = {
        'ok': 'OK',
        'baixo': 'Baixo',
        'critico': 'Crítico',
        'sem_estoque': 'Sem Estoque'
    };
    return statusMap[status] || status;
}

// ============================
// FUNÇÕES DE MODAL
// ============================

/**
 * Abre modal para novo produto ou edição
 */
function abrirModal(tipo, produtoId = null) {
    const modal = document.getElementById('modalProduto');
    const modalTitle = document.getElementById('modalTitle');
    const form = document.getElementById('formProduto');
    const submitBtn = document.getElementById('submitBtn');

    if (tipo === 'novoProduto') {
        modalTitle.textContent = 'Novo Produto';
        form.reset();
        document.getElementById('produtoId').value = '';
        document.getElementById('codigo').value = gerarCodigoProduto();
        submitBtn.textContent = 'Cadastrar Produto';
    } else if (tipo === 'editarProduto' && produtoId) {
        const produto = buscarProdutoPorId(produtoId);
        if (produto) {
            modalTitle.textContent = 'Editar Produto';
            preencherFormulario(produto);
            submitBtn.textContent = 'Atualizar Produto';
        }
    }

    modal.classList.add('active');
}

/**
 * Fecha todos os modais
 */
function fecharModal() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active');
    });
}

/**
 * Preenche formulário com dados do produto
 */
function preencherFormulario(produto) {
    document.getElementById('produtoId').value = produto.id;
    document.getElementById('codigo').value = produto.codigo;
    document.getElementById('categoria').value = produto.categoria;
    document.getElementById('nome').value = produto.nome;
    document.getElementById('descricao').value = produto.descricao || '';
    document.getElementById('quantidade').value = produto.quantidade;
    document.getElementById('estoqueMinimo').value = produto.estoqueMinimo;
    document.getElementById('precoCusto').value = `R$ ${produto.precoCusto.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    document.getElementById('precoVenda').value = `R$ ${produto.precoVenda.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    document.getElementById('fornecedor').value = produto.fornecedor || '';
    document.getElementById('localizacao').value = produto.localizacao || '';
}

// ============================
// FUNÇÕES DE CRUD
// ============================

/**
 * Visualiza detalhes do produto
 */
function visualizarProduto(id) {
    const produto = buscarProdutoPorId(id);
    if (!produto) return;

    produtoAtual = produto;
    const modal = document.getElementById('modalVisualizar');
    const detalhes = document.getElementById('produtoDetalhes');

    const status = calcularStatusEstoque(produto.quantidade, produto.estoqueMinimo);
    const valorTotal = produto.quantidade * produto.precoCusto;

    detalhes.innerHTML = `
        <div class="product-details">
            <div class="product-header">
                <div class="product-icon-large">${getIconeCategoria(produto.categoria)}</div>
                <div class="product-info-large">
                    <h3>${produto.nome}</h3>
                    <p class="product-category">${produto.categoria}</p>
                </div>
            </div>
            
            <div class="product-details-grid">
                <div class="detail-item">
                    <label>Código:</label>
                    <span>${produto.codigo}</span>
                </div>
                <div class="detail-item">
                    <label>Quantidade:</label>
                    <span class="${status === 'critico' ? 'critico' : status === 'baixo' ? 'baixo' : ''}">${produto.quantidade} unidades</span>
                </div>
                <div class="detail-item">
                    <label>Estoque Mínimo:</label>
                    <span>${produto.estoqueMinimo} unidades</span>
                </div>
                <div class="detail-item">
                    <label>Status:</label>
                    <span class="stock-badge ${status}">${getStatusText(status)}</span>
                </div>
                <div class="detail-item">
                    <label>Preço de Custo:</label>
                    <span>R$ ${produto.precoCusto.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>
                </div>
                <div class="detail-item">
                    <label>Preço de Venda:</label>
                    <span>R$ ${produto.precoVenda.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>
                </div>
                <div class="detail-item">
                    <label>Valor Total:</label>
                    <span>R$ ${valorTotal.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>
                </div>
                <div class="detail-item">
                    <label>Fornecedor:</label>
                    <span>${produto.fornecedor || 'Não informado'}</span>
                </div>
                <div class="detail-item">
                    <label>Localização:</label>
                    <span>${produto.localizacao || 'Não informado'}</span>
                </div>
                <div class="detail-item">
                    <label>Data de Cadastro:</label>
                    <span>${formatarDataHora(produto.dataCadastro)}</span>
                </div>
                ${produto.descricao ? `
                <div class="detail-item full-width">
                    <label>Descrição:</label>
                    <span>${produto.descricao}</span>
                </div>
                ` : ''}
            </div>
        </div>
    `;

    modal.classList.add('active');
}

/**
 * Edita produto
 */
function editarProduto(id) {
    abrirModal('editarProduto', id);
}

/**
 * Edita o produto atual (do modal de visualização)
 */
function editarProdutoAtual() {
    if (produtoAtual) {
        fecharModal();
        setTimeout(() => {
            editarProduto(produtoAtual.id);
        }, 300);
    }
}

/**
 * Exclui produto
 */
async function excluirProduto(id) {
    const produto = buscarProdutoPorId(id);
    if (!produto) return;

    if (confirm(`Tem certeza que deseja excluir o produto "${produto.nome}"?\n\nEsta ação não pode ser desfeita.`)) {
        try {
            await removerProduto(id);
            alert('Produto excluído com sucesso!');
            await carregarProdutos(); // Recarrega produtos após exclusão
            aplicarFiltros();
            atualizarEstatisticas();
        } catch (e) {
            alert('Erro ao excluir produto. Tente novamente.');
        }
    }
}

/**
 * Exporta lista de produtos
 */
function exportarProdutos() {
    if (produtosFiltrados.length === 0) {
        alert('Nenhum produto para exportar.');
        return;
    }

    let csv = 'Código,Nome,Categoria,Quantidade,Estoque Mínimo,Preço Custo,Preço Venda,Valor Total,Status,Fornecedor\n';
    
    produtosFiltrados.forEach(produto => {
        const status = calcularStatusEstoque(produto.quantidade, produto.estoqueMinimo);
        const valorTotal = produto.quantidade * produto.precoCusto;
        
        csv += `"${produto.codigo}","${produto.nome}","${produto.categoria}","${produto.quantidade}","${produto.estoqueMinimo}","R$ ${produto.precoCusto.toFixed(2)}","R$ ${produto.precoVenda.toFixed(2)}","R$ ${valorTotal.toFixed(2)}","${getStatusText(status)}","${produto.fornecedor || ''}"\n`;
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `produtos_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// ============================
// INICIALIZAÇÃO (agora chamada apenas pelo template)
// ============================

/**
 * Inicializa o módulo de estoque - deve ser chamada apenas após o DOM estar carregado
 */
async function initEstoque() {
    await carregarProdutos();
    aplicarFiltros();
    atualizarEstatisticas();
    console.log('✅ estoque.js carregado com sucesso!');
    console.log('📊 Total de produtos:', produtosEmMemoria.length);
}

// ============================
// EVENTOS
// ============================

// Evento de submit do formulário de produto
document.addEventListener('DOMContentLoaded', function() {
    const formProduto = document.getElementById('formProduto');
    if (formProduto) {
        formProduto.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const dados = Object.fromEntries(formData.entries());

            // Validação
            const validacao = validarFormularioProduto(dados);
            if (!validacao.valido) {
                alert('Erro na validação:\n' + validacao.erros.join('\n'));
                return;
            }

            const produtoId = document.getElementById('produtoId').value;

            try {
                if (produtoId) {
                    // Atualizar produto existente
                    await atualizarProduto(produtoId, dados);
                    alert('Produto atualizado com sucesso!');
                } else {
                    // Adicionar novo produto
                    await adicionarProduto(dados);
                    alert('Produto cadastrado com sucesso!');
                }
                fecharModal();
                await carregarProdutos(); // Recarrega produtos após operação
                aplicarFiltros();
                atualizarEstatisticas();
            } catch (e) {
                // Exibe a mensagem de erro do backend se disponível
                const mensagemErro = e.message || 'Erro ao processar a solicitação. Tente novamente.';
                alert('❌ Erro: ' + mensagemErro);
                console.error('Erro ao salvar produto:', e);
            }
        });
    }
});
