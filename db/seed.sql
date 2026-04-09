-- SAADI - Seeds iniciais (idempotente)

BEGIN;

INSERT INTO perfis (nome, descricao)
VALUES
    ('administrador', 'Acesso total ao sistema'),
    ('secretaria', 'Gestao de alunos e encaminhamentos da unidade'),
    ('psicopedagogo', 'Triagens, planos e relatorios psicopedagogicos'),
    ('professor', 'Acesso pedagogico restrito'),
    ('diretor', 'Acompanhamento e visao gerencial da unidade')
ON CONFLICT (nome) DO NOTHING;

INSERT INTO permissoes (chave, descricao)
VALUES
    ('usuarios.criar', 'Criar usuarios'),
    ('usuarios.listar', 'Listar usuarios'),
    ('usuarios.atualizar', 'Atualizar usuarios'),
    ('usuarios.remover', 'Remover usuarios'),
    ('unidades.criar', 'Criar unidades'),
    ('unidades.listar', 'Listar unidades'),
    ('unidades.atualizar', 'Atualizar unidades'),
    ('unidades.remover', 'Remover unidades'),
    ('alunos.criar', 'Criar alunos'),
    ('alunos.listar', 'Listar alunos'),
    ('alunos.atualizar', 'Atualizar alunos'),
    ('alunos.remover', 'Remover alunos'),
    ('triagens.criar', 'Criar triagens'),
    ('triagens.listar', 'Listar triagens'),
    ('triagens.atualizar', 'Atualizar triagens'),
    ('planos.criar', 'Criar planos de acompanhamento'),
    ('planos.listar', 'Listar planos de acompanhamento'),
    ('planos.atualizar', 'Atualizar planos de acompanhamento'),
    ('encaminhamentos.criar', 'Criar encaminhamentos'),
    ('encaminhamentos.listar', 'Listar encaminhamentos'),
    ('encaminhamentos.atualizar', 'Atualizar encaminhamentos'),
    ('relatorios.criar', 'Criar relatorios'),
    ('relatorios.listar', 'Listar relatorios'),
    ('auditoria.listar', 'Listar auditoria'),
    ('parametros.gerenciar', 'Gerenciar parametros do sistema')
ON CONFLICT (chave) DO NOTHING;

-- Administrador recebe todas as permissoes
INSERT INTO perfil_permissoes (perfil_id, permissao_id)
SELECT p.id, pm.id
FROM perfis p
CROSS JOIN permissoes pm
WHERE p.nome = 'administrador'
ON CONFLICT DO NOTHING;

-- Secretaria
INSERT INTO perfil_permissoes (perfil_id, permissao_id)
SELECT p.id, pm.id
FROM perfis p
JOIN permissoes pm ON pm.chave IN (
    'alunos.criar', 'alunos.listar', 'alunos.atualizar', 'alunos.remover',
    'encaminhamentos.criar', 'encaminhamentos.listar', 'encaminhamentos.atualizar',
    'relatorios.listar'
)
WHERE p.nome = 'secretaria'
ON CONFLICT DO NOTHING;

-- Psicopedagogo
INSERT INTO perfil_permissoes (perfil_id, permissao_id)
SELECT p.id, pm.id
FROM perfis p
JOIN permissoes pm ON pm.chave IN (
    'alunos.listar',
    'triagens.criar', 'triagens.listar', 'triagens.atualizar',
    'planos.criar', 'planos.listar', 'planos.atualizar',
    'encaminhamentos.criar', 'encaminhamentos.listar', 'encaminhamentos.atualizar',
    'relatorios.criar', 'relatorios.listar'
)
WHERE p.nome = 'psicopedagogo'
ON CONFLICT DO NOTHING;

INSERT INTO categorias_neurodiversidade (nome, descricao)
VALUES
    ('Autismo', 'Transtorno do Espectro Autista (TEA)'),
    ('TDAH', 'Transtorno de Deficit de Atencao e Hiperatividade'),
    ('Dislexia', 'Transtorno especifico de aprendizagem'),
    ('Deficiencia Auditiva', 'Surdez e deficiencia auditiva'),
    ('Altas Habilidades', 'Superdotacao e altas habilidades')
ON CONFLICT (nome) DO NOTHING;

INSERT INTO parametros_sistema (chave, valor_json, descricao)
VALUES
    ('email.smtp', '{"server":"smtp.gmail.com","port":587,"tls":true}', 'Configuracao SMTP padrao'),
    ('sistema.geral', '{"instituicao":"SAADI","timeout_sessao_min":30}', 'Configuracoes gerais do sistema'),
    ('anos_letivos.ativos', '[{"ano":2026,"status":"ativo"}]', 'Ano letivo inicial')
ON CONFLICT (chave) DO NOTHING;

COMMIT;
