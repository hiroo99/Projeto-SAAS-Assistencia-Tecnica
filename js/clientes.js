// ========================================
// CLIENTES.JS - Gerenciamento de Clientes
// ========================================
// Este arquivo contém todas as funções relacionadas ao módulo de clientes

// Array que mantém os clientes em memória durante a sessão
let clientesEmMemoria = [];

// ============================
// FUNÇÕES DE DADOS
// ============================

/**
 * Carrega todos os clientes da API
 * @returns {Promise<Array>} Array de clientes
 */
async function carregarClientes() {
  try {
    const clientes = await listarClientesApi();
    clientesEmMemoria = clientes || [];
  } catch (e) {
    clientesEmMemoria = [];
  }
  return clientesEmMemoria;
}

/**
 * (Mantida por compatibilidade – agora não faz nada além de retornar true)
 */
function salvarClientes() {
  return true;
}

/**
 * Adiciona um novo cliente via API
 * @param {object} cliente - Dados do cliente
 * @returns {Promise<object|null>} Cliente criado com ID ou null em caso de erro
 */
async function adicionarCliente(cliente) {
  try {
    const criado = await criarClienteApi(cliente);
    clientesEmMemoria.push(criado);
    console.log("✅ Cliente adicionado:", criado.nome);

    // Atualiza notificações se disponível
    if (window.notificationManager) {
      window.notificationManager.atualizarContador();
    }

    return criado;
  } catch (e) {
    console.error("❌ Erro ao adicionar cliente:", e);
    // Se o erro já tem uma mensagem amigável (vinda do backend), lança novamente
    // O código que chama essa função deve tratar o erro e exibir a mensagem
    throw e;
  }
}

/**
 * Atualiza um cliente existente via API
 * @param {string|number} id - ID do cliente
 * @param {object} dadosAtualizados - Novos dados do cliente
 * @returns {Promise<boolean>} true se atualizou com sucesso
 */
async function atualizarCliente(id, dadosAtualizados) {
  const indice = clientesEmMemoria.findIndex((c) => c.id === parseInt(id));

  if (indice === -1) {
    console.error("❌ Cliente não encontrado:", id);
    throw new Error("Cliente não encontrado");
  }

  try {
    const atualizado = await atualizarClienteApi(id, dadosAtualizados);
    clientesEmMemoria[indice] = atualizado;

    console.log("✅ Cliente atualizado:", atualizado.nome);
    return true;
  } catch (e) {
    console.error("❌ Erro ao atualizar cliente:", e);
    // Re-lança o erro para que o código que chama possa tratar
    throw e;
  }
}

/**
 * Busca um cliente por ID
 * @param {string|number} id - ID do cliente
 * @returns {object|null} Cliente encontrado ou null
 */
function buscarClientePorId(id) {
  return clientesEmMemoria.find((c) => c.id === parseInt(id)) || null;
}

/**
 * Busca clientes por termo (nome, CPF, telefone, email)
 * @param {string} termo - Termo de busca
 * @returns {Array} Array de clientes encontrados
 */
function buscarClientes(termo) {
  if (!termo || termo.trim() === "") {
    return clientesEmMemoria;
  }

  const termoLower = termo.toLowerCase();

  return clientesEmMemoria.filter((cliente) => {
    return (
      cliente.nome.toLowerCase().includes(termoLower) ||
      cliente.cpfCnpj.includes(termo) ||
      cliente.telefone.includes(termo) ||
      (cliente.email && cliente.email.toLowerCase().includes(termoLower))
    );
  });
}

// ============================
// FUNÇÕES DE VALIDAÇÃO
// ============================

/**
 * Valida CPF
 * @param {string} cpf - CPF a ser validado
 * @returns {boolean} true se válido
 */
function validarCPF(cpf) {
  cpf = cpf.replace(/[^\d]/g, "");

  if (cpf.length !== 11) return false;
  if (/^(\d)\1+$/.test(cpf)) return false; // Verifica se todos os dígitos são iguais

  // Validação do primeiro dígito
  let soma = 0;
  for (let i = 0; i < 9; i++) {
    soma += parseInt(cpf.charAt(i)) * (10 - i);
  }
  let resto = 11 - (soma % 11);
  let digitoVerificador1 = resto === 10 || resto === 11 ? 0 : resto;

  if (digitoVerificador1 !== parseInt(cpf.charAt(9))) return false;

  // Validação do segundo dígito
  soma = 0;
  for (let i = 0; i < 10; i++) {
    soma += parseInt(cpf.charAt(i)) * (11 - i);
  }
  resto = 11 - (soma % 11);
  let digitoVerificador2 = resto === 10 || resto === 11 ? 0 : resto;

  return digitoVerificador2 === parseInt(cpf.charAt(10));
}

/**
 * Valida CNPJ
 * @param {string} cnpj - CNPJ a ser validado
 * @returns {boolean} true se válido
 */
