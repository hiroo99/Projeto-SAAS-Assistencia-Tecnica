-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Tempo de geração: 16/01/2026 às 04:50
-- Versão do servidor: 10.4.32-MariaDB
-- Versão do PHP: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Banco de dados: `assistencia_tecnica`
--

-- --------------------------------------------------------

--
-- Estrutura para tabela `clientes`
--

CREATE TABLE `clientes` (
  `id` int(11) NOT NULL,
  `nome` varchar(150) NOT NULL,
  `cpf_cnpj` varchar(14) NOT NULL,
  `tipo_pessoa` varchar(20) NOT NULL DEFAULT 'pessoa_fisica',
  `endereco` varchar(200) DEFAULT NULL,
  `email` varchar(120) DEFAULT NULL,
  `telefone` varchar(20) NOT NULL,
  `observacoes` text DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'ativo',
  `criado_em` datetime NOT NULL,
  `atualizado_em` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Despejando dados para a tabela `clientes`
--

INSERT INTO `clientes` (`id`, `nome`, `cpf_cnpj`, `tipo_pessoa`, `endereco`, `email`, `telefone`, `observacoes`, `status`, `criado_em`, `atualizado_em`) VALUES
(1, 'Hiro', '05893613252', 'pessoa_fisica', 'Av ali bem ali', 'teste@teste.com', '(91) 99334-5286', 'jbjb', 'ativo', '2025-12-05 00:58:10', '2025-12-05 00:58:10'),
(2, 'Obi wan', '59773339009', 'pessoa_fisica', NULL, 'obimestre@gmail.com', '(21) 222-2222', NULL, 'ativo', '2025-12-05 13:58:35', '2025-12-05 13:58:35'),
(3, 'Arroz', '76859664096', 'pessoa_fisica', NULL, 'obimestre@gmail.com', '(21) 222-2222', NULL, 'ativo', '2025-12-05 16:22:59', '2025-12-05 16:22:59'),
(4, 'Fulano', '74220716000130', 'pessoa_juridica', 'Rua 12', 'fulano12@gmail.com', '(91) 99276-4597', 'Cliente Empresarial', 'ativo', '2026-01-11 15:53:00', '2026-01-11 15:53:00'),
(5, 'Miguel santos', '04274005038', 'pessoa_fisica', 'Av. julio cesar, R. A, 11', 'miguel@gmail.com', '(99) 9999-9999', NULL, 'ativo', '2026-01-14 11:54:17', '2026-01-14 11:54:17'),
(6, 'Ciclano', '46017220047', 'pessoa_fisica', NULL, NULL, '91998873523', NULL, 'ativo', '2026-01-15 18:18:14', '2026-01-15 18:18:14'),
(7, 'fulano de tal', '28138260068', 'pessoa_fisica', NULL, NULL, '91998763629', NULL, 'ativo', '2026-01-15 23:23:35', '2026-01-15 23:23:35');

-- --------------------------------------------------------

--
-- Estrutura para tabela `notificacoes`
--

CREATE TABLE `notificacoes` (
  `id` int(11) NOT NULL,
  `tipo` varchar(50) NOT NULL,
  `titulo` varchar(200) NOT NULL,
  `mensagem` text NOT NULL,
  `dados_referencia` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`dados_referencia`)),
  `lida` tinyint(1) DEFAULT NULL,
  `prioridade` varchar(20) DEFAULT NULL,
  `usuario_id` int(11) NOT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Despejando dados para a tabela `notificacoes`
--

INSERT INTO `notificacoes` (`id`, `tipo`, `titulo`, `mensagem`, `dados_referencia`, `lida`, `prioridade`, `usuario_id`, `criado_em`, `atualizado_em`) VALUES
(1, 'cliente_novo', 'Novo Cliente Cadastrado', 'Ciclano foi adicionado à base de dados.', '{\"cliente_id\": 6}', 0, 'baixa', 1, '2026-01-15 18:18:14', '2026-01-15 18:18:14'),
(2, 'cliente_novo', 'Novo Cliente Cadastrado', 'fulano de tal foi adicionado à base de dados.', '{\"cliente_id\": 7}', 0, 'baixa', 1, '2026-01-15 23:23:35', '2026-01-15 23:23:35');

