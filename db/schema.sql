-- SAADI - Schema inicial PostgreSQL
-- Script idempotente: pode rodar mais de uma vez sem quebrar.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS perfis (
    id BIGSERIAL PRIMARY KEY,
    nome VARCHAR(60) NOT NULL UNIQUE,
    descricao TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS permissoes (
    id BIGSERIAL PRIMARY KEY,
    chave VARCHAR(120) NOT NULL UNIQUE,
    descricao TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS perfil_permissoes (
    perfil_id BIGINT NOT NULL REFERENCES perfis(id) ON DELETE CASCADE,
    permissao_id BIGINT NOT NULL REFERENCES permissoes(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (perfil_id, permissao_id)
);

CREATE TABLE IF NOT EXISTS unidades (
    id BIGSERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    sigla VARCHAR(20) NOT NULL,
    cnpj VARCHAR(18) NOT NULL UNIQUE,
    email VARCHAR(160) NOT NULL,
    telefone VARCHAR(30),
    celular VARCHAR(30),
    rua VARCHAR(180),
    numero VARCHAR(20),
    complemento VARCHAR(80),
    cidade VARCHAR(120),
    estado CHAR(2),
    cep VARCHAR(9),
    diretor_nome VARCHAR(150),
    diretor_cpf VARCHAR(14),
    diretor_email VARCHAR(160),
    diretor_telefone VARCHAR(30),
    tipo_unidade VARCHAR(40),
    capacidade_estudantes INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'ativa' CHECK (status IN ('ativa', 'inativa', 'manutencao')),
    data_inicio_operacao DATE,
    observacoes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT uq_unidade_nome_sigla UNIQUE (nome, sigla)
);

CREATE TABLE IF NOT EXISTS usuarios (
    id BIGSERIAL PRIMARY KEY,
    unidade_id BIGINT REFERENCES unidades(id) ON DELETE SET NULL,
    perfil_id BIGINT NOT NULL REFERENCES perfis(id),
    nome_completo VARCHAR(150) NOT NULL,
    cpf VARCHAR(14) NOT NULL UNIQUE,
    email VARCHAR(160) NOT NULL UNIQUE,
    telefone VARCHAR(30),
    matricula VARCHAR(60) NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    departamento VARCHAR(80),
    status VARCHAR(20) NOT NULL DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo')),
    data_admissao DATE,
    enviar_email_boas_vindas BOOLEAN NOT NULL DEFAULT TRUE,
    ultimo_login_em TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS anos_letivos (
    id BIGSERIAL PRIMARY KEY,
    ano INTEGER NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'ativo' CHECK (status IN ('ativo', 'arquivado')),
    data_inicio DATE,
    data_fim DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_ano_valido CHECK (ano BETWEEN 2000 AND 2100)
);

CREATE TABLE IF NOT EXISTS categorias_neurodiversidade (
    id BIGSERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    descricao TEXT,
    ativa BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alunos (
    id BIGSERIAL PRIMARY KEY,
    unidade_id BIGINT NOT NULL REFERENCES unidades(id),
    nome_completo VARCHAR(150) NOT NULL,
    cpf VARCHAR(14) UNIQUE,
    data_nascimento DATE NOT NULL,
    endereco TEXT,
    responsavel_nome VARCHAR(150) NOT NULL,
    responsavel_telefone VARCHAR(30) NOT NULL,
    serie_turma VARCHAR(80),
    nivel_suporte SMALLINT CHECK (nivel_suporte IN (1, 2, 3)),
    status VARCHAR(20) NOT NULL DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS aluno_categorias (
    aluno_id BIGINT NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
    categoria_id BIGINT NOT NULL REFERENCES categorias_neurodiversidade(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (aluno_id, categoria_id)
);

CREATE TABLE IF NOT EXISTS laudos (
    id BIGSERIAL PRIMARY KEY,
    aluno_id BIGINT NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
    descricao TEXT NOT NULL,
    arquivo_nome VARCHAR(255),
    arquivo_caminho TEXT,
    mime_type VARCHAR(120),
    tamanho_bytes BIGINT,
    data_emissao DATE,
    profissional_responsavel VARCHAR(160),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS triagens (
    id BIGSERIAL PRIMARY KEY,
    aluno_id BIGINT NOT NULL REFERENCES alunos(id),
    psicopedagogo_id BIGINT NOT NULL REFERENCES usuarios(id),
    data_registro DATE NOT NULL,
    tipo_registro VARCHAR(30) NOT NULL CHECK (tipo_registro IN ('triagem', 'acompanhamento', 'concluido')),
    status VARCHAR(30) NOT NULL DEFAULT 'aguardando_entrevista'
        CHECK (status IN ('aguardando_entrevista', 'em_avaliacao', 'concluida', 'alta_prioridade')),
    descricao TEXT,
    evolucao TEXT,
    observacoes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS planos_acompanhamento (
    id BIGSERIAL PRIMARY KEY,
    aluno_id BIGINT NOT NULL REFERENCES alunos(id),
    psicopedagogo_id BIGINT NOT NULL REFERENCES usuarios(id),
    titulo VARCHAR(180) NOT NULL,
    objetivo_geral TEXT,
    estrategias TEXT,
    periodicidade VARCHAR(60),
    status VARCHAR(30) NOT NULL DEFAULT 'ativo'
        CHECK (status IN ('ativo', 'em_revisao', 'concluido', 'pendente_atualizacao')),
    data_inicio DATE,
    data_fim_prevista DATE,
    data_fim_real DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS plano_metas (
    id BIGSERIAL PRIMARY KEY,
    plano_id BIGINT NOT NULL REFERENCES planos_acompanhamento(id) ON DELETE CASCADE,
    descricao TEXT NOT NULL,
    indicador_sucesso TEXT,
    prazo DATE,
    status VARCHAR(30) NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente', 'em_andamento', 'atingida', 'nao_atingida')),
    ordem INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS encaminhamentos (
    id BIGSERIAL PRIMARY KEY,
    aluno_id BIGINT NOT NULL REFERENCES alunos(id),
    solicitante_id BIGINT NOT NULL REFERENCES usuarios(id),
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('interno', 'externo')),
    destino VARCHAR(140) NOT NULL,
    prioridade VARCHAR(10) NOT NULL CHECK (prioridade IN ('alta', 'media', 'baixa')),
    status VARCHAR(30) NOT NULL DEFAULT 'aberto' CHECK (status IN ('aberto', 'retorno_recebido', 'sem_retorno', 'concluido')),
    descricao TEXT NOT NULL,
    prazo_retorno DATE,
    data_retorno DATE,
    observacao_retorno TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS relatorios (
    id BIGSERIAL PRIMARY KEY,
    unidade_id BIGINT REFERENCES unidades(id),
    aluno_id BIGINT REFERENCES alunos(id),
    autor_id BIGINT NOT NULL REFERENCES usuarios(id),
    tipo VARCHAR(40) NOT NULL CHECK (tipo IN ('aluno', 'turma', 'unidade', 'consolidado', 'psicopedagogico')),
    origem VARCHAR(20) NOT NULL DEFAULT 'manual' CHECK (origem IN ('manual', 'automatico')),
    ano_referencia INTEGER,
    periodo_inicio DATE,
    periodo_fim DATE,
    titulo VARCHAR(180) NOT NULL,
    conteudo TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'rascunho' CHECK (status IN ('rascunho', 'publicado', 'arquivado')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS auditoria (
    id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT REFERENCES usuarios(id) ON DELETE SET NULL,
    acao VARCHAR(40) NOT NULL,
    entidade VARCHAR(80) NOT NULL,
    entidade_id BIGINT,
    detalhes JSONB,
    ip_origem VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS parametros_sistema (
    id BIGSERIAL PRIMARY KEY,
    chave VARCHAR(120) NOT NULL UNIQUE,
    valor_json JSONB NOT NULL,
    descricao TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usuarios_unidade ON usuarios(unidade_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_perfil ON usuarios(perfil_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_status ON usuarios(status);
CREATE INDEX IF NOT EXISTS idx_alunos_unidade ON alunos(unidade_id);
CREATE INDEX IF NOT EXISTS idx_alunos_status ON alunos(status);
CREATE INDEX IF NOT EXISTS idx_triagens_aluno ON triagens(aluno_id);
CREATE INDEX IF NOT EXISTS idx_triagens_status ON triagens(status);
CREATE INDEX IF NOT EXISTS idx_planos_aluno ON planos_acompanhamento(aluno_id);
CREATE INDEX IF NOT EXISTS idx_planos_status ON planos_acompanhamento(status);
CREATE INDEX IF NOT EXISTS idx_encaminhamentos_aluno ON encaminhamentos(aluno_id);
CREATE INDEX IF NOT EXISTS idx_encaminhamentos_status ON encaminhamentos(status);
CREATE INDEX IF NOT EXISTS idx_encaminhamentos_prazo ON encaminhamentos(prazo_retorno);
CREATE INDEX IF NOT EXISTS idx_relatorios_tipo ON relatorios(tipo);
CREATE INDEX IF NOT EXISTS idx_relatorios_ano ON relatorios(ano_referencia);
CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON auditoria(usuario_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_data ON auditoria(created_at DESC);

COMMIT;
