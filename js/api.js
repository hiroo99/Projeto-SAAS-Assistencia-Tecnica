// ========================================
// API.JS - Cliente genérico para a API Flask
// ========================================

const API_BASE_URL = "http://127.0.0.1:5000";

async function apiRequest(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  const config = adicionarAuthHeader({
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  try {
    const resp = await fetch(url, config);

    if (!resp.ok) {
      const contentType = resp.headers.get("content-type");
      let texto = await resp.text();

      // Tenta fazer parse como JSON primeiro
      let erroJson = null;
      try {
        erroJson = JSON.parse(texto);
      } catch (e) {
        // Se não for JSON, verifica se é HTML
        if (contentType && contentType.includes("text/html")) {
          console.error(
            "Erro na API - Recebeu HTML em vez de JSON",
            resp.status
          );
          // Tenta extrair mensagem de erro do HTML se possível
          const match =
            texto.match(/<p class="errormsg">([^<]+)<\/p>/i) ||
            texto.match(/<h1>([^<]+)<\/h1>/i);
          const mensagemErro = match ? match[1].trim() : null;
          throw new Error(
            mensagemErro ||
              `Erro no servidor (${resp.status}). O servidor retornou HTML em vez de JSON.`
          );
        }
      }

      // Se conseguiu fazer parse como JSON, usa a mensagem de erro
      if (erroJson) {
        const mensagemErro = erroJson.mensagem || erroJson.erro || texto;
        const erroPersonalizado = new Error(mensagemErro);
        erroPersonalizado.status = resp.status;
        erroPersonalizado.dados = erroJson;
        console.error("Erro na API", resp.status, erroJson);
        throw erroPersonalizado;
      }

      // Fallback: usa o texto como está
      console.error("Erro na API", resp.status, texto);
      throw new Error(texto || `Erro na API (${resp.status})`);
    }

    if (resp.status === 204) {
      return null;
    }

    return await resp.json();
  } catch (e) {
    // Se já é um erro nosso (com status), apenas re-lança
    if (e.status) {
      throw e;
    }

    console.error("Falha ao chamar API:", e);

    // Verifica se é erro de rede/conexão
    if (
      e.message.includes("fetch") ||
      e.message.includes("Failed to fetch") ||
      e.message.includes("NetworkError")
    ) {
      alert(
        "Não foi possível comunicar com o servidor. Verifique se o Flask está rodando."
      );
      throw e;
    }

    // Para outros erros, re-lança para que o código chamador possa tratar
    throw e;
  }
}

// ========================================
// CLIENTES - Funções específicas
// ========================================

async function listarClientesApi() {
  return await apiRequest("/api/clientes");
}

async function criarClienteApi(dados) {
  return await apiRequest("/api/clientes", {
    method: "POST",
    body: JSON.stringify(dados),
  });
}

async function atualizarClienteApi(id, dados) {
  return await apiRequest(`/api/clientes/${id}`, {
    method: "PUT",
    body: JSON.stringify(dados),
  });
}

async function deletarClienteApi(id) {
  await apiRequest(`/api/clientes/${id}`, {
    method: "DELETE",
  });
  return true;
}

// ========================================
// ESTOQUE - Funções específicas
// ========================================

async function listarProdutosApi() {
  return await apiRequest("/api/estoque");
}

async function criarProdutoApi(dados) {
  return await apiRequest("/api/estoque", {
    method: "POST",
    body: JSON.stringify(dados),
  });
}

async function atualizarProdutoApi(id, dados) {
  return await apiRequest(`/api/estoque/${id}`, {
    method: "PUT",
    body: JSON.stringify(dados),
  });
}

async function deletarProdutoApi(id) {
  await apiRequest(`/api/estoque/${id}`, {
    method: "DELETE",
  });
  return true;
}

// ========================================
// OS - Funções específicas
// ========================================

async function listarOSApi() {
  return await apiRequest("/api/os");
}

async function criarOSApi(dados) {
  return await apiRequest("/api/os", {
    method: "POST",
    body: JSON.stringify(dados),
  });
}

async function atualizarOSApi(id, dados) {
  return await apiRequest(`/api/os/${id}`, {
    method: "PUT",
    body: JSON.stringify(dados),
  });
}

async function deletarOSApi(id) {
  await apiRequest(`/api/os/${id}`, {
    method: "DELETE",
  });
  return true;
}

// ========================================
// AI - Funções específicas
// ========================================

async function gerarDiagnosticoApi(dados) {
  return await apiRequest("/api/ai/diagnostico", {
    method: "POST",
    body: JSON.stringify(dados),
  });
}