-- --------------------------------------------------------

--
-- Estrutura para tabela `ordens_servico`
--

CREATE TABLE `ordens_servico` (
  `id` int(11) NOT NULL,
  `numero_os` varchar(20) NOT NULL,
  `cliente_id` int(11) NOT NULL,
  `tipo_aparelho` varchar(50) NOT NULL,
  `marca_modelo` varchar(100) NOT NULL,
  `imei_serial` varchar(100) DEFAULT NULL,
  `cor_aparelho` varchar(50) DEFAULT NULL,
  `problema_relatado` varchar(400) NOT NULL,
  `diagnostico_tecnico` varchar(400) DEFAULT NULL,
  `prazo_estimado` int(11) NOT NULL DEFAULT 3,
  `valor_orcamento` decimal(10,2) DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'aguardando',
  `prioridade` varchar(20) NOT NULL DEFAULT 'normal',
  `observacoes` text DEFAULT NULL,
  `criado_em` datetime NOT NULL,
  `atualizado_em` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Despejando dados para a tabela `ordens_servico`
--

INSERT INTO `ordens_servico` (`id`, `numero_os`, `cliente_id`, `tipo_aparelho`, `marca_modelo`, `imei_serial`, `cor_aparelho`, `problema_relatado`, `diagnostico_tecnico`, `prazo_estimado`, `valor_orcamento`, `status`, `prioridade`, `observacoes`, `criado_em`, `atualizado_em`) VALUES
(5, '#OS0005', 2, 'smartphone', 'Xioami Redmi ', '', 'Branco', 'tela quebrada', '', 3, 80.00, 'entregue', 'normal', '', '2026-01-11 14:26:46', '2026-01-11 14:44:13'),
(6, '#OS0006', 1, 'outro', 'Fone de Ouvido', '', 'branco', 'Bateria', 'Troca de bateria', 1, 25.00, 'entregue', 'alta', '', '2026-01-11 14:31:55', '2026-01-11 14:44:18'),
(8, '#OS0008', 4, 'desktop', 'Placa-Mãe MSI', '435673454', '', 'Problemas no barramento', '', 4, 199.99, 'aguardando', 'alta', '', '2026-01-11 14:41:03', '2026-01-11 14:41:03'),
(9, '#OS0009', 1, 'tablet', 'iPad Air', '', 'Branco', 'Trincamento', '', 2, 49.99, 'aguardando', 'urgente', '', '2026-01-11 14:41:52', '2026-01-11 14:41:52'),
(10, '#OS0010', 5, 'tablet', 'Alienware 16', '', '', 'Teclado', 'em Analise pelo técnico', 3, 50000.00, 'entregue', 'normal', '', '2026-01-11 14:43:43', '2026-01-14 16:37:20'),
(11, '#OS0011', 5, 'smartphone', 'iphone 8', NULL, NULL, 'botão de volume não esta funcionando', NULL, 3, NULL, 'aguardando', 'normal', '[IA] Resumo: **Resumo técnico do problema:**\n\n- **Componente afetado:** Botão de controle de volume (hardware).\n- **Sintoma:** Falha no funcionamento (não responde a comandos de aumento/diminuição de volume).\n- **Possíveis causas:**\n  - Desgaste mecânico (mola, contato interno).\n  - Oxidação ou sujeira nos contatos.\n  - Falha no circuito de controle (flexível, PCB).\n  - Problema de firmware/software (driver, sistema operacional).\n- **Diagnóstico recomendado:**\n  - Teste de continuidade (multímetro) nos contatos do botão.\n  - Inspeção visual de danos físicos ou corrosão.\n  - Verificação de atualizações de software/drivers.\n  - Substituição do componente (se necessário).\n\n**Ação imediata:** Isolar causa (hardware vs. software) antes de reparo.', '2026-01-14 14:37:11', '2026-01-14 14:37:17'),
(12, '#OS0012', 3, 'notebook', 'dell', '', 'prata', 'o aparelho notbook apresentou tela azul e não está ligando', 'Provável falha na memória RAM ou slot danificado.\n\nVerificar conexão e oxidação nos contatos da RAM.\n\nSuspeitos principais:\n1) RAM defeituosa – Testar: troca por módulo conhecido bom\n2) Slot de memória danificado – Testar: inserir RAM em outro slot', 3, 100.00, 'aguardando', 'normal', '[IA] Resumo: **Resumo Técnico do Problema:**\n\n- **Sintoma:** *Tela Azul da Morte (BSOD)* seguida de **falha no boot** (notebook não liga).\n- **Possíveis Causas:**\n  - **Hardware:** Falha na RAM, GPU, HD/SSD, superaquecimento ou curto-circuito.\n  - **Software:** Corrupção do sistema operacional, drivers incompatíveis ou atualização mal-sucedida.\n  - **Firmware:** BIOS/UEFI desatualizada ou corrompida.\n- **Diagnóstico Recomendado:**\n  1. **Teste de hardware:** Verificar RAM (memtest), HD/SSD (SMART), e conexões internas.\n  2. **Modo de segurança:** Tentar inicialização em *Safe Mode* para descartar falhas de software.\n  3. **Recuperação:** Usar mídia de instalação do SO para reparo ou restauração.\n  4. **Logs:** Analisar *dump files* (`.dmp`) do BSOD para identificar o código de erro.\n\n**Ação Imediata:** Desconectar periféricos, testar fonte de alimentação e verificar sinais de vida (ventoinha, LEDs).', '2026-01-14 19:47:34', '2026-01-14 19:48:34'),
(13, '#OS0013', 4, 'smartphone', 'samsung a15', '', 'Rosa', 'tela trincada e ', 'Possível dano no display e/ou touch por impacto físico.\n\nVerificar continuidade do flex do display com multímetro.\n\nSuspeitos principais:\n1) Vidro trincado + touch inoperante – Testar: substituir conjunto display\n2) Conector do flex danificado – Testar: limpar e reconectar flex', 3, 200.00, 'entregue', 'alta', '[IA] Resumo: **Resumo técnico do problema:**\n\n- **Defeito principal:** Tela trincada (fissuras visíveis no display).\n- **Possíveis causas:**\n  - Impacto mecânico (queda, pressão excessiva).\n  - Defeito estrutural (vidro ou camadas internas danificadas).\n  - Tensão térmica (aquecimento irregular).\n- **Sintomas associados:**\n  - Distorção visual (linhas, manchas ou áreas inoperantes).\n  - Comprometimento da sensibilidade ao toque (se aplicável).\n  - Risco de danos adicionais (umidade, poeira infiltrada).\n- **Ação recomendada:** Substituição do módulo de tela ou reparo especializado, dependendo da extensão do dano.\n\n*Nota:* Avaliar integridade do *frame* e componentes adjacentes para evitar recorrência.', '2026-01-14 19:52:52', '2026-01-14 20:40:01');

-- --------------------------------------------------------

--
-- Estrutura para tabela `produtos_estoque`
--

CREATE TABLE `produtos_estoque` (
  `id` int(11) NOT NULL,
  `codigo` varchar(20) NOT NULL,
  `nome` varchar(150) NOT NULL,
  `categoria` varchar(50) NOT NULL,
  `descricao` text DEFAULT NULL,
  `quantidade` int(11) NOT NULL DEFAULT 0,
  `estoque_minimo` int(11) NOT NULL DEFAULT 0,
  `preco_custo` decimal(10,2) NOT NULL DEFAULT 0.00,
  `preco_venda` decimal(10,2) NOT NULL DEFAULT 0.00,
  `fornecedor` varchar(150) DEFAULT NULL,
  `localizacao` varchar(100) DEFAULT NULL,
  `criado_em` datetime NOT NULL,
  `atualizado_em` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Despejando dados para a tabela `produtos_estoque`
--

INSERT INTO `produtos_estoque` (`id`, `codigo`, `nome`, `categoria`, `descricao`, `quantidade`, `estoque_minimo`, `preco_custo`, `preco_venda`, `fornecedor`, `localizacao`, `criado_em`, `atualizado_em`) VALUES
(1, 'P0001', 'tela 1', 'Telas', NULL, 9, 5, 12.22, 40.00, NULL, NULL, '2025-12-05 16:36:30', '2026-01-10 14:36:53'),
(2, 'P0002', 'Conector USB -C', 'Conectores', 'conector original samsung', 4, 5, 80.00, 110.00, NULL, NULL, '2025-12-05 16:38:59', '2026-01-11 01:46:38'),
(3, 'P0003', 'Bateria de Lítio', 'Baterias', 'Bateria para celular', 0, 5, 49.99, 80.00, 'BaterryAI', 'Pratereira A2', '2026-01-13 18:24:06', '2026-01-13 18:24:06');

-- --------------------------------------------------------

--
-- Estrutura para tabela `usuarios`
--

CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL,
  `usuario` varchar(50) NOT NULL,
  `senha_hash` varchar(255) NOT NULL,
  `nome` varchar(120) NOT NULL,
  `email` varchar(120) DEFAULT NULL,
  `ativo` tinyint(1) NOT NULL DEFAULT 1,
  `criado_em` datetime NOT NULL,
  `atualizado_em` datetime NOT NULL,
  `cpf` varchar(14) DEFAULT NULL,
  `telefone` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Despejando dados para a tabela `usuarios`
--

INSERT INTO `usuarios` (`id`, `usuario`, `senha_hash`, `nome`, `email`, `ativo`, `criado_em`, `atualizado_em`, `cpf`, `telefone`) VALUES
(1, 'admin', 'scrypt:32768:8:1$A0dFxYD4FAWNrhxH$49d47d4bf69e136bb8030b2d437af9a2b875d1f8a8c98508afac7a619c072b91b1437f2a231e24fa345e11db6d8a55e97666424f3b793bf403004884020b068a', 'Administrador', 'admin@iasistem.com', 1, '2026-01-10 22:52:38', '2026-01-10 22:52:38', NULL, NULL);

--
-- Índices para tabelas despejadas
--

--
-- Índices de tabela `clientes`
--
ALTER TABLE `clientes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_clientes_cpf_cnpj` (`cpf_cnpj`),
  ADD KEY `idx_clientes_nome` (`nome`),
  ADD KEY `idx_clientes_email` (`email`);

--
-- Índices de tabela `notificacoes`
--
ALTER TABLE `notificacoes`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_notificacoes_lida` (`lida`),
  ADD KEY `ix_notificacoes_tipo` (`tipo`),
  ADD KEY `ix_notificacoes_usuario_id` (`usuario_id`);

--
-- Índices de tabela `ordens_servico`
--
ALTER TABLE `ordens_servico`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_ordens_numero_os` (`numero_os`),
  ADD KEY `idx_ordens_cliente_id` (`cliente_id`),
  ADD KEY `idx_ordens_status` (`status`),
  ADD KEY `idx_ordens_prioridade` (`prioridade`);

--
-- Índices de tabela `produtos_estoque`
--
ALTER TABLE `produtos_estoque`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_produtos_codigo` (`codigo`),
  ADD KEY `idx_produtos_categoria` (`categoria`);

--
-- Índices de tabela `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_usuarios_usuario` (`usuario`),
  ADD UNIQUE KEY `uq_usuarios_email` (`email`),
  ADD UNIQUE KEY `uq_usuarios_cpf` (`cpf`);

--
-- AUTO_INCREMENT para tabelas despejadas
--

--
-- AUTO_INCREMENT de tabela `clientes`
--
ALTER TABLE `clientes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT de tabela `notificacoes`
--
ALTER TABLE `notificacoes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de tabela `ordens_servico`
--
ALTER TABLE `ordens_servico`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT de tabela `produtos_estoque`
--
ALTER TABLE `produtos_estoque`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de tabela `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Restrições para tabelas despejadas
--

--
-- Restrições para tabelas `notificacoes`
--
ALTER TABLE `notificacoes`
  ADD CONSTRAINT `notificacoes_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Restrições para tabelas `ordens_servico`
--
ALTER TABLE `ordens_servico`
  ADD CONSTRAINT `fk_ordens_cliente` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`) ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
