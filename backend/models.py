from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from backend.extensions import db


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.BigInteger, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())


perfil_permissoes = db.Table(
    'perfil_permissoes',
    db.Column('perfil_id', db.BigInteger, db.ForeignKey('perfis.id', ondelete='CASCADE'), primary_key=True),
    db.Column('permissao_id', db.BigInteger, db.ForeignKey('permissoes.id', ondelete='CASCADE'), primary_key=True),
    db.Column('created_at', db.DateTime(timezone=True), nullable=False, server_default=db.func.now()),
)

aluno_categorias = db.Table(
    'aluno_categorias',
    db.Column('aluno_id', db.BigInteger, db.ForeignKey('alunos.id', ondelete='CASCADE'), primary_key=True),
    db.Column('categoria_id', db.BigInteger, db.ForeignKey('categorias_neurodiversidade.id'), primary_key=True),
    db.Column('created_at', db.DateTime(timezone=True), nullable=False, server_default=db.func.now()),
)


class Perfil(BaseModel):
    __tablename__ = 'perfis'

    nome = db.Column(db.String(60), nullable=False, unique=True)
    descricao = db.Column(db.Text)


class Permissao(BaseModel):
    __tablename__ = 'permissoes'

    chave = db.Column(db.String(120), nullable=False, unique=True)
    descricao = db.Column(db.Text)


class Unidade(BaseModel):
    __tablename__ = 'unidades'
    __table_args__ = (
        UniqueConstraint('nome', 'sigla', name='uq_unidade_nome_sigla'),
    )

    nome = db.Column(db.String(150), nullable=False)
    sigla = db.Column(db.String(20), nullable=False)
    cnpj = db.Column(db.String(18), nullable=False, unique=True)
    email = db.Column(db.String(160), nullable=False)
    telefone = db.Column(db.String(30))
    celular = db.Column(db.String(30))
    rua = db.Column(db.String(180))
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(80))
    cidade = db.Column(db.String(120))
    estado = db.Column(db.String(2))
    cep = db.Column(db.String(9))
    diretor_nome = db.Column(db.String(150))
    diretor_cpf = db.Column(db.String(14))
    diretor_email = db.Column(db.String(160))
    diretor_telefone = db.Column(db.String(30))
    tipo_unidade = db.Column(db.String(40))
    capacidade_estudantes = db.Column(db.Integer)
    status = db.Column(db.String(20), nullable=False, default='ativa')
    data_inicio_operacao = db.Column(db.Date)
    observacoes = db.Column(db.Text)
    deleted_at = db.Column(db.DateTime(timezone=True))


class Usuario(BaseModel):
    __tablename__ = 'usuarios'

    unidade_id = db.Column(db.BigInteger, db.ForeignKey('unidades.id', ondelete='SET NULL'))
    perfil_id = db.Column(db.BigInteger, db.ForeignKey('perfis.id'), nullable=False)
    nome_completo = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), nullable=False, unique=True)
    email = db.Column(db.String(160), nullable=False, unique=True)
    telefone = db.Column(db.String(30))
    matricula = db.Column(db.String(60), nullable=False, unique=True)
    senha_hash = db.Column(db.Text, nullable=False)
    departamento = db.Column(db.String(80))
    status = db.Column(db.String(20), nullable=False, default='ativo')
    data_admissao = db.Column(db.Date)
    enviar_email_boas_vindas = db.Column(db.Boolean, nullable=False, default=True)
    ultimo_login_em = db.Column(db.DateTime(timezone=True))
    deleted_at = db.Column(db.DateTime(timezone=True))

    perfil = db.relationship('Perfil', backref=db.backref('usuarios', lazy=True))
    unidade = db.relationship('Unidade', backref=db.backref('usuarios', lazy=True))


class AnoLetivo(BaseModel):
    __tablename__ = 'anos_letivos'
    __table_args__ = (
        CheckConstraint('ano BETWEEN 2000 AND 2100', name='ck_ano_valido'),
    )

    ano = db.Column(db.Integer, nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default='ativo')
    data_inicio = db.Column(db.Date)
    data_fim = db.Column(db.Date)


class CategoriaNeurodiversidade(BaseModel):
    __tablename__ = 'categorias_neurodiversidade'

    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    ativa = db.Column(db.Boolean, nullable=False, default=True)


class Aluno(BaseModel):
    __tablename__ = 'alunos'
    __table_args__ = (
        CheckConstraint('nivel_suporte IN (1, 2, 3)', name='ck_nivel_suporte'),
    )

    unidade_id = db.Column(db.BigInteger, db.ForeignKey('unidades.id'), nullable=False)
    nome_completo = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), unique=True)
    data_nascimento = db.Column(db.Date, nullable=False)
    endereco = db.Column(db.Text)
    responsavel_nome = db.Column(db.String(150), nullable=False)
    responsavel_telefone = db.Column(db.String(30), nullable=False)
    serie_turma = db.Column(db.String(80))
    nivel_suporte = db.Column(db.SmallInteger)
    status = db.Column(db.String(20), nullable=False, default='ativo')
    deleted_at = db.Column(db.DateTime(timezone=True))

    unidade = db.relationship('Unidade', backref=db.backref('alunos', lazy=True))
    categorias = db.relationship('CategoriaNeurodiversidade', secondary=aluno_categorias, lazy='subquery', backref='alunos')