function validarCNPJ(cnpj) {
  cnpj = cnpj.replace(/[^\d]/g, "");

  if (cnpj.length !== 14) return false;
  if (/^(\d)\1+$/.test(cnpj)) return false;

  // Validação dos dígitos verificadores
  let tamanho = cnpj.length - 2;
  let numeros = cnpj.substring(0, tamanho);
  let digitos = cnpj.substring(tamanho);
  let soma = 0;
  let pos = tamanho - 7;

  for (let i = tamanho; i >= 1; i--) {
    soma += numeros.charAt(tamanho - i) * pos--;
    if (pos < 2) pos = 9;
  }

  let resultado = soma % 11 < 2 ? 0 : 11 - (soma % 11);
  if (resultado != digitos.charAt(0)) return false;

  tamanho = tamanho + 1;
  numeros = cnpj.substring(0, tamanho);
  soma = 0;
  pos = tamanho - 7;

  for (let i = tamanho; i >= 1; i--) {
    soma += numeros.charAt(tamanho - i) * pos--;
    if (pos < 2) pos = 9;
  }

  resultado = soma % 11 < 2 ? 0 : 11 - (soma % 11);
  return resultado == digitos.charAt(1);
}

/**
 * Valida formulário de cliente
 * @param {object} dados - Dados do formulário
 * @returns {object} {valido: boolean, erros: Array}
 */
function validarFormularioCliente(dados) {
  const erros = [];

  // Nome obrigatório
  if (!dados.nome || dados.nome.trim() === "") {
    erros.push("Nome é obrigatório");
  }

  // CPF/CNPJ obrigatório e válido
  if (!dados.cpfCnpj || dados.cpfCnpj.trim() === "") {
    erros.push("CPF/CNPJ é obrigatório");
  } else {
    const documento = dados.cpfCnpj.replace(/[^\d]/g, "");
    if (documento.length === 11) {
      if (!validarCPF(documento)) {
        erros.push("CPF inválido");
      }
    } else if (documento.length === 14) {
      if (!validarCNPJ(documento)) {
        erros.push("CNPJ inválido");
      }
    } else {
      erros.push("CPF/CNPJ deve ter 11 ou 14 dígitos");
    }
  }

  // Telefone obrigatório
  if (!dados.telefone || dados.telefone.trim() === "") {
    erros.push("Telefone é obrigatório");
  }

  // Email opcional, mas se preenchido deve ser válido
  if (dados.email && dados.email.trim() !== "") {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(dados.email)) {
      erros.push("Email inválido");
    }
  }

  return {
    valido: erros.length === 0,
    erros: erros,
  };
}

// ============================
// FUNÇÕES DE FORMATAÇÃO
// ============================

/**
 * Formata CPF/CNPJ
 * @param {string} valor - Valor a ser formatado
 * @returns {string} Valor formatado
 */
function formatarCpfCnpj(valor) {
  valor = valor.replace(/\D/g, "");

  // Limita a 14 dígitos (CNPJ)
  if (valor.length > 14) {
    valor = valor.substring(0, 14);
  }

  if (valor.length <= 11) {
    // Formata como CPF: 000.000.000-00
    valor = valor.replace(/(\d{3})(\d)/, "$1.$2");
    valor = valor.replace(/(\d{3})(\d)/, "$1.$2");
    valor = valor.replace(/(\d{3})(\d{1,2})$/, "$1-$2");
  } else {
    // Formata como CNPJ: 00.000.000/0000-00
    valor = valor.replace(/^(\d{2})(\d)/, "$1.$2");
    valor = valor.replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3");
    valor = valor.replace(/\.(\d{3})(\d)/, ".$1/$2");
    valor = valor.replace(/(\d{4})(\d)/, "$1-$2");
  }

  return valor;
}

/**
 * Formata telefone
 * @param {string} valor - Valor a ser formatado
 * @returns {string} Valor formatado
 */
function formatarTelefone(valor) {
  valor = valor.replace(/\D/g, "");

  // Limita a 11 dígitos (DDD + 9 + 8 dígitos)
  if (valor.length > 11) {
    valor = valor.substring(0, 11);
  }

  // Formato: (99) 9 9999-9999
  if (valor.length <= 11) {
    valor = valor.replace(/^(\d{2})(\d{1})(\d{4})(\d{4})$/, "($1) $2 $3-$4");
    // Para números menores, aplica formatação parcial
    if (valor.length >= 2) {
      valor = valor.replace(
        /^(\d{2})(\d{0,1})(\d{0,4})(\d{0,4})$/,
        function (match, ddd, nono, primeiros, segundos) {
          let result = `(${ddd}`;
          if (nono) result += `) ${nono}`;
          if (primeiros) result += ` ${primeiros}`;
          if (segundos) result += `-${segundos}`;
          return result;
        }
      );
    }
  }

  return valor;
}

// ============================
// INICIALIZAÇÃO
// ============================

// Carrega clientes ao iniciar
carregarClientes();
console.log("✅ clientes.js carregado com sucesso!");
console.log("📊 Total de clientes:", clientesEmMemoria.length);