class Laudo(BaseModel):
    __tablename__ = 'laudos'

    aluno_id = db.Column(db.BigInteger, db.ForeignKey('alunos.id', ondelete='CASCADE'), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    arquivo_nome = db.Column(db.String(255))
    arquivo_caminho = db.Column(db.Text)
    mime_type = db.Column(db.String(120))
    tamanho_bytes = db.Column(db.BigInteger)
    data_emissao = db.Column(db.Date)
    profissional_responsavel = db.Column(db.String(160))
    aluno = db.relationship('Aluno', backref=db.backref('laudos', lazy=True))


class Triagem(BaseModel):
    __tablename__ = 'triagens'

    aluno_id = db.Column(db.BigInteger, db.ForeignKey('alunos.id'), nullable=False)
    psicopedagogo_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    data_registro = db.Column(db.Date, nullable=False)
    tipo_registro = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(30), nullable=False, default='aguardando_entrevista')
    descricao = db.Column(db.Text)
    evolucao = db.Column(db.Text)
    observacoes = db.Column(db.Text)

    aluno = db.relationship('Aluno', backref=db.backref('triagens', lazy=True))
    psicopedagogo = db.relationship('Usuario', foreign_keys=[psicopedagogo_id], backref=db.backref('triagens', lazy=True))


class PlanoAcompanhamento(BaseModel):
    __tablename__ = 'planos_acompanhamento'

    aluno_id = db.Column(db.BigInteger, db.ForeignKey('alunos.id'), nullable=False)
    psicopedagogo_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    titulo = db.Column(db.String(180), nullable=False)
    objetivo_geral = db.Column(db.Text)
    estrategias = db.Column(db.Text)
    periodicidade = db.Column(db.String(60))
    status = db.Column(db.String(30), nullable=False, default='ativo')
    data_inicio = db.Column(db.Date)
    data_fim_prevista = db.Column(db.Date)
    data_fim_real = db.Column(db.Date)

    aluno = db.relationship('Aluno', backref=db.backref('planos_acompanhamento', lazy=True))
    psicopedagogo = db.relationship('Usuario', foreign_keys=[psicopedagogo_id], backref=db.backref('planos_acompanhamento', lazy=True))


class PlanoMeta(BaseModel):
    __tablename__ = 'plano_metas'

    plano_id = db.Column(db.BigInteger, db.ForeignKey('planos_acompanhamento.id', ondelete='CASCADE'), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    indicador_sucesso = db.Column(db.Text)
    prazo = db.Column(db.Date)
    status = db.Column(db.String(30), nullable=False, default='pendente')
    ordem = db.Column(db.Integer, nullable=False, default=1)


class Encaminhamento(BaseModel):
    __tablename__ = 'encaminhamentos'

    aluno_id = db.Column(db.BigInteger, db.ForeignKey('alunos.id'), nullable=False)
    solicitante_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    destino = db.Column(db.String(140), nullable=False)
    prioridade = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(30), nullable=False, default='aberto')
    descricao = db.Column(db.Text, nullable=False)
    prazo_retorno = db.Column(db.Date)
    data_retorno = db.Column(db.Date)
    observacao_retorno = db.Column(db.Text)

    aluno = db.relationship('Aluno', backref=db.backref('encaminhamentos', lazy=True))
    solicitante = db.relationship('Usuario', foreign_keys=[solicitante_id], backref=db.backref('encaminhamentos', lazy=True))


class Relatorio(BaseModel):
    __tablename__ = 'relatorios'

    unidade_id = db.Column(db.BigInteger, db.ForeignKey('unidades.id'))
    aluno_id = db.Column(db.BigInteger, db.ForeignKey('alunos.id'))
    autor_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id'), nullable=False)
    tipo = db.Column(db.String(40), nullable=False)
    origem = db.Column(db.String(20), nullable=False, default='manual')
    ano_referencia = db.Column(db.Integer)
    periodo_inicio = db.Column(db.Date)
    periodo_fim = db.Column(db.Date)
    titulo = db.Column(db.String(180), nullable=False)
    conteudo = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='rascunho')

    unidade = db.relationship('Unidade', backref=db.backref('relatorios', lazy=True))
    aluno = db.relationship('Aluno', backref=db.backref('relatorios', lazy=True))
    autor = db.relationship('Usuario', foreign_keys=[autor_id], backref=db.backref('relatorios', lazy=True))


class Auditoria(BaseModel):
    __tablename__ = 'auditoria'

    usuario_id = db.Column(db.BigInteger, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    acao = db.Column(db.String(40), nullable=False)
    entidade = db.Column(db.String(80), nullable=False)
    entidade_id = db.Column(db.BigInteger)
    detalhes = db.Column(JSONB)
    ip_origem = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())


class ParametroSistema(BaseModel):
    __tablename__ = 'parametros_sistema'

    chave = db.Column(db.String(120), nullable=False, unique=True)
    valor_json = db.Column(JSONB, nullable=False)
    descricao = db.Column(db.Text)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())
